#!/usr/bin/env python3
"""Budgeted fixed96 observations only; no posterior table, training or inference."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import sys
import tempfile
import time


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('action',choices=['preflight','build-orfs','generate','verify'])
    p.add_argument('--project-root',type=Path,default=Path(__file__).resolve().parents[1])
    p.add_argument('--experiment',type=Path,required=True)
    p.add_argument('--protocol',type=Path,required=True)
    p.add_argument('--generation-config',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--implementation-path',type=Path,
                   help='Explicit candidate module for pre-integration review; omitted after integration.')
    args=p.parse_args();root=args.project_root.resolve();sys.path.insert(0,str(root/'src'))
    import numpy as np
    import scipy
    import inference
    if args.implementation_path:
        spec=importlib.util.spec_from_file_location('inference.fixed_generation',args.implementation_path.resolve())
        module=importlib.util.module_from_spec(spec);sys.modules[spec.name]=module;spec.loader.exec_module(module)
    from inference.fixed_generation import validate_design,generate_fixed_fixture
    from inference.model import experiment
    from inference.data_generation import StoredExactORF
    from inference.orf_backend import ExactNodeORF
    from inference.orf_blas import estimate
    from inference.orf_table_builder import build_checked_nodes,ConstructionBudget,token
    from inference.campaign_io import write_npz_new,write_json_new,load_observations
    from pta.orf import raw_direct_orf
    cfg=json.loads(args.experiment.read_text());protocol=json.loads(args.protocol.read_text())
    settings=json.loads(args.generation_config.read_text());exp=validate_design(cfg,protocol)
    base=experiment(json.loads((root/protocol['experiment_config']).read_text()))
    for k in ['points','distance_ly','sigma','red','T','dt','f','scale','H','weights']:
        if not np.array_equal(exp[k],base[k]):raise ValueError('Fixed generation changed C07 geometry/scaling: '+k)
    if cfg['orf'] != json.loads((root/protocol['experiment_config']).read_text())['orf']:
        raise ValueError('Physical ORF signature must remain the C07 signature.')
    masses=np.unique([r['truth'][0] for r in protocol['scenarios'] if r['signal_present']])
    if not np.array_equal(masses,settings['requested_signal_mass_nodes']) or len(masses)>3:
        raise ValueError('Only the two prescribed exact signal nodes may be generated.')
    budget=ConstructionBudget(**settings['construction_budget'])
    if budget.maximum_requested_nodes>3 or settings['maximum_requested_nodes']>3:
        raise ValueError('Three-node maximum cannot be enlarged by this fixed-data script.')
    with tempfile.TemporaryDirectory() as d:meta=ExactNodeORF(exp,cfg['orf'],d)
    K,P=len(exp['f']),len(exp['points']);N=len(masses)
    work=int(2*N*P*np.sum((meta.l-1)*meta.n+(meta.lf-1)*meta.nf))
    memory=int(16*N*(K+2)*P*P+8*N*K+max(estimate(int(l),int(n),P,N)['estimated_memory_bytes']
        for l,n in zip(np.r_[meta.l,meta.lf],np.r_[meta.n,meta.nf])))
    ds=settings['direct_checks']
    if ds['channels_zero_based'] != [0,3] or ds['low_frequency_pairs'] != [[3,8],[0,11]] or ds['high_frequency_pairs'] != [[3,8]]:
        raise ValueError('Predeclared fixed-scenario independent direct checks required.')
    if ds['absolute_tolerance'] != 1e-7:raise ValueError('Direct tolerance cannot be relaxed.')
    direct_work=int(N*(len(ds['low_frequency_pairs'])*2*meta.nf[0]**2+
                       len(ds['high_frequency_pairs'])*2*meta.nf[-1]**2))
    direct_memory=int(24*16*meta.nf[-1]*128+544*meta.nf[-1])
    if (work>budget.maximum_total_real_multiplications or memory>budget.maximum_estimated_numeric_memory_bytes or
        direct_work>ds['maximum_work_proxy'] or direct_memory>ds['maximum_estimated_memory_bytes']):
        raise RuntimeError('Explicit fixed-data ORF construction/direct-check budget exceeded.')
    preview=dict(realizations=96,scenarios=3,replications_each=32,exact_nodes=masses.tolist(),
        maximum_requested_nodes=3,estimated_numeric_bytes=memory,real_multiplications=work,
        direct_work_proxy=direct_work,direct_estimated_memory_bytes=direct_memory,
        maximum_phase=float(meta.y.max()),interpolation=False,posterior_execution=False,
        experiment_sha256=sha(args.experiment),protocol_sha256=sha(args.protocol),
        generation_config_sha256=sha(args.generation_config))
    if args.action=='preflight':print(json.dumps(preview,indent=2));return
    out=args.output.resolve();out.mkdir(parents=True,exist_ok=True);cache=out/'orf_cache'
    implementation=Path(sys.modules['inference.fixed_generation'].__file__).resolve()
    sources={'script':Path(__file__).resolve(),'implementation':implementation,
        'experiment':args.experiment.resolve(),'protocol':args.protocol.resolve(),
        'generation_config':args.generation_config.resolve(),
        'base_experiment':(root/protocol['experiment_config']).resolve()}
    for module_name in ['inference.model','inference.likelihood_reference','inference.data_generation',
        'inference.orf_backend','inference.orf_blas','inference.orf_table_builder','inference.campaign_io',
        'pta','pta.simulation','pta.statistics','pta.orf','pta.transfer','pta.response','pta.validation']:
        spec=importlib.util.find_spec(module_name)
        if spec is not None and spec.origin:sources[module_name]=Path(spec.origin)
    hashes={name:sha(path) for name,path in sources.items()}
    def unchanged():
        if any(sha(path)!=hashes[name] for name,path in sources.items()):
            raise RuntimeError('Frozen generation source changed during execution.')
    manifest_path=out/'orf_construction.json';started=time.perf_counter()
    if args.action=='build-orfs':
        if manifest_path.exists():raise FileExistsError('Preserve the existing construction manifest.')
        report=build_checked_nodes(exp,cfg['orf'],masses,cache,budget=budget,validate_direct=False)
        provider=StoredExactORF(exp,cfg['orf'],cache)
        matrices={float(u):provider.evaluate(float(u)) for u in masses}
        checks=[]
        for u in masses:
            for k,pairs in [(0,ds['low_frequency_pairs']),(3,ds['high_frequency_pairs'])]:
                beta=float(np.sqrt((1-u/(k+1))*(1+u/(k+1))))
                for a,b in pairs:
                    t=time.perf_counter();y=meta.y[k]
                    value=raw_direct_orf(beta,float(exp['points'][a]@exp['points'][b]),
                        y[a],y[b],nmu=int(meta.nf[k]),nphi=int(2*meta.nf[k]))
                    error=float(abs(value-matrices[float(u)][k,a,b]))
                    if not np.isfinite(error) or error>ds['absolute_tolerance']:
                        raise RuntimeError('Fixed-data independent direct ORF check failed.')
                    checks.append(dict(u=float(u),channel=k+1,pair=[a,b],
                        absolute_difference=error,nmu=int(meta.nf[k]),nphi=int(2*meta.nf[k]),
                        direct_real=float(value.real),direct_imag=float(value.imag),seconds=time.perf_counter()-t))
        unchanged()
        report.update(preflight=preview,source_sha256=hashes,fixed_scenario_direct_checks=checks,
            fixed_direct_status='PASS',checked_node_records=provider.records,
            direct_budget=ds,posterior_execution=False,interpolation=False,
            total_seconds_including_direct=time.perf_counter()-started)
        write_json_new(manifest_path,report)
        print(json.dumps({'status':'TWO_EXACT_NODES_CHECKED_NO_DATA_YET',
              'seconds':report['total_seconds_including_direct'],'max_direct_error':max(r['absolute_difference'] for r in checks)},indent=2));return
    construction=json.loads(manifest_path.read_text())
    if (construction['status']!='COMPLETE' or construction['fixed_direct_status']!='PASS' or
        construction['preflight']!=preview or construction['source_sha256']!=hashes or
        len(construction['fixed_scenario_direct_checks'])!=6):
        raise RuntimeError('Fixed-node construction provenance/checks do not match this generation.')
    for record in construction['checked_node_records']:
        if sha(cache/record['file'])!=record['sha256']:raise RuntimeError('Checked exact node changed.')
    data_path=out/'data.npz';report_path=out/'generation.json'
    if args.action=='generate' and (data_path.exists() or report_path.exists()):
        raise FileExistsError('Preserve the existing fixed observations; use verify.')
    provider=StoredExactORF(exp,cfg['orf'],cache)
    arrays=generate_fixed_fixture(cfg,protocol,provider);unchanged()
    if args.action=='verify':
        report=json.loads(report_path.read_text())
        if (report['source_sha256']!=hashes or report['data_sha256']!=sha(data_path) or
            report['orf_construction_sha256']!=sha(manifest_path)):
            raise RuntimeError('Fixed-generation identity or payload changed.')
        with np.load(data_path,allow_pickle=False) as saved:
            if set(saved.files)!=set(arrays):raise RuntimeError('Unexpected fixed-data schema.')
            for key,value in arrays.items():
                if not np.array_equal(value,saved[key],equal_nan=True):
                    raise RuntimeError('Fixed observation regeneration differs: '+key)
        load_observations(data_path,exp)
        write_json_new(out/'verification.json',dict(status='BIT_IDENTICAL_REGENERATION_96',
            source_sha256=hashes,data_sha256=sha(data_path),seconds=time.perf_counter()-started,
            no_new_posterior_execution=True))
        print('96 fixed observations regenerated bit-identically, including missing-truth masks.');return
    write_npz_new(data_path,**arrays)
    # Observation-only loader verifies compatibility without reading masked truth.
    loaded=load_observations(data_path,exp)
    if loaded['q'].shape!=(96,4,12):raise RuntimeError('Unexpected runtime observation shape.')
    snapshot=out/'executed_sources';snapshot.mkdir()
    for name,path in sources.items():
        destination=snapshot/(name.replace('.','_')+path.suffix)
        with path.open('rb') as src,destination.open('xb') as dst:shutil.copyfileobj(src,dst)
    unchanged()
    report=dict(status='FIXED_DATA_GENERATED_NOT_POSTERIOR_INFERENCE',preflight=preview,
        source_sha256=hashes,data_sha256=sha(data_path),orf_construction_sha256=sha(manifest_path),
        seeds=[r['data_seed'] for r in protocol['scenarios']],scenario_order=[r['id'] for r in protocol['scenarios']],
        row_ranges=[[0,31],[32,63],[64,95]],planned_inference_models=['A0_CN'],planned_targets=list(range(96)),
        runtime_models=cfg['models'],truth_defined_per_parameter=arrays['truth_defined'].sum(axis=0).tolist(),
        defined_signal_model_logL_at_truth=int(arrays['log_likelihood_at_truth_defined'].sum()),
        absent_signal_covariance_exactly_zero=bool(np.all(arrays['gw_covariance_by_scenario'][2]==0)),
        minimum_covariance_eigenvalues=np.linalg.eigvalsh(arrays['covariance_by_scenario']).min(axis=(1,2)).tolist(),
        numpy_version=np.__version__,scipy_version=scipy.__version__,seconds=time.perf_counter()-started,
        interpolation=False,posterior_execution=False,gaussian_control_saved_but_not_selected_for_fit=True)
    write_json_new(report_path,report)
    print(json.dumps({'status':report['status'],'data_sha256':report['data_sha256'],
        'seconds':report['seconds'],'realizations':96},indent=2))


if __name__=='__main__':main()
