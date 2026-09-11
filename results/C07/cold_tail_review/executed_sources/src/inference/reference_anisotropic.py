"""Explicit anisotropic cost/convergence experiment, same truncated CDF numerators."""
from inference.reference_paths import ROOT,CONFIG,DATA,ORF_CACHE,CUT_SOURCE,CUBATURE_RESULTS,QUANTILE_RESULTS
import argparse,json,time
import numpy as np
from scipy.special import logsumexp
from inference.reference_cubature import (HERE,PILOT,LogAmplitudeBox,experiment,FrozenMassTable,digest,
                      mass_nodes,mass_integral,diagnostic_cuts,trapezoid_weights)
from inference.reference_truncated import truncated_box

def run(orders,masses):
    cfg=json.loads((CONFIG).read_text());e=experiment(cfg)
    with np.load(DATA,allow_pickle=False) as p:data={k:p[k] for k in p.files}
    q=data['q'][14];box=LogAmplitudeBox();table=FrozenMassTable(e,cfg['orf']);cuts,cut_hash=diagnostic_cuts(cfg,data,14)
    expected=len(masses)*(len(cuts)+1)*9*np.prod(orders)
    if expected>500_000_000:raise RuntimeError('Explicit500M point budget exceeded before execution.')
    logvalues=np.empty((len(masses),len(cuts)+1));start=time.perf_counter();min_den=np.inf;min_eig=np.inf
    for j,u in enumerate(masses):
        gamma=table.get(float(u))
        cases=[(box,0.)]+[truncated_box(box,c['parameter'],c['value']) for c in cuts]
        for c,(small,lf) in enumerate(cases):
            value,_,r=mass_integral(gamma,e,q,small,orders)
            logvalues[j,c]=value+lf
            min_den=min(min_den,r['minimum_denominator']);min_eig=min(min_eig,r['minimum_whitened_orf_eigenvalue'])
        if j%10==0:print(json.dumps(dict(order=orders,mass_progress=j+1,total=len(masses),elapsed=time.perf_counter()-start)),flush=True)
    logz=logvalues[0] if len(masses)==1 else logsumexp(logvalues+np.log(trapezoid_weights(masses))[:,None],axis=0)
    return dict(scope='A0_CN datum14 anisotropic cubature at fixed original cuts; no full all-target approval',order_b_a_gamma=orders,
                mass_nodes=len(masses),masses=masses.tolist(),parameter_points=int(expected),seconds=time.perf_counter()-start,
                cdf_cuts=cuts,cut_source_hash=cut_hash,log_evidence=float(logz[0]),original_nuisance_CDF_at_frozen_cuts=np.exp(logz[1:]-logz[0]).tolist(),
                log_mass_marginal=logvalues[:,0].tolist(),log_CDF_numerator_mass_marginals=logvalues[:,1:].tolist(),
                minimum_spectral_denominator=min_den,minimum_whitened_orf_eigenvalue=min_eig,
                source_hashes={str(p):digest(p) for p in [HERE/'reference_cubature.py',HERE/'reference_anisotropic.py',HERE/'reference_truncated.py',CONFIG,DATA]},
                orf_signature=table.meta.signature,cache_hashes={str(u):digest(path) for u,path in table.paths.items()},
                thresholds=cfg['diagnostic_thresholds'],nuisance_quantile_acceptance_assessed=False,
                prior_preserved=True,no_cdf_pruning=True,no_eigenvalue_clipping=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--orders',type=int,nargs=3,required=True);p.add_argument('--mass',type=float,nargs='+');a=p.parse_args()
    masses=mass_nodes() if a.mass is None else np.asarray(a.mass,float)
    CUBATURE_RESULTS.mkdir(parents=True,exist_ok=True)
    tag='_'.join(map(str,a.orders));filename=CUBATURE_RESULTS/f'A0_d14_GL{tag}_{"mass" if a.mass else "full"}_truncated_cdf.json'
    if filename.exists():print('Preserving',filename.name)
    else:
        out=run(a.orders,masses);filename.write_text(json.dumps(out,indent=2)+'\n')
        print(json.dumps({k:out[k] for k in ['order_b_a_gamma','mass_nodes','parameter_points','seconds','log_evidence','original_nuisance_CDF_at_frozen_cuts']}),flush=True)
