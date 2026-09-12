"""Bounded Taylor continuation, with original cumulative ledger and exact caches."""
from pathlib import Path
import argparse
import json
import math
import resource
import time
import numpy as np
import refinar_fatias_piloto_c10 as base
from ledger import GlobalLedger,ScalarCache
from epsilon_event import reference_slice
from harmonic_margin import event_level
from aggregate import aggregate_slices
from c10_taylor_adapter import TaylorEvent
from c10_mass_roundoff import with_roundoff
R,P,S=base.R,base.P,base.S
O=R/'tmp/c10_taylor_completion_v1'
B=R/'tmp/c10_event_refinement_v1'
T=R/'results/C10/taylor_selected_probe'


def freeze():
    inputs={}
    def bind(path):inputs[str(path.relative_to(R))]=base.sha(path);return base.read(path)
    previous=bind(B/'plan.json');done=bind(B/'complete.json');probe=bind(T/'plan.json');completed=bind(T/'complete.json')
    assert completed['cumulative_values']==13882582 and list(completed['states'].values())==[36]
    for plan in (previous,probe):
        for name,digest in plan['inputs'].items():assert base.sha(R/name)==digest,name
    spec=bind(S/'execution_spec.json');axes=bind(S/'axes.json')
    for name,digest in spec['source_sha256'].items():inputs[name]=digest
    for path in (Path(__file__),Path(base.__file__),R/'scripts/c10_taylor_adapter.py',R/'src/pta/epsilon_taylor.py',
                 R/'scripts/c10_mass_roundoff.py',R/'tmp/c10_taylor_event_v1/DERIVACAO.md',T/'ledger.json',
                 R/'results/C10/primary_grid_refinement_audit/audit.json',P/'generation.npz',P/'nodal_component.npz',P/'truth_logL.npy',
                 R/spec['protocol']['path'],R/'configs/experiments/c06_moments.json'):
        inputs[str(path.relative_to(R))]=base.sha(path)
    all_rows=[];pending=[]
    for item in previous['all_rows']:
        item=dict(item);name=Path(item['path']).name
        candidates=[T/'slices'/name,B/'slices'/name,R/item['path']]
        path=next(p for p in candidates if p.exists());row=bind(path)
        inputs[str(path.with_suffix('.npz').relative_to(R))]=base.sha(path.with_suffix('.npz'))
        item['path']=str(path.relative_to(R));all_rows.append(item)
        if with_roundoff(row,relative_allowance=1e-10)['status']=='UNRESOLVED':pending.append(item)
    # Interleave rules/curves in a deterministic round-robin; each group sorts
    # its own contribution to uncertainty. A global cap cannot starve u384 solely
    # because its individual integration weights are smaller than u192 weights.
    groups={}
    for item in pending:groups.setdefault((item['label'],item['id'],item['order']),[]).append(item)
    for rows in groups.values():rows.sort(key=lambda x:(-x.get('score',0.),x['node_index']))
    selected=[]
    while any(groups.values()):
        for key in sorted(groups):
            if groups[key]:selected.append(groups[key].pop(0))
    plan=dict(schema='C10_TAYLOR_EVENT_COMPLETION_v1',inputs=inputs,all_rows=all_rows,selected=selected,
              historical_values=13882582,new_value_cap=1100000,cumulative_cap=14982582,CPU_seconds_cap=300,
              maximum_splits=128,maximum_depth=24,additional_values_per_slice=512,output_cap_bytes=256*1024**2,
              reservation='Before each slice reserve 256 KiB plus 1 MiB terminal allowance; validate exact serialization+uncompressed cache bound before writing.',
              new_ORFs=0,new_observations=0,production_authorized=False)
    O.mkdir(exist_ok=False);(O/'plan.json').write_text(json.dumps(plan,indent=2,allow_nan=False)+'\n')
    print(json.dumps(dict(selected=len(selected),all_rows=len(all_rows),cumulative_cap=plan['cumulative_cap'])))


def execute():
    start=time.process_time();plan=base.read(O/'plan.json')
    for name,digest in plan['inputs'].items():assert base.sha(R/name)==digest,name
    resource.setrlimit(resource.RLIMIT_CPU,(math.ceil(start)+300,math.ceil(start)+301))
    def guard():
        rss=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*(1 if base.sys.platform=='darwin' else 1024)
        if rss>4*1024**3 or time.process_time()-start>300:raise RuntimeError('Taylor completion CPU/RSS cap')
    def disk(reserve=0):
        size=sum(p.stat().st_size for p in O.rglob('*') if p.is_file())
        if size+reserve>plan['output_cap_bytes']:raise RuntimeError('Taylor completion disk reservation failed')
        return size
    ledger=GlobalLedger(O/'ledger.json',identity=base.sha(O/'plan.json'),allocations={'density':1100000},maximum_values=1100000,maximum_cpu_seconds=300)
    spec=base.read(S/'execution_spec.json');axes=base.read(S/'axes.json');geometry=base.load_geometry(R,spec)
    with np.load(P/'nodal_component.npz') as f:
        provider=base.NodalCovariances(f['masses'],f['gamma'],geometry,base.read(R/spec['protocol']['path']),base.read(R/'configs/experiments/c06_moments.json'))
    with np.load(P/'generation.npz') as f:data=tuple(f[k] for k in ('q','x','g'))
    truth=np.load(P/'truth_logL.npy');labels=sum((list(base.LABELS[r]) for r in base.ROUTES),[])
    engines={i:base.engine_for(data,geometry,[i]) for i in axes['independent_reference_ids']}
    (O/'slices').mkdir(exist_ok=False);states=base.collections.Counter();failures=base.collections.Counter();visited=0;checks=0;stop='ALL_SELECTED_VISITED'
    try:
        for item in plan['selected']:
            guard()
            if sum(ledger.state['charged'].values())+515>plan['new_value_cap']:stop='LIKELIHOOD_REMAINDER_PRESERVED';break
            if time.process_time()-start>275:stop='CPU_REMAINDER_PRESERVED';break
            if disk()+1280*1024>plan['output_cap_bytes']:stop='DISK_REMAINDER_PRESERVED';break
            old=base.read(R/item['path'])
            with np.load((R/item['path']).with_suffix('.npz')) as f:eps,vals=f['epsilon'],f['log_likelihood']
            e=engines[item['id']];c0,c1=provider(old['node_u'],item['route'],2)
            def evaluate(points):guard();return e.evaluate(c0,c1,points,models=(item['model'],))[0][:,0,0]
            order=np.argsort(eps);ix=order[[0,len(order)//2,-1]]
            direct=ledger.evaluate('density',3,lambda:evaluate(eps[ix]));delta=float(np.max(abs(direct-vals[ix])));assert delta<=1e-10
            identity=f'{base.sha(P/"generation.npz")}:{item["label"]}:{item["id"]}:{float(old["node_u"]).hex()}:H11'
            if 'identity' in old:assert identity==old['identity']
            cache=ScalarCache(evaluate,ledger,'density',identity=identity,maximum_values=512)
            assert len(set(eps))==len(eps) and np.isfinite(vals).all()
            cache.cache={float(x).hex():float(y) for x,y in zip(eps,vals)}
            event=TaylorEvent(e,c0,c1,item['model'],roundoff_allowance=1e-10,validation_cache=cache)
            level=event_level(float(truth[2,item['id'],labels.index(item['label'])]),old['delta_logL_node'],old['delta_logL_truth'])
            raw=reference_slice(event,cache,level,maximum_splits=128,maximum_depth=24,controls=old['controls'])
            row=with_roundoff(raw,relative_allowance=1e-10)
            row.update(selection=item,identity=identity,reused_values=len(eps),bridge_max_delta=delta,
                       checked_cached_points=event.checked_cached_points,total_cells=event.total_cells,taylor_available_cells=event.taylor_available_cells,
                       node_u=old['node_u'],delta_logL_node=old['delta_logL_node'],delta_logL_truth=old['delta_logL_truth'])
            name=Path(item['path']).stem;payload=json.dumps(base.json_report(row),indent=2,allow_nan=False)+'\n'
            reserved=len(payload.encode())+16*len(cache.cache)+4096
            if reserved>256*1024:raise RuntimeError('Prospective per-slice output bound exceeded')
            disk(reserve=reserved+1024**2)
            (O/'slices'/f'{name}.json').write_text(payload)
            np.savez_compressed(O/'slices'/f'{name}.npz',epsilon=[float.fromhex(k) for k in cache.cache],log_likelihood=list(cache.cache.values()))
            visited+=1;states[row['status']]+=1;checks+=event.checked_cached_points
            if 'failure_preserved' in row:failures[row['failure_preserved']]+=1
            if visited%1000==0:print(json.dumps(dict(visited=visited,charged=sum(ledger.state['charged'].values()),CPU=time.process_time()-start)),flush=True)
    except Exception as exc:
        base.save(O/'FAILED_PRESERVED.json',dict(reason=type(exc).__name__+': '+str(exc),visited=visited,charged=ledger.state['charged']))
        raise
    assert ledger.state['charged']==ledger.state['completed']
    groups={}
    for item in plan['all_rows']:
        path=O/'slices'/Path(item['path']).name
        row=base.read(path) if path.exists() else with_roundoff(base.read(R/item['path']),relative_allowance=1e-10)
        key=f'{item["label"]}_d{item["id"]}_u{item["order"]}';groups.setdefault(key,[]).append((item['node_index'],row,item['order']))
    aggregates={}
    for key,items in groups.items():
        items.sort(key=lambda x:x[0]);rows=[x[1] for x in items];order=items[0][2]
        result=aggregate_slices(rows,axes['u_reference'][order]['prior_weights'],[r['delta_logL_node'] for r in rows],
                                controls={'same_node_reference':True,'roundoff':True,'harmonic_level_enclosure':True})
        base.save(O/f'{key}_mass_reference.json',result);aggregates[key]=dict(status=result['status'],candidate_interval=result.get('candidate_interval',[0.,1.]))
    charged=sum(ledger.state['charged'].values());result=dict(status='TAYLOR_COMPLETION_TERMINAL_NOT_POPULATION_APPROVAL',stop=stop,
              selected=len(plan['selected']),visited=visited,states=dict(states),failures=dict(failures),checked_cached_points=checks,
              charged_new_values=charged,cumulative_values=plan['historical_values']+charged,CPU=time.process_time()-start,
              aggregates=aggregates,output_bytes_before_terminal=disk(reserve=512*1024),plan_sha256=base.sha(O/'plan.json'),
              new_ORFs=0,new_observations=0,C10_complete=False,production_authorized=False)
    base.save(O/'complete.json',result);disk();print(json.dumps({k:v for k,v in result.items() if k!='aggregates'}))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--execute',action='store_true')
    execute() if p.parse_args().execute else freeze()
