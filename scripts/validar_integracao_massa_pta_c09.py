"""Compare batched posteriors with frozen independent PTA pilot references.

Only the original common fine grid supplies likelihoods. Adaptive reference
queries in the same caches are excluded. No new likelihood or ORF evaluations.
Requires archived C09 pilot and W1 executions restored to their original paths.
"""
from pathlib import Path
import argparse
import hashlib
import json
import resource
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'src'), str(ROOT / 'tmp/c09_event_repair_v1')]
import numpy as np
from inference.mass_batch import MassPosteriorBatch
from d1.grid import event_grid, exact_union
from d1.measure import Prior


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--stride', type=int, default=1,
                        help='Select every nth frozen grid node, preserving support and panel edges')
    args = parser.parse_args()
    if args.stride < 1:
        parser.error('stride must be positive')
    started = time.process_time()
    bindings = {}

    def bind(path):
        bindings[str(path.relative_to(ROOT))] = hashlib.sha256(path.read_bytes()).hexdigest()
        return path

    def read(path):
        return json.loads(bind(path).read_text())

    for path in (Path(__file__), ROOT / 'src/inference/mass_batch.py',
                 ROOT / 'tmp/c09_event_repair_v1/d1/grid.py',
                 ROOT / 'tmp/c09_event_repair_v1/d1/measure.py'):
        bind(path)
    table = bind(ROOT / 'results/C07/orf_interpolation/orf_table_pilot12x4.npz')
    with np.load(table) as data:
        grid = event_grid(data['nodes'], Prior('uniform_u'), validation_count=1)
    fine = exact_union(grid['fine_u'], [0., 1e-4, .001, .01, .8, 1.])
    if args.stride != 1:
        fine = exact_union(fine[::args.stride], [0., 1e-4, .001, .01, .8, 1.])
    reports = []
    for datum in list(range(13)) + [15]:
        base = ROOT / f'tmp/c09_D3_components_v1/posterior_execution/d{datum}'
        plan = read(base / 'plan.json')
        names = [c['curve_id'] for c in plan['curves']]
        saved = [read(base / 'results' / f'{name}.json')['results'][0] for name in names]
        prior = saved[0]['prior']
        assert all(r['prior'] == prior for r in saved)
        u = exact_union(fine[fine >= prior['lower']], [prior['lower']])
        columns = []
        for name in names:
            with np.load(bind(base / 'caches' / f'{name}.npz')) as cache:
                indices = np.searchsorted(cache['u'], u)
                assert np.all(indices < len(cache['u']))
                assert np.array_equal(cache['u'][indices], u), 'Exact cached grid required'
                columns.append(cache['log_likelihood'][indices])
        batch = MassPosteriorBatch(u, np.column_stack(columns), prior=prior['kind'], lower=prior['lower'])
        w1 = batch.wasserstein_bounds()
        quantiles = batch.quantile_brackets()
        wbase = ROOT / f'tmp/c09_D3_w1_v1/execution/nominal_{datum}'
        wplan = read(wbase / 'plan.json')
        wref = read(wbase / 'reference_2.json')
        wmap = {c['curve_id']: r for c, r in zip(wplan['curves'], wref['results'], strict=True)}
        for column, (name, result) in enumerate(zip(names, saved, strict=True)):
            reference = result['reference']
            deltas = {key: abs(float(batch.summary[key][column]) - reference[old])
                      for key, old in [('logZ', 'logZ'), ('mean', 'mean'), ('second', 'second'), ('KL', 'kl_to_prior')]}
            cdf = batch.cdf(reference['cut_values'])[:, column]
            deltas['CDF'] = float(np.max(np.abs(cdf - reference['cdf'])))
            wl, wh = float(w1['lower'][column]), float(w1['upper'][column])
            wr = wmap[name]['W1']
            deltas['W1_max_endpoint_distance'] = max(abs(wl-wr), abs(wh-wr))
            overlap = all(max(q['lower'], quantiles['lower'][i, column]) <=
                          min(q['upper'], quantiles['upper'][i, column])
                          for i, q in enumerate(result['quantiles']))
            passed = all(v <= (.002 if key == 'CDF' else .001) for key, v in deltas.items()) and overlap
            reports.append(dict(curve=name, prior=prior, nodes=len(u), deltas=deltas,
                                quantile_reference_overlap=bool(overlap), W1_interval=[wl, wh],
                                W1_reference=wr, passed=bool(passed)))
        print(f'd{datum}: {sum(r["passed"] for r in reports[-len(names):])}/{len(names)}', flush=True)
    rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    if sys.platform != 'darwin':
        rss *= 1024
    audit = dict(schema='C09_MASS_BATCH_PTA_VALIDATION_v1', results=reports, stride=args.stride,
                 passed=all(r['passed'] for r in reports) and rss <= 1536*1024**2,
                 cpu_seconds=time.process_time()-started, peak_rss_bytes=rss,
                 new_likelihood_evaluations=0, new_ORF_evaluations=0,
                 inputs_sha256=bindings,
                 scope='Frozen nominal-distance engineering pilot, three priors and ten models; no production SBC, distance-mixture or uniform physical-error certificate. Quantile overlap is consistency, not a proof of the new bracket against the physical posterior.')
    out = ROOT / 'results/C09/mass_batch_pta' / ('audit.json' if args.stride == 1 else f'stride_{args.stride}.json')
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(audit, indent=2, allow_nan=False)+'\n')
    print(json.dumps({k: v for k, v in audit.items() if k not in ('results', 'inputs_sha256')}))
    if not audit['passed']:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
