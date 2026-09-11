"""Read-only adapter for (draw,target,chain,param); writes only --output.

No likelihood, sampler, ORF, or data generator is implemented here. Inputs must
already contain normalized truth coordinates and same-data truth log likelihood.
"""
import argparse,hashlib,json,math,sys,time
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from mcmc_diagnostics import target_diagnostics


def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        while chunk:=f.read(1048576):h.update(chunk)
    return h.hexdigest()


def json_safe(value):
    if isinstance(value,dict):return {k:json_safe(v) for k,v in value.items()}
    if isinstance(value,(list,tuple)):return [json_safe(v) for v in value]
    if isinstance(value,(np.bool_,)):return bool(value)
    if isinstance(value,(float,np.floating)):return float(value) if math.isfinite(value) else None
    if isinstance(value,(np.integer,)):return int(value)
    return value


def main():
    p=argparse.ArgumentParser()
    for name in ['draws','loglikelihood','truth-unit','loglikelihood-truth','metadata','output']:
        p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--target',type=int,action='append')
    p.add_argument('--known-limitation',default='ORF interpolation has not been approved; report concerns mixture/MC only.')
    args=p.parse_args();started=time.perf_counter()
    source_paths=[ROOT/'src/mcmc_diagnostics.py',Path(__file__),ROOT/'protocol_config.json']
    frozen_sources={str(path):sha(path) for path in source_paths}
    x=np.load(args.draws,mmap_mode='r');ll=np.load(args.loglikelihood,mmap_mode='r')
    true=np.load(args.truth_unit);lltrue=np.load(args.loglikelihood_truth)
    metadata=json.loads(args.metadata.read_text());cfg=json.loads((ROOT/'protocol_config.json').read_text())
    if x.ndim!=4 or x.shape[1:]!=(80,4,5) or ll.shape!=x.shape[:3] or true.shape!=(x.shape[1],5) or lltrue.shape!=(x.shape[1],):
        raise ValueError('Input shape mismatch')
    if metadata.get('production_adaptation') is not False or metadata.get('thinning')!=1:
        raise ValueError('Adapter requires declared unthinned fixed-kernel production')
    if metadata.get('models')!=cfg['models'] or list(x.shape)!=metadata.get('shape'):
        raise ValueError('Metadata/order mismatch')
    targets=list(range(x.shape[1])) if args.target is None else args.target
    if len(targets)!=len(set(targets)) or any(i<0 or i>=x.shape[1] for i in targets):raise ValueError('Invalid target IDs')
    names=['u','log10_Agw','gamma_gw','log10_Ar','log10_EFAC']; records=[]
    for i in targets:
        result=target_diagnostics(x[:,i],true[i],loglikelihood=ll[:,i],loglikelihood_truth=float(lltrue[i]),names=names)
        result.update(target=i,model=metadata['models'][i//16],realization=i%16)
        records.append(result)
        if len(records)%10==0: print(f'diagnosed {len(records)}/{len(targets)} targets',flush=True)
    all_cdfs=[c for r in records for c in r['truth_cdfs']]+[q['cdf'] for r in records for q in r['quantiles']]
    allconv=[c for r in records for c in r['convergence'].values()]
    max_mcse=max(c['mcse'] for c in all_cdfs);max_finite=max([c['mcse'] for c in all_cdfs if math.isfinite(c['mcse'])],default=math.inf)
    summary={
      'targets_examined':len(records),'targets_total':x.shape[1],
      'targets_passing_diagnostic_mc_only':sum(r['diagnostic_and_mc_precision_pass'] for r in records),
      'targets_passing_rhat_ess_floors':sum(all(c['diagnostic_floor_pass'] for c in r['convergence'].values()) for r in records),
      'maximum_rhat':max(c['rhat']['maximum'] for c in allconv),
      'minimum_bulk_ess':min(c['ess']['bulk'] for c in allconv),'minimum_tail_ess':min(c['ess']['tail'] for c in allconv),
      'cdf_count':len(all_cdfs),'maximum_mcse':max_mcse,'maximum_finite_mcse':max_finite,
      'cdf_above_mcse_target':sum(c['mcse']>cfg['cdf_mcse_max'] for c in all_cdfs),
      'constant_unresolved_indicators':sum(c['status']=='constant_indicator_unresolved' for c in all_cdfs),
      'batch_adequacy_failures':sum(not c.get('batch_adequate',False) for c in all_cdfs),
      'maximum_estimated_indicator_tau':max(c.get('tau',math.inf) for c in all_cdfs),
      'maximum_finite_estimated_indicator_tau':max(c['tau'] for c in all_cdfs if c.get('tau') is not None and math.isfinite(c['tau'])),
    }
    paths={name:getattr(args,name) for name in ['draws','loglikelihood','truth_unit','loglikelihood_truth','metadata']}
    result={'label':'HISTORICAL_PILOT_DIAGNOSTICS_NOT_SBC500_NOT_NUMERICAL_APPROVAL',
      'input_hashes':{name:{'path':str(path),'sha256':sha(path)} for name,path in paths.items()},
      'diagnostic_config_sha256':sha(ROOT/'protocol_config.json'),
      'source_hashes':frozen_sources,
      'summary':summary,'records':records,'elapsed_seconds':time.perf_counter()-started,
      'known_limitation':args.known_limitation,
      'finite_approximate_mc_intervals_not_exact_coverage':True,'PTA_SBC500_executed':False}
    if any(sha(Path(path))!=digest for path,digest in frozen_sources.items()):
        raise RuntimeError('Diagnostic source changed during execution; rerun before saving evidence')
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(json_safe(result),indent=2,allow_nan=False)+'\n')
    print(json.dumps(json_safe({'summary':summary,'elapsed_seconds':result['elapsed_seconds']}),indent=2))


if __name__=='__main__':main()
