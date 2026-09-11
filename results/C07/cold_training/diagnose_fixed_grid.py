"""Cold-training comparison on 54 cuts frozen before the new IID production.

Reads no injected truth; this one-target planning check is separate from the
original 16-target validation protocol and does not approve a campaign.
"""
import os
os.environ.setdefault('VECLIB_MAXIMUM_THREADS', '1')
from pathlib import Path
import hashlib
import json
import sys
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'src'))
from inference.iid_diagnostics import (
    replicated_cdf, replicated_weights, simultaneous_differences, json_safe)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    base = Path(__file__).resolve().parent
    grid_path = ROOT / 'tmp/c07_iid_portable/results/gmm_truth_blind_planning.json'
    grid = json.loads(grid_path.read_text())
    cuts = next(t for t in grid['targets'] if t['target'] == 62)['functions']
    assert len(cuts) == 54
    hashes = {str(grid_path.relative_to(ROOT)): sha(grid_path),
              str(Path(__file__).relative_to(ROOT)): sha(Path(__file__)),
              'src/inference/iid_diagnostics.py': sha(ROOT / 'src/inference/iid_diagnostics.py')}
    levels = []
    for count in (4096, 8192):
        path = base / f'results/cold{count}_iid_N32768.npz'
        hashes[str(path.relative_to(ROOT))] = sha(path)
        with np.load(path) as data:
            assert data['targets'].tolist() == [62]
            x = data['x_unit'][:, :, 0, :]
            logw = data['log_weights'][:, :, 0]
            logl = data['log_likelihood'][:, :, 0]
        assert x.shape == (4, 32768, 5)
        rows = []
        for name in dict.fromkeys(c['function'] for c in cuts):
            group = [c for c in cuts if c['function'] == name]
            values = logl if name == 'log_likelihood' else x[:, :, int(name[-1])]
            diagnostics = replicated_cdf(values, logw, [c['cdf']['threshold'] for c in group])
            rows.extend(dict(function=name,
                             pilot_quantile_probability=c['pilot_quantile_probability'],
                             cdf=d) for c, d in zip(group, diagnostics))
        worst = max(rows, key=lambda r: r['cdf']['mcse'])
        weights = replicated_weights(logw)
        levels.append(dict(warmup_steps=count, target=62, replications=4,
                           draws_per_replication=32768, grid_points=54,
                           precise_grid_points=sum(r['cdf']['precision_pass'] for r in rows),
                           maximum_grid_mcse=worst['cdf']['mcse'],
                           worst_function=worst['function'],
                           worst_probability=worst['pilot_quantile_probability'],
                           functions=rows, weights=weights))
    a, b = levels
    contrasts = simultaneous_differences(
        [r['cdf']['estimate'] for r in a['functions']],
        [r['cdf']['mcse'] for r in a['functions']],
        [r['cdf']['estimate'] for r in b['functions']],
        [r['cdf']['mcse'] for r in b['functions']])
    evidence = simultaneous_differences(
        [a['weights']['log_evidence']], [a['weights']['log_evidence_delta_mcse']],
        [b['weights']['log_evidence']], [b['weights']['log_evidence_delta_mcse']])
    report = dict(
        status='truth_blind_one_target_planning_comparison_not_campaign_approval',
        read_npz_fields=['x_unit', 'log_weights', 'log_likelihood', 'targets'],
        no_truth_fields_read=True, target=62, model='A_G', data_index=14,
        cdf_mcse_target=.00335, levels=levels, independent_cdf_contrasts=contrasts,
        separate_descriptive_evidence_contrast=evidence, source_sha256=hashes,
        limitations=[
            '54 thresholds fixed from old GMM N1024 before these new productions; no cut optimization.',
            'Both new likelihoods use the approved 8336-node table; old logL cuts came from 553 nodes and serve only as fixed scalar cuts.',
            'Training streams and IID production streams are independent across both levels.',
            'These generic T=1 diagnostics do not impersonate the frozen T=16 benchmark.',
            'Finite IID influence/replication errors are asymptotic and do not certify unseen tails.',
            'Training size comparison of one difficult dataset cannot validate every new dataset.',
            'CDF and evidence contrasts are separate descriptive families; no combined global error claim.',
            'No requirement on evidence MCSE was retrospectively introduced.'])
    out = base / 'results/fixed_grid_diagnostics.json'
    if out.exists():
        raise FileExistsError(out)
    out.write_text(json.dumps(json_safe(report), indent=2) + '\n')
    print(json.dumps(json_safe(dict(
        levels=[{k: v for k, v in x.items() if k != 'functions'} for x in levels],
        cdf_contrasts_all_consistent=contrasts['all_consistent'],
        cdf_contrast_max_standardized=float(np.max(np.abs(contrasts['difference']) / contrasts['difference_mcse'])),
        evidence_contrast=evidence)), indent=2))


if __name__ == '__main__':
    main()
