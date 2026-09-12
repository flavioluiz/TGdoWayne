"""C09 production campaign: freeze nominal inference jobs without reading truths.

Preparation does not run inference. Distance mixtures retain a separate backend
requirement; compressed self-controls require their own observation adapter.
"""
from pathlib import Path
import argparse
import hashlib
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'tmp/c09_event_repair_v1')]
import numpy as np
from d1.grid import event_grid, exact_union
from d1.measure import Prior


def prepare(output):
    if output.exists():
        raise FileExistsError('Preserve existing frozen campaign; choose a new directory')
    bindings = {}

    def bind(path):
        bindings[str(path.relative_to(ROOT))] = hashlib.sha256(path.read_bytes()).hexdigest()
        return path

    def read(path):
        return json.loads(bind(path).read_text())

    bind(Path(__file__))
    for rel in ('tmp/c09_event_repair_v1/d1/grid.py', 'tmp/c09_event_repair_v1/d1/measure.py'):
        bind(ROOT / rel)
    for stride in (8, 16):
        audit = read(ROOT / f'results/C09/mass_batch_pta/stride_{stride}.json')
        assert audit['passed'] and len(audit['results']) == 140
    config = read(ROOT / 'configs/robustness/c09_production_v1.json')
    index = read(ROOT / 'tmp/c09_production_v1/generation/inference_index.json')
    assert len(index) == 5396 and len({r['id'] for r in index}) == 5396
    assert all(not {'truth_u', 'distance_scale', 'latent_seed'} & r.keys() for r in index)
    for filename in sorted({r['file'] for r in index}):
        bind(ROOT / 'tmp/c09_production_v1/generation' / filename)
    with np.load(bind(ROOT / 'results/C07/orf_interpolation/orf_table_pilot12x4.npz')) as data:
        grid = event_grid(data['nodes'], Prior('uniform_u'), validation_count=1)
    edges = [0., 1e-4, .001, .01, .8, 1.]
    original = exact_union(grid['fine_u'], edges)
    fine = exact_union(original[::8], edges)
    coarse = exact_union(original[::16], edges)
    assert np.isin(coarse, fine).all()
    grouped = {}
    pending = []
    for row in index:
        if row['stage_id'] in (2, 6):
            pending.append(dict(id=row['id'], models=row['models'], stage_id=row['stage_id'],
                                reason='compressed_self_control_adapter' if row['stage_id'] == 2 else 'distance_response_and_mixture_validation'))
            continue
        for model in row['models']:
            analysis, _, treatment = model.partition('__')
            ratio = row.get('contaminant_ratio', 0.) if treatment == 'known_included' else 0.
            key = (row['stage_id'], row['prior_id'], row['scenario_id'], tuple(row['eta']), ratio, treatment)
            grouped.setdefault(key, []).append(dict(curve_id=row['id']+'__'+model,
                data_id=row['row'], datum_id=row['datum_id'], observation_id=row['id'],
                analysis=analysis, eta_physical_coordinates=row['eta'], analysis_contaminant_ratio=ratio,
                observation_field='q' if analysis == 'A0_CN' else ('x_physical' if analysis.startswith('B_CN') else 'x_gaussian'),
                file=row['file'], prior=row['prior'], covariance_kind=row['kind']))
    jobs = []
    for number, (key, curves) in enumerate(sorted(grouped.items())):
        lower = .001 if curves[0]['prior'] == 'log_uniform_u' else 0.
        nodes = fine[fine >= lower]
        assert nodes[0] == lower
        assert len(curves) <= 5000
        jobs.append(dict(job_id=f'nominal_{number:02d}', curves=curves, lower=lower,
                         fine_nodes=len(nodes), grid_likelihood_values=len(nodes)*len(curves),
                         maximum_posterior_columns=500, likelihood_node_batch=32,
                         grid_numeric_bytes=8*len(nodes)*len(curves)))
    planned = sum(len(j['curves']) for j in jobs)
    pending_count = sum(len(r['models']) for r in pending)
    assert planned + pending_count == 25956
    grid_values = sum(j['grid_likelihood_values'] for j in jobs)
    assert grid_values + 5999394 < 120000000
    plan = dict(schema='C09_NOMINAL_PRODUCTION_PLAN_v1', execution_enabled=False,
        jobs=jobs, pending=pending, planned_posteriors=planned, pending_posteriors=pending_count,
        grid_likelihood_values=grid_values, historical_likelihood_values=5999394,
        remaining_LL_after_planned_grid=120000000-5999394-grid_values,
        criteria=dict(logZ=.001, moments=.001, KL=.001, CDF=.002, W1=.001, quantile_width=.001),
        numeric_array_cap_bytes=1024**3, process_RSS_cap_bytes=1536*1024**2,
        input_sha256=bindings, new_likelihood_evaluations=0, new_ORF_evaluations=0,
        calibration_complete=False,
        limitations=['Preparation only; executor and CPU preflight required before activation.',
                     'Pilot-tested nested grid replaces proposed GL panels for nominal likelihoods only; retain all per-case convergence failures.',
                     'Prior sensitivity panel, log-likelihood events and SBC synthesis remain required.',
                     'No uniform physical-error bound is inferred from finite pilot comparisons.'])
    output.mkdir(parents=True)
    np.savez_compressed(output / 'grids.npz', fine_u=fine, coarse_u=coarse)
    plan['grids_sha256'] = hashlib.sha256((output/'grids.npz').read_bytes()).hexdigest()
    (output/'plan.json').write_text(json.dumps(plan, indent=2, allow_nan=False)+'\n')
    print(json.dumps({k: plan[k] for k in ('planned_posteriors', 'pending_posteriors', 'grid_likelihood_values', 'remaining_LL_after_planned_grid')}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['prepare'])
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    prepare(args.output.resolve())
