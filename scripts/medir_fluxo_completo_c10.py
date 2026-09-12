"""Bounded end-to-end D benchmark on two existing pilot observations."""
from pathlib import Path
import argparse
import json
import math
import resource
import sys
import time
import numpy as np
import refinar_fatias_piloto_c10 as base
sys.path.insert(0,str(base.R/'tmp/c10_nested_quadrature_v1'))
from nested_event import reference_slice
from c10_memoized_kernel import MemoizedLikelihood
from c10_taylor_adapter import TaylorEvent
from pta.moment_cache import MomentCache
from ledger import GlobalLedger,ScalarCache
from harmonic_margin import polynomial_pair,uniform_loglike_difference,event_level
from references import summary,compare_summaries
from aggregate import aggregate_slices
from pta.nested_quadrature import clenshaw_curtis_prior_weights
R,P,S=base.R,base.P,base.S
B=R/'tmp/c10_nested_integral_validation_v1'
O=R/'results/C10/full_flow_benchmark_v1'


def freeze():
    inputs={}
    def bind(p):inputs[str(p.relative_to(R))]=base.sha(p);return base.read(p)
    spec=bind(S/'execution_spec.json');axes=bind(S/'axes.json')
    previous=bind(R/'results/C10/production_preflight_v1/plan.json')
    for n,h in spec['source_sha256'].items():assert base.sha(R/n)==h;inputs[n]=h
    for p in (Path(__file__),Path(base.__file__),R/'scripts/c10_memoized_kernel.py',R/'scripts/c10_taylor_adapter.py',
              R/'src/pta/moment_cache.py',R/'src/pta/epsilon_taylor.py',R/'src/pta/nested_quadrature.py',
              R/'tmp/c10_nested_quadrature_v1/nested_event.py',P/'nodal_component.npz',P/'generation.npz',P/'truth_logL.npy',
              P/'D_high.npy',R/spec['protocol']['path'],R/'configs/experiments/c06_moments.json'):
        inputs[str(p.relative_to(R))]=base.sha(p)
    for j in range(0,513,2):
        for i in (0,3):
            for label in base.LABELS['D']:bind(B/'slices'/f'{label}_d{i}_m{j}.json')
    plan=dict(inputs=inputs,ids=[0,3],historical_values=14622522,grid_values=331530,
              event_values_cap=20000,new_values_cap=351530,CPU_cap=50,
              prior_CPU_upper=previous['resources']['pilot_CPU_upper_seconds'],
              disk_cap=64*1024**2,scope='Full D grid, summaries and events on existing engineering observations only',
              new_ORFs=0,new_observations=0,production_enabled=False)
    assert plan['historical_values']+plan['new_values_cap']<=15000000
    assert plan['prior_CPU_upper']+plan['CPU_cap']<=1800
    O.mkdir(exist_ok=False);(O/'plan.json').write_text(json.dumps(plan,indent=2)+'\n')
    print(json.dumps({k:v for k,v in plan.items() if k!='inputs'}))


def execute():
    start=time.process_time();wall=time.monotonic();p=base.read(O/'plan.json')
    for n,h in p['inputs'].items():assert base.sha(R/n)==h,n
    resource.setrlimit(resource.RLIMIT_CPU,(math.ceil(start)+50,math.ceil(start)+51))
    def guard():
        if time.process_time()-start>47:raise RuntimeError('CPU remainder reserved for terminal receipt')
        if resource.getrusage(resource.RUSAGE_SELF).ru_maxrss>4*1024**3:raise RuntimeError('RSS cap')
    ledger=GlobalLedger(O/'ledger.json',identity=base.sha(O/'plan.json'),allocations={'grid':331530,'events':20000},maximum_values=351530,maximum_cpu_seconds=50)
    spec=base.read(S/'execution_spec.json');axes=base.read(S/'axes.json');geometry=base.load_geometry(R,spec)
    with np.load(P/'nodal_component.npz') as f:provider=base.NodalCovariances(f['masses'],f['gamma'],geometry,base.read(R/spec['protocol']['path']),base.read(R/'configs/experiments/c06_moments.json'))
    with np.load(P/'generation.npz') as f:data=tuple(f[k][p['ids']] for k in ('q','x','g'));truths=f['truth'][p['ids']]
    truthll=np.load(P/'truth_logL.npy');labels=base.LABELS['D'];eps=np.array(axes['master_epsilon_nodes'])[::2];masses=np.array(axes['master_mass_nodes'])[::2]
    shared=MomentCache();options=dict(moment_cache=shared,maximum_logl_values=15000000,maximum_workspace_bytes=256*1024**2)
    engine=MemoizedLikelihood(*data,geometry['estimator_matrices'],geometry['frequency_weights'],**options)
    individual=[MemoizedLikelihood(*(a[[r]] for a in data),geometry['estimator_matrices'],geometry['frequency_weights'],**options) for r in range(2)]
    high=np.load(P/'D_high.npy',mmap_mode='r');columns=[axes['independent_reference_ids'].index(i) for i in p['ids']]
    grid=np.lib.format.open_memmap(O/'grid.npy',mode='w+',dtype=float,shape=(257,129,5,2));grid[:]=np.nan
    groups={(r,m):[] for r in range(2) for m in range(5)};summaries=[];timings={'grid':0.,'summaries':0.,'events':0.};visited=0;status='COMPLETE';reason=None
    try:
        for j,u in enumerate(masses):
            guard();c0,c1=provider(float(u),'D',2);t=time.process_time()
            values=ledger.evaluate('grid',129*5*2,lambda:engine.evaluate(c0,c1,eps,models=labels)[0])
            timings['grid']+=time.process_time()-t
            if np.max(abs(values-high[2*j,::2][:,:,columns]))>1e-10:raise ArithmeticError('Grid mismatch with exact pilot nodes')
            grid[j]=values
        grid.flush()
        for r,i in enumerate(p['ids']):
            for m,label in enumerate(labels):
                guard();t=time.process_time()
                fine=summary(masses,eps,grid[:,:,m,r],truths[r],truthll[2,i,m]);coarse=summary(masses[::2],eps[::2],grid[::2,::2,m,r],truths[r],truthll[2,i,m])
                timings['summaries']+=time.process_time()-t
                summaries.append(dict(id=i,label=label,fine=fine,coarse=coarse,comparison=compare_summaries(fine,coarse)))
        for j,u in enumerate(masses):
            guard();cov=[provider(float(u),'D',level) for level in (0,1,2)];c0,c1=cov[2]
            for r,i in enumerate(p['ids']):
                for m,label in enumerate(labels):
                    t=time.process_time();e=individual[r];old=base.read(B/'slices'/f'{label}_d{i}_m{2*j}.json')
                    cache=ScalarCache(lambda x:e.evaluate(c0,c1,x,models=(label,))[0][:,0,0],ledger,'events',identity=f'{i}:{label}:{float(u).hex()}',maximum_values=256)
                    cache.cache={float(x).hex():float(y) for x,y in zip(eps,grid[j,:,m,r])}
                    fine=polynomial_pair(e,c0,c1,label)
                    delta=max(uniform_loglike_difference(fine,polynomial_pair(e,a,b,label),normal=label!='A0_CN',roundoff_allowance=1e-10)['delta_loglike'] for a,b in cov[:2])
                    assert delta==old['delta_logL_node']
                    row=reference_slice(TaylorEvent(e,c0,c1,label,roundoff_allowance=1e-10),cache,event_level(float(truthll[2,i,m]),delta,old['delta_logL_truth']),maximum_splits=128,maximum_depth=24,controls=old['controls'])
                    row['delta_logL_node']=delta
                    # Small batching roundoff may alter the exact boundary partition.
                    if abs(row['denominator']['fine']-old['denominator']['fine'])>1e-10*max(1,abs(old['denominator']['fine'])):raise ArithmeticError('Event normalization mismatch')
                    groups[r,m].append({k:v for k,v in row.items() if k not in ('partition','remaining_2D_gates')})
                    np.savez_compressed(O/f'cache_{j}_{r}_{m}.npz',epsilon=[float.fromhex(k) for k in cache.cache],log_likelihood=list(cache.cache.values()))
                    timings['events']+=time.process_time()-t;visited+=1
    except Exception as exc:
        status='STOPPED_PRESERVED';reason=type(exc).__name__+': '+str(exc)
    grid.flush();aggregates=[]
    if status=='COMPLETE':
        for key,rows in groups.items():
            for step in (1,2):
                selected=rows[::step]
                aggregates.append(dict(key=key,nodes=len(selected),result=aggregate_slices(selected,clenshaw_curtis_prior_weights(masses[::step]),[x['delta_logL_node'] for x in selected],controls={'same_node_reference':True,'roundoff':True,'harmonic_level_enclosure':True})))
    base.save(O/'summaries.json',dict(summaries=summaries,aggregates=aggregates))
    size=sum(x.stat().st_size for x in O.rglob('*') if x.is_file())
    result=dict(status=status,reason=reason,events=visited,timings=timings,CPU=time.process_time()-start,wall=time.monotonic()-wall,
                charged=ledger.state['charged'],completed=ledger.state['completed'],cumulative_values=p['historical_values']+sum(ledger.state['charged'].values()),
                output_bytes_before_terminal=size,output_cap=p['disk_cap'],cache=shared.statistics(),new_ORFs=0,new_observations=0,production_enabled=False)
    base.save(O/'complete.json',result);print(json.dumps(result))
    if status!='COMPLETE' or size>p['disk_cap']:raise SystemExit(1)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--execute',action='store_true');execute() if parser.parse_args().execute else freeze()
