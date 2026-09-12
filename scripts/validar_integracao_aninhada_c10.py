"""Pilot CC129/257/513 and nested-Simpson validation against completed GL events."""
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
from c10_taylor_adapter import TaylorEvent
from ledger import GlobalLedger,ScalarCache
from harmonic_margin import polynomial_pair,uniform_loglike_difference,event_level
from aggregate import aggregate_slices
from pta.nested_quadrature import clenshaw_curtis_prior_weights
R,P,S=base.R,base.P,base.S
O=R/'tmp/c10_nested_integral_validation_v1'


def freeze():
    inputs={}
    def bind(path):inputs[str(path.relative_to(R))]=base.sha(path);return base.read(path)
    spec=bind(S/'execution_spec.json');axes=bind(S/'axes.json');probe=bind(R/'results/C10/nested_quadrature_probe_v2/complete.json')
    assert probe['passed']==probe['total']==36 and probe['cumulative_values']==14541958
    ledger=bind(R/'results/C10/nested_quadrature_probe_v2/ledger.json');assert ledger['charged']==ledger['completed']
    bind(R/'results/C10/nested_quadrature_probe/FAILED_PRESERVED.json')
    bind(R/'results/C10/taylor_event_final_gate/audit.json')
    for name,digest in spec['source_sha256'].items():assert base.sha(R/name)==digest,name;inputs[name]=digest
    for path in (Path(__file__),Path(base.__file__),R/'src/pta/nested_quadrature.py',R/'src/pta/epsilon_taylor.py',R/'scripts/c10_taylor_adapter.py',
                 R/'tmp/c10_nested_quadrature_v1/nested_event.py',R/'tmp/c10_nested_quadrature_v1/bounded_output.py',
                 R/'tmp/c10_nested_quadrature_v1/test_output.txt',P/'generation.npz',P/'nodal_component.npz',P/'truth_logL.npy',
                 R/spec['protocol']['path'],R/'configs/experiments/c06_moments.json'):
        inputs[str(path.relative_to(R))]=base.sha(path)
    for route in base.ROUTES:
        path=P/f'{route}_high.npy';inputs[str(path.relative_to(R))]=base.sha(path);state=bind(path.with_suffix('.state.json'))
        assert state['status']=='COMPLETE' and state['sha256']==base.sha(path)
    weights={str(n):clenshaw_curtis_prior_weights(np.array(axes['master_mass_nodes'])[::(512//(n-1))]).tolist() for n in (129,257,513)}
    curves=[dict(id=i,route=route,model=model,label=label) for i in axes['independent_reference_ids'] for route,(models,_) in base.ROUTES.items() for model,label in zip(models,base.LABELS[route])]
    plan=dict(schema='C10_NESTED_FULL_PILOT_VALIDATION_v1',inputs=inputs,curves=curves,weights=weights,
              historical_values=14541958,new_value_cap=450000,cumulative_cap=14991958,CPU_cap_seconds=200,
              conservative_prior_CPU_upper=1584.962149,prospective_cumulative_CPU_upper=1784.962149,
              additional_values_per_slice=256,maximum_splits=128,maximum_depth=24,output_cap_bytes=192*1024**2,
              reservation='Incremental exact cache/report byte count; 256 KiB reserved per slice and 2 MiB for terminal/ledger/log files.',
              controls='Three density bridges per curve; every final cached point checked against its final cell.',
              new_ORFs=0,new_observations=0,production_authorized=False)
    O.mkdir(exist_ok=False);(O/'plan.json').write_text(json.dumps(plan,indent=2)+'\n')
    print(json.dumps({k:v for k,v in plan.items() if k not in ('inputs','curves','weights')}))


def execute():
    start=time.process_time();plan=base.read(O/'plan.json')
    for name,digest in plan['inputs'].items():assert base.sha(R/name)==digest,name
    resource.setrlimit(resource.RLIMIT_CPU,(math.ceil(start)+200,math.ceil(start)+201))
    def guard():
        rss=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*(1 if sys.platform=='darwin' else 1024)
        if rss>4*1024**3 or time.process_time()-start>200:raise RuntimeError('Nested integral CPU/RSS cap')
    ledger=GlobalLedger(O/'ledger.json',identity=base.sha(O/'plan.json'),allocations={'bridges':108,'epsilon':449892},maximum_values=450000,maximum_cpu_seconds=200)
    writer=BoundedOutput(O,plan['output_cap_bytes'])
    spec=base.read(S/'execution_spec.json');axes=base.read(S/'axes.json');geometry=base.load_geometry(R,spec)
    with np.load(P/'nodal_component.npz') as f:provider=base.NodalCovariances(f['masses'],f['gamma'],geometry,base.read(R/spec['protocol']['path']),base.read(R/'configs/experiments/c06_moments.json'))
    with np.load(P/'generation.npz') as f:data=tuple(f[k] for k in ('q','x','g'))
    truth=np.load(P/'truth_logL.npy');labels=sum((list(base.LABELS[r]) for r in base.ROUTES),[])
    eps=np.array(axes['master_epsilon_nodes'])[::2];mass=np.array(axes['master_mass_nodes']);generation_sha=base.sha(P/'generation.npz')
    high={route:np.load(P/f'{route}_high.npy',mmap_mode='r') for route in base.ROUTES}
    engines={i:base.engine_for(data,geometry,[i]) for i in axes['independent_reference_ids']}
    for curve in plan['curves']:
        e=engines[curve['id']];m=base.ROUTES[curve['route']][0].index(curve['model']);ri=axes['independent_reference_ids'].index(curve['id'])
        for j,k in ((0,0),(256,64),(512,128)):
            c0,c1=provider(float(mass[j]),curve['route'],2)
            value=ledger.evaluate('bridges',1,lambda:e.evaluate(c0,c1,[eps[k]],models=(curve['model'],))[0][0,0,0])
            assert abs(value-high[curve['route']][j,2*k,m,ri])<=1e-10
    groups={f'{c["label"]}:{c["id"]}':[] for c in plan['curves']};states=base.collections.Counter();visited=0;checks=0;stop='ALL_SLICES_VISITED';current_cache=None;name=None
    try:
        for j,u in enumerate(mass):
            if stop!='ALL_SLICES_VISITED':break
            covariances={route:[provider(float(u),route,level) for level in (0,1,2)] for route in base.ROUTES}
            for curve in plan['curves']:
                guard()
                if time.process_time()-start>185:stop='CPU_REMAINDER_PRESERVED';break
                if ledger.state['charged']['epsilon']+256>449892:stop='LIKELIHOOD_REMAINDER_PRESERVED';break
                if not writer.can_start():stop='DISK_REMAINDER_PRESERVED';break
                i=curve['id'];route=curve['route'];model=curve['model'];label=curve['label'];key=f'{label}:{i}';name=f'{label}_d{i}_m{j}'
                e=engines[i];c0,c1=covariances[route][2];m=base.ROUTES[route][0].index(model);ri=axes['independent_reference_ids'].index(i)
                def evaluate(points):guard();return e.evaluate(c0,c1,points,models=(model,))[0][:,0,0]
                identity=f'{generation_sha}:{label}:{i}:{float(u).hex()}:H11'
                cache=ScalarCache(evaluate,ledger,'epsilon',identity=identity,maximum_values=256);current_cache=cache
                original=high[route][j,::2,m,ri];cache.cache={float(x).hex():float(v) for x,v in zip(eps,original)}
                fine=polynomial_pair(e,c0,c1,model);bounds=[]
                for level in (0,1):
                    a,b=covariances[route][level]
                    bounds.append(uniform_loglike_difference(fine,polynomial_pair(e,a,b,model),normal=model!='A0_CN',roundoff_allowance=1e-10))
                assert all(b['delta_loglike'] is not None for b in bounds)
                delta=max(b['delta_loglike'] for b in bounds);col=labels.index(label);dt=float(np.max(abs(truth[:2,i,col]-truth[2,i,col])))+1e-10
                threshold=event_level(float(truth[2,i,col]),delta,dt)
                event=TaylorEvent(e,c0,c1,model,roundoff_allowance=1e-10)
                row=reference_slice(event,cache,threshold,maximum_splits=128,maximum_depth=24,
                                    controls={'roundoff_allowance_validated':True,'same_node_covariance_reference_validated':True})
                cells=row['partition'];points=np.array([float.fromhex(k) for k in cache.cache]);values=np.array(list(cache.cache.values()))
                indices=np.searchsorted([c['right'] for c in cells],points,side='left')
                lo=np.array([c['logL_lower'] for c in cells])[indices];hi=np.array([c['logL_upper'] for c in cells])[indices]
                if not np.all((lo<=values)&(values<=hi)):raise ArithmeticError('Final cell excludes cached density')
                checks+=len(points)
                row.update(selection=dict(curve,mass_index=j),identity=identity,reused_values=129,node_u=float(u),delta_logL_node=delta,
                           delta_logL_truth=dt,level_bounds=bounds,final_cached_point_checks=len(points))
                writer.save(name,cache,row);current_cache=None
                # Only compact masses are retained in RAM; full cells/caches are on disk.
                compact={k:v for k,v in row.items() if k not in ('partition','level_bounds','remaining_2D_gates')}
                groups[key].append(compact);visited+=1;states[row['status']]+=1
            if (j+1)%64==0:print(json.dumps(dict(mass_nodes=j+1,visited=visited,charged=sum(ledger.state['charged'].values()),CPU=time.process_time()-start)),flush=True)
    except Exception as exc:
        if current_cache is not None and writer.pending:
            if not (writer.directory/(name+'.npz')).exists():
                writer.save(name,current_cache,dict(status='FAILED_PARTIAL_CACHE_PRESERVED',reason=type(exc).__name__+': '+str(exc),identity=current_cache.identity,charged_values=current_cache.charged))
        base.save(O/'FAILED_PRESERVED.json',dict(reason=type(exc).__name__+': '+str(exc),visited=visited,charged=ledger.state['charged'],completed=ledger.state['completed']))
        raise
    assert ledger.state['charged']==ledger.state['completed'];aggregates={}
    for key,rows in groups.items():
        if len(rows)!=513:continue
        label,i=key.split(':')
        for n,step in ((129,4),(257,2),(513,1)):
            selected=rows[::step]
            result=aggregate_slices(selected,plan['weights'][str(n)],[r['delta_logL_node'] for r in selected],
                                    controls={'same_node_reference':True,'roundoff':True,'harmonic_level_enclosure':True})
            base.save(O/f'{label}_d{i}_cc{n}.json',result);aggregates[f'{key}:{n}']=dict(status=result['status'],candidate_interval=result.get('candidate_interval',[0.,1.]))
    charged=sum(ledger.state['charged'].values());result=dict(status='NESTED_INTEGRATION_VALIDATION_TERMINAL',stop=stop,visited=visited,states=dict(states),
                charged_new_values=charged,cumulative_values=plan['historical_values']+charged,CPU=time.process_time()-start,final_cached_point_checks=checks,
                aggregates=aggregates,output_bytes_before_terminal=writer.final_check(),new_ORFs=0,new_observations=0,production_authorized=False,plan_sha256=base.sha(O/'plan.json'))
    base.save(O/'complete.json',result);writer.final_check();print(json.dumps({k:v for k,v in result.items() if k!='aggregates'}))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--execute',action='store_true');execute() if p.parse_args().execute else freeze()
