"""Bounded diagnostic: freeze 36 worst weighted u384 slices, then reuse caches.

This is a selected numerical experiment, not a population or 2D CDF approval.
Run without arguments to freeze the plan; --execute consumes that plan once.
"""
from pathlib import Path
import argparse
import collections
import hashlib
import json
import math
import resource
import sys
import time
import numpy as np

R = Path(__file__).resolve().parents[1]
P = R/'tmp/c10_physical_pilot_v1'
S = R/'tmp/c10_exact_lifecycle_v1'
O = R/'results/C10/slice_refinement_probe'
sys.path[:0] = [str(R/'src'), str(S)]
from physical import load_geometry, NodalCovariances, engine_for, ROUTES, LABELS, sha
from ledger import GlobalLedger, ScalarCache
from epsilon_event import PolynomialEvent, reference_slice
from harmonic_margin import event_level
from report_io import json_report


def save(path, value):
    with path.open('x') as stream:
        json.dump(json_report(value), stream, indent=2, allow_nan=False)
        stream.write('\n')


def read(path):
    value = json.loads(path.read_text())
    return value['payload'] if value.get('schema') == 'C10_OPERATIONAL_REPORT_JSON_v1' else value


def freeze():
    bindings = {}
    def bind(path):
        bindings[str(path.relative_to(R))] = sha(path)
        return read(path) if path.suffix == '.json' else path
    spec = bind(S/'execution_spec.json')
    for name, digest in spec['source_sha256'].items():
        assert sha(R/name) == digest, name
        bindings[name] = digest
    axes = bind(S/'axes.json')
    ledger = bind(P/'ledger.json')
    assert ledger['charged'] == ledger['completed']
    historical = sum(ledger['charged'].values())
    bind(P/'complete.json')
    for path in (P/'nodal_component.npz', P/'generation.npz', P/'truth_logL.npy',
                 R/spec['protocol']['path'], R/'configs/experiments/c06_moments.json',
                 R/'results/C10/pilot_terminal_audit/audit.json', Path(__file__)):
        bind(path)
    selected = []
    for i in axes['independent_reference_ids']:
        for route, (models, _) in ROUTES.items():
            for model, label in zip(models, LABELS[route]):
                stem = f'{label}_d{i}_u384'
                aggregate = bind(P/f'{stem}_mass_reference.json')
                candidates = []
                for j, weight in enumerate(axes['u_reference']['384']['prior_weights']):
                    path = P/'event_slices'/f'{stem}_{j}.json'
                    row = bind(path)
                    den = row['denominator']
                    assert den is not None and row['delta_logL_node'] is not None
                    refs = row['numerator_references']
                    if 'failure_preserved' in row or not all(k in refs for k in ('inside', 'ambiguous')):
                        uncertain = den['upper']
                    else:
                        uncertain = min(den['upper'], refs['inside']['upper']+refs['ambiguous']['upper'])-refs['inside']['lower']
                    log_score = (math.log(weight)+row['log_shift']+row['delta_logL_node']
                                 +math.log(max(uncertain, np.finfo(float).tiny))
                                 -aggregate['log_masses']['Zlow'])
                    candidates.append((log_score, -j, path))
                log_score, neg_j, path = max(candidates)
                bind(path.with_suffix('.npz'))
                selected.append(dict(id=i, route=route, model=model, label=label, node_index=-neg_j,
                                     path=str(path.relative_to(R)), weighted_uncertainty=math.exp(log_score)))
    assert len(selected) == 36 and historical == 11930676
    cap = 36*(2048+3)
    assert historical+cap <= 15000000
    plan = dict(schema='C10_SELECTED_SLICE_PROBE_v1', selected=selected, inputs=bindings,
                selection='Largest posterior-weighted unknown N/A mass per curve on u384; deterministic lowest-index ties.',
                historical_charged=historical, new_logL_cap=cap, cumulative_cap=historical+cap,
                maximum_splits=256, maximum_depth=24, additional_values_per_slice=2048,
                CPU_cap_seconds=120, new_ORFs=0, new_observations=0,
                scope='Diagnostic selection only; cannot approve 2D events or production population.')
    O.mkdir(parents=True, exist_ok=False)
    (O/'plan.json').write_text(json.dumps(plan, indent=2, allow_nan=False)+'\n')
    print(json.dumps({k:v for k,v in plan.items() if k not in ('inputs', 'selected')}))


def execute():
    start = time.process_time()
    plan = read(O/'plan.json')
    for name, digest in plan['inputs'].items():
        assert sha(R/name) == digest, name
    # One-shot ledger plus OS resource guards. Historical work is never reset.
    resource.setrlimit(resource.RLIMIT_CPU, (math.ceil(start)+120, math.ceil(start)+121))
    resource.setrlimit(resource.RLIMIT_AS, (4*1024**3, 4*1024**3))
    ledger = GlobalLedger(O/'ledger.json', identity=sha(O/'plan.json'),
                          allocations={'bridges':108, 'refinement':73728},
                          maximum_values=plan['new_logL_cap'], maximum_cpu_seconds=120)
    spec = read(S/'execution_spec.json')
    geometry = load_geometry(R, spec)
    with np.load(P/'nodal_component.npz') as f:
        provider = NodalCovariances(f['masses'], f['gamma'], geometry,
                                   read(R/spec['protocol']['path']), read(R/'configs/experiments/c06_moments.json'))
    with np.load(P/'generation.npz') as f:
        data = tuple(f[k] for k in ('q', 'x', 'g'))
    truth = np.load(P/'truth_logL.npy')
    labels = sum((list(LABELS[r]) for r in ROUTES), [])
    rows = []
    (O/'slices').mkdir(exist_ok=False)
    for selection in plan['selected']:
        ledger.checkpoint()
        old = read(R/selection['path'])
        cachepath = (R/selection['path']).with_suffix('.npz')
        with np.load(cachepath) as f:
            eps, vals = f['epsilon'], f['log_likelihood']
        order = np.argsort(eps)
        probes = order[[0, len(order)//2, -1]]
        e = engine_for(data, geometry, [selection['id']])
        c0, c1 = provider(old['node_u'], selection['route'], 2)
        model = selection['model']
        def evaluate(x):
            return e.evaluate(c0, c1, x, models=(model,))[0][:,0,0]
        direct = ledger.evaluate('bridges', 3, lambda: evaluate(eps[probes]))
        discrepancy = float(np.max(abs(direct-vals[probes])))
        assert discrepancy <= 1e-10, selection
        identity = f'{sha(P/"generation.npz")}:{selection["label"]}:{selection["id"]}:{float(old["node_u"]).hex()}:H11'
        cache = ScalarCache(evaluate, ledger, 'refinement', identity=identity,
                            maximum_values=plan['additional_values_per_slice'])
        assert len(set(eps)) == len(eps) and np.isfinite(vals).all()
        cache.cache = {float(x).hex():float(y) for x,y in zip(eps,vals)}
        level = event_level(float(truth[2,selection['id'],labels.index(selection['label'])]),
                            old['delta_logL_node'], old['delta_logL_truth'])
        event = PolynomialEvent(e,c0,c1,model,roundoff_allowance=spec['roundoff_logL_allowance'])
        row = reference_slice(event,cache,level,maximum_splits=plan['maximum_splits'],
                              maximum_depth=plan['maximum_depth'],controls=old['controls'])
        row.update(selection=selection, identity=identity, bridge_max_delta=discrepancy,
                   original_status=old['status'], original_candidate_interval=old['candidate_interval'],
                   reused_values=len(eps), delta_logL_node=old['delta_logL_node'],
                   delta_logL_truth=old['delta_logL_truth'],node_u=old['node_u'])
        name = Path(selection['path']).stem
        save(O/'slices'/f'{name}.json',row)
        np.savez_compressed(O/'slices'/f'{name}.npz',
                            epsilon=[float.fromhex(k) for k in cache.cache],log_likelihood=list(cache.cache.values()))
        rows.append(row)
    assert ledger.state['charged'] == ledger.state['completed']
    charged = sum(ledger.state['charged'].values())
    result = dict(status='SELECTED_DIAGNOSTIC_COMPLETED_NOT_2D_APPROVAL', selected_slices=len(rows),
                  states=dict(collections.Counter(r['status'] for r in rows)),
                  failures=dict(collections.Counter(r['failure_preserved'] for r in rows if 'failure_preserved' in r)),
                  original_resolved=sum(r['original_status'].startswith('SLICE_OPERATIONAL') for r in rows),
                  maximum_bridge_difference=max(r['bridge_max_delta'] for r in rows),
                  charged_new_values=charged, cumulative_values=plan['historical_charged']+charged,
                  reused_cache_values=sum(r['reused_values'] for r in rows), CPU=time.process_time()-start,
                  production_authorized=False, C10_complete=False,
                  plan_sha256=sha(O/'plan.json'), new_ORFs=0, new_observations=0)
    save(O/'complete.json',result)
    print(json.dumps(result))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--execute',action='store_true')
    args = parser.parse_args()
    execute() if args.execute else freeze()
