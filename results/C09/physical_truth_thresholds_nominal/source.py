"""Direct saved-response truth thresholds for nominal and B10 production.

Truth is accessed only after all posterior fits; no regeneration or refitting.
Independent SciPy densities are charged alongside every kernel value.
"""
from pathlib import Path
import collections
import gc
import json
import resource
import sys
import time
import traceback
import executar_lote_nominal_c09 as worker
from backend_checks import scipy_loglike
import numpy as np

R = Path(__file__).resolve().parents[1]


def main():
    out = R/'results/C09/physical_truth_thresholds_nominal'
    out.mkdir(parents=True, exist_ok=False)
    start = time.process_time(); wall = time.monotonic(); bindings = {}; budgets = []; records = []
    def bind(p): bindings[str(p.relative_to(R))] = worker.sha(p); return p
    def read(p): return json.loads(bind(p).read_text())
    class Guard:
        config = {'estimated_numeric_bytes': 1024**3}
        def check(self):
            if time.process_time()-start > 600 or time.monotonic()-wall > 900: raise RuntimeError('CPU600/wall900 cap')
            if resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*(1 if sys.platform == 'darwin' else 1024) > 1.5*1024**3:
                raise MemoryError('RSS1.5GiB cap')
    guard = Guard()
    truth = {r['id']:r for r in read(R/'tmp/c09_production_v1/prepared/rows.json')}
    assert read(R/'tmp/c09_production_v1/response_audit/response_audit.json')['passed']
    with np.load(bind(R/'tmp/c09_production_v1/response_audit/truth_responses.npz')) as f:
        gamma, truth_u, scales = f['Gamma'], f['u'], f['distance_scale']
    config = read(R/'tmp/c09_nominal14_v4/config.json')
    exp = worker.experiment(read(R/config['experiment_config']))
    bind(R/config['table_file'])
    table = worker.load_table(R/config['table_file'], config['table_sha256'], guard, expected_shape=(8336,4,12,12))
    anchor = table(np.array([.5]))[0].copy(); del table; gc.collect()
    plans = [(campaign, read(R/'tmp'/campaign/'plan.json')) for campaign in ('c09_nominal_production_v1', 'c09_self_production_v1')]
    assert sum(len(j['curves']) for _, p in plans for j in p['jobs']) == 22956
    bind(Path(__file__))
    for module in list(sys.modules.values()):
        path = getattr(module, '__file__', None)
        if path and Path(path).suffix == '.py' and Path(path).resolve().is_relative_to(R) and '.venv' not in Path(path).parts:
            bind(Path(path).resolve())
    worker.write(out/'activation.json', dict(input_sha256=bindings.copy(), additional_cap=45912,
        historical_likelihood_values=67017097, CPU_cap=600, wall_cap=900, RSS_cap_bytes=int(1.5*1024**3),
        physical_nodes_added=0, scope='Saved physical truth responses; fixed anchors unchanged from production'))
    (out/'source.py').write_bytes(Path(__file__).read_bytes())
    status = 'FAILED'; error = None
    try:
        for campaign, plan in plans:
            for job in plan['jobs']:
                rows = [dict(r, additional_likelihood_cap=2) for r in job['curves']]
                budget = worker.Budget(rows, additional_cap=2*len(rows), historical_values=67017097, checkpoint=guard.check)
                budgets.append(budget)
                is_self = rows[0]['observation_field'] == 'B_gaussian'
                with np.load(bind(R/'tmp/c09_production_v1/generation'/rows[0]['file'])) as f:
                    data = {k:f[k] for k in (('B_gaussian',) if is_self else ('q', 'x_physical', 'x_gaussian'))}
                    for r in rows: assert str(f['ids'][r['data_id']]) == r['observation_id']
                kind = rows[0]['covariance_kind']
                if kind not in ('monopole_rank1', 'dipole_rank3'): kind = 'monopole_rank1'
                options = dict(covariance=worker.ScenarioCovariance(exp, rows[0]['eta_physical_coordinates'], kind=kind,
                    ratio=rows[0]['analysis_contaminant_ratio']), moments=lambda c:worker.quadratic_moments(c, exp['H']),
                    weights=exp['weights'], anchor_gamma=anchor, budget=budget)
                group = worker.SelfControlGroup(rows, {r['curve_id']:data['B_gaussian'][r['data_id']] for r in rows}, **options) if is_self else worker.KernelGroup(rows, data, **options)
                by_truth = collections.defaultdict(list)
                for r in rows: by_truth[r['observation_id']].append(r)
                for identity, selected in by_truth.items():
                    datum = truth[identity]; idx = datum['truth_response_index']; g = gamma[idx]
                    assert scales[idx] == 1. and truth_u[idx] == datum['truth_u']
                    values = group.evaluate_gamma(g[None], [r['curve_id'] for r in selected], reason='functional_reference')
                    for r in selected:
                        name = r['curve_id']; reservation = budget.reserve([name], 1, reason='scipy_reference'); success = False
                        try:
                            if is_self:
                                m, s = worker._direct_moments(group.covariance(g[None])[0], exp['H'])
                                mu = sum(w*mi for w, mi in zip(group.weights, m))
                                if r['variant'].endswith('fixed'): _, s = worker._direct_moments(group.covariance(anchor[None])[0], exp['H'])
                                cov = sum(w*w*si for w, si in zip(group.weights, s))
                                if r['variant'].startswith('diagonal'): cov = np.diag(np.diag(cov))
                                reference = float(worker.multivariate_normal.logpdf(group.observations[name], mean=mu, cov=cov))
                            else: reference = scipy_loglike(group, r, g, exp['H'], anchor)
                            assert np.isfinite(reference); success = True
                        finally: budget.complete(reservation, success=success)
                        value = float(values[name][0]); delta = abs(value-reference)
                        records.append(dict(curve_id=name, truth_u=float(truth_u[idx]), truth_response_index=idx,
                            logL=value, scipy_logL=reference, scipy_delta=delta, scipy_passed=delta <= 1e-8))
                worker.write(out/(job['job_id']+'.json'), records[-len(rows):])
                print(campaign, job['job_id'], len(records), flush=True)
        assert len(records) == len({r['curve_id'] for r in records}) == 22956
        status = 'COMPLETED'
    except Exception:
        error = traceback.format_exc()
    finally:
        reports = [b.report() for b in budgets]; charged = sum(b.charged for b in budgets)
        worker.write(out/'receipt.json', dict(status=status, error=error, records=len(records),
            scipy_passed=sum(r['scipy_passed'] for r in records), maximum_scipy_delta=max((r['scipy_delta'] for r in records), default=None),
            new_likelihood_values=charged, cumulative_C09=67017097+charged, budgets=reports, inputs=bindings,
            CPU=time.process_time()-start, wall=time.monotonic()-wall,
            RSS_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*(1 if sys.platform == 'darwin' else 1024)))
    if status != 'COMPLETED': raise RuntimeError(error)


if __name__ == '__main__': main()
