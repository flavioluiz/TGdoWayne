"""Event stability at INTERPOLATED truth thresholds, not physical SBC validation.

No new physical response or likelihood evaluation. Parent failures are retained.
Independent direct truth thresholds remain required before physical SBC claims.
"""
from pathlib import Path
import hashlib
import json
import resource
import sys
import time
import numpy as np
from scipy.special import logsumexp
R = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(R/'src'))
from inference.mass_batch import MassPosteriorBatch
from inference.likelihood_events import likelihood_event_cdf


def main():
    start = time.process_time(); bindings = {}; records = {}
    def bind(p):
        bindings[str(p.relative_to(R))] = hashlib.sha256(p.read_bytes()).hexdigest()
        return p
    def read(p): return json.loads(bind(p).read_text())
    parents = {r['curve_id']: r for r in read(R/'results/C09/production_mass_PIT/records.json')}
    for p in (Path(__file__), R/'src/inference/mass_batch.py', R/'src/inference/likelihood_events.py'): bind(p)

    def process(u, ci, ell, names, prior, lower, replace=False):
        for first in range(0, len(names), 250):
            ids = names[first:first+250]; values = ell[:, first:first+len(ids)]
            truth = np.array([parents[n]['truth_u'] for n in ids]); columns = np.arange(len(ids))
            outputs = []; thresholds = []
            for nodes, likelihood, order in ((u, values, 32), (u[ci], values[ci], 32), (u, values, 16)):
                table = MassPosteriorBatch(nodes, likelihood, prior=prior, lower=lower, order=order)
                h = table.interpolator(np.arcsin(truth))[columns, columns]+table.shift
                outputs.append(likelihood_event_cdf(table, h)); thresholds.append(h)
                del table
            fine, coarse, quad = outputs
            for j, name in enumerate(ids):
                assert replace == (name in records)
                lo = min(float(o['strict'][j, 0]) for o in outputs)
                hi = max(float(o['inclusive'][j, 1]) for o in outputs)
                stable = hi-lo <= .002 and parents[name]['parent_mesh_passed'] and parents[name]['parent_response_passed']
                records[name] = dict(curve_id=name, interpolated_truth_logL=float(thresholds[0][j]),
                    threshold_grid_delta=float(abs(thresholds[0][j]-thresholds[1][j])),
                    fine_strict=fine['strict'][j].tolist(), fine_inclusive=fine['inclusive'][j].tolist(),
                    coarse_strict=coarse['strict'][j].tolist(), coarse_inclusive=coarse['inclusive'][j].tolist(),
                    order16_strict=quad['strict'][j].tolist(), order16_inclusive=quad['inclusive'][j].tolist(),
                    atom_mass=float(fine['atom_mass'][j]), crossings=int(fine['crossings'][j]),
                    observed_envelope=[lo, hi], interpolated_table_stable=bool(stable),
                    physical_logL_PIT_interval=[0., 1.], physical_logL_resolved=False,
                    threshold_source='PCHIP at truth; direct physical threshold pending')
            rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
            if sys.platform != 'darwin': rss *= 1024
            if rss > 1.5*1024**3: raise MemoryError('Process RSS cap exceeded')

    for campaign in ('c09_nominal_production_v1', 'c09_self_production_v1', 'c09_nominal_refinement_v1'):
        base = R/'tmp'/campaign; plan = read(base/'plan.json')
        with np.load(bind(base/'grids.npz')) as f: coarse = f['coarse_u']
        for job in plan['jobs']:
            with np.load(bind(base/'execution'/job['job_id']/'likelihoods.npz')) as f:
                u, ell, names = f['u'], f['log_likelihood'], f['curve_ids'].tolist()
            lower = job['lower']; cu = coarse[coarse >= lower]; ci = np.searchsorted(u, cu)
            assert np.array_equal(u[ci], cu)
            process(u, ci, ell, names, job['curves'][0]['prior'], lower, replace=campaign.endswith('refinement_v1'))
            print(campaign, job['job_id'], len(records), flush=True)
    base = R/'tmp/c09_distance_production_v1'
    with np.load(bind(base/'prepared/response_atlas.npz')) as f: ci = f['coarse_indices']
    for model in ('A0_CN', 'B_CN_full_variable', 'B_G_full_variable'):
        components = []
        for k in range(3):
            with np.load(bind(base/f'execution/component_{k}.npz')) as f:
                allnames = f['curves'].tolist(); columns = [i for i, n in enumerate(allnames) if n.endswith('__'+model)]
                names = [allnames[i] for i in columns]; u = f['u']; components.append(f['log_likelihood'][:, columns])
        for mode in ('correct_mixture', 'nominal_scale_only'):
            ell = logsumexp(np.array(components)+np.log([.25, .5, .25])[:, None, None], axis=0) if mode == 'correct_mixture' else components[1]
            process(u, ci, ell, [n+'__'+mode for n in names], 'uniform_u', 0.)
            print(model, mode, len(records), flush=True)
    assert set(records) == set(parents) and len(records) == 25956
    out = R/'results/C09/production_event_diagnostics'; out.mkdir(parents=True, exist_ok=False)
    payload = json.dumps(list(records.values()), indent=2, allow_nan=False)+'\n'
    (out/'records.json').write_text(payload)
    audit = dict(status='INTERPOLATED_TABLE_DIAGNOSTIC_ONLY', count=len(records),
        interpolated_table_stable=sum(r['interpolated_table_stable'] for r in records.values()),
        physical_logL_resolved=0, new_likelihood_evaluations=0, new_physical_nodes=0,
        cpu_seconds=time.process_time()-start, peak_RSS_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*(1 if sys.platform == 'darwin' else 1024),
        records_sha256=hashlib.sha256(payload.encode()).hexdigest(), inputs=bindings,
        limitation='Thresholds and event domains use PCHIP. No physical SBC resolution inferred.')
    (out/'audit.json').write_text(json.dumps(audit, indent=2)+'\n')
    print(json.dumps({k:v for k,v in audit.items() if k != 'inputs'}), flush=True)


if __name__ == '__main__': main()
