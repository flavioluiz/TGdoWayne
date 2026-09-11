#!/usr/bin/env python3
"""Sequential campaign orchestration; numerical failures remain in the products."""
from pathlib import Path
import argparse, contextlib, fcntl, importlib, json, os, shutil, sys, time
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from inference.campaign_runtime import CampaignRuntime
from inference.campaign_training import train_block
from inference.campaign_iid import produce_target, release_raw
from inference.campaign_diagnostics import diagnose_target
from inference.campaign_archive import prepare_archive, verify_archive_receipt
from inference.campaign_io import read_json, sha256, canonical_hash, write_json_new, atomic_new


def extra_sources():
    paths={'driver':Path(__file__).resolve()}
    for name in ('campaign_diagnostics','campaign_diagnostic_io','iid_optimized','iid_diagnostics'):
        paths[name]=Path(importlib.import_module('inference.'+name).__file__).resolve()
    return paths


def campaign_plan(runtime, protocol_path, truth_data_path, truth_logl_path, output, *, engineering=False):
    plan=runtime.preflight(); ids=np.asarray(runtime.targets)
    if not engineering and (runtime.n!=500 or not np.array_equal(ids,np.arange(2500))):
        raise ValueError('The production driver requires all2500 model-major targets; use explicit --engineering for a separate trial.')
    if len(ids)!=len(set(ids.tolist())):raise ValueError('Duplicate targets in campaign.')
    protocol=read_json(protocol_path)
    if protocol['population_targets']!=len(ids) or protocol['levels']!=plan['levels'] or protocol['independent_replications']!=4:
        raise ValueError('Diagnostic family/levels do not match the full planned target set.')
    if protocol.get('global_replicate_contrasts',204*len(ids))!=204*len(ids) or protocol.get('global_refinement_contrasts',7*len(ids))!=7*len(ids):
        raise ValueError('Numerical contrast family count differs.')
    if sha256(truth_data_path)!=runtime.input_hashes['data']:raise RuntimeError('Diagnostic truth data differs from observation data.')
    extra_inputs={k:sha256(p) for k,p in dict(protocol=protocol_path,truth_data=truth_data_path,truth_logl=truth_logl_path).items()}
    sources={k:sha256(p) for k,p in extra_sources().items()}
    identity=canonical_hash(dict(runtime_identity=runtime.identity,extra_input_sha256=extra_inputs,driver_source_sha256=sources,engineering=engineering))
    output=Path(output).resolve();existing=output
    while not existing.exists():existing=existing.parent
    reserve=runtime.settings['budget']['maximum_active_raw_bytes']+len(ids)*1024**2+512*1024**2
    available=shutil.disk_usage(existing).free
    if reserve>available:raise RuntimeError('Insufficient filesystem space for bounded raw plus conservative compact archives.')
    plan.update(driver_identity=identity,scope='ENGINEERING_ONLY' if engineering else 'PRIOR_PREDICTIVE500_POSTERIOR_NUMERICS',extra_input_sha256=extra_inputs,driver_source_sha256=sources,
        output=str(output),all_target_ids=ids.tolist(),free_disk_bytes=available,minimum_free_disk_bytes=reserve,
        raw_strategy='One target at a time; preserve numerical failures before raw retirement',
        truth_deserialized_during_preflight=False,numerical_uniformity_is_not_a_stopping_rule=True)
    return plan


@contextlib.contextmanager
def campaign_lock(output):
    output.mkdir(parents=True,exist_ok=True)
    with (output/'.campaign.lock').open('a+b') as lock:
        try:fcntl.flock(lock.fileno(),fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError as exc:raise RuntimeError('Another driver owns this campaign output.') from exc
        try:yield
        finally:fcntl.flock(lock.fileno(),fcntl.LOCK_UN)


class Ledger:
    """Exclusive-writer immutable reservations; abandoned calls spend their cap."""
    def __init__(self,root,identity,budget):
        self.root=Path(root);self.root.mkdir(parents=True,exist_ok=True);self.identity=identity;self.budget=budget
    def totals(self):
        result=dict(training=0,production=0,other=0,unclosed_reservations=0)
        intents=sorted(self.root.glob('event_*.intent.json'))
        if [p.name for p in intents]!=[f'event_{i:06d}.intent.json' for i in range(len(intents))]:raise RuntimeError('Ledger reservation sequence has a gap.')
        if any(not p.with_name(p.name.replace('.end.json','.intent.json')).exists() for p in self.root.glob('event_*.end.json')):raise RuntimeError('Ledger completion has no reservation.')
        for path in intents:
            event=read_json(path)
            if event['driver_identity']!=self.identity:raise RuntimeError('Ledger identity changed.')
            end=path.with_name(path.name.replace('.intent.json','.end.json'))
            if end.exists():
                final=read_json(end)
                if final['intent_sha256']!=sha256(path) or final['likelihood_evaluations']>event['reserved_likelihood_values'] or final['likelihood_evaluations']<0:raise RuntimeError('Ledger completion differs from its reservation.')
                used=final['likelihood_evaluations']
            else:used=event['reserved_likelihood_values'];result['unclosed_reservations']+=1
            result[event['kind']]+=used
        result['total']=result['training']+result['production']+result['other'];return result
    def call(self,runtime,kind,reserved,stage,targets,function):
        used=self.totals(); reserved=int(reserved)
        limits={'training':'maximum_training_likelihood_values','production':'maximum_production_likelihood_values'}
        if reserved<0 or used['total']+reserved>self.budget['maximum_total_likelihood_values'] or (kind in limits and used[kind]+reserved>self.budget[limits[kind]]):
            raise RuntimeError('Campaign ledger likelihood budget exceeded before '+stage)
        seq=len(list(self.root.glob('event_*.intent.json')))
        path=self.root/f'event_{seq:06d}.intent.json'
        event=dict(driver_identity=self.identity,kind=kind,stage=stage,targets=list(map(int,targets)),reserved_likelihood_values=reserved)
        write_json_new(path,event);before=runtime.likelihood_evaluations;start=time.perf_counter()
        try:
            value=function();actual=runtime.likelihood_evaluations-before
            if actual>reserved:raise RuntimeError('Actual likelihood evaluations exceeded the pre-call reservation.')
        except BaseException as exc:
            write_json_new(path.with_name(path.name.replace('.intent.json','.end.json')),dict(intent_sha256=sha256(path),status='COMPUTATIONAL_OR_INTEGRITY_FAILURE',likelihood_evaluations=runtime.likelihood_evaluations-before,seconds=time.perf_counter()-start,error_type=type(exc).__name__,error=str(exc)))
            raise
        write_json_new(path.with_name(path.name.replace('.intent.json','.end.json')),dict(intent_sha256=sha256(path),status='COMPLETED',likelihood_evaluations=actual,seconds=time.perf_counter()-start))
        return value


def verify_done(path, output, plan):
    row=read_json(path)
    if row['driver_identity']!=plan['driver_identity'] or row['status']!='TARGET_ARCHIVED':raise RuntimeError('Completed target identity changed.')
    for artifact in row['artifacts']:
        relative=Path(artifact['file']);p=(output/relative).resolve()
        if relative.is_absolute() or output not in p.parents or sha256(p)!=artifact['sha256']:raise RuntimeError('Completed target artifact changed.')
    production=read_json(output/'production'/f'target_{row["target"]:06d}.json')
    verify_archive_receipt(output/'production'/f'archive_receipt_target_{row["target"]:06d}.json',output/'production',plan['identity'],row['target'],{r['raw_file']:r['raw_sha256'] for r in production['replicates']})
    if any((output/'raw'/r['raw_file']).exists() for r in production['replicates']):raise RuntimeError('A completed retired target unexpectedly has raw files.')
    return row


def snapshot_driver(runtime,output,plan,protocol_path,truth_logl_path):
    runtime.snapshot(output)
    root=output/'driver_provenance'/plan['driver_identity']
    for name,path in extra_sources().items():
        target=root/(name+'.py')
        if target.exists():
            if sha256(target)!=plan['driver_source_sha256'][name]:raise RuntimeError('Driver snapshot collision.')
        else:atomic_new(target,lambda p,path=path:p.write_bytes(path.read_bytes()))
    for name,path in [('protocol',Path(protocol_path)),('truth_logl',Path(truth_logl_path))]:
        target=root/(name+'.json')
        if target.exists():
            if sha256(target)!=plan['extra_input_sha256'][name]:raise RuntimeError('Diagnostic input snapshot changed.')
        else:atomic_new(target,lambda p,path=path:p.write_bytes(path.read_bytes()))


def run_campaign(runtime,plan,protocol_path,truth_data_path,truth_logl_path,output,*,resume=False,operations=None):
    """Single runtime, trained proposal blocks and strictly sequential raw lifecycle."""
    output=Path(output).resolve();ops=operations or dict(train=train_block,produce=produce_target,diagnose=diagnose_target,archive=prepare_archive,release=release_raw)
    if not plan['execution_ready']:raise RuntimeError('Prospective execution is disabled or pending.')
    started=time.perf_counter()
    with campaign_lock(output):
        manifest=output/'campaign_plan.json'
        if manifest.exists():
            if not resume or read_json(manifest)['driver_identity']!=plan['driver_identity']:raise RuntimeError('Existing campaign requires --resume with identical frozen inputs/sources.')
        else:
            if not resume and any((output/name).exists() for name in ('proposals','production','diagnostics','state','ledger')):raise RuntimeError('Existing stage outputs require an identified resumed campaign.')
            write_json_new(manifest,plan)
        snapshot_driver(runtime,output,plan,protocol_path,truth_logl_path)
        ledger=Ledger(output/'ledger',plan['driver_identity'],runtime.settings['budget'])
        state=output/'state';state.mkdir(parents=True,exist_ok=True);done={}
        for path in state.glob('target_*.json'):
            row=verify_done(path,output,plan)
            if row['target'] not in plan['all_target_ids'] or row['target'] in done:raise RuntimeError('Unplanned/duplicate completed target.')
            done[row['target']]=row
        # Pre-start replay budget includes previous failed calls and unresolved
        # reservations; no restart silently resets the campaign-wide cap.
        remaining=[t for t in plan['all_target_ids'] if t not in done]
        missing=sum(not (output/'proposals'/f'target_{t:06d}.json').exists() for t in remaining)
        minimum_training=(runtime.settings['training']['steps']+1)*4*missing
        levels=runtime.settings['production']['levels']
        minimum_production=sum(n for t in remaining if not (output/'production'/f'target_{t:06d}.json').exists() for n in levels for r in range(4) if not (output/'production'/f'target_{t:06d}_N{n}_rep_{r:02d}.json').exists())
        spent=ledger.totals();budget=runtime.settings['budget']
        if spent['training']+minimum_training>budget['maximum_training_likelihood_values'] or spent['production']+minimum_production>budget['maximum_production_likelihood_values'] or spent['total']+minimum_training+minimum_production>budget['maximum_total_likelihood_values']:
            raise RuntimeError('Remaining campaign plus recorded/replay-reserved work exceeds its budget before restart.')
        if sum(p.stat().st_size for p in (output/'raw').glob('target_*.npz'))>budget['maximum_active_raw_bytes']:
            raise RuntimeError('Existing raw already exceeds the declared active-raw budget.')
        attempt=len(list(state.glob('attempt_*.start.json')))
        write_json_new(state/f'attempt_{attempt:04d}.start.json',dict(driver_identity=plan['driver_identity'],completed_targets=sorted(done),ledger=ledger.totals()))
        def progress(event,**fields):print(json.dumps(dict(event=event,**fields)),flush=True)
        try:
            for block_index,block in enumerate(plan['training_blocks']):
                pending=[int(t) for t in block if int(t) not in done]
                if not pending:continue
                progress('block_started',block=block_index,targets=pending,completed=len(done))
                new_proposals=[t for t in pending if not (output/'proposals'/f'target_{t:06d}.json').exists()]
                reserve=(runtime.settings['training']['steps']+1)*4*len(new_proposals)
                ledger.call(runtime,'training',reserve,'train',pending,lambda:ops['train'](runtime,pending,output/'proposals',resume=resume))
                for target in pending:
                    levels=runtime.settings['production']['levels']
                    production_path=output/'production'/f'target_{target:06d}.json'
                    reserve=0 if production_path.exists() else sum(n for n in levels for r in range(4) if not (output/'production'/f'target_{target:06d}_N{n}_rep_{r:02d}.json').exists())
                    ledger.call(runtime,'production',reserve,'produce',[target],lambda:ops['produce'](runtime,target,output/'proposals',output/'production',output/'raw',resume=resume))
                    diagnostic_path=output/'diagnostics'/f'diagnostic_target_{target:06d}.json'
                    diagnostic=ledger.call(runtime,'other',0,'diagnose',[target],lambda:ops['diagnose'](runtime,production_path,output/'raw',truth_data_path,protocol_path,output/'diagnostics',truth_loglikelihood_path=truth_logl_path,resume=resume))
                    archive=ledger.call(runtime,'other',0,'archive',[target],lambda:ops['archive'](runtime,target,output/'proposals',output/'production',diagnostic_path,resume=resume))
                    receipt=output/'production'/f'archive_receipt_target_{target:06d}.json'
                    ledger.call(runtime,'other',0,'release',[target],lambda:ops['release'](runtime,target,output/'production',output/'raw',receipt,resume=resume))
                    files=[production_path,diagnostic_path,output/'diagnostics'/diagnostic['numeric_file'],receipt,output/'production'/f'released_target_{target:06d}.json']
                    row=dict(status='TARGET_ARCHIVED',driver_identity=plan['driver_identity'],target=target,model=archive['model'],datum=archive['datum'],numerical_status=archive['numerical_status'],numerical_flags=archive['numerical_flags'],artifacts=[dict(file=str(p.relative_to(output)),sha256=sha256(p)) for p in files],no_scientific_calibration_claim=True)
                    write_json_new(state/f'target_{target:06d}.json',row);done[target]=row
                block_summary=dict(driver_identity=plan['driver_identity'],block=block_index,targets=pending,completed_total=len(done),unresolved_total=sum(r['numerical_status']=='NUMERICALLY_UNRESOLVED' for r in done.values()),ledger=ledger.totals(),seconds_since_attempt_start=time.perf_counter()-started)
                write_json_new(state/f'attempt_{attempt:04d}_block_{block_index:04d}.json',block_summary);progress('block_completed',**{k:v for k,v in block_summary.items() if k!='driver_identity'})
                runtime.verify_unchanged()
                if any(sha256(p)!=plan['driver_source_sha256'][k] for k,p in extra_sources().items()) or sha256(protocol_path)!=plan['extra_input_sha256']['protocol'] or sha256(truth_logl_path)!=plan['extra_input_sha256']['truth_logl']:raise RuntimeError('Driver/diagnostic inputs changed during campaign.')
            if sorted(done)!=sorted(plan['all_target_ids']):raise RuntimeError('Campaign target inventory is incomplete.')
            result=dict(status='ALL_TARGET_PRODUCTS_ARCHIVED',driver_identity=plan['driver_identity'],targets=sorted(done),numerically_unresolved_targets=[t for t in sorted(done) if done[t]['numerical_status']=='NUMERICALLY_UNRESOLVED'],ledger=ledger.totals(),seconds=time.perf_counter()-started,no_SBC_uniformity_claim=True)
            final=output/'campaign_complete.json'
            if final.exists():
                old=read_json(final)
                if old['driver_identity']!=plan['driver_identity'] or old['targets']!=result['targets']:raise RuntimeError('Completed campaign identity changed.')
                write_json_new(state/f'attempt_{attempt:04d}.end.json',dict(status='COMPLETED_ALREADY_VERIFIED',ledger=ledger.totals(),completed=len(done)))
                return old
            write_json_new(final,result);write_json_new(state/f'attempt_{attempt:04d}.end.json',dict(status='COMPLETED',ledger=ledger.totals(),completed=len(done)));return result
        except BaseException as exc:
            write_json_new(state/f'attempt_{attempt:04d}.end.json',dict(status='STOPPED_COMPUTATIONAL_OR_INTEGRITY_ERROR',completed_targets=sorted(done),ledger=ledger.totals(),error_type=type(exc).__name__,error=str(exc)))
            raise


def main():
    parser=argparse.ArgumentParser()
    for name in ('experiment','data','table','table_manifest','validation_config','run_config','protocol','truth_data','truth_logl','output'):
        parser.add_argument('--'+name.replace('_','-'),type=Path,required=True)
    parser.add_argument('--native-library',type=Path);parser.add_argument('--native-build-manifest',type=Path)
    parser.add_argument('--backend-factory');parser.add_argument('--training-threads',type=int,default=1);parser.add_argument('--threads',type=int,default=1)
    parser.add_argument('--engineering',action='store_true');parser.add_argument('--execute',action='store_true');parser.add_argument('--resume',action='store_true');parser.add_argument('--plan-file',type=Path)
    args=parser.parse_args()
    runtime=CampaignRuntime(args.experiment,args.data,args.table,args.table_manifest,args.validation_config,args.run_config,backend_factory=args.backend_factory,threads=args.threads,training_threads=args.training_threads,native_library_path=args.native_library,native_build_manifest_path=args.native_build_manifest)
    try:
        plan=campaign_plan(runtime,args.protocol,args.truth_data,args.truth_logl,args.output,engineering=args.engineering)
        if args.plan_file:write_json_new(args.plan_file,plan)
        print(json.dumps({k:v for k,v in plan.items() if k not in ('training_blocks','production_blocks','all_target_ids')}),flush=True)
        if not args.execute:return
        result=run_campaign(runtime,plan,args.protocol,args.truth_data,args.truth_logl,args.output,resume=args.resume)
        print(json.dumps(result),flush=True)
    finally:runtime.close()

if __name__=='__main__':main()
