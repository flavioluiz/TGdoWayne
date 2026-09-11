"""Smooth-region CDFs: truncate original rectangular prior, retain its full density.

For an original coordinate x, integral_{x<=z} L p_full equals
Z(truncated box)*volume(truncated box)/volume(full box). Each positive integral
uses new panels at all scale-bound switches, eliminating the extra CDF kinks.
This is algebraically the same conditional-scale numerator, not a new prior.
"""
import argparse,json,time
from dataclasses import replace
import numpy as np
from scipy.special import logsumexp
from cubature import (HERE,PILOT,LogAmplitudeBox,experiment,FrozenMassTable,digest,
                      mass_nodes,mass_integral,diagnostic_cuts,trapezoid_weights)

def truncated_box(full,param,threshold):
    name={1:'gw',2:'slope',3:'red',4:'efac'}[param]
    lo,hi=getattr(full,name)
    if not lo<threshold<hi:raise ValueError('CDF benchmark uses strictly interior original cuts.')
    return replace(full,**{name:(lo,threshold)}),np.log((threshold-lo)/(hi-lo))

def run(order,*,masses=None,max_points=1_500_000_000):
    cfg=json.loads((PILOT/'config.json').read_text());e=experiment(cfg)
    with np.load(PILOT/'results/data.npz',allow_pickle=False) as p:data={k:p[k] for k in p.files}
    q=data['q'][14];box=LogAmplitudeBox();table=FrozenMassTable(e,cfg['orf'])
    cuts,cut_hash=diagnostic_cuts(cfg,data,14)
    selected=mass_nodes() if masses is None else np.asarray(masses,float)
    expected=len(selected)*(len(cuts)+1)*9*order**3
    if expected>max_points:raise RuntimeError(f'{expected} node budget exceeds {max_points}.')
    logvalues=np.empty((len(selected),len(cuts)+1));records=[];start=time.perf_counter()
    for j,u in enumerate(selected):
        gamma=table.get(float(u))
        logvalues[j,0],_,r=mass_integral(gamma,e,q,box,[order]*3)
        records.append(r)
        for c,cut in enumerate(cuts):
            small,logfraction=truncated_box(box,cut['parameter'],cut['value'])
            value,_,r=mass_integral(gamma,e,q,small,[order]*3)
            logvalues[j,c+1]=value+logfraction;records.append(r)
        if j%10==0:print(json.dumps(dict(order=order,mass_progress=j+1,total=len(selected),elapsed=time.perf_counter()-start)),flush=True)
    if len(selected)>1:
        logz=logsumexp(logvalues+np.log(trapezoid_weights(selected))[:,None],axis=0)
    else:logz=logvalues[0]
    result=dict(scope='A0_CN datum14, original-coordinate CDFs by smooth panels for truncated numerator integrals; no completed SBC or all-target approval',
                order=order,mass_nodes=len(selected),masses=selected.tolist(),parameter_points=expected,seconds=time.perf_counter()-start,
                maximum_points_budget=max_points,cdf_cuts=cuts,cut_source_hash=cut_hash,log_evidence=float(logz[0]),
                original_nuisance_CDF_at_frozen_cuts=np.exp(logz[1:]-logz[0]).tolist(),
                log_mass_marginal=logvalues[:,0].tolist(),log_CDF_numerator_mass_marginals=logvalues[:,1:].tolist(),
                minimum_spectral_denominator=min(r['minimum_denominator'] for r in records),
                minimum_whitened_orf_eigenvalue=min(r['minimum_whitened_orf_eigenvalue'] for r in records),
                source_hashes={str(p):digest(p) for p in [HERE/'cubature.py',HERE/'truncated_cdf.py',HERE.parent/'c07_scale/scale_marginalization.py',PILOT/'config.json',PILOT/'results/data.npz']},
                orf_signature=table.meta.signature,cache_hashes={str(u):digest(path) for u,path in table.paths.items()},
                thresholds=cfg['diagnostic_thresholds'],nuisance_quantile_acceptance_assessed=False,
                prior_preserved=True,no_cdf_pruning=True,no_eigenvalue_clipping=True)
    return result

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--orders',type=int,nargs='+',default=[12,20,32]);p.add_argument('--mass',type=float,nargs='+');p.add_argument('--maximum-points',type=int,default=1_500_000_000);a=p.parse_args()
    dest=HERE/'results';dest.mkdir(exist_ok=True)
    for n in a.orders:
        filename=dest/f'A0_d14_GL{n}_{"mass" if a.mass else "full"}_truncated_cdf.json'
        if filename.exists():print('Preserving',filename.name,flush=True);continue
        result=run(n,masses=a.mass,max_points=a.maximum_points)
        filename.write_text(json.dumps(result,indent=2)+'\n')
        print(json.dumps({k:result[k] for k in ['order','mass_nodes','parameter_points','seconds','log_evidence','original_nuisance_CDF_at_frozen_cuts']}),flush=True)
