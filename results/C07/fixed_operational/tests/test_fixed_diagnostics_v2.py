"""Run the same10 masked-reader tests against operational v2; no PTA posteriors."""
import importlib.util
from pathlib import Path
import sys
import unittest

PACKAGE=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('fixed_masked_tests_base',PACKAGE/'tests/test_fixed_diagnostics.py')
test_base=importlib.util.module_from_spec(spec);spec.loader.exec_module(test_base)
spec=importlib.util.spec_from_file_location('inference.fixed_diagnostics_v2',PACKAGE/'src/inference/fixed_diagnostics_v2.py')
module=importlib.util.module_from_spec(spec);sys.modules[spec.name]=module;spec.loader.exec_module(module)
test_base.fixed=module


class OperationalMaskedTests(test_base.FixedDiagnosticsTests):
    pass


if __name__=='__main__':unittest.main()
