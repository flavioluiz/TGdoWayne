"""Run C05's declared cases through checked_orf and preserve execution evidence.

Examples after integration:
  python scripts/benchmark_orf.py
  python scripts/benchmark_orf.py --verify-only results/C05/checked_benchmark_results.json

--source-root supports staging the script while evaluating the repository modules.
Only the declared output file is written; sources and configuration remain unchanged.
"""
import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from math import isfinite
from pathlib import Path
import platform
import sys
from time import perf_counter

import numpy as np
import scipy
from scipy.optimize import brentq

SCRIPT_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATHS = [f'src/pta/{name}.py' for name in
                ('__init__', '_domain', 'response', 'orf', 'validation')]


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def complex_record(value):
    return {'real': float(np.real(value)), 'imag': float(np.imag(value))}


def fingerprint(source_root, config_path):
    return {
        'source_sha256': {path: sha256(source_root / path) for path in MODULE_PATHS},
        'config_sha256': sha256(config_path), 'script_sha256': sha256(Path(__file__)),
        'numpy': np.__version__, 'scipy': scipy.__version__,
    }


def save(path, report):
    # Atomic replacement prevents a partial JSON from resembling a completed run.
    path.parent.mkdir(parents=True, exist_ok=True)
    staging = path.with_suffix(path.suffix + '.partial')
    staging.write_text(json.dumps(report, indent=2, allow_nan=False) + '\n')
    staging.replace(path)


def error_record(absolute, scale, config):
    absolute, scale = float(absolute), float(abs(scale))
    near_zero = scale <= config['near_zero_magnitude']
    relative = None if near_zero else absolute / scale
    passed = isfinite(absolute) and absolute <= config['atol']
    if relative is not None:
        passed = passed and isfinite(relative) and relative <= config['rtol']
    return {'absolute': absolute, 'relative': relative, 'scale': scale,
            'relative_masked_near_zero': near_zero,
            'absolute_limit': config['atol'], 'relative_limit': config['rtol'],
            'status': 'PASS' if passed else 'FAIL'}


def validate_config(config, max_phase):
    if config['schema_version'] != 1:
        raise ValueError('Unsupported configuration schema.')
    # A new configuration may tighten the agreed acceptance but never weaken it.
    for key, maximum in [('atol', 1e-5), ('rtol', 1e-3), ('near_zero_magnitude', 1e-5)]:
        if not isinstance(config[key], (int, float)) or isinstance(config[key], bool):
            raise ValueError(f'{key} must be a finite positive real number.')
        if not isfinite(config[key]) or not 0 < config[key] <= maximum:
            raise ValueError(f'{key} exceeds the C05 acceptance contract.')
    if config['max_phase'] != max_phase:
        raise ValueError('Configuration and response module disagree about the audited phase envelope.')
    counts = dict(Counter(case['group'] for case in config['cases']))
    if counts != config['expected_group_counts']:
        raise ValueError('Case counts differ from the declared campaign.')
    if len({case['id'] for case in config['cases']}) != len(config['cases']):
        raise ValueError('Case identifiers must be unique.')


def run_case(case, config, api, orf):
    started = perf_counter()
    coarse, fine = api.Resolution(**case['coarse']), api.Resolution(**case['fine'])
    budget = api.ResourceBudget(**config['per_call_budget'])
    group, beta = case['group'], case['beta']
    if group == 'hd_zero':
        angle = brentq(lambda z: float(orf.hellings_downs(np.cos(z))),
                       *case['root_bracket_radians'])
        ya = yb = None
    else:
        angle = case['angle_radians']
        ya = 2*np.pi*case['fL_a_over_c']
        yb = ya + case['phase_delta_b']
    cosine = float(np.cos(angle))
    wrapper_started = perf_counter()
    gamma, validation = api.checked_orf(
        beta, cosine, ya, yb, coarse=coarse, fine=fine, budget=budget,
        atol=config['atol'], rtol=config['rtol'])
    wrapper_seconds = perf_counter() - wrapper_started
    checks = {name: error_record(error, abs(gamma), config)
              for name, error in validation['errors'].items()}
    references = {'earth_only': float(orf.earth_analytic(beta, cosine))}
    reference_started = perf_counter()
    if group == 'auto' or (group == 'coherence' and angle == 0 and ya == yb):
        auto, estimate = orf.raw_auto_weighted(beta, ya, **config['auto_reference'])
        references['auto_1d'] = {'value': float(auto), 'quadrature_error_estimate': float(estimate),
                                 'parameters': config['auto_reference']}
        checks['auto_1d_reference'] = error_record(abs(gamma-auto), abs(auto), config)
    if beta == 0 and ya is not None:
        threshold = orf.threshold_full(cosine, ya, yb)
        references['threshold_exact'] = complex_record(threshold)
        checks['threshold_reference'] = error_record(abs(gamma-threshold), abs(threshold), config)
    if group == 'hd_zero':
        direct_coarse = orf.raw_direct_orf(beta, cosine,
            nmu=coarse.nmu_direct, nphi=coarse.nphi_direct)
        direct_fine = orf.raw_direct_orf(beta, cosine,
            nmu=fine.nmu_direct, nphi=fine.nphi_direct)
        references['hd_zero'] = {'angle_radians': angle, 'angle_degrees': float(np.degrees(angle)),
            'analytic_residual_at_root': float(orf.hellings_downs(cosine)),
            'direct_coarse': complex_record(direct_coarse),
            'direct_fine': complex_record(direct_fine)}
        # Root references use absolute errors; the true analytic target is zero.
        checks['hd_zero_harmonic'] = error_record(abs(gamma), 0, config)
        checks['hd_zero_direct'] = error_record(abs(direct_fine), 0, config)
        checks['hd_zero_direct_refinement'] = error_record(abs(direct_fine-direct_coarse), 0, config)
        checks['hd_zero_cross_method'] = error_record(abs(gamma-direct_fine), 0, config)
    row = {
        'id': case['id'], 'group': group,
        'status': 'PASS' if all(check['status'] == 'PASS' for check in checks.values()) else 'FAIL',
        'beta': beta, 'angle_radians': angle, 'cosine': cosine, 'ya': ya, 'yb': yb,
        'fL_a_over_c': None if ya is None else float(ya/(2*np.pi)),
        'fL_b_over_c': None if yb is None else float(yb/(2*np.pi)),
        'gamma': complex_record(gamma), 'validation': validation, 'checks': checks,
        'references': references, 'budget': config['per_call_budget'],
        'seconds': {'checked_orf': wrapper_seconds,
                    'references': perf_counter()-reference_started,
                    'total_case': perf_counter()-started},
    }
    return row


def summarize(rows):
    valid = [row for row in rows if 'checks' in row]
    summary = {'completed_cases': len(rows), 'group_counts': dict(Counter(row['group'] for row in rows)),
               'failures': [row['id'] for row in rows if row['status'] != 'PASS'], 'by_group': {}}
    for group in sorted({row['group'] for row in valid}):
        selected = [row for row in valid if row['group'] == group]
        checks = [(row['id'], name, check) for row in selected for name, check in row['checks'].items()]
        max_abs = max(checks, key=lambda item: item[2]['absolute'])
        relative = [item for item in checks if item[2]['relative'] is not None]
        max_rel = max(relative, key=lambda item: item[2]['relative']) if relative else None
        summary['by_group'][group] = {
            'maximum_absolute_error': max_abs[2]['absolute'], 'maximum_absolute_case': max_abs[0],
            'maximum_absolute_check': max_abs[1],
            'maximum_relative_error': None if max_rel is None else max_rel[2]['relative'],
            'seconds_total': sum(row['seconds']['total_case'] for row in selected),
            'seconds_largest_case': max(row['seconds']['total_case'] for row in selected),
            'max_work_units_proxy': max(row['validation']['resources']['work_units_proxy'] for row in selected),
            'max_estimated_memory_bytes': max(row['validation']['resources']['estimated_memory_bytes'] for row in selected),
        }
    if valid:
        summary['sum_checked_work_units_proxy'] = sum(row['validation']['resources']['work_units_proxy'] for row in valid)
        summary['resource_scope'] = 'Per-call wrapper estimates; additional 1D and HD-zero direct references are timed separately and are not included in this work proxy.'
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-root', type=Path, default=SCRIPT_ROOT)
    parser.add_argument('--config', type=Path, default=SCRIPT_ROOT/'configs/benchmarks_orf/c05.json')
    parser.add_argument('--output', type=Path)
    parser.add_argument('--verify-only', type=Path)
    args = parser.parse_args()
    source_root, config_path = args.source_root.resolve(), args.config.resolve()
    output = (args.output or source_root/'results/C05/checked_benchmark_results.json').resolve()
    sys.path.insert(0, str(source_root/'src'))
    from pta import validation as api
    from pta import orf
    config = json.loads(config_path.read_text())
    validate_config(config, api.MAX_VALIDATED_PHASE)
    signature = fingerprint(source_root, config_path)
    if args.verify_only:
        existing = json.loads(args.verify_only.read_text())
        if existing.get('fingerprint') != signature or existing.get('status') != 'PASS':
            raise SystemExit('Benchmark status or source/config/environment fingerprint does not match.')
        if existing.get('fingerprint_after') != signature:
            raise SystemExit('Sources changed during the recorded campaign.')
        if {row['id'] for row in existing['rows']} != {case['id'] for case in config['cases']}:
            raise SystemExit('Recorded cases differ from configuration.')
        if existing['summary'] != summarize(existing['rows']):
            raise SystemExit('Recorded summary is inconsistent with case rows.')
        if any(row['status'] != 'PASS' for row in existing['rows']):
            raise SystemExit('At least one recorded case did not pass.')
        print(f"Verified {len(existing['rows'])} cases and current source/config hashes.")
        return
    started = perf_counter()
    report = {'status': 'in_progress', 'started_utc': utc_now(), 'fingerprint': signature,
              'python': platform.python_version(), 'platform': platform.platform(),
              'config': config, 'rows': [],
              'interpretation': 'Empirical convergence of selected ORFs; no inference, no uniform precision claim over the full phase envelope.'}
    save(output, report)
    for case in config['cases']:
        try:
            row = run_case(case, config, api, orf)
        except Exception as error:
            row = {'id': case['id'], 'group': case['group'], 'status': 'FAIL',
                   'exception': type(error).__name__, 'message': str(error)}
            if hasattr(error, 'report'):
                row['validation'] = error.report
        report['rows'].append(row)
        report['elapsed_seconds'] = perf_counter()-started
        save(output, report)
        maximum = max((item['absolute'] for item in row.get('checks', {}).values()), default=float('nan'))
        seconds = row.get('seconds', {}).get('total_case', 0)
        print(f"{case['id']}: {row['status']}; max_abs={maximum:.3g}; seconds={seconds:.3f}", flush=True)
    report['fingerprint_after'] = fingerprint(source_root, config_path)
    report['summary'] = summarize(report['rows'])
    unchanged = report['fingerprint_after'] == signature
    report['status'] = 'PASS' if unchanged and not report['summary']['failures'] else 'FAIL'
    report['sources_unchanged_during_execution'] = unchanged
    report['finished_utc'] = utc_now()
    report['elapsed_seconds'] = perf_counter()-started
    save(output, report)
    print(json.dumps({'status': report['status'], 'elapsed_seconds': report['elapsed_seconds'],
                      'summary': report['summary']}, indent=2), flush=True)
    if report['status'] != 'PASS':
        raise SystemExit(1)


if __name__ == '__main__':
    main()
