"""Bounded prepared-density/batched-Taylor comparison against complete pilot caches."""
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
from bounded_output import BoundedOutput
from c10_memoized_kernel import MemoizedLikelihood
from c10_batched_taylor_adapter import BatchedTaylorEvent
from pta.moment_cache import MomentCache
from pta.prepared_density import PreparedDensity
from ledger import GlobalLedger,ScalarCache
from harmonic_margin import polynomial_pair,uniform_loglike_difference,event_level
from aggregate import aggregate_slices
from pta.nested_quadrature import clenshaw_curtis_prior_weights
R,P,S=base.R,base.P,base.S
F=R/'results/C10/full_flow_benchmark_v1';B=R/'tmp/c10_nested_integral_validation_v1'
O=R/'tmp/c10_prepared_event_benchmark_v1'


def freeze():
    old=base.read(F/'plan.json');inputs=dict(old['inputs'])
    for n,h in inputs.items():assert base.sha(R/n)==h,n
    for path in (Path(__file__),R/'scripts/c10_batched_taylor_adapter.py',R/'src/pta/prepared_density.py',
                 R/'src/pta/epsilon_taylor_batched.py',R/'tests/test_c10_prepared_and_batched.py',R/'tmp/c10_prepared_tests.txt',
                 R/'tmp/c10_nested_quadrature_v1/bounded_output.py',F/'audit.json',F/'complete.json',F/'grid.npy',F/'summaries.json'):
        inputs[str(path.relative_to(R))]=base.sha(path)
    for path in F.glob('cache_*.npz'):inputs[str(path.relative_to(R))]=base.sha(path)
    prior=base.read(F/'audit.json')
    plan=dict(inputs=inputs,historical_values=prior['cumulative_values'],prior_CPU_upper=prior['cumulative_CPU_upper'],
              ids=[0,3],bridges=5140,event_cap=19860,new_values_cap=25000,CPU_cap=30,output_cap=64*1024**2,
              controls='Interior epsilon bridges and every new node against preserved full-flow caches; final cell membership; CC aggregates',
              new_ORFs=0,new_observations=0,production_enabled=False)
    assert plan['historical_values']+plan['new_values_cap']<=15000000 and plan['prior_CPU_upper']+plan['CPU_cap']<=1800
    O.mkdir(exist_ok=False);(O/'plan.json').write_text(json.dumps(plan,indent=2)+'\n')
    print(json.dumps({k:v for k,v in plan.items() if k!='inputs'}))


def execute():
    start=time.process_time();p=base.read(O/'plan.json')
    for n,h in p['inputs'].items():assert base.sha(R/n)==h,n
    resource.setrlimit(resource.RLIMIT_CPU,(math.ceil(start)+30,math.ceil(start)+31))
    def guard():
        if time.process_time()-start>27:raise RuntimeError('CPU remainder reserved')
        if resource.getrusage(resource.RUSAGE_SELF).ru_maxrss>4*1024**3:raise RuntimeError('RSS cap')
    ledger=GlobalLedger(O/'ledger.json',identity=base.sha(O/'plan.json'),allocations={'bridges':5140,'events':19860},maximum_values=25000,maximum_cpu_seconds=30)
    writer=BoundedOutput(O,p['output_cap'])
    spec=base.read(S/'execution_spec.json');axes=base.read(S/'axes.json');geometry=base.load_geometry(R,spec)
    with np.load(P/'nodal_component.npz') as f:provider=base.NodalCovariances(f['masses'],f['gamma'],geometry,base.read(R/spec['protocol']['path']),base.read(R/'configs/experiments/c06_moments.json'))
    with np.load(P/'generation.npz') as f:data=tuple(f[k][p['ids']] for k in ('q','x','g'))
    shared=MomentCache();engines=[MemoizedLikelihood(*(a[[r]] for a in data),geometry['estimator_matrices'],geometry['frequency_weights'],moment_cache=shared,maximum_logl_values=15000000,maximum_workspace_bytes=256*1024**2) for r in range(2)]
    grid=np.load(F/'grid.npy',mmap_mode='r');eps=np.array(axes['master_epsilon_nodes'])[::2];masses=np.array(axes['master_mass_nodes'])[::2]
    truthll=np.load(P/'truth_logL.npy');labels=base.LABELS['D'];groups={(r,m):[] for r in range(2) for m in range(5)}
    visited=0;max_error=0.;unmatched=0;event_CPU=0.;check_CPU=0.;stop='COMPLETE';reason=None
    try:
        for j,u in enumerate(masses):
            guard();cov=[provider(float(u),'D',level) for level in (0,1,2)];c0,c1=cov[2]
            for r,i in enumerate(p['ids']):
                for m,label in enumerate(labels):
                    guard()
                    if not writer.can_start():raise RuntimeError('Output remainder reserved')
                    e=engines[r];old=base.read(B/'slices'/f'{label}_d{i}_m{2*j}.json')
                    t=time.process_time();fine=polynomial_pair(e,c0,c1,label);prepared=PreparedDensity(*fine,maximum_values=258)
                    delta=max(uniform_loglike_difference(fine,polynomial_pair(e,a,b,label),normal=label!='A0_CN',roundoff_allowance=1e-10)['delta_loglike'] for a,b in cov[:2])
                    event_CPU+=time.process_time()-t
                    t=time.process_time();values=ledger.evaluate('bridges',2,lambda:prepared(eps[[37,91]]))
                    error=float(np.max(abs(values-grid[j,[37,91],m,r])));max_error=max(max_error,error)
                    assert error<=1e-10
                    check_CPU+=time.process_time()-t
                    cache=ScalarCache(prepared,ledger,'events',identity=f'{i}:{label}:{float(u).hex()}',maximum_values=256)
                    cache.cache={float(x).hex():float(y) for x,y in zip(eps,grid[j,:,m,r])}
                    t=time.process_time()
                    row=reference_slice(BatchedTaylorEvent(e,c0,c1,label,roundoff_allowance=1e-10),cache,event_level(float(truthll[2,i,m]),delta,old['delta_logL_truth']),maximum_splits=128,maximum_depth=24,controls=old['controls'])
                    event_CPU+=time.process_time()-t
                    t=time.process_time()
                    with np.load(F/f'cache_{j}_{r}_{m}.npz') as f:previous={float(x).hex():float(y) for x,y in zip(f['epsilon'],f['log_likelihood'])}
                    for k,v in cache.cache.items():
                        if k in previous:max_error=max(max_error,abs(v-previous[k]))
                        else:unmatched+=1
                    assert max_error<=1e-10
                    points=np.array([float.fromhex(k) for k in cache.cache]);values=np.array(list(cache.cache.values()));cells=row['partition']
                    indices=np.searchsorted([c['right'] for c in cells],points,side='left')
                    assert np.all((values>=np.array([c['logL_lower'] for c in cells])[indices])&(values<=np.array([c['logL_upper'] for c in cells])[indices]))
                    assert prepared.charged==prepared.completed==cache.charged+2
                    row.update(delta_logL_node=delta,selection=dict(mass_index=2*j,id=i,label=label),new_values=cache.charged)
                    check_CPU+=time.process_time()-t
                    t=time.process_time();writer.save(f'event_{j}_{r}_{m}',cache,row);event_CPU+=time.process_time()-t
                    groups[r,m].append({k:v for k,v in row.items() if k not in ('partition','remaining_2D_gates')});visited+=1
    except Exception as exc:stop='STOPPED_PRESERVED';reason=type(exc).__name__+': '+str(exc)
    aggregates=[];max_cdf_error=0.
    if stop=='COMPLETE':
        previous=base.read(F/'summaries.json')['aggregates']
        for (r,m),rows in groups.items():
            for step in (1,2):
                selected=rows[::step]
                result=aggregate_slices(selected,clenshaw_curtis_prior_weights(masses[::step]),[x['delta_logL_node'] for x in selected],controls={'same_node_reference':True,'roundoff':True,'harmonic_level_enclosure':True})
                old=next(x['result'] for x in previous if x['key']==[r,m] and x['nodes']==len(selected))
                max_cdf_error=max(max_cdf_error,float(np.max(abs(np.array(result['candidate_interval'])-old['candidate_interval']))))
                assert result['slice_controls_pass'] and result['finite_controls_pass'] and max_cdf_error<=1e-10
                aggregates.append(dict(key=[r,m],nodes=len(selected),result=result))
    base.save(O/'aggregates.json',dict(aggregates=aggregates))
    size=writer.final_check()
    result=dict(status=stop,reason=reason,events=visited,event_CPU=event_CPU,additional_check_CPU=check_CPU,CPU=time.process_time()-start,
                maximum_logL_change=max_error,new_points_without_old_reference=unmatched,maximum_CDF_endpoint_change=max_cdf_error,
                charged=ledger.state['charged'],completed=ledger.state['completed'],cumulative_values=p['historical_values']+sum(ledger.state['charged'].values()),
                output_bytes_before_terminal=size,new_ORFs=0,new_observations=0,production_enabled=False)
    base.save(O/'complete.json',result);print(json.dumps(result))
    if stop!='COMPLETE':raise SystemExit(1)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--execute',action='store_true');execute() if parser.parse_args().execute else freeze()
