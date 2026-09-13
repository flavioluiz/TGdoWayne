"""Replay the ORF block of C10 Fisher, without its superseded derivative code."""
import os
for name in ('OPENBLAS_NUM_THREADS', 'OMP_NUM_THREADS', 'VECLIB_MAXIMUM_THREADS'):
    os.environ[name] = '1'
from pathlib import Path
import hashlib
import json
import resource
import runpy
import time
import numpy as np

root = Path(__file__).resolve().parents[1]
output = root / 'tmp/c13_fisher_orf'
output.mkdir(exist_ok=False)
source = root / 'scripts/refinar_fisher_escalar_c10.py'
worker = runpy.run_path(str(source))
plan = worker['read'](root / 'results/C10/fisher_v3/plan.json')
for name, expected in plan['sources'].items():
    assert worker['sha'](root / name) == expected, name
start = time.process_time()
resource.setrlimit(resource.RLIMIT_CPU, (int(start) + 60, int(start) + 61))
spec = worker['read'](root / 'tmp/c10_exact_lifecycle_v1/execution_spec.json')
geo = worker['load_geometry'](root, spec)
with np.load(root / 'tmp/c10_population_v1/nodal_component.npz') as f:
    old_index = {float(u).hex() for u in f['masses']}
masses = np.array([u for u in plan['mass_nodes'] if float(u).hex() not in old_index])
from inference.orf_blas import RealHarmonicBasis, TableBudget
from scalar_blas import RealScalarHarmonicBasis, ScalarTableBudget
new = np.empty((3, len(masses), 5, 2, 10, 10), complex)
for level, resolution in enumerate(plan['harmonic_resolutions']):
    tt = RealHarmonicBasis(geo['directions'], **resolution,
        budget=TableBudget(maximum_estimated_memory_bytes=128*1024**2), planned_batch=8)
    fp = RealScalarHarmonicBasis(geo['directions'], **resolution,
        budget=ScalarTableBudget(maximum_estimated_memory_bytes=128*1024**2), planned_batch=8)
    for case, (k, phase) in enumerate(((1, 0), (2, 1), (3, 2), (1, 1), (1, 2))):
        for a in range(0, len(masses), 8):
            b = min(a + 8, len(masses))
            beta = np.sqrt((1-masses[a:b]/k)*(1+masses[a:b]/k))
            new[level, a:b, case, 0] = tt.evaluate(beta, geo['phases'][phase])
            new[level, a:b, case, 1] = fp.evaluate(beta, geo['phases'][phase])
    del tt, fp
elapsed = time.process_time() - start
assert elapsed <= 60 and plan['historical_ORF_CPU'] + elapsed <= 600
for a, b in ((0, 1), (1, 2)):
    assert np.all(abs(new[a]-new[b]) <= 1e-5 + 1e-3*abs(new[b]))
np.savez_compressed(output / 'new_orf.npz', masses=masses, gamma=new)
reference = root / 'results/C10/fisher_v3/new_orf.npz'
assert reference.read_bytes() == (output / 'new_orf.npz').read_bytes()
report = dict(passed=True, mass_nodes=len(masses), ORF_matrices=3*len(masses)*5*2,
    reproduced_CPU=elapsed, original_CPU_cap=60,
    archive_sha256=worker['sha'](reference), source_sha256=worker['sha'](source),
    replay_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    scope='Physical tensor and scalar ORFs regenerated with the original kernels, resolutions and mass nodes; exact NPZ comparison. Replay extracts the ORF block and omits superseded derivative calculations.')
(output / 'comparison.json').write_text(json.dumps(report, indent=2)+'\n')
print(json.dumps(report))
