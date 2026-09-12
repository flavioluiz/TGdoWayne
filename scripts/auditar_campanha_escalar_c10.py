"""Independent positive-grid integrals, cache accounting and event reconstruction."""
from pathlib import Path
import json,math,sys
import numpy as np
from scipy.special import logsumexp
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'src'),str(R/'tmp/c10_exact_lifecycle_v1')]
from physical import sha,LABELS
O=R/'tmp/c10_production_v1'


def read(path):
    raw=json.loads(path.read_text())
    if 'payload' not in raw:return raw
    data=raw['payload']
    for entry in raw.get('unbounded_fields',[]):
        keys=entry['path'].lstrip('/').split('/');node=data
        for key in keys[:-1]:node=node[int(key)] if isinstance(node,list) else node[key]
        key=int(keys[-1]) if isinstance(node,list) else keys[-1]
        assert node[key] is None
        node[key]=math.inf if entry['kind']=='positive_infinity' else -math.inf
    return data


def trapezoid_weights(x):
    d=np.diff(x);return np.r_[d[0]/2,(d[:-1]+d[1:])/2,d[-1]/2]


def marginal_cdf(axis,values,x):
    total=float(np.sum(np.diff(axis)*(values[:-1]+values[1:])/2))
    if x<=axis[0]:return 0.
    if x>=axis[-1]:return 1.
    j=int(np.searchsorted(axis,x,side='right')-1);areas=np.diff(axis)*(values[:-1]+values[1:])/2
    endpoint=values[j]+(values[j+1]-values[j])*(x-axis[j])/(axis[j+1]-axis[j])
    return float((sum(areas[:j])+(values[j]+endpoint)*(x-axis[j])/2)/total)


def cc_weights(axis):
    x=2*(axis-.001)/.999-1.;n=np.arange(len(x));moments=np.zeros(len(x));moments[::2]=1/(1-n[::2]**2)
    weights=np.linalg.solve(np.polynomial.chebyshev.chebvander(x,len(x)-1).T,moments)
    assert np.all(weights>0) and abs(weights.sum()-1)<1e-12
    return weights


def main():
    plan=read(O/'plan.json');done=read(O/'complete.json');ledger=read(O/'ledger.json')
    assert done['targets']==6344 and done['charged']==done['completed']==ledger['charged']==ledger['completed']
    for n,h in plan['inputs'].items():assert sha(R/n)==h,n
    assert done['CPU']<=plan['CPU_cap'] and sum(done['charged'].values())<=300000000
    axes=read(R/'tmp/c10_exact_lifecycle_v1/axes.json');u=np.array(axes['master_mass_nodes'])[::2];e=np.array(axes['master_epsilon_nodes'])[::2]
    epsilon_keys={float(x).hex() for x in e};weights={step:cc_weights(u[::step]) for step in (1,2)}
    count=0;grid_count=0;extra_count=0;event_count=0;memberships=0;max_z=0.;max_cdf=0.;max_quantile=0.;max_aggregate=0.;bindings={}
    for batch_index,batch in enumerate(plan['batches']):
        path=O/'grids'/f'batch_{batch_index}.npy';meta=read(path.with_suffix('.json'));assert sha(path)==meta['sha256']
        grid=np.load(path,mmap_mode='r');assert np.isfinite(grid).all();grid_count+=grid.size
        for r,i in enumerate(batch['ids']):
            for m,label in enumerate(LABELS[batch['route']]):
                name=f'{label}_d{i}';target_path=O/'targets'/f'{name}.json';target=read(target_path);bindings[str(target_path.relative_to(R))]=sha(target_path)
                assert target['global_id']==i and target['grid_batch']==batch_index and target['model_index']==m and target['data_index']==r
                for step,key in ((1,'fine'),(2,'coarse')):
                    x=u[::step];y=e[::step];logs=grid[::step,::step,m,r];wx=trapezoid_weights(x)/.999;wy=trapezoid_weights(y)
                    z1=float(logsumexp(logs+np.log(wx)[:,None]+np.log(wy)[None]));z0=float(logsumexp(logs[:,0]+np.log(wx)))
                    max_z=max(max_z,abs(z1-target[key]['logZ_H1']),abs(z0-target[key]['logZ_H0']))
                    values=np.exp(logs-float(np.max(logs)));marginals=(values@wy,wx@values)
                    for j,(axis,density) in enumerate(zip((x,y),marginals)):
                        cdf=marginal_cdf(axis,density,target['truth'][j]);max_cdf=max(max_cdf,abs(cdf-target[key]['parameter_CDF'][j]))
                        for p,q in zip((.05,.5,.9,.95),target[key]['quantiles'][j]):max_quantile=max(max_quantile,abs(marginal_cdf(axis,density,q)-p))
                if target['ensemble']=='prior2D' and target['route']=='D':
                    event=read(O/'events'/f'{name}.json');assert event['failure'] is None and len(event['rows'])==257
                    with np.load(O/'events'/f'{name}.npz') as f:extra=f['additional']
                    assert extra.ndim==2 and extra.shape[1]==3 and np.isfinite(extra).all()
                    assert np.all(extra[:,0]==extra[:,0].astype(int)) and np.all((extra[:,0]>=0)&(extra[:,0]<257))
                    extra_count+=len(extra)
                    for j,row in enumerate(event['rows']):
                        additions=extra[extra[:,0]==j];assert len(additions)==row.get('new_values',0)
                        assert all(float(x).hex() not in epsilon_keys for x in additions[:,1])
                        assert len(set(float(x).hex() for x in additions[:,1]))==len(additions)
                        if not row.get('partition'):continue
                        cells=row['partition'];points=np.r_[e,additions[:,1]];values=np.r_[grid[j,:,m,r],additions[:,2]]
                        assert cells[0]['left']==0. and cells[-1]['right']==1. and all(a['right']==b['left'] for a,b in zip(cells[:-1],cells[1:]))
                        idx=np.searchsorted([c['right'] for c in cells],points,side='left')
                        assert np.all((values>=np.array([c['logL_lower'] for c in cells])[idx])&(values<=np.array([c['logL_upper'] for c in cells])[idx]))
                        memberships+=len(points)
                    for step,reported in zip((2,1),target['logL_event']['rules']):
                        rows=event['rows'][::step];terms={k:[] for k in ('Nlow','NAhigh','Zlow','Zhigh','Zpoint')};missing=False
                        for row,weight in zip(rows,weights[step]):
                            d=row.get('denominator');delta=row['delta_logL_node'];shift=row.get('log_shift')
                            if d is None or shift is None or not math.isfinite(delta) or not d['lower']>0:missing=True;break
                            refs=row.get('numerator_references',{})
                            nl=0.;nh=d['upper']
                            if 'inside' in refs and 'ambiguous' in refs and 'failure_preserved' not in row:
                                nl=refs['inside']['lower'];nh=min(d['upper'],refs['inside']['upper']+refs['ambiguous']['upper'])
                            base=math.log(weight)+shift
                            for k,v,sign in (('Nlow',nl,-1),('NAhigh',nh,1),('Zlow',d['lower'],-1),('Zhigh',d['upper'],1),('Zpoint',d['value'],0)):
                                terms[k].append(-math.inf if v==0 else base+sign*delta+math.log(v))
                        if missing:assert reported['status']=='UNRESOLVED';continue
                        totals={k:float(logsumexp(v)) for k,v in terms.items()}
                        for k,value in totals.items():
                            original=reported['log_masses'][k]
                            if value==original:continue
                            assert math.isfinite(value) and math.isfinite(original);max_aggregate=max(max_aggregate,abs(value-original))
                    event_count+=1
                count+=1
        print(json.dumps(dict(batch=batch_index,targets_checked=count)),flush=True)
    assert count==6344 and event_count==2500 and grid_count==done['charged']['grid'] and extra_count==done['charged']['events']
    assert max_z<1e-10 and max_cdf<1e-10 and max_quantile<1e-9 and max_aggregate<1e-9
    truth=np.load(O/'truth_logL.npy');assert np.count_nonzero(np.isfinite(truth))==done['charged']['truth']==19032
    result=dict(status='PRODUCTION_INDEPENDENT_NUMERICAL_AUDIT_PASS',targets=count,direct_events=event_count,grid_values=grid_count,additional_event_values=extra_count,
                cached_points_in_final_cells=memberships,maximum_logZ_difference=max_z,maximum_parameter_CDF_difference=max_cdf,
                maximum_quantile_CDF_residual=max_quantile,maximum_event_log_mass_difference=max_aggregate,
                source_sha256=sha(Path(__file__)),target_sha256=bindings,complete_sha256=sha(O/'complete.json'),
                scope='Independent reconstruction of stored finite numerical representations; no uniform physical error certificate',new_likelihood_values=0,new_ORFs=0)
    out=R/'results/C10/production_audit';out.mkdir(exist_ok=False);(out/'audit.json').write_text(json.dumps(result,indent=2)+'\n')
if __name__=='__main__':main()
