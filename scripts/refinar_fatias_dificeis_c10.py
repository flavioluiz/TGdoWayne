"""Second bounded diagnostic: refine only the eight unresolved selected slices.

Shares the frozen v2 evaluator via an audited source snapshot; plans and outputs
remain separate. No population or complete-event inference follows from selection.
"""
from pathlib import Path
import argparse
import json
import math
import resource
import time
import numpy as np
import refinar_fatias_piloto_c10 as base
from ledger import GlobalLedger, ScalarCache
from epsilon_event import PolynomialEvent, reference_slice
from harmonic_margin import event_level

R, P, S = base.R, base.P, base.S
PREVIOUS = base.O
O = R/'results/C10/slice_refinement_hard_probe'


def freeze():
    old = base.read(PREVIOUS/'plan.json')
    done = base.read(PREVIOUS/'complete.json')
    inputs = dict(old['inputs'])
    for name, digest in inputs.items():
        assert base.sha(R/name) == digest, name
    selected = []
    for path in sorted((PREVIOUS/'slices').glob('*.json')):
        row = base.read(path)
        for f in (path, path.with_suffix('.npz')):
            inputs[str(f.relative_to(R))] = base.sha(f)
        if row['status'] == 'UNRESOLVED':
            item = dict(row['selection'])
            item['path'] = str(path.relative_to(R))
            selected.append(item)
    assert len(selected) == 8 and done['cumulative_values'] == 11940280
    for f in (PREVIOUS/'plan.json', PREVIOUS/'complete.json', PREVIOUS/'ledger.json', Path(__file__)):
        inputs[str(f.relative_to(R))] = base.sha(f)
    plan = dict(schema='C10_HARD_SELECTED_SLICE_PROBE_v1', inputs=inputs, selected=selected,
                historical_charged=done['cumulative_values'], maximum_splits=2048,
                maximum_depth=24, additional_values_per_slice=8192, new_logL_cap=8*(8192+3),
                CPU_cap_seconds=120, maximum_RSS_bytes=4*1024**3,
                selection='All eight unresolved slices from preceding frozen selected diagnostic.',
                new_ORFs=0,new_observations=0,production_authorized=False)
    assert plan['historical_charged']+plan['new_logL_cap'] <= 15000000
    O.mkdir(parents=True,exist_ok=False)
    (O/'plan.json').write_text(json.dumps(plan,indent=2,allow_nan=False)+'\n')
    print(json.dumps({k:v for k,v in plan.items() if k not in ('inputs','selected')}))


def execute():
    start=time.process_time(); plan=base.read(O/'plan.json')
    for name,digest in plan['inputs'].items():
        assert base.sha(R/name)==digest,name
    resource.setrlimit(resource.RLIMIT_CPU,(math.ceil(start)+120,math.ceil(start)+121))
    def guard():
        rss=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*(1 if base.sys.platform=='darwin' else 1024)
        if rss>plan['maximum_RSS_bytes'] or time.process_time()-start>120:
            raise RuntimeError('Selected diagnostic resource ceiling')
    ledger=GlobalLedger(O/'ledger.json',identity=base.sha(O/'plan.json'),
                        allocations={'bridges':24,'refinement':65536},
                        maximum_values=plan['new_logL_cap'],maximum_cpu_seconds=120)
    spec=base.read(S/'execution_spec.json'); geometry=base.load_geometry(R,spec)
    with np.load(P/'nodal_component.npz') as f:
        provider=base.NodalCovariances(f['masses'],f['gamma'],geometry,
                                      base.read(R/spec['protocol']['path']),base.read(R/'configs/experiments/c06_moments.json'))
    with np.load(P/'generation.npz') as f:data=tuple(f[k] for k in ('q','x','g'))
    truth=np.load(P/'truth_logL.npy'); labels=sum((list(base.LABELS[r]) for r in base.ROUTES),[])
    (O/'slices').mkdir(exist_ok=False); rows=[]
    for item in plan['selected']:
        guard();old=base.read(R/item['path'])
        with np.load((R/item['path']).with_suffix('.npz')) as f:eps,vals=f['epsilon'],f['log_likelihood']
        e=base.engine_for(data,geometry,[item['id']]);c0,c1=provider(old['node_u'],item['route'],2)
        def evaluate(points):
            guard()
            return e.evaluate(c0,c1,points,models=(item['model'],))[0][:,0,0]
        order=np.argsort(eps); probes=order[[0,len(order)//2,-1]]
        checked=ledger.evaluate('bridges',3,lambda:evaluate(eps[probes]))
        discrepancy=float(np.max(abs(checked-vals[probes])));assert discrepancy<=1e-10
        identity=f'{base.sha(P/"generation.npz")}:{item["label"]}:{item["id"]}:{float(old["node_u"]).hex()}:H11'
        assert old['identity']==identity
        cache=ScalarCache(evaluate,ledger,'refinement',identity=identity,maximum_values=8192)
        cache.cache={float(x).hex():float(y) for x,y in zip(eps,vals)}
        event=PolynomialEvent(e,c0,c1,item['model'],roundoff_allowance=spec['roundoff_logL_allowance'])
        level=event_level(float(truth[2,item['id'],labels.index(item['label'])]),old['delta_logL_node'],old['delta_logL_truth'])
        row=reference_slice(event,cache,level,maximum_splits=2048,maximum_depth=24,controls=old['controls'])
        row.update(selection=item,identity=identity,reused_values=len(eps),bridge_max_delta=discrepancy,
                   original_candidate_interval=old['candidate_interval'],node_u=old['node_u'],
                   delta_logL_node=old['delta_logL_node'],delta_logL_truth=old['delta_logL_truth'])
        name=Path(item['path']).stem
        base.save(O/'slices'/f'{name}.json',row)
        np.savez_compressed(O/'slices'/f'{name}.npz',epsilon=[float.fromhex(k) for k in cache.cache],log_likelihood=list(cache.cache.values()))
        rows.append(row)
    assert ledger.state['charged']==ledger.state['completed']
    charged=sum(ledger.state['charged'].values())
    result=dict(status='SELECTED_DIAGNOSTIC_COMPLETED_NOT_2D_APPROVAL',selected_slices=len(rows),
                states=dict(base.collections.Counter(r['status'] for r in rows)),
                failures=dict(base.collections.Counter(r['failure_preserved'] for r in rows if 'failure_preserved' in r)),
                charged_new_values=charged,cumulative_values=plan['historical_charged']+charged,
                reused_cache_values=sum(r['reused_values'] for r in rows),CPU=time.process_time()-start,
                maximum_bridge_difference=max(r['bridge_max_delta'] for r in rows),
                plan_sha256=base.sha(O/'plan.json'),new_ORFs=0,new_observations=0,C10_complete=False,production_authorized=False)
    base.save(O/'complete.json',result);print(json.dumps(result))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--execute',action='store_true')
    execute() if parser.parse_args().execute else freeze()
