"""Physical truth likelihood components and global distance-mixture thresholds."""
from pathlib import Path
import gc
import json
import sys
import time
import traceback
import executar_lote_nominal_c09 as w
from backend_checks import scipy_loglike
from scipy.special import logsumexp
import numpy as np
R = w.ROOT


def main():
    out = R/'results/C09/physical_truth_thresholds_distance'; out.mkdir(parents=True, exist_ok=False)
    bindings = {}; start = time.process_time(); wall = time.monotonic()
    def bind(p): bindings[str(p.relative_to(R))] = w.sha(p); return p
    def read(p): return json.loads(bind(p).read_text())
    audit = read(R/'results/C09/distance_truth_responses/audit.json'); assert audit['passed']
    response = bind(R/'results/C09/distance_truth_responses/responses.npz'); assert w.sha(response) == audit['responses_sha256']
    with np.load(response) as f: gamma, u, ids = f['Gamma'], f['u'], f['ids'].tolist()
    rows = read(R/'tmp/c09_distance_production_v1/execution/activation.json')['rows']
    assert len(rows) == 1500
    for r in rows: r['additional_likelihood_cap'] = 6
    class Guard:
        config = {'estimated_numeric_bytes': 1024**3}
        def check(self):
            if time.process_time()-start > 180 or time.monotonic()-wall > 240: raise RuntimeError('CPU180/wall240 cap')
            if w.resource.getrusage(w.resource.RUSAGE_SELF).ru_maxrss > 1536*1024**2: raise MemoryError('RSS cap')
    guard = Guard(); budget = w.Budget(rows, additional_cap=9000, historical_values=67063009, checkpoint=guard.check)
    config = read(R/'tmp/c09_nominal14_v4/config.json'); exp = w.experiment(read(R/config['experiment_config']))
    bind(R/config['table_file']); table = w.load_table(R/config['table_file'], config['table_sha256'], guard, expected_shape=(8336,4,12,12))
    anchor = table(np.array([.5]))[0].copy(); del table; gc.collect()
    with np.load(bind(R/'tmp/c09_production_v1/generation/stage_6.npz')) as f:
        data = {k:f[k] for k in ('q', 'x_physical', 'x_gaussian')}; assert f['ids'].tolist() == ids
    group = w.KernelGroup(rows, data, covariance=w.ScenarioCovariance(exp, rows[0]['eta_physical_coordinates'], ratio=0.),
        moments=lambda c:w.quadratic_moments(c, exp['H']), weights=exp['weights'], anchor_gamma=anchor, budget=budget)
    for module in list(sys.modules.values()):
        path = getattr(module, '__file__', None)
        if path and Path(path).suffix == '.py' and Path(path).resolve().is_relative_to(R) and '.venv' not in Path(path).parts: bind(Path(path).resolve())
    bind(Path(__file__)); w.write(out/'activation.json', dict(inputs=bindings.copy(), additional_cap=9000, CPU_cap=180, wall_cap=240, historical_C09=67063009))
    (out/'source.py').write_bytes(Path(__file__).read_bytes())
    records = []; status = 'FAILED'; error = None
    try:
        for i, identity in enumerate(ids):
            selected = [r for r in rows if r['data_id'] == i]; assert len(selected) == 3
            assert all(r['curve_id'].split('__')[0] == identity for r in selected)
            names = [r['curve_id'] for r in selected]; components = []; reference = []
            for s in range(3):
                values = group.evaluate_gamma(gamma[s, i][None], names, reason='functional_reference'); refs = []
                for r in selected:
                    reservation = budget.reserve([r['curve_id']], 1, reason='scipy_reference'); success = False
                    try:
                        value = scipy_loglike(group, r, gamma[s, i], exp['H'], anchor); assert np.isfinite(value); success = True
                    finally: budget.complete(reservation, success=success)
                    refs.append(value)
                components.append([float(values[n][0]) for n in names]); reference.append(refs)
            components = np.array(components); reference = np.array(reference)
            mixture = logsumexp(components+np.log([.25, .5, .25])[:, None], axis=0)
            for j, name in enumerate(names):
                delta = float(np.max(abs(components[:, j]-reference[:, j])))
                for mode, value in [('correct_mixture', mixture[j]), ('nominal_scale_only', components[1, j])]:
                    records.append(dict(curve_id=name+'__'+mode, truth_u=float(u[i]), logL=float(value),
                        component_logL=components[:, j].tolist(), scipy_component_logL=reference[:, j].tolist(),
                        scipy_delta=delta, scipy_passed=delta <= 1e-8))
        assert len(records) == len({r['curve_id'] for r in records}) == 3000
        w.write(out/'records.json', records); status = 'COMPLETED'
    except Exception: error = traceback.format_exc()
    finally:
        w.write(out/'receipt.json', dict(status=status, error=error, records=len(records), inputs=bindings, budget=budget.report(),
            scipy_passed=sum(r['scipy_passed'] for r in records), maximum_scipy_delta=max((r['scipy_delta'] for r in records), default=None),
            CPU=time.process_time()-start, RSS_bytes=w.resource.getrusage(w.resource.RUSAGE_SELF).ru_maxrss,
            scope='Global mixture after all channels; no averaging of covariance or per-channel mixtures'))
    if status != 'COMPLETED': raise RuntimeError(error)
    print(status, len(records), budget.report()['cumulative_values'])


if __name__ == '__main__': main()
