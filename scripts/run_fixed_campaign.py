#!/usr/bin/env python3
"""Fixed96 A0 lifecycle using ROOT producer/runtime/archive unchanged.

Generation is an explicit masked-diagnostic input. No truth-logL CLI or fake
truth-logL metadata is used. Default is preflight, not posterior execution.
"""
from pathlib import Path
import argparse,importlib,importlib.util,json,shutil,sys,time
import numpy as np

BASE=None;MASKED=None


def initialize(project_root,masked_module_path=None):
    global BASE,MASKED,CampaignRuntime,train_block,produce_target,release_raw,prepare_archive
    global read_json,sha256,canonical_hash,write_json_new,atomic_new
    root=Path(project_root).resolve();sys.path.insert(0,str(root/'src'))
    spec=importlib.util.spec_from_file_location('fixed_campaign_base',root/'scripts/run_calibration_campaign.py')
    BASE=importlib.util.module_from_spec(spec);spec.loader.exec_module(BASE)
    if masked_module_path is None:MASKED=importlib.import_module('inference.fixed_diagnostics_v2')
    else:
        spec=importlib.util.spec_from_file_location('inference.fixed_diagnostics_v2',Path(masked_module_path).resolve())
        MASKED=importlib.util.module_from_spec(spec);sys.modules[spec.name]=MASKED;spec.loader.exec_module(MASKED)
    from inference.campaign_runtime import CampaignRuntime
    from inference.campaign_training import train_block
    from inference.campaign_iid import produce_target,release_raw
    from inference.campaign_archive import prepare_archive
    from inference.campaign_io import read_json,sha256,canonical_hash,write_json_new,atomic_new


def extra_sources():
    if BASE is None or MASKED is None:raise RuntimeError('Initialize explicit project and masked-reader sources first.')
    paths={'fixed_driver':Path(__file__).resolve(),'base_driver':Path(BASE.__file__).resolve(),
           'fixed_masked_reader':Path(MASKED.__file__).resolve()}
    for name in ('campaign_diagnostic_io','iid_optimized','iid_diagnostics','campaign_archive','campaign_iid'):
        paths[name]=Path(importlib.import_module('inference.'+name).__file__).resolve()
    return paths


def fixed_plan(runtime,protocol_path,truth_data_path,generation_path,output):
    plan=runtime.preflight();ids=np.asarray(runtime.targets)
    if runtime.n!=96 or not np.array_equal(ids,np.arange(96)) or runtime.settings['models']!=['A0_CN']:
        raise ValueError('The fixed driver requires all96 A0 targets0..95, exactly once.')
    protocol=read_json(protocol_path);generation=read_json(generation_path)
    if (protocol['population_targets']!=96 or protocol['models']!=['A0_CN'] or
        protocol['levels']!=plan['levels'] or protocol['independent_replications']!=4 or
        protocol['global_replicate_contrasts']!=204*96 or protocol['global_refinement_contrasts']!=7*96):
        raise ValueError('Fixed diagnostic levels/families differ from the full96 target plan.')
    digest=sha256(truth_data_path)
    if (digest!=runtime.input_hashes['data'] or digest!=generation['data_sha256'] or
        generation['status']!='FIXED_DATA_GENERATED_NOT_POSTERIOR_INFERENCE' or
        generation['preflight']['experiment_sha256']!=runtime.input_hashes['experiment'] or
        generation['truth_defined_per_parameter']!=[64,64,64,96,96] or
        generation['defined_signal_model_logL_at_truth']!=64 or generation['row_ranges']!=[[0,31],[32,63],[64,95]]):
        raise RuntimeError('Generation/data/configuration or declared mask inventory differs from fixed96.')
    inputs={k:sha256(p) for k,p in dict(protocol=protocol_path,truth_data=truth_data_path,generation=generation_path).items()}
    sources={k:sha256(p) for k,p in extra_sources().items()}
    identity=canonical_hash(dict(runtime_identity=runtime.identity,scope='FIXED_TRUTH96_NOT_SBC',
        extra_input_sha256=inputs,driver_source_sha256=sources,
        masked_schema='C07_FIXED_MASKED_IID_DIAGNOSTICS_v2_OPERATIONAL'))
    output=Path(output).resolve();existing=output
    while not existing.exists():existing=existing.parent
    reserve=runtime.settings['budget']['maximum_active_raw_bytes']+96*1024**2+512*1024**2
    available=shutil.disk_usage(existing).free
    if reserve>available:raise RuntimeError('Insufficient disk for bounded raw and complete fixed96 archives.')
    plan.update(driver_identity=identity,scope='FIXED_TRUTH96_NOT_SBC',extra_input_sha256=inputs,
        driver_source_sha256=sources,output=str(output),all_target_ids=ids.tolist(),
        free_disk_bytes=available,minimum_free_disk_bytes=reserve,
        numerical_replicate_family_maximum=19584,numerical_refinement_family_maximum=672,
        expected_executed_replicate_contrasts=17664,expected_executed_refinement_contrasts=512,
        raw_strategy='One target at a time; complete masked diagnostics and immutable archive before retirement',
        truth_deserialized_during_preflight=False,table_or_moment_bank_built_during_preflight=False,
        numerical_uniformity_is_not_a_stopping_rule=True)
    return plan


def snapshot_driver(runtime,output,plan,protocol_path,generation_path):
    runtime.snapshot(output);root=output/'driver_provenance'/plan['driver_identity']
    for name,path in extra_sources().items():
        if sha256(path)!=plan['driver_source_sha256'][name]:raise RuntimeError('Fixed driver source changed before snapshot.')
        target=root/(name+'.py')
        if target.exists():
            if sha256(target)!=plan['driver_source_sha256'][name]:raise RuntimeError('Fixed driver snapshot collision.')
        else:atomic_new(target,lambda p,path=path:p.write_bytes(path.read_bytes()))
    for name,path in [('protocol',Path(protocol_path)),('generation',Path(generation_path))]:
        if sha256(path)!=plan['extra_input_sha256'][name]:raise RuntimeError('Fixed input changed before snapshot.')
        target=root/(name+'.json')
        if target.exists():
            if sha256(target)!=plan['extra_input_sha256'][name]:raise RuntimeError('Fixed diagnostic input snapshot changed.')
        else:atomic_new(target,lambda p,path=path:p.write_bytes(path.read_bytes()))


def verify_extra_inputs(plan,protocol_path,truth_data_path,generation_path):
    if any(sha256(p)!=plan['driver_source_sha256'][k] for k,p in extra_sources().items()):
        raise RuntimeError('Fixed driver source changed after preflight.')
    for name,path in [('protocol',protocol_path),('truth_data',truth_data_path),('generation',generation_path)]:
        if sha256(path)!=plan['extra_input_sha256'][name]:raise RuntimeError('Fixed diagnostic input changed: '+name)


def run_fixed_campaign(runtime,plan,protocol_path,truth_data_path,generation_path,output,*,resume=False,operations=None):
    """Same bounded lifecycle as ROOT driver; reuse its lock, ledger and done verifier."""
    ops=operations or dict(train=train_block,produce=produce_target,diagnose=MASKED.diagnose_fixed_target,
                          archive=prepare_archive,release=release_raw)
    output=Path(output).resolve()
    if not plan['execution_ready']:raise RuntimeError('Fixed posterior execution remains disabled or pending.')
    if plan['scope']!='FIXED_TRUTH96_NOT_SBC':raise ValueError('Explicit fixed96 scope required.')
    verify_extra_inputs(plan,protocol_path,truth_data_path,generation_path)
    started=time.perf_counter()
    with BASE.campaign_lock(output):
        manifest=output/'campaign_plan.json'
        if manifest.exists():
            if not resume or read_json(manifest)['driver_identity']!=plan['driver_identity']:
                raise RuntimeError('Existing fixed campaign requires resume with identical sources/inputs.')
        else:
            if not resume and any((output/n).exists() for n in ('proposals','production','diagnostics','state','ledger')):
                raise RuntimeError('Existing fixed stages require an identified resume.')
            write_json_new(manifest,plan)
        snapshot_driver(runtime,output,plan,protocol_path,generation_path)
        ledger=BASE.Ledger(output/'ledger',plan['driver_identity'],runtime.settings['budget'])
        state=output/'state';state.mkdir(parents=True,exist_ok=True);done={}
        for path in state.glob('target_*.json'):
            row=BASE.verify_done(path,output,plan)
            if row['target'] not in plan['all_target_ids'] or row['target'] in done:raise RuntimeError('Unplanned/duplicate target.')
            done[row['target']]=row
        remaining=[t for t in plan['all_target_ids'] if t not in done]
        missing=sum(not (output/'proposals'/f'target_{t:06d}.json').exists() for t in remaining)
        training_min=(runtime.settings['training']['steps']+1)*4*missing
        levels=runtime.settings['production']['levels']
        production_min=sum(n for t in remaining if not (output/'production'/f'target_{t:06d}.json').exists()
            for n in levels for r in range(4) if not (output/'production'/f'target_{t:06d}_N{n}_rep_{r:02d}.json').exists())
        spent=ledger.totals();budget=runtime.settings['budget']
        if (spent['training']+training_min>budget['maximum_training_likelihood_values'] or
            spent['production']+production_min>budget['maximum_production_likelihood_values'] or
            spent['total']+training_min+production_min>budget['maximum_total_likelihood_values']):
            raise RuntimeError('Remaining fixed campaign plus prior/replay-reserved work exceeds its ledger budget.')
        if sum(p.stat().st_size for p in (output/'raw').glob('target_*.npz'))>budget['maximum_active_raw_bytes']:
            raise RuntimeError('Existing raw exceeds the declared quota.')
        attempt=len(list(state.glob('attempt_*.start.json')))
        write_json_new(state/f'attempt_{attempt:04d}.start.json',dict(driver_identity=plan['driver_identity'],completed_targets=sorted(done),ledger=ledger.totals()))
        try:
            for block_index,block in enumerate(plan['training_blocks']):
                pending=[int(t) for t in block if int(t) not in done]
                if not pending:continue
                print(json.dumps(dict(event='fixed_block_started',block=block_index,targets=pending)),flush=True)
                new=[t for t in pending if not (output/'proposals'/f'target_{t:06d}.json').exists()]
                reserve=(runtime.settings['training']['steps']+1)*4*len(new)
                ledger.call(runtime,'training',reserve,'train',pending,lambda:ops['train'](runtime,pending,output/'proposals',resume=resume))
                for target in pending:
                    production=output/'production'/f'target_{target:06d}.json'
                    reserve=0 if production.exists() else sum(n for n in levels for r in range(4)
                        if not (output/'production'/f'target_{target:06d}_N{n}_rep_{r:02d}.json').exists())
                    ledger.call(runtime,'production',reserve,'produce',[target],lambda:ops['produce'](runtime,target,output/'proposals',output/'production',output/'raw',resume=resume))
                    diagnostic_path=output/'diagnostics'/f'diagnostic_target_{target:06d}.json'
                    diagnostic=ledger.call(runtime,'other',0,'diagnose_fixed',[target],lambda:ops['diagnose'](
                        runtime,production,output/'raw',truth_data_path,generation_path,protocol_path,output/'diagnostics',resume=resume))
                    if (diagnostic['status']!='NUMERICAL_DIAGNOSTICS_COMPLETE' or
                        diagnostic['schema']!='C07_FIXED_MASKED_IID_DIAGNOSTICS_v2_OPERATIONAL' or
                        diagnostic['scope']!='FIXED_TRUTH96_NOT_SBC' or
                        diagnostic['diagnostic_inputs']['generation_sha256']!=plan['extra_input_sha256']['generation']):
                        raise RuntimeError('Wrong diagnostic scope/schema/generation; fixed masked product required before archive.')
                    verify_extra_inputs(plan,protocol_path,truth_data_path,generation_path)
                    archive=ledger.call(runtime,'other',0,'archive',[target],lambda:ops['archive'](runtime,target,output/'proposals',output/'production',diagnostic_path,resume=resume))
                    receipt=output/'production'/f'archive_receipt_target_{target:06d}.json'
                    ledger.call(runtime,'other',0,'release',[target],lambda:ops['release'](runtime,target,output/'production',output/'raw',receipt,resume=resume))
                    files=[production,diagnostic_path,output/'diagnostics'/diagnostic['numeric_file'],receipt,output/'production'/f'released_target_{target:06d}.json']
                    row=dict(status='TARGET_ARCHIVED',driver_identity=plan['driver_identity'],target=target,
                        model=archive['model'],datum=archive['datum'],numerical_status=archive['numerical_status'],
                        numerical_flags=archive['numerical_flags'],artifacts=[dict(file=str(p.relative_to(output)),sha256=sha256(p)) for p in files],
                        no_scientific_calibration_claim=True,fixed_masked_scope_preserved=True)
                    write_json_new(state/f'target_{target:06d}.json',row);done[target]=row
                summary=dict(driver_identity=plan['driver_identity'],block=block_index,targets=pending,completed_total=len(done),
                    unresolved_total=sum(r['numerical_status']=='NUMERICALLY_UNRESOLVED' for r in done.values()),ledger=ledger.totals(),seconds=time.perf_counter()-started)
                write_json_new(state/f'attempt_{attempt:04d}_block_{block_index:04d}.json',summary)
                runtime.verify_unchanged()
                if (any(sha256(p)!=plan['driver_source_sha256'][k] for k,p in extra_sources().items()) or
                    sha256(protocol_path)!=plan['extra_input_sha256']['protocol'] or
                    sha256(generation_path)!=plan['extra_input_sha256']['generation']):
                    raise RuntimeError('Fixed driver/diagnostic inputs changed during campaign.')
            if sorted(done)!=sorted(plan['all_target_ids']):raise RuntimeError('Incomplete fixed target inventory.')
            ledger.totals(audit=True)
            result=dict(status='ALL_TARGET_PRODUCTS_ARCHIVED',scope='FIXED_TRUTH96_NOT_SBC',driver_identity=plan['driver_identity'],
                targets=sorted(done),numerically_unresolved_targets=[t for t in sorted(done) if done[t]['numerical_status']=='NUMERICALLY_UNRESOLVED'],
                ledger=ledger.totals(),seconds=time.perf_counter()-started,no_SBC_uniformity_claim=True)
            final=output/'campaign_complete.json'
            if final.exists():
                old=read_json(final)
                if old['driver_identity']!=plan['driver_identity'] or old['targets']!=result['targets']:raise RuntimeError('Completed identity changed.')
                write_json_new(state/f'attempt_{attempt:04d}.end.json',dict(status='COMPLETED_ALREADY_VERIFIED',ledger=ledger.totals(),completed=len(done)));return old
            write_json_new(final,result)
            write_json_new(state/f'attempt_{attempt:04d}.end.json',dict(status='COMPLETED',ledger=ledger.totals(),completed=len(done)));return result
        except BaseException as exc:
            write_json_new(state/f'attempt_{attempt:04d}.end.json',dict(status='STOPPED_COMPUTATIONAL_OR_INTEGRITY_ERROR',
                completed_targets=sorted(done),ledger=ledger.totals(),error_type=type(exc).__name__,error=str(exc)));raise


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--project-root',type=Path,default=Path(__file__).resolve().parents[1])
    p.add_argument('--masked-module-path',type=Path,help='Explicit candidate for review; omit after integration.')
    for name in ('experiment','data','table','table_manifest','validation_config','run_config','protocol','truth_data','generation','output'):
        p.add_argument('--'+name.replace('_','-'),type=Path,required=True)
    p.add_argument('--native-library',type=Path);p.add_argument('--native-build-manifest',type=Path);p.add_argument('--backend-factory')
    p.add_argument('--training-threads',type=int,default=1);p.add_argument('--threads',type=int,default=1)
    p.add_argument('--execute',action='store_true');p.add_argument('--resume',action='store_true');p.add_argument('--plan-file',type=Path)
    a=p.parse_args();initialize(a.project_root,a.masked_module_path)
    runtime=CampaignRuntime(a.experiment,a.data,a.table,a.table_manifest,a.validation_config,a.run_config,
        backend_factory=a.backend_factory,threads=a.threads,training_threads=a.training_threads,
        native_library_path=a.native_library,native_build_manifest_path=a.native_build_manifest)
    try:
        plan=fixed_plan(runtime,a.protocol,a.truth_data,a.generation,a.output)
        if a.plan_file:write_json_new(a.plan_file,plan)
        print(json.dumps({k:v for k,v in plan.items() if k not in ('training_blocks','production_blocks','all_target_ids')}),flush=True)
        if not a.execute:return
        print(json.dumps(run_fixed_campaign(runtime,plan,a.protocol,a.truth_data,a.generation,a.output,resume=a.resume)),flush=True)
    finally:runtime.close()


if __name__=='__main__':main()
