"""Same-node Simpson/GL comparison using exact high-grid densities as cache."""
from pathlib import Path
import argparse
import hashlib
import json
import math
import resource
import sys
import time
import numpy as np
import refinar_fatias_piloto_c10 as base
sys.path.insert(0,str(base.R/'tmp/c10_nested_quadrature_v1'))
from nested_event import reference_slice as simpson_slice
from epsilon_event import reference_slice as gauss_slice
from c10_taylor_adapter import TaylorEvent
from c10_mass_roundoff import with_roundoff
from ledger import GlobalLedger,ScalarCache
from harmonic_margin import polynomial_pair,uniform_loglike_difference,event_level
R,P,S=base.R,base.P,base.S
O=R/'results/C10/nested_quadrature_probe_v2'


def freeze():
    inputs={}
    def bind(path):inputs[str(path.relative_to(R))]=base.sha(path);return base.read(path)
    spec=bind(S/'execution_spec.json');axes=bind(S/'axes.json');audit=bind(R/'results/C10/taylor_event_final_gate/audit.json')
    assert audit['cumulative_likelihood_values']==14537983 and audit['states']=={'RESOLVED_OPERATIONAL_FINITE_REFERENCE_ONLY':36}
    for name,digest in spec['source_sha256'].items():assert base.sha(R/name)==digest,name;inputs[name]=digest
    failed=bind(R/'results/C10/nested_quadrature_probe/FAILED_PRESERVED.json');assert failed['charged_completed_values']==51
    first=bind(R/'results/C10/slice_refinement_probe_v2/plan.json');master=np.array(axes['master_mass_nodes']);selected=[]
    for item in first['selected']:
        old=bind(R/item['path']);j=int(np.argmin(abs(master-old['node_u'])))
        selected.append(dict(label=item['label'],model=item['model'],route=item['route'],id=item['id'],mass_index=j,u=float(master[j])))
    for path in (Path(__file__),Path(base.__file__),R/'src/pta/nested_quadrature.py',R/'src/pta/epsilon_taylor.py',R/'scripts/c10_taylor_adapter.py',
                 R/'scripts/c10_mass_roundoff.py',R/'tmp/c10_nested_quadrature_v1/nested_event.py',
                 R/'tmp/c10_nested_quadrature_v1/test_quadrature.py',R/'tmp/c10_nested_quadrature_v1/test_nested_event.py',R/'tmp/c10_nested_quadrature_v1/test_output.txt',
                 P/'generation.npz',P/'nodal_component.npz',P/'truth_logL.npy',R/spec['protocol']['path'],R/'configs/experiments/c06_moments.json'):
        inputs[str(path.relative_to(R))]=base.sha(path)
    for route in base.ROUTES:
        path=P/f'{route}_high.npy';inputs[str(path.relative_to(R))]=base.sha(path);state=bind(path.with_suffix('.state.json'))
        assert state['status']=='COMPLETE' and state['sha256']==base.sha(path)
    plan=dict(schema='C10_NESTED_SAME_NODE_PROBE_v1',inputs=inputs,selected=selected,historical_values=14538034,
              additional_value_cap=18540,maximum_values_per_slice=512,CPU_cap_seconds=30,output_cap_bytes=16*1024**2,
              order='Simpson first, then independent GL, same cached physical density; component charges distinguished.',
              new_ORFs=0,new_observations=0,production_authorized=False)
    O.mkdir(exist_ok=False);(O/'plan.json').write_text(json.dumps(plan,indent=2)+'\n');print(json.dumps({k:v for k,v in plan.items() if k not in ('inputs','selected')}))


def execute():
    start=time.process_time();plan=base.read(O/'plan.json')
    for name,digest in plan['inputs'].items():assert base.sha(R/name)==digest,name
    resource.setrlimit(resource.RLIMIT_CPU,(math.ceil(start)+30,math.ceil(start)+31))
    def guard():
        rss=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*(1 if sys.platform=='darwin' else 1024)
        if rss>4*1024**3 or time.process_time()-start>30:raise RuntimeError('Probe CPU/RSS cap')
    def disk(reserve=0):
        size=sum(p.stat().st_size for p in O.rglob('*') if p.is_file())
        if size+reserve>plan['output_cap_bytes']:raise RuntimeError('Probe disk reservation failed')
        return size
    ledger=GlobalLedger(O/'ledger.json',identity=base.sha(O/'plan.json'),allocations={'density':18540},maximum_values=18540,maximum_cpu_seconds=30)
    spec=base.read(S/'execution_spec.json');axes=base.read(S/'axes.json');geometry=base.load_geometry(R,spec)
    with np.load(P/'nodal_component.npz') as f:provider=base.NodalCovariances(f['masses'],f['gamma'],geometry,base.read(R/spec['protocol']['path']),base.read(R/'configs/experiments/c06_moments.json'))
    with np.load(P/'generation.npz') as f:data=tuple(f[k] for k in ('q','x','g'))
    truth=np.load(P/'truth_logL.npy');labels=sum((list(base.LABELS[r]) for r in base.ROUTES),[]);eps=np.array(axes['master_epsilon_nodes'])[::2]
    high={route:np.load(P/f'{route}_high.npy',mmap_mode='r') for route in base.ROUTES}
    (O/'slices').mkdir(exist_ok=False);results=[]
    for item in plan['selected']:
        guard();disk(reserve=512*1024);route=item['route'];i=item['id'];u=item['u'];model=item['model'];j=item['mass_index']
        m=base.ROUTES[route][0].index(model);ri=axes['independent_reference_ids'].index(i)
        values=high[route][j,::2,m,ri];e=base.engine_for(data,geometry,[i]);c0,c1=provider(u,route,2)
        def evaluate(points):guard();return e.evaluate(c0,c1,points,models=(model,))[0][:,0,0]
        ix=[0,64,128];direct=ledger.evaluate('density',3,lambda:evaluate(eps[ix]));assert np.max(abs(direct-values[ix]))<=1e-10
        identity=f'{base.sha(P/"generation.npz")}:{item["label"]}:{i}:{float(u).hex()}:H11'
        cache=ScalarCache(evaluate,ledger,'density',identity=identity,maximum_values=512);cache.cache={float(x).hex():float(y) for x,y in zip(eps,values)}
        fine=polynomial_pair(e,c0,c1,model);bounds=[]
        for level in (0,1):
            a,b=provider(u,route,level);bounds.append(uniform_loglike_difference(fine,polynomial_pair(e,a,b,model),normal=model!='A0_CN',roundoff_allowance=1e-10))
        assert all(b['delta_loglike'] is not None for b in bounds)
        delta=max(b['delta_loglike'] for b in bounds);col=labels.index(item['label']);dt=float(np.max(abs(truth[:2,i,col]-truth[2,i,col])))+1e-10
        threshold=event_level(float(truth[2,i,col]),delta,dt);controls={'roundoff_allowance_validated':True,'same_node_covariance_reference_validated':True}
        event=TaylorEvent(e,c0,c1,model,roundoff_allowance=1e-10,validation_cache=cache)
        simpson=simpson_slice(event,cache,threshold,maximum_splits=128,maximum_depth=24,controls=controls)
        simpson_cost=cache.charged
        gauss=with_roundoff(gauss_slice(event,cache,threshold,maximum_splits=128,maximum_depth=24,controls=controls),relative_allowance=1e-10)
        dz=abs(math.log(simpson['denominator']['value'])-math.log(gauss['denominator']['value']))
        intervals=[simpson['candidate_interval'],gauss['candidate_interval']];hull=[min(x[0] for x in intervals),max(x[1] for x in intervals)]
        passed=simpson['status'].startswith('SLICE_OPERATIONAL') and gauss['status'].startswith('SLICE_OPERATIONAL') and hull[1]-hull[0]<=.002 and dz<=.001
        row=dict(selection=item,identity=identity,simpson=simpson,gauss=gauss,simpson_new_values=simpson_cost,gauss_additional_values=cache.charged-simpson_cost,
                 total_new_values=cache.charged,reused_values=129,passed=passed,CDF_hull=hull,logZ_difference=dz,
                 delta_logL_node=delta,delta_logL_truth=dt,level_bounds=bounds,checked_cached_points=event.checked_cached_points)
        name=f'{item["label"]}_d{i}_m{j}'
        np.savez_compressed(O/'slices'/f'{name}.npz',epsilon=[float.fromhex(k) for k in cache.cache],log_likelihood=list(cache.cache.values()))
        payload=json.dumps(base.json_report(row),indent=2)+'\n'
        reserve=len(payload.encode())+16*len(cache.cache)+4096;disk(reserve=reserve+256*1024)
        (O/'slices'/f'{name}.json').write_text(payload)
        results.append(row)
    assert ledger.state['charged']==ledger.state['completed'];charged=sum(ledger.state['charged'].values())
    result=dict(status='SAME_NODE_QUADRATURE_PROBE_COMPLETE',passed=sum(r['passed'] for r in results),total=len(results),charged_new_values=charged,
                simpson_new_values=sum(r['simpson_new_values'] for r in results),gauss_additional_values=sum(r['gauss_additional_values'] for r in results),
                cumulative_values=plan['historical_values']+charged,CPU=time.process_time()-start,
                maximum_logZ_difference=max(r['logZ_difference'] for r in results),new_ORFs=0,new_observations=0,production_authorized=False,
                plan_sha256=base.sha(O/'plan.json'))
    base.save(O/'complete.json',result);disk();print(json.dumps(result))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--execute',action='store_true');execute() if p.parse_args().execute else freeze()
