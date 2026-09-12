"""Reconstruct pilot draws by explicit matrix contractions; no new observations."""
from pathlib import Path
import hashlib
import json
import sys
import time
import numpy as np
R = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(R/'src'), str(R/'tmp/c10_exact_lifecycle_v1')]
from physical import load_geometry, NodalCovariances


def main():
    start = time.process_time(); base = R/'tmp/c10_physical_pilot_v1'; bindings = {}
    def bind(p): bindings[str(p.relative_to(R))] = hashlib.sha256(p.read_bytes()).hexdigest(); return p
    def read(p): return json.loads(bind(p).read_text())
    spec = read(R/'tmp/c10_exact_lifecycle_v1/execution_spec.json')
    axes = read(R/spec['axes']['path']); protocol = read(R/spec['protocol']['path'])
    c06 = read(R/'configs/experiments/c06_moments.json'); bind(R/spec['physical_inputs']['C06_fixture']['path'])
    geometry = load_geometry(R, spec)
    with np.load(bind(base/'nodal_component.npz')) as f: provider = NodalCovariances(f['masses'], f['gamma'], geometry, protocol, c06)
    with np.load(bind(base/'generation.npz')) as f: stored = {k:f[k] for k in f.files}
    assert stored['ids'].tolist() == list(range(16))
    H = geometry['estimator_matrices']; rows = []
    for i, datum in enumerate(axes['pilot_data']):
        assert datum['id'] == i and np.array_equal(stored['truth'][i], [datum['u'], datum['epsilon']])
        c0, c1 = provider(datum['u']); cov = c0+datum['epsilon']*c1
        rng = np.random.default_rng(np.random.SeedSequence([axes['pilot_seed'], 0, i]))
        z = (rng.standard_normal((1,3,10))+1j*rng.standard_normal((1,3,10)))[0]/np.sqrt(2)
        q = np.array([np.linalg.cholesky(c)@zk for c,zk in zip(cov,z)])
        x = np.array([[np.vdot(v,h@v).real for h in H] for v in q])
        mu = np.array([[np.trace(h@c).real for h in H] for c in cov])
        sigma = np.array([[[np.trace(a@c@b@c).real for b in H] for a in H] for c in cov])
        g = np.array([m+np.linalg.cholesky(s)@(np.sqrt(2)*zk.real) for m,s,zk in zip(mu,sigma,z)])
        errors = {name:float(np.max(abs(value-stored[name][i]))/max(1.,float(np.max(abs(stored[name][i]))))) for name,value in [('q',q),('x',x),('g',g)]}
        assert max(errors.values()) < 1e-10
        rows.append(dict(id=i, errors=errors))
    for p in (Path(__file__), R/'tmp/c10_exact_lifecycle_v1/physical.py', R/'src/pta/simulation.py'): bind(p)
    out = R/'results/C10/pilot_generation_audit'; out.mkdir(parents=True, exist_ok=False)
    audit = dict(status='PASS', reconstructed_datasets=16, checks=rows, maximum_scaled_error=max(max(r['errors'].values()) for r in rows),
        CPU=time.process_time()-start, inputs=bindings, new_likelihood_values=0, new_ORFs=0,
        scope='Seeded draws and independent direct trace/quadratic contractions. Same response covariance provider; no independent ORF proof or population calibration.')
    (out/'audit.json').write_text(json.dumps(audit, indent=2)+'\n')
    print(json.dumps({k:v for k,v in audit.items() if k not in ('inputs','checks')}))


if __name__ == '__main__': main()
