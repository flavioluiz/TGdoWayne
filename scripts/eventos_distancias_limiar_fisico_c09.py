"""Distance event diagnostics with physical truth thresholds and cached domains."""
from pathlib import Path
import hashlib
import json
import sys
import time
import resource
import numpy as np
from scipy.special import logsumexp
R = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(R/'src'))
from inference.mass_batch import MassPosteriorBatch
from inference.likelihood_events import likelihood_event_cdf


def main():
    start = time.process_time(); bindings = {}; records = []
    def bind(p): bindings[str(p.relative_to(R))] = hashlib.sha256(p.read_bytes()).hexdigest(); return p
    def read(p): return json.loads(bind(p).read_text())
    direct = R/'results/C09/physical_truth_thresholds_distance'
    receipt = read(direct/'receipt.json'); assert receipt['status'] == 'COMPLETED' and receipt['records'] == 3000
    truth = {r['curve_id']:r for r in read(direct/'records.json')}
    parents = {r['curve_id']:r for r in read(R/'results/C09/production_mass_PIT/records.json')}
    previous = {r['curve_id']:r for r in read(R/'results/C09/production_event_diagnostics/records.json')}
    for p in (Path(__file__), R/'src/inference/mass_batch.py', R/'src/inference/likelihood_events.py'): bind(p)
    base = R/'tmp/c09_distance_production_v1'
    with np.load(bind(base/'prepared/response_atlas.npz')) as f: ci = f['coarse_indices']
    for model in ('A0_CN', 'B_CN_full_variable', 'B_G_full_variable'):
        components = []
        for k in range(3):
            with np.load(bind(base/f'execution/component_{k}.npz')) as f:
                allnames = f['curves'].tolist(); columns = [i for i,n in enumerate(allnames) if n.endswith('__'+model)]
                names = [allnames[i] for i in columns]; u = f['u']; components.append(f['log_likelihood'][:, columns])
        for mode in ('correct_mixture', 'nominal_scale_only'):
            ell = logsumexp(np.array(components)+np.log([.25, .5, .25])[:, None, None], axis=0) if mode == 'correct_mixture' else components[1]
            for first in range(0, len(names), 250):
                ids = [n+'__'+mode for n in names[first:first+250]]; values = ell[:, first:first+len(ids)]
                thresholds = np.array([truth[n]['logL'] for n in ids]); outputs = []
                for nodes, likelihood, order in ((u, values, 32), (u[ci], values[ci], 32), (u, values, 16)):
                    table = MassPosteriorBatch(nodes, likelihood, order=order)
                    outputs.append(likelihood_event_cdf(table, thresholds)); del table
                for j, name in enumerate(ids):
                    low = min(float(o['strict'][j, 0]) for o in outputs); high = max(float(o['inclusive'][j, 1]) for o in outputs)
                    delta = abs(thresholds[j]-previous[name]['interpolated_truth_logL'])
                    shift = float(np.max(abs(outputs[0]['strict'][j]-np.array(previous[name]['fine_strict']))))
                    passed = high-low <= .002 and delta <= .001 and truth[name]['scipy_passed'] and parents[name]['parent_response_passed'] and parents[name]['parent_mesh_passed']
                    records.append(dict(curve_id=name, direct_logL=float(thresholds[j]), threshold_delta=float(delta),
                        event_shift_from_interpolated_threshold=shift, observed_envelope=[low, high],
                        fine_strict=outputs[0]['strict'][j].tolist(), fine_inclusive=outputs[0]['inclusive'][j].tolist(),
                        finite_operational_gates_passed=bool(passed), operational_PIT_interval=[low, high] if passed else [0., 1.],
                        physical_uniform_bound=False, scope='Direct global-mixture or nominal threshold; interpolated domain'))
                if resource.getrusage(resource.RUSAGE_SELF).ru_maxrss > 1536*1024**2: raise MemoryError('RSS cap')
            print(model, mode, len(records), flush=True)
    assert len(records) == 3000 and {r['curve_id'] for r in records} == set(truth)
    out = R/'results/C09/events_distance_direct_threshold'; out.mkdir(parents=True, exist_ok=False)
    payload = json.dumps(records, indent=2, allow_nan=False)+'\n'; (out/'records.json').write_text(payload)
    audit = dict(status='DIRECT_THRESHOLD_INTERPOLATED_DOMAIN', count=len(records),
        finite_operational_gates_passed=sum(r['finite_operational_gates_passed'] for r in records),
        threshold_gate_failures=sum(r['threshold_delta'] > .001 for r in records),
        maximum_threshold_delta=max(r['threshold_delta'] for r in records),
        maximum_event_shift=max(r['event_shift_from_interpolated_threshold'] for r in records),
        CPU=time.process_time()-start, RSS_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        new_likelihood_values=0, records_sha256=hashlib.sha256(payload.encode()).hexdigest(), inputs=bindings,
        scope='Finite operational diagnostics only; parent failures retained, no uniform physical bound')
    (out/'audit.json').write_text(json.dumps(audit, indent=2)+'\n'); print(json.dumps({k:v for k,v in audit.items() if k != 'inputs'}))


if __name__ == '__main__': main()
