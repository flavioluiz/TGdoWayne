"""Budgeted continuation of pilot event slices, ranked by integral uncertainty.

Frozen original and selected-probe caches are reused exactly. This does not
activate a population campaign, change the likelihood, or assert 2D convergence.
"""
from pathlib import Path
import argparse
import json
import math
import resource
import time
import numpy as np
import refinar_fatias_piloto_c10 as base
from ledger import GlobalLedger, ScalarCache, CapacityExceeded
from epsilon_event import PolynomialEvent, reference_slice
from harmonic_margin import event_level
from aggregate import aggregate_slices

R,P,S=base.R,base.P,base.S
O=R/'tmp/c10_event_refinement_v1'
PROBES=[R/'results/C10/slice_refinement_probe_v2',R/'results/C10/slice_refinement_hard_probe']


def freeze():
    inputs={}
    def bind(path):
        inputs[str(path.relative_to(R))]=base.sha(path)
        return base.read(path) if path.suffix=='.json' else path
    spec=bind(S/'execution_spec.json')
    for name,digest in spec['source_sha256'].items():
        assert base.sha(R/name)==digest,name
        inputs[name]=digest
    axes=bind(S/'axes.json');bind(P/'ledger.json');bind(P/'complete.json')
    for path in (Path(__file__),Path(base.__file__),P/'nodal_component.npz',P/'generation.npz',
                 P/'truth_logL.npy',R/spec['protocol']['path'],R/'configs/experiments/c06_moments.json'):
        bind(path)
    replacements={}
    for directory in PROBES:
        plan=bind(directory/'plan.json');done=bind(directory/'complete.json');ledger=bind(directory/'ledger.json')
        assert ledger['charged']==ledger['completed']
        for name,digest in plan['inputs'].items():assert base.sha(R/name)==digest,name
        for path in sorted((directory/'slices').glob('*.json')):replacements[path.name]=path
    assert done['cumulative_values']==11952564
    all_rows=[];pending=[]
    for i in axes['independent_reference_ids']:
        for route,(models,_) in base.ROUTES.items():
            for model,label in zip(models,base.LABELS[route]):
                for order in ('192','384'):
                    stem=f'{label}_d{i}_u{order}';aggregate=bind(P/f'{stem}_mass_reference.json')
                    for j,weight in enumerate(axes['u_reference'][order]['prior_weights']):
                        filename=f'{stem}_{j}.json'
                        path=replacements.get(filename,P/'event_slices'/filename)
                        row=bind(path);bind(path.with_suffix('.npz'))
                        den=row['denominator'];assert den is not None and row['delta_logL_node'] is not None
                        refs=row['numerator_references']
                        if 'failure_preserved' in row or not all(k in refs for k in ('inside','ambiguous')):
                            uncertainty=den['upper']
                        else:
                            uncertainty=max(0.,min(den['upper'],refs['inside']['upper']+refs['ambiguous']['upper'])-refs['inside']['lower'])
                        score=math.exp(math.log(weight)+row['log_shift']+row['delta_logL_node']
                                       +math.log(max(uncertainty,np.finfo(float).tiny))-aggregate['log_masses']['Zlow'])
                        item=dict(id=i,route=route,model=model,label=label,order=order,node_index=j,
                                  path=str(path.relative_to(R)),score=score)
                        all_rows.append(item)
                        if row['status']=='UNRESOLVED':pending.append(item)
    pending.sort(key=lambda x:(-x['score'],x['path']))
    plan=dict(schema='C10_EVENT_REFINEMENT_v1',inputs=inputs,all_rows=all_rows,selected=pending,
              historical_charged=11952564,new_logL_cap=2800000,cumulative_cap=14752564,
              CPU_cap_seconds=900,maximum_RSS_bytes=4*1024**3,maximum_output_bytes=256*1024**2,
              maximum_splits=512,maximum_depth=24,additional_values_per_slice=1536,
              selection='All currently unresolved slices, descending original relative uncertainty; ties by path.',
              stop='Stop before next slice if fewer than 1539 ledger values remain or CPU/disk cap approached.',
              new_ORFs=0,new_observations=0,production_authorized=False)
    O.mkdir(exist_ok=False)
    (O/'plan.json').write_text(json.dumps(plan,indent=2,allow_nan=False)+'\n')
    print(json.dumps(dict(selected=len(pending),all_rows=len(all_rows),new_logL_cap=plan['new_logL_cap'],cumulative_cap=plan['cumulative_cap'])))


def execute():
    start=time.process_time();plan=base.read(O/'plan.json')
    for name,digest in plan['inputs'].items():assert base.sha(R/name)==digest,name
    resource.setrlimit(resource.RLIMIT_CPU,(math.ceil(start)+900,math.ceil(start)+901))
    def guard():
        rss=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*(1 if base.sys.platform=='darwin' else 1024)
        if rss>plan['maximum_RSS_bytes'] or time.process_time()-start>900:
            raise CapacityExceeded('Event refinement CPU/RSS allowance exhausted')
    ledger=GlobalLedger(O/'ledger.json',identity=base.sha(O/'plan.json'),
                        allocations={'all_density_values':plan['new_logL_cap']},
                        maximum_values=plan['new_logL_cap'],maximum_cpu_seconds=900)
    spec=base.read(S/'execution_spec.json');geometry=base.load_geometry(R,spec)
    with np.load(P/'nodal_component.npz') as f:
        provider=base.NodalCovariances(f['masses'],f['gamma'],geometry,
                                      base.read(R/spec['protocol']['path']),base.read(R/'configs/experiments/c06_moments.json'))
    with np.load(P/'generation.npz') as f:data=tuple(f[k] for k in ('q','x','g'))
    truth=np.load(P/'truth_logL.npy');labels=sum((list(base.LABELS[r]) for r in base.ROUTES),[])
    axes=base.read(S/'axes.json');(O/'slices').mkdir(exist_ok=False)
    states=base.collections.Counter();failures=base.collections.Counter();completed=0;reused=0;stop='ALL_SELECTED_VISITED';maximum_bridge=0.
    engines={i:base.engine_for(data,geometry,[i]) for i in axes['independent_reference_ids']}
    try:
        for item in plan['selected']:
            guard()
            if plan['new_logL_cap']-sum(ledger.state['charged'].values())<1539:
                stop='LIKELIHOOD_REMAINDER_PRESERVED';break
            if time.process_time()-start>880:
                stop='CPU_REMAINDER_PRESERVED';break
            if completed%100==0 and sum(p.stat().st_size for p in O.rglob('*') if p.is_file())>plan['maximum_output_bytes']-1024**2:
                stop='DISK_REMAINDER_PRESERVED';break
            old=base.read(R/item['path'])
            with np.load((R/item['path']).with_suffix('.npz')) as f:eps,vals=f['epsilon'],f['log_likelihood']
            e=engines[item['id']];c0,c1=provider(old['node_u'],item['route'],2)
            def evaluate(points):
                guard()
                return e.evaluate(c0,c1,points,models=(item['model'],))[0][:,0,0]
            order=np.argsort(eps);probes=order[[0,len(order)//2,-1]]
            direct=ledger.evaluate('all_density_values',3,lambda:evaluate(eps[probes]))
            discrepancy=float(np.max(abs(direct-vals[probes])));assert discrepancy<=1e-10
            maximum_bridge=max(maximum_bridge,discrepancy)
            identity=f'{base.sha(P/"generation.npz")}:{item["label"]}:{item["id"]}:{float(old["node_u"]).hex()}:H11'
            if 'identity' in old:assert identity==old['identity']
            cache=ScalarCache(evaluate,ledger,'all_density_values',identity=identity,maximum_values=1536)
            assert len(set(eps))==len(eps) and np.isfinite(vals).all()
            cache.cache={float(x).hex():float(y) for x,y in zip(eps,vals)}
            event=PolynomialEvent(e,c0,c1,item['model'],roundoff_allowance=spec['roundoff_logL_allowance'])
            level=event_level(float(truth[2,item['id'],labels.index(item['label'])]),old['delta_logL_node'],old['delta_logL_truth'])
            row=reference_slice(event,cache,level,maximum_splits=512,maximum_depth=24,controls=old['controls'])
            row.update(selection=item,identity=identity,reused_values=len(eps),bridge_max_delta=discrepancy,
                       node_u=old['node_u'],delta_logL_node=old['delta_logL_node'],delta_logL_truth=old['delta_logL_truth'])
            name=Path(item['path']).stem
            base.save(O/'slices'/f'{name}.json',row)
            np.savez_compressed(O/'slices'/f'{name}.npz',epsilon=[float.fromhex(k) for k in cache.cache],log_likelihood=list(cache.cache.values()))
            states[row['status']]+=1
            if 'failure_preserved' in row:failures[row['failure_preserved']]+=1
            completed+=1;reused+=len(eps)
            if completed%500==0:print(json.dumps(dict(visited=completed,charged=sum(ledger.state['charged'].values()),CPU=time.process_time()-start)),flush=True)
    except Exception as exc:
        base.save(O/'FAILED_PRESERVED.json',dict(reason=type(exc).__name__+': '+str(exc),visited=completed,charged=ledger.state['charged']))
        raise
    assert ledger.state['charged']==ledger.state['completed']
    # Preserve the earlier report whenever the new candidate is wider; never
    # splice two incompatible quadrature estimates into a claimed tighter one.
    groups={};improved=0
    for item in plan['all_rows']:
        old=base.read(R/item['path']);path=O/'slices'/Path(item['path']).name
        row=old
        if path.exists():
            new=base.read(path)
            def width(r):
                if 'failure_preserved' in r:return 1.
                a,b=r.get('candidate_interval',[0.,1.]);return b-a
            if width(new)<=width(old):row=new;improved+=1
        key=f'{item["label"]}_d{item["id"]}_u{item["order"]}'
        groups.setdefault(key,[]).append((item['node_index'],row,item))
    aggregates={}
    for key,values in groups.items():
        values.sort(key=lambda x:x[0]);order=values[0][2]['order']
        rows=[x[1] for x in values]
        result=aggregate_slices(rows,axes['u_reference'][order]['prior_weights'],[r['delta_logL_node'] for r in rows],
                                controls={'same_node_reference':True,'roundoff':True,'harmonic_level_enclosure':True})
        base.save(O/f'{key}_mass_reference.json',result)
        aggregates[key]=dict(status=result['status'],candidate_interval=result.get('candidate_interval',[0.,1.]))
    charged=sum(ledger.state['charged'].values())
    result=dict(status='BUDGETED_REFINEMENT_TERMINAL_NOT_2D_APPROVAL',stop=stop,visited=completed,selected=len(plan['selected']),
                states=dict(states),failures=dict(failures),chosen_refined_rows=improved,
                charged_new_values=charged,cumulative_values=plan['historical_charged']+charged,
                reused_cache_values=reused,CPU=time.process_time()-start,maximum_bridge_difference=maximum_bridge,
                aggregates=aggregates,plan_sha256=base.sha(O/'plan.json'),new_ORFs=0,new_observations=0,
                C10_complete=False,production_authorized=False)
    base.save(O/'complete.json',result)
    print(json.dumps({k:v for k,v in result.items() if k!='aggregates'}))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--execute',action='store_true')
    execute() if parser.parse_args().execute else freeze()
