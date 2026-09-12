"""Reconstruct positive-grid evidences independently from saved logL arrays."""
from pathlib import Path
import hashlib
import json
import sys
import numpy as np
from scipy.special import logsumexp
R = Path(__file__).resolve().parents[1]


def main():
    bindings = {}
    def bind(p): bindings[str(p.relative_to(R))] = hashlib.sha256(p.read_bytes()).hexdigest(); return p
    def read(p): return json.loads(bind(p).read_text())
    base = R/'tmp/c10_physical_pilot_v1'; axes = read(R/'tmp/c10_exact_lifecycle_v1/axes.json')
    summaries = read(base/'nodal_posterior_summaries.json')['payload']; checks = []
    def weights(x):
        dx = np.diff(x); return np.r_[dx[0]/2, (dx[:-1]+dx[1:])/2, dx[-1]/2]/(x[-1]-x[0])
    routes = dict(D=['A0_CN','A_CN','B_CN','A_G','B_G'], C_beta=['C_beta_CN','C_beta_G'], C_full=['C_full_CN','C_full_G'])
    for route, labels in routes.items():
        for kind, field in [('fine','fine'), ('high','high'), ('product','independent_grid')]:
            values = np.load(bind(base/f'{route}_{kind}.npy'), mmap_mode='r')
            if kind == 'product':
                u = np.r_[.001, axes['u_reference']['384']['nodes'], 1.]
                e = np.r_[0., axes['epsilon_product_reference']['nodes'], 1.]
            else:
                step = 2 if kind == 'fine' else 1
                u = np.array(axes['master_mass_nodes'])[::step]; e = np.array(axes['master_epsilon_nodes'])[::step]
            ids = range(16) if kind == 'fine' else axes['independent_reference_ids']
            assert values.shape == (len(u),len(e),len(labels),len(ids)) and np.isfinite(values).all()
            wu, we = weights(u), weights(e)
            for m,label in enumerate(labels):
                for j,i in enumerate(ids):
                    logL = values[:,:,m,j]
                    h1 = float(logsumexp(logL+np.log(wu)[:,None]+np.log(we)[None]))
                    h0 = float(logsumexp(logL[:,0]+np.log(wu)))
                    saved = summaries[f'{label}:{i}'][field]
                    delta = max(abs(h1-saved['logZ_H1']), abs(h0-saved['logZ_H0']), abs(h1-h0-saved['logBF']))
                    assert delta < 1e-10
                    checks.append(dict(analysis=label, datum_id=i, grid=kind, maximum_absolute_difference=delta))
            del values
    assert len(checks) == 216
    bind(Path(__file__))
    out = R/'results/C10/pilot_normalization_audit'; out.mkdir(parents=True,exist_ok=False)
    audit = dict(status='PASS', posterior_grids=len(checks), checks=checks, inputs=bindings,
        maximum_absolute_difference=max(r['maximum_absolute_difference'] for r in checks), new_likelihood_values=0,
        scope='Independent trapezoidal tensor weights for the positive bilinear surrogate. No physical interpolation approval or event validation.')
    (out/'audit.json').write_text(json.dumps(audit,indent=2)+'\n')
    print(json.dumps({k:v for k,v in audit.items() if k not in ('checks','inputs')}))


if __name__ == '__main__': main()
