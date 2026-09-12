"""Freeze only missing truth/scale response pairs, without changing observations."""
from pathlib import Path
import hashlib
import json
import sys
import numpy as np
R = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(R/'src'))
from inference.orf_blas import estimate


def main():
    out = R/'tmp/c09_distance_truth_thresholds_v1'
    (out/'prepared').mkdir(parents=True, exist_ok=False)
    sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
    rowsfile = R/'tmp/c09_production_v1/prepared/rows.json'
    bankfile = R/'tmp/c09_production_v1/response_audit/truth_responses.npz'
    rows = [r for r in json.loads(rowsfile.read_text()) if r['stage_id'] == 6]
    assert len(rows) == 500
    with np.load(bankfile) as f:
        existing = {(float(u).hex(), float(s).hex()) for u, s in zip(f['u'], f['distance_scale'])}
    needed = {(float(r['truth_u']).hex(), float(s).hex()) for r in rows for s in (.9, 1., 1.1)}
    missing = sorted(needed-existing, key=lambda p:(float.fromhex(p[1]), float.fromhex(p[0])))
    assert len(needed) == 1500 and len(missing) == 735
    u = np.array([float.fromhex(p[0]) for p in missing]); scales = np.array([float.fromhex(p[1]) for p in missing])
    np.savez_compressed(out/'prepared/rules.npz', u=u, distance_scale=scales)
    resolvedfile = R/'tmp/c09_D3_components_v1/backend_execution/plan.json'
    resolved = json.loads(resolvedfile.read_text()); jobs = []
    for k, resolution in enumerate(resolved['resolutions']):
        for j, level in enumerate(resolution['levels']):
            l, n = level['lmax'], level['nmu']
            products = 4*n*(l-1)+6*144*(l-1)+len(u)*(24*n*(l-1)+6*144*(l-1)+16*12*n)
            memory = estimate(l, n, 12, 16); assert memory['estimated_memory_bytes'] < 1024**3
            jobs.append(dict(name=f'channel_{k+1}_level_{j}', channel=k, level_index=j, level=level, products=products, estimate=memory))
    products = sum(j['products'] for j in jobs)
    assert 7185+len(u) <= 8000 and 77747878549200+products <= 90000000000000
    source = R/'tmp/c09_D3_distances_v1'
    worker = (source/'worker.py').read_text()
    worker = worker.replace("with np.load(R/plan['rules_file'],allow_pickle=False) as f:u=f['u']", "with np.load(R/plan['rules_file'],allow_pickle=False) as f:u=f['u'];scales=f['distance_scale']")
    worker = worker.replace('gamma=np.empty((2,len(u),12,12),complex)', 'gamma=np.empty((len(u),12,12),complex)')
    worker = worker.replace("for s,scale in enumerate(plan['scales']):", "for scale in plan['scales']:\n  indices=np.flatnonzero(scales==scale)")
    worker = worker.replace('for first in range(0,len(u),16):\n   masses=u[first:first+16];', 'for first in range(0,len(indices),16):\n   selected=indices[first:first+16];masses=u[selected];')
    worker = worker.replace('gamma[s,first:first+len(masses)]=basis.evaluate(beta,phase)', 'gamma[selected]=basis.evaluate(beta,phase)')
    assert 'gamma[s,' not in worker and 'selected=indices' in worker
    compile(worker, 'worker.py', 'exec'); (out/'worker.py').write_text(worker)
    driver = (source/'run_backend.py').read_text().replace('1920 direct nodes, three refinements, no likelihood/data generation',
        '735 missing truth/scale pairs, three resolutions; no likelihood or data generation')
    (out/'run_backend.py').write_text(driver)
    plan = dict(schema='C09_MISSING_DISTANCE_TRUTH_RESPONSES_v1', execution_enabled_by_default=False,
        scales=[.9, 1.1], rules_file=str((out/'prepared/rules.npz').relative_to(R)), rules_sha256=sha(out/'prepared/rules.npz'),
        new_full_four_channel_nodes=len(u), reused_truth_pairs=len(needed & existing), jobs=jobs, real_products=products,
        historical_D3_nodes=7185, cumulative_D3_nodes=7185+len(u), D3_node_cap=8000,
        historical_D3_products=77747878549200, cumulative_D3_products=77747878549200+products, revised_D3_product_cap=90000000000000,
        maximum_RSS_bytes=1536*1024**2, combined_worker_CPU_cap=1440, maximum_numeric_array_bytes=1024**3,
        scope='Post-inference truth threshold components; no training-grid insertion, data regeneration or posterior refit',
        bindings={str(p.relative_to(R)):sha(p) for p in [Path(__file__), rowsfile, bankfile, resolvedfile,
            source/'worker.py', source/'run_backend.py', R/'src/inference/orf_blas.py',
            R/'configs/calibration/prior_predictive_500_v1.json', R/'results/C09/distance_broad_validation/audit.json']})
    (out/'prepared/plan.json').write_text(json.dumps(plan, indent=2)+'\n')
    print(json.dumps({k:v for k,v in plan.items() if k not in ('bindings', 'jobs')}))


if __name__ == '__main__': main()
