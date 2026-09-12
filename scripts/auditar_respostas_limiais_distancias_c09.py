"""Validate three response resolutions and assemble all 1500 truth components."""
from pathlib import Path
import hashlib
import json
import numpy as np
R = Path(__file__).resolve().parents[1]


def main():
    base = R/'tmp/c09_distance_truth_thresholds_v1'; bindings = {}
    def bind(p): bindings[str(p.relative_to(R))] = hashlib.sha256(p.read_bytes()).hexdigest(); return p
    def read(p): return json.loads(bind(p).read_text())
    plan = read(base/'prepared/plan.json'); summary = read(base/'backend_execution/summary.json')
    assert summary['all_jobs_completed'] and summary['products'] == plan['real_products']
    for p, h in plan['bindings'].items(): assert hashlib.sha256((R/p).read_bytes()).hexdigest() == h
    stages = np.empty((3, 735, 4, 12, 12), complex)
    for job in plan['jobs']:
        d = base/'backend_execution'/job['name']; receipt = read(d/'receipt.json')
        assert receipt['status'] == 'COMPLETED' and receipt['products'] == job['products']
        p = bind(d/'matrices.npz'); assert hashlib.sha256(p.read_bytes()).hexdigest() == receipt['matrix_sha256']
        with np.load(p) as f: stages[job['level_index'], :, job['channel']] = f['Gamma']
    angular = float(np.max(abs(stages[1]-stages[0]))); harmonic = float(np.max(abs(stages[2]-stages[1])))
    eig = float(np.linalg.eigvalsh(stages).min()); hermitian = float(np.max(abs(stages-stages.swapaxes(-1,-2).conj())))
    assert angular <= 1e-8 and harmonic <= 1e-8 and eig >= -1e-12 and hermitian <= 1e-12
    bank = {}
    with np.load(bind(R/'tmp/c09_production_v1/response_audit/truth_responses.npz')) as f:
        for i, (u, scale) in enumerate(zip(f['u'], f['distance_scale'])): bank[(float(u).hex(), float(scale).hex())] = f['Gamma'][i]
    with np.load(bind(base/'prepared/rules.npz')) as f:
        for i, (u, scale) in enumerate(zip(f['u'], f['distance_scale'])):
            key = (float(u).hex(), float(scale).hex()); assert key not in bank; bank[key] = stages[2, i]
    rows = [r for r in read(R/'tmp/c09_production_v1/prepared/rows.json') if r['stage_id'] == 6]
    assert len(rows) == 500
    u = np.array([r['truth_u'] for r in rows]); scales = np.array([.9, 1., 1.1])
    gamma = np.array([[bank[(float(x).hex(), float(s).hex())] for x in u] for s in scales])
    assert gamma.shape == (3, 500, 4, 12, 12)
    out = R/'results/C09/distance_truth_responses'; out.mkdir(parents=True, exist_ok=False)
    np.savez_compressed(out/'responses.npz', Gamma=gamma, u=u, scales=scales, ids=np.array([r['id'] for r in rows]))
    bind(Path(__file__))
    audit = dict(passed=True, angular_delta=angular, harmonic_delta=harmonic, minimum_eigenvalue=eig,
        hermitian_delta=hermitian, new_nodes=735, reused_nodes=765, cumulative_D3_nodes=plan['cumulative_D3_nodes'],
        new_products=summary['products'], cumulative_D3_products=plan['cumulative_D3_products'], CPU=summary['CPU'],
        responses_sha256=hashlib.sha256((out/'responses.npz').read_bytes()).hexdigest(), inputs=bindings,
        scope='Three-resolution finite response validation at all distance truth components, no uniform posterior bound')
    (out/'audit.json').write_text(json.dumps(audit, indent=2)+'\n')
    print(json.dumps({k:v for k,v in audit.items() if k != 'inputs'}))


if __name__ == '__main__': main()
