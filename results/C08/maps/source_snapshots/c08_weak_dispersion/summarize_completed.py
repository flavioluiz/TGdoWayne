"""Read the complete finite G2/weak experiment and independently audit its metrics."""
import os
for key in ('VECLIB_MAXIMUM_THREADS', 'OPENBLAS_NUM_THREADS', 'OMP_NUM_THREADS'):
    os.environ[key] = '1'
from pathlib import Path
import argparse
import csv
import hashlib
import json
import resource
import time
import numpy as np
from scipy.linalg import eigh, cho_factor, cho_solve


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def require(ok, message):
    if not ok:
        raise ValueError(message)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--campaign', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    resource.setrlimit(resource.RLIMIT_CPU, (29, 30))
    root = args.campaign
    complete = json.loads((root/'complete.json').read_text())
    require(complete['status'] == 'FINITE_G2_WEAK_GATES_PASS_NOT_POSTERIORS_OR_ASYMPTOTIC_PROOF', 'Closed experiment required')
    require(len(complete['workers']) == 13 and complete['new_frequency_nodes'] == 67, 'Incomplete workload')
    files = {str(root/'complete.json'): sha(root/'complete.json')}
    for row in complete['workers']:
        report = root/row['name']/'report.json'
        require(sha(report) == row['report_sha256'], 'Worker receipt changed')
        value = json.loads(report.read_text())
        require(value['passed'] is True and value['authorization_sha256'] == complete['authorization_sha256'], 'Worker identity/success')
        arrays = report.parent/'arrays.npz'
        require(sha(arrays) == value['arrays_sha256'], 'Worker arrays changed')
        files[str(report)], files[str(arrays)] = sha(report), value['arrays_sha256']
    for k in range(1, 5):
        gate = root/f'channel_gate_{k:02d}.json'
        require(json.loads(gate.read_text())['passed'] is True, 'Separate resolution gate')
        files[str(gate)] = sha(gate)
    remainder_path = root/'moments_00/weak_remainders.json'
    require(sha(remainder_path) == complete['workers'][-1]['weak_remainders_sha256'], 'Remainder report changed')
    files[str(remainder_path)] = sha(remainder_path)
    with np.load(root/'moments_00/arrays.npz', allow_pickle=False) as f:
        a = {k: f[k] for k in f.files}
    require(all(np.isfinite(v).all() for v in a.values()), 'Nonfinite saved array')
    require(a['metadata'].shape == (1152, 4) and a['comparisons'].shape == (1152, 8), 'Full map shape')
    require(a['weak_metadata'].shape == (144, 3), 'Full weak grid')
    lookup = {tuple(row): i for i, row in enumerate(a['metadata'])}
    require(len(lookup) == 1152, 'Duplicate moment identity')
    fine = a['comparisons'][a['comparisons'][:, 2] == 2]
    errors, symmetry_errors = [], []
    for row in fine:
        u, ei, lev, vi, vj = row[:5]
        ip, iq = lookup[u, ei, lev, vi], lookup[u, ei, lev, vj]
        delta = a['means'][iq] - a['means'][ip]
        cp, cq = a['covariances'][ip], a['covariances'][iq]
        for c in (cp, cq):
            error = float(np.max(abs(c-c.T))/np.max(abs(c)))
            symmetry_errors.append(error)
            require(error < 1e-13, 'Symmetry exceeds declared roundoff averaging threshold')
        cp, cq = (cp+cp.T)/2, (cq+cq.T)/2
        # Independent generalized eigensolver route. No clipping/jitter.
        eigenvalues = eigh(cp, cq, eigvals_only=True, check_finite=True)
        require(np.all(eigenvalues > 0), 'Positive covariance spectrum required')
        mp = float(delta @ cho_solve(cho_factor(cp), delta))
        mq = float(delta @ cho_solve(cho_factor(cq), delta))
        kl = .5*(np.sum(eigenvalues-1-np.log(eigenvalues))+mq)
        discrepancy = float(np.linalg.norm(eigenvalues-1))
        errors.append(abs(np.array([kl, mp, discrepancy])-row[5:]))
    maxima = np.max(errors, axis=0)
    require(np.all(maxima < 1e-10), 'Independent saved-moment metric check failed')
    variants = ['B', 'C_beta', 'C_full']
    envelopes, extrema = [], []
    for vi, vj in [(0, 1), (0, 2), (1, 2)]:
        subset = fine[(fine[:, 3] == vi) & (fine[:, 4] == vj)]
        require(len(subset) == 128, 'Every contrast requires eight masses and16 vertices')
        for u in sorted(set(subset[:, 0])):
            rows = subset[subset[:, 0] == u]
            require(set(rows[:, 1]) == set(range(16)), 'Missing nuisance vertex')
            item = dict(p=variants[vi], q=variants[vj], u=float(u))
            for column, metric in [(5, 'KL'), (6, 'mean_squared_in_p'), (7, 'covariance_in_q')]:
                item[metric+'_min'] = float(rows[:, column].min())
                item[metric+'_max'] = float(rows[:, column].max())
            envelopes.append(item)
        for column, metric in [(5, 'KL'), (6, 'mean_squared_in_p'), (7, 'covariance_in_q')]:
            row = subset[np.argmax(subset[:, column])]
            extrema.append(dict(p=variants[vi], q=variants[vj], metric=metric, maximum=float(row[column]),
                                u=float(row[0]), eta_index=int(row[1]), eta=a['eta'][int(row[1])].tolist()))
    old = json.loads(remainder_path.read_text())
    weak_rows = []
    for i, (u, ei, lev) in enumerate(a['weak_metadata']):
        require(lev in (0, 1, 2), 'Unknown weak resolution')
        saved = next(x for x in old['rows'] if (x['u'], x['eta_index'], x['level']) == (u, ei, lev))
        for name in ('Gamma', 'C', 'mean', 'covariance'):
            actual, first = a['delta_'+name+'_actual'][i], a['delta_'+name+'_first'][i]
            measured = dict(actual_Frobenius=float(np.linalg.norm(actual)), first_order_Frobenius=float(np.linalg.norm(first)),
                            remainder_Frobenius=float(np.linalg.norm(actual-first)))
            require(measured == saved[name], 'Remainder not derived from saved arrays')
            if lev == 2:
                weak_rows.append(dict(u=float(u), eta_index=int(ei), quantity=name, **measured,
                    relative_remainder=measured['remainder_Frobenius']/measured['actual_Frobenius']))
    weak_envelopes = []
    for name in ('Gamma', 'C', 'mean', 'covariance'):
        for u in [.001, .002, .004]:
            rows = [r for r in weak_rows if r['quantity'] == name and r['u'] == u]
            weak_envelopes.append(dict(quantity=name, u=u,
                relative_remainder_min=min(r['relative_remainder'] for r in rows),
                relative_remainder_max=max(r['relative_remainder'] for r in rows),
                absolute_remainder_min=min(r['remainder_Frobenius'] for r in rows),
                absolute_remainder_max=max(r['remainder_Frobenius'] for r in rows)))
    args.output.mkdir(parents=True, exist_ok=False)
    for name, rows in [('g2_envelopes', envelopes), ('weak_envelopes', weak_envelopes), ('weak_cases', weak_rows)]:
        with (args.output/(name+'.csv')).open('x', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=list(rows[0]))
            writer.writeheader(); writer.writerows(rows)
    report = dict(schema='C08_COMPLETED_G2_WEAK_SUMMARY_v1', status='PASS_READ_ONLY_SUMMARY_AND_INDEPENDENT_METRICS',
        complete_sha256=sha(root/'complete.json'), source_sha256=sha(__file__), source_artifact_sha256=files,
        independent_fine_comparisons=384, independent_metric_max_errors=dict(zip(['KL', 'mean_squared_in_p', 'covariance_in_q'], maxima.tolist())),
        maximum_covariance_symmetry_roundoff=max(symmetry_errors), symmetry_averaging_threshold=1e-13,
        saved_remainder_norms_checked=576, extrema=extrema, resources=complete['resources'],
        weak_remainder_ratios=old['ratios'],
        interpretation=['Finite Gaussian distributions built from physical quadratic moments; not posterior bias or coverage.',
            'Eight u values and16 fixed nuisance vertices. Min/max envelopes are not confidence intervals.',
            'C_full phase discrepancy grows at the threshold u=1 in this finite experiment; no extrapolation from the earlier u<=.995 map.',
            'Weak expansion compares C_beta-B at fixed phases. Remainder ratios are descriptive; no global uniform error proof.',
            'Independent metrics use saved moments; physical moments/ORFs were not regenerated in this audit.'],
        numeric_arrays_bytes=sum(v.nbytes for v in a.values()), RSS_peak_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        CPU_seconds_including_imports=time.process_time(), ORF_evaluations=0, likelihood_evaluations=0, data_draws=0)
    require(report['RSS_peak_bytes'] < 128*1024**2, 'Read-only summary memory cap')
    with (args.output/'summary.json').open('x') as f:
        json.dump(report, f, indent=2, allow_nan=False); f.write('\n')
    print(json.dumps(dict(status=report['status'], summary_sha256=sha(args.output/'summary.json'),
                         independent_errors=report['independent_metric_max_errors'], CPU_seconds=report['CPU_seconds_including_imports'])))


if __name__ == '__main__':
    main()
