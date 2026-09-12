"""Prospective 36-slice Taylor diagnostic; exact cache reuse and zero new ORFs."""
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
from c10_taylor_adapter import TaylorEvent
from c10_mass_roundoff import with_roundoff
R,P,S=base.R,base.P,base.S
O=R/'results/C10/taylor_selected_probe'


def freeze():
    first=base.read(R/'results/C10/slice_refinement_probe_v2/plan.json');inputs=dict(first['inputs'])
    for name,digest in inputs.items():assert base.sha(R/name)==digest,name
    selected=[]
    for item in first['selected']:
        item=dict(item);name=Path(item['path']).name
        candidates=[R/'tmp/c10_event_refinement_v1/slices'/name,R/'results/C10/slice_refinement_hard_probe/slices'/name,R/'results/C10/slice_refinement_probe_v2/slices'/name]
        path=next(p for p in candidates if p.exists());item['path']=str(path.relative_to(R));selected.append(item)
        for p in (path,path.with_suffix('.npz')):inputs[str(p.relative_to(R))]=base.sha(p)
    audit=base.read(R/'results/C10/primary_grid_refinement_audit/audit.json');assert audit['cumulative_values']==13880746
    for p in (Path(__file__),Path(base.__file__),R/'scripts/c10_taylor_adapter.py',R/'src/pta/epsilon_taylor.py',
              R/'scripts/c10_mass_roundoff.py',R/'tmp/c10_taylor_event_v1/test_taylor.py',R/'tmp/c10_taylor_event_v1/test_output.txt',
              R/'tmp/c10_taylor_event_v1/DERIVACAO.md',R/'results/C10/primary_grid_refinement_audit/audit.json'):
        inputs[str(p.relative_to(R))]=base.sha(p)
    plan=dict(schema='C10_TAYLOR_SELECTED_PROBE_v1',inputs=inputs,selected=selected,
              historical_values=13880746,new_value_cap=36*515,maximum_splits=128,maximum_depth=24,
              additional_values_per_slice=512,CPU_cap_seconds=120,output_cap_bytes=16*1024**2,
              reservation='Reserve 256 KiB before each slice and 1 MiB for final report; check serialized report before writing.',
              new_ORFs=0,new_observations=0,production_authorized=False)
    O.mkdir(exist_ok=False);(O/'plan.json').write_text(json.dumps(plan,indent=2)+'\n')
    print(json.dumps({k:v for k,v in plan.items() if k not in ('inputs','selected')}))


def execute():
    start=time.process_time();plan=base.read(O/'plan.json')
    for name,digest in plan['inputs'].items():assert base.sha(R/name)==digest,name
    resource.setrlimit(resource.RLIMIT_CPU,(math.ceil(start)+120,math.ceil(start)+121))
    def guard():
        rss=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*(1 if base.sys.platform=='darwin' else 1024)
        if rss>4*1024**3 or time.process_time()-start>120:raise RuntimeError('Taylor probe CPU/RSS cap')
    def disk(reserve=0):
        size=sum(p.stat().st_size for p in O.rglob('*') if p.is_file())
        if size+reserve>plan['output_cap_bytes']:raise RuntimeError('Taylor probe disk reservation failed')
        return size
    ledger=GlobalLedger(O/'ledger.json',identity=base.sha(O/'plan.json'),allocations={'bridges':108,'refinement':18432},maximum_values=18540,maximum_cpu_seconds=120)
    spec=base.read(S/'execution_spec.json');geometry=base.load_geometry(R,spec)
    with np.load(P/'nodal_component.npz') as f:
        provider=base.NodalCovariances(f['masses'],f['gamma'],geometry,base.read(R/spec['protocol']['path']),base.read(R/'configs/experiments/c06_moments.json'))
    with np.load(P/'generation.npz') as f:data=tuple(f[k] for k in ('q','x','g'))
    truth=np.load(P/'truth_logL.npy');labels=sum((list(base.LABELS[r]) for r in base.ROUTES),[])
    (O/'slices').mkdir(exist_ok=False);rows=[]
    for item in plan['selected']:
        guard();disk(reserve=1280*1024);old=base.read(R/item['path'])
        with np.load((R/item['path']).with_suffix('.npz')) as f:eps,vals=f['epsilon'],f['log_likelihood']
        e=base.engine_for(data,geometry,[item['id']]);c0,c1=provider(old['node_u'],item['route'],2)
        def evaluate(points):guard();return e.evaluate(c0,c1,points,models=(item['model'],))[0][:,0,0]
        order=np.argsort(eps);ix=order[[0,len(order)//2,-1]]
        direct=ledger.evaluate('bridges',3,lambda:evaluate(eps[ix]));delta=float(np.max(abs(direct-vals[ix])));assert delta<=1e-10
        identity=f'{base.sha(P/"generation.npz")}:{item["label"]}:{item["id"]}:{float(old["node_u"]).hex()}:H11'
        assert old['identity']==identity
        cache=ScalarCache(evaluate,ledger,'refinement',identity=identity,maximum_values=512)
        cache.cache={float(x).hex():float(y) for x,y in zip(eps,vals)}
        event=TaylorEvent(e,c0,c1,item['model'],roundoff_allowance=1e-10,validation_cache=cache)
        level=event_level(float(truth[2,item['id'],labels.index(item['label'])]),old['delta_logL_node'],old['delta_logL_truth'])
        raw=reference_slice(event,cache,level,maximum_splits=128,maximum_depth=24,controls=old['controls'])
        row=with_roundoff(raw,relative_allowance=1e-10)
        row.update(selection=item,identity=identity,reused_values=len(eps),bridge_max_delta=delta,
                   checked_cached_points=event.checked_cached_points,total_cells=event.total_cells,taylor_available_cells=event.taylor_available_cells,
                   original_status=old['status'],original_candidate_interval=old['candidate_interval'],
                   node_u=old['node_u'],delta_logL_node=old['delta_logL_node'],delta_logL_truth=old['delta_logL_truth'])
        name=Path(item['path']).stem;payload=json.dumps(base.json_report(row),indent=2,allow_nan=False)+'\n'
        # Uncompressed NPZ <= 16 bytes/value plus fixed headers, regardless of compression ratio.
        reserved=len(payload.encode())+16*len(cache.cache)+4096
        if reserved>256*1024:raise RuntimeError('Prospective per-slice size bound exceeded')
        disk(reserve=reserved+1024**2)
        (O/'slices'/f'{name}.json').write_text(payload)
        np.savez_compressed(O/'slices'/f'{name}.npz',epsilon=[float.fromhex(k) for k in cache.cache],log_likelihood=list(cache.cache.values()))
        rows.append(row)
    assert ledger.state['charged']==ledger.state['completed'];charged=sum(ledger.state['charged'].values())
    result=dict(status='TAYLOR_SELECTED_DIAGNOSTIC_COMPLETE_NOT_2D_APPROVAL',states=dict(base.collections.Counter(r['status'] for r in rows)),
                failures=dict(base.collections.Counter(r['failure_preserved'] for r in rows if 'failure_preserved' in r)),
                charged_new_values=charged,cumulative_values=plan['historical_values']+charged,
                checked_cached_points=sum(r['checked_cached_points'] for r in rows),CPU=time.process_time()-start,
                output_bytes_before_terminal=disk(reserve=1024**2),plan_sha256=base.sha(O/'plan.json'),
                new_ORFs=0,new_observations=0,C10_complete=False,production_authorized=False)
    base.save(O/'complete.json',result);disk();print(json.dumps(result))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--execute',action='store_true')
    execute() if p.parse_args().execute else freeze()
