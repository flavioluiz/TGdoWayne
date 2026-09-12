"""Event integration at direct truth logL; response-domain error remains separate."""
from pathlib import Path
import hashlib
import json
import sys
import time
import resource
import numpy as np
R = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(R/'src'))
from inference.mass_batch import MassPosteriorBatch
from inference.likelihood_events import likelihood_event_cdf


def main():
    start = time.process_time(); bindings = {}; records = {}
    def bind(p): bindings[str(p.relative_to(R))] = hashlib.sha256(p.read_bytes()).hexdigest(); return p
    def read(p): return json.loads(bind(p).read_text())
    base = R/'results/C09/physical_truth_thresholds_nominal'
    receipt = read(base/'receipt.json'); assert receipt['status'] == 'COMPLETED' and receipt['records'] == 22956
    for rel, digest in receipt['inputs'].items(): assert hashlib.sha256((R/rel).read_bytes()).hexdigest() == digest
    truth = {}
    for p in sorted(base.glob('nominal_*.json'))+sorted(base.glob('self_*.json')):
        for row in read(p):
            assert row['curve_id'] not in truth; truth[row['curve_id']] = row
    assert len(truth) == 22956
    parents = {r['curve_id']:r for r in read(R/'results/C09/production_mass_PIT/records.json')}
    previous = {r['curve_id']:r for r in read(R/'results/C09/production_event_diagnostics/records.json')}
    for p in (Path(__file__), R/'src/inference/mass_batch.py', R/'src/inference/likelihood_events.py'): bind(p)
    for campaign in ('c09_nominal_production_v1', 'c09_self_production_v1', 'c09_nominal_refinement_v1'):
        base = R/'tmp'/campaign; plan = read(base/'plan.json')
        with np.load(bind(base/'grids.npz')) as f: coarse = f['coarse_u']
        for job in plan['jobs']:
            with np.load(bind(base/'execution'/job['job_id']/'likelihoods.npz')) as f:
                u, ell, names = f['u'], f['log_likelihood'], f['curve_ids'].tolist()
            lower = job['lower']; cu = coarse[coarse >= lower]; ci = np.searchsorted(u, cu); assert np.array_equal(u[ci], cu)
            for first in range(0, len(names), 250):
                ids = names[first:first+250]; values = ell[:, first:first+len(ids)]
                thresholds = np.array([truth[n]['logL'] for n in ids]); outputs = []
                for nodes, likelihood, order in ((u, values, 32), (u[ci], values[ci], 32), (u, values, 16)):
                    table = MassPosteriorBatch(nodes, likelihood, prior=job['curves'][0]['prior'], lower=lower, order=order)
                    outputs.append(likelihood_event_cdf(table, thresholds)); del table
                for j, name in enumerate(ids):
                    assert (name in records) == campaign.endswith('refinement_v1')
                    low = min(float(o['strict'][j, 0]) for o in outputs); high = max(float(o['inclusive'][j, 1]) for o in outputs)
                    threshold_delta = abs(thresholds[j]-previous[name]['interpolated_truth_logL'])
                    event_shift = float(np.max(abs(outputs[0]['strict'][j]-np.array(previous[name]['fine_strict']))))
                    passed = high-low <= .002 and threshold_delta <= .001 and truth[name]['scipy_passed'] and parents[name]['parent_response_passed'] and parents[name]['parent_mesh_passed']
                    records[name] = dict(curve_id=name, direct_logL=float(thresholds[j]), threshold_delta=float(threshold_delta),
                        event_shift_from_interpolated_threshold=event_shift, observed_envelope=[low, high],
                        fine_strict=outputs[0]['strict'][j].tolist(), fine_inclusive=outputs[0]['inclusive'][j].tolist(),
                        finite_operational_gates_passed=bool(passed), operational_PIT_interval=[low, high] if passed else [0., 1.],
                        physical_uniform_bound=False, scope='Direct truth threshold; interpolated event domain, observed numerical envelope')
                rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*(1 if sys.platform == 'darwin' else 1024)
                if rss > 1.5*1024**3: raise MemoryError('RSS cap exceeded')
            print(campaign, job['job_id'], len(records), flush=True)
    assert set(records) == set(truth)
    out = R/'results/C09/events_direct_threshold'; out.mkdir(parents=True, exist_ok=False)
    payload = json.dumps(list(records.values()), indent=2, allow_nan=False)+'\n'; (out/'records.json').write_text(payload)
    audit = dict(status='DIRECT_THRESHOLD_INTERPOLATED_DOMAIN', count=len(records),
        finite_operational_gates_passed=sum(r['finite_operational_gates_passed'] for r in records.values()),
        threshold_gate_failures=sum(r['threshold_delta'] > .001 for r in records.values()),
        maximum_threshold_delta=max(r['threshold_delta'] for r in records.values()),
        maximum_event_shift=max(r['event_shift_from_interpolated_threshold'] for r in records.values()),
        CPU=time.process_time()-start, RSS_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*(1 if sys.platform == 'darwin' else 1024),
        new_likelihood_values=0, records_sha256=hashlib.sha256(payload.encode()).hexdigest(), inputs=bindings,
        scope='Finite operational diagnostics; no uniform physical bound. Distance analyses still pending.')
    (out/'audit.json').write_text(json.dumps(audit, indent=2)+'\n')
    print(json.dumps({k:v for k,v in audit.items() if k != 'inputs'}))


if __name__ == '__main__': main()
