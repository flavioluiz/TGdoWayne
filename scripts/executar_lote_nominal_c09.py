"""Bounded C09 production job; immutable inputs, charged failures, no truth access."""
from pathlib import Path
import argparse
import hashlib
import json
import os
import resource
import sys
import time
import traceback

for key in ('OPENBLAS_NUM_THREADS', 'OMP_NUM_THREADS', 'VECLIB_MAXIMUM_THREADS'):
    os.environ[key] = '1'
ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT/'src')] + [str(ROOT/'tmp'/p) for p in
    ('c09_D3_components_v1', 'c09_nominal14_v2', 'c09_nominal14_v4',
     'c09_D2_components_v1', 'c09_D2_continuation_v3')]
sys.path.insert(0,str(ROOT/'tmp/c09_D3_self_controls_v1'))
import numpy as np
from inference.mass_batch import MassPosteriorBatch
from inference.model import experiment
from pta.statistics import quadratic_moments
from scenarios import ScenarioCovariance
from runtime_adapter import load_table
from kernel_group import KernelGroup
from budget import Budget
from backend_checks import check_new_functions
from backend_checks import _direct_moments
from kernel import SelfControlGroup
from scipy.stats import multivariate_normal


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, allow_nan=False)+'\n')


def check_self_controls(group, table, oracle, rows, h, anchor, guard):
    """Independent trace moments and SciPy density for genuine B10 observations."""
    names=[r['curve_id'] for r in rows]
    gamma=table(oracle['u'])
    tab=group.evaluate_gamma(gamma,names,reason='backend_check')
    exact=group.evaluate_gamma(oracle['Gamma'],names,reason='backend_check')
    reports={}
    for row in rows:
        name=row['curve_id'];refs=[]
        for i in (0,len(gamma)//2,len(gamma)-1):
            reservation=guard.budget.reserve([name],1,reason='scipy_reference');success=False
            try:
                m,s=_direct_moments(group.covariance(gamma[i][None])[0],h)
                mu=sum(w*mi for w,mi in zip(group.weights,m))
                if row['variant'].endswith('fixed'):
                    _,s=_direct_moments(group.covariance(anchor[None])[0],h)
                cov=sum(w*w*si for w,si in zip(group.weights,s))
                if row['variant'].startswith('diagonal'):
                    cov=np.diag(np.diag(cov))
                value=float(multivariate_normal.logpdf(group.observations[name],mean=mu,cov=cov))
                assert np.isfinite(value)
                success=True
            finally:
                guard.budget.complete(reservation,success=success)
            refs.append(dict(u=float(oracle['u'][i]),scipy_logL=value,kernel_logL=float(tab[name][i]),delta=float(abs(value-tab[name][i]))))
        delta=float(np.max(abs(tab[name]-exact[name])))
        ds=max(r['delta'] for r in refs)
        evidence=dict(curve_id=name,accepted_finite_domain=delta<=.001 and ds<=1e-8,
            maximum_absolute_logL_difference=delta,scipy_maximum_absolute_difference=ds,
            scipy_references=refs,table_logL=tab[name].tolist(),harmonic_logL=exact[name].tolist(),
            saved_harmonic_control_count=16,uniform_probability_bound=None,
            observation_space='genuine_B10_no_synthetic_frequency_channels')
        guard.write_json('backend_checks/'+name+'.json',evidence);reports[name]=evidence
    return reports


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--plan', type=Path, required=True)
    parser.add_argument('--job', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    plan = json.loads(args.plan.read_text())
    job = next(j for j in plan['jobs'] if j['job_id'] == args.job)
    for rel, digest in plan['input_sha256'].items():
        assert sha(ROOT/rel) == digest, rel
    gridfile = args.plan.parent/'grids.npz'
    assert sha(gridfile) == plan['grids_sha256']
    with np.load(gridfile) as grid:
        fine = grid['fine_u'][grid['fine_u'] >= job['lower']]
        coarse = grid['coarse_u'][grid['coarse_u'] >= job['lower']]
    ci = np.searchsorted(fine, coarse)
    assert np.array_equal(fine[ci], coarse)
    rows = job['curves']
    # Fine table plus small moment/kernel blocks and 500-column posteriors.
    estimate = job['grid_numeric_bytes'] + 500*len(fine)*8*12 + 160*1024**2
    assert estimate < plan['numeric_array_cap_bytes']
    args.output.mkdir(parents=True, exist_ok=False)
    start, wall = time.process_time(), time.monotonic()

    class Guard:
        config = {'estimated_numeric_bytes': 1024**3}

        def check(self):
            rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
            if sys.platform != 'darwin':
                rss *= 1024
            if time.process_time()-start > 600 or time.monotonic()-wall > 900:
                raise RuntimeError('Frozen CPU600/wall900 second job limit')
            if rss > plan['process_RSS_cap_bytes']:
                raise MemoryError('Job RSS limit')

        def write_json(self, relative, value):
            write(args.output/relative, value)

    guard = Guard()
    # 16 harmonic and 16 table controls plus three independent SciPy values.
    for row in rows:
        row['additional_likelihood_cap'] = len(fine)+35
    budget = Budget(rows, additional_cap=sum(r['additional_likelihood_cap'] for r in rows),
                    historical_values=plan['historical_likelihood_values'], checkpoint=guard.check)
    guard.budget = budget
    source_files = [Path(__file__), ROOT/'src/inference/mass_batch.py',
        ROOT/'tmp/c09_D3_components_v1/scenarios.py', ROOT/'tmp/c09_nominal14_v2/kernels.py',
        ROOT/'tmp/c09_nominal14_v4/runtime_adapter.py']
    source_files += list((ROOT/'tmp/c09_D2_continuation_v3').glob('*.py'))
    source_files += list((ROOT/'tmp/c09_D2_components_v1').glob('*.py'))
    source_files += [ROOT/'src/inference/model.py', ROOT/'src/pta/statistics.py']
    source_files += [ROOT/'tmp/c09_D3_self_controls_v1/kernel.py']
    nominal_config = ROOT/'tmp/c09_nominal14_v4/config.json'
    source_files += [nominal_config, ROOT/json.loads(nominal_config.read_text())['experiment_config'],
                     ROOT/'tmp/c09_nominal14_backend_v4/gates/harmonic_nodes.npz']
    activation = dict(plan_sha256=sha(args.plan), job=job['job_id'], curves=len(rows),
        CPU_cap=600, wall_cap=900, array_estimate_bytes=estimate,
        likelihood_cap=budget.cap, source_sha256={str(p.relative_to(ROOT)):sha(p) for p in source_files},
        scope='Production conditional posterior; acceptance gates do not establish SBC calibration')
    write(args.output/'activation.json', activation)
    (args.output/'worker_source.py').write_bytes(Path(__file__).read_bytes())
    status, error, reports = 'FAILED', None, []
    try:
        config = json.loads((ROOT/'tmp/c09_nominal14_v4/config.json').read_text())
        e = experiment(json.loads((ROOT/config['experiment_config']).read_text()))
        table = load_table(ROOT/config['table_file'], config['table_sha256'], guard, expected_shape=(8336,4,12,12))
        anchor = table(np.array([.5]))[0]
        is_self=rows[0]['observation_field']=='B_gaussian'
        with np.load(ROOT/'tmp/c09_production_v1/generation'/rows[0]['file']) as datafile:
            data = {k:datafile[k] for k in (('B_gaussian',) if is_self else ('q', 'x_physical', 'x_gaussian'))}
            for row in rows:
                assert str(datafile['ids'][row['data_id']]) == row['observation_id']
        kind = rows[0]['covariance_kind']
        if kind not in ('monopole_rank1', 'dipole_rank3'):
            kind = 'monopole_rank1'
        options=dict(covariance=ScenarioCovariance(e, rows[0]['eta_physical_coordinates'],
            kind=kind, ratio=rows[0]['analysis_contaminant_ratio']), moments=lambda c:quadratic_moments(c,e['H']),
            weights=e['weights'], anchor_gamma=anchor, budget=budget)
        if is_self:
            observations={r['curve_id']:data['B_gaussian'][r['data_id']] for r in rows}
            group=SelfControlGroup(rows,observations,**options)
        else:
            group=KernelGroup(rows,data,**options)
        names = [r['curve_id'] for r in rows]
        with np.load(ROOT/'tmp/c09_nominal14_backend_v4/gates/harmonic_nodes.npz') as f:
            oracle = {k:f[k] for k in f.files}
        assert len(oracle['u']) == 16
        if is_self:
            evidence=check_self_controls(group,table,oracle,rows,e['H'],anchor,guard)
        else:
            evidence = check_new_functions([group], {n:0 for n in names}, table, oracle, rows, e['H'], anchor, guard,
                source_binding=sha(args.output/'activation.json'))
        values = np.empty((len(fine), len(rows)))
        for first in range(0, len(fine), 32):
            u = fine[first:first+32]
            evaluated = group.evaluate_gamma(table(u), names, reason='grid')
            values[first:first+len(u)] = np.column_stack([evaluated[n] for n in names])
        np.savez_compressed(args.output/'likelihoods.npz', u=fine, log_likelihood=values, curve_ids=np.array(names))
        for first in range(0,len(rows),500):
            subset = rows[first:first+500]
            ell = values[:,first:first+len(subset)]
            kwargs = dict(prior=subset[0]['prior'], lower=job['lower'])
            posterior = MassPosteriorBatch(fine, ell, **kwargs)
            comparison = MassPosteriorBatch(coarse, ell[ci], **kwargs)
            cuts = np.unique(np.r_[np.linspace(job['lower'],1,101), .2])
            delta_cdf = np.max(abs(posterior.cdf(cuts)-comparison.cdf(cuts)),axis=0)
            q, qc = posterior.quantile_brackets(), comparison.quantile_brackets()
            w, wc = posterior.wasserstein_bounds(), comparison.wasserstein_bounds()
            for j,row in enumerate(subset):
                delta = {k:abs(float(posterior.summary[k][j]-comparison.summary[k][j])) for k in posterior.summary}
                delta['CDF'] = float(delta_cdf[j])
                delta['W1'] = float(max(abs(w['upper'][j]-wc['lower'][j]), abs(wc['upper'][j]-w['lower'][j])))
                qlow = np.minimum(q['lower'][:,j],qc['lower'][:,j])
                qhigh = np.maximum(q['upper'][:,j],qc['upper'][:,j])
                passed = all(v <= (.002 if k=='CDF' else .001) for k,v in delta.items()) and np.max(qhigh-qlow)<=.001
                reports.append(dict(curve_id=row['curve_id'], summary={k:float(v[j]) for k,v in posterior.summary.items()},
                    delta=delta, quantile_probabilities=q['probabilities'].tolist(), quantile_lower=qlow.tolist(),
                    quantile_upper=qhigh.tolist(), W1=[float(w['lower'][j]),float(w['upper'][j])],
                    mesh_gate=bool(passed), finite_backend_gate=evidence[row['curve_id']]['accepted_finite_domain'],
                    mass_PIT=None, logL_event=None, calibration_complete=False))
            guard.check()
            print(json.dumps(dict(completed=len(reports), total=len(rows), CPU=time.process_time()-start)),flush=True)
        write(args.output/'posteriors.json', reports)
        status = 'COMPLETED_WITH_PER_CASE_GATES'
    except Exception:
        error = traceback.format_exc()
        print(error,flush=True)
    finally:
        peak_rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        if sys.platform != 'darwin':
            peak_rss *= 1024
        write(args.output/'receipt.json', dict(status=status,error=error,budget=budget.report(),
            CPU=time.process_time()-start,wall=time.monotonic()-wall,recorded_posteriors=len(reports),
            peak_RSS_bytes=peak_rss,
            mesh_passed=sum(r['mesh_gate'] for r in reports),
            finite_backend_passed=sum(r['finite_backend_gate'] for r in reports), C09_complete=False))
    if error:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
