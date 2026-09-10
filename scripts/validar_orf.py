"""Run C05's original, independent and interface tests and record provenance.

--check runs all tests and verifies the stored evidence belongs to current sources;
it leaves results untouched. It does not rerun the larger benchmark campaigns.
"""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import platform
import sys
import unittest

import numpy as np
import scipy

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
REPORT = ROOT / 'results' / 'C05' / 'test_results.json'


def source_hashes():
    paths = [ROOT / 'src' / 'pta' / name for name in
             ('__init__.py', '_domain.py', 'response.py', 'orf.py', 'validation.py')]
    paths += [ROOT / 'tests' / 'test_orf.py', Path(__file__)]
    return {str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in paths}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    spec = importlib.util.spec_from_file_location('test_orf', ROOT / 'tests' / 'test_orf.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    suite = unittest.defaultTestLoader.loadTestsFromModule(module)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    report = {
        'status': 'PASS' if result.wasSuccessful() else 'FAIL',
        'tests_run': result.testsRun,
        'failures': len(result.failures), 'errors': len(result.errors),
        'python': platform.python_version(), 'numpy': np.__version__,
        'scipy': scipy.__version__, 'source_sha256': source_hashes(),
        'independent_physical_metrics': module.METRICS,
        'scope': '23 C05 tests; separate 20-case and 16-case campaigns are not rerun here.',
    }
    if args.check:
        previous = json.loads(REPORT.read_text())
        for field in ('status', 'tests_run', 'failures', 'errors', 'source_sha256', 'numpy', 'scipy'):
            if previous.get(field) != report[field]:
                raise SystemExit(f'Stored C05 evidence differs in {field}; regenerate and review it.')
    else:
        REPORT.parent.mkdir(parents=True, exist_ok=True)
        REPORT.write_text(json.dumps(report, indent=2, allow_nan=False) + '\n')
    raise SystemExit(0 if result.wasSuccessful() else 1)


if __name__ == '__main__':
    main()
