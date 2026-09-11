"""Descriptive, truth-blind pilot cost projection; never production approval.

Only x_unit/log_likelihood/log_weights/targets are loaded from each NPZ.
No truth field is read. Grid is fixed here; low/high pilots must be independent.
"""
from pathlib import Path
import argparse,hashlib,json,math,sys
import numpy as np
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from inference.iid_diagnostics import replicated_cdf,weighted_quantiles,replicated_weights,json_safe

GRID=np.array([.01,.05,.1,.25,.5,.75,.9,.95,.99])
def load(path):
    with np.load(path,allow_pickle=False) as f:
        return {key:f[key] for key in ('x_unit','log_likelihood','log_weights','targets')}
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def main():
    p=argparse.ArgumentParser()
    for key in ('cut_pilot','precision_pilot','protocol','output'):p.add_argument('--'+key.replace('_','-'),type=Path,required=True)
    args=p.parse_args()
    if args.output.exists():raise FileExistsError('Preserve previous planning report')
    cfg=json.loads(args.protocol.read_text());low=load(args.cut_pilot);high=load(args.precision_pilot)
    if not np.array_equal(low['targets'],high['targets']):raise ValueError('Mismatched target IDs')
    r,n,t,d=high['x_unit'].shape
    if d!=5 or r<2 or low['x_unit'].shape[0]!=r:raise ValueError('Expected equal-R independent five-parameter pilot levels')
    goal=cfg['cdf_mcse_target'];rows=[]
    for j,target in enumerate(high['targets']):
        lw=low['log_weights'][:,:,j];hw=high['log_weights'][:,:,j];functions=[]
        for par in range(6):
            lv=low['x_unit'][:,:,j,par] if par<5 else low['log_likelihood'][:,:,j]
            hv=high['x_unit'][:,:,j,par] if par<5 else high['log_likelihood'][:,:,j]
            cuts=weighted_quantiles(lv.ravel(),lw.ravel(),GRID)
            reports=replicated_cdf(hv,hw,cuts,mcse_target=goal)
            for prob,report in zip(GRID,reports):
                functions.append({'function':f'parameter{par}' if par<5 else 'log_likelihood',
                    'pilot_quantile_probability':float(prob),'cdf':report})
        worst=max(functions,key=lambda a:a['cdf']['mcse']);maximum=worst['cdf']['mcse']
        proposals=[]
        for margin in (1.,2.):
            raw=n*(margin*maximum/goal)**2 if np.isfinite(maximum) else math.inf
            planned=max(n,2**math.ceil(math.log2(max(1.,raw)))) if np.isfinite(raw) else None
            proposals.append({'mcse_planning_margin':margin,'N_per_replication_projection_unrounded':raw,
                'N_per_replication_rounded_power_two':planned,
                'interpretation':'cost projection assuming stable sqrt(N) regime; not MCSE certification'})
        rows.append({'target':int(target),'maximum_grid_mcse':maximum,'limiting_function':worst['function'],
            'limiting_pilot_quantile_probability':worst['pilot_quantile_probability'],
            'finite_resolved_grid_points':sum(np.isfinite(a['cdf']['mcse']) for a in functions),
            'grid_points':54,'functions':functions,'weights':replicated_weights(hw),'cost_projections':proposals})
    import inference.iid_diagnostics as executed
    paths=[Path(__file__),Path(executed.__file__),args.protocol,args.cut_pilot,args.precision_pilot]
    result={'label':'TRUTH_BLIND_DESCRIPTIVE_PLANNING_AFTER_PILOTS_NO_NEW_PRODUCTION',
        'read_fields':['x_unit','log_likelihood','log_weights','targets'],
        'no_truth_fields_read':True,'grid_probabilities':GRID,'R':r,'precision_pilot_N':n,
        'cdf_mcse_target':goal,'targets':rows,
        'limitations':['Grid maximum is not a uniform variance bound.','No claim of finite variance or absence of unvisited modes.',
            'No automatic extension or stopping decision is executed.','m=2 is a proposed planning margin, not a confidence bound.',
            'Proposal training and pilot cost are separate from projected production.','Historical acceptance flags are not changed.'],
        'source_hashes':{str(path):sha(path) for path in paths}}
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(json_safe(result),indent=2,allow_nan=False)+'\n')
    print(json.dumps([{'target':a['target'],'max_mcse':a['maximum_grid_mcse'],'function':a['limiting_function'],
        'p':a['limiting_pilot_quantile_probability'],'N_margin1':a['cost_projections'][0]['N_per_replication_rounded_power_two'],
        'N_margin2':a['cost_projections'][1]['N_per_replication_rounded_power_two']} for a in rows],indent=2))

if __name__=='__main__':main()
