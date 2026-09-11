"""Deterministic independent checks, not a PTA simulation campaign."""
from pathlib import Path
import sys
import unittest
import numpy as np
from scipy import stats

BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE / 'src'))
from inference.diagnostics import (holm, clopper_pearson, uniformity_summary, paired_summary,
                         fixed_injection_summary, diagnose_sbc, binomial_summary)


class DiagnosticsTests(unittest.TestCase):
    def test_holm_known_values_and_arbitrary_order(self):
        adjusted, rejected = holm([.03, .001, .04, .02])
        np.testing.assert_allclose(adjusted, [.06, .004, .06, .06])
        np.testing.assert_array_equal(rejected, [False, True, False, False])

    def test_exact_binomial_independent_inversion(self):
        for k, n in [(0, 20), (20, 20), (4, 20), (450, 500)]:
            lo, hi = clopper_pearson(k, n)
            if k:
                self.assertAlmostEqual(stats.binom.sf(k - 1, n, lo), .025, places=11)
            if k < n:
                self.assertAlmostEqual(stats.binom.cdf(k, n, hi), .025, places=11)
        exact = stats.binomtest(450, 500).proportion_ci(method='exact')
        np.testing.assert_allclose(clopper_pearson(450, 500), [exact.low, exact.high], atol=1e-11)

    def test_ks_statistic_against_independent_scipy_frontend(self):
        values = np.array([.03, .12, .31, .55, .72, .8, .81, .98])
        got = uniformity_summary(values)
        expected = stats.kstest(values, 'uniform', method='exact')
        self.assertAlmostEqual(got['statistic'], expected.statistic, places=14)
        self.assertAlmostEqual(got['pvalue'], expected.pvalue, places=14)
        self.assertLessEqual(got['sensitivity_pvalue_lower'], got['pvalue'])
        self.assertGreaterEqual(got['sensitivity_pvalue_upper'], got['pvalue'])

    def test_paired_not_independent_errors_and_exact_discordances(self):
        x = np.array([1, 1, 1, 1, 0, 0])
        y = np.array([0, 0, 0, 1, 1, 0])
        got = paired_summary(x, y, range(6), range(6))
        self.assertEqual(got['discordant_x_only'], 3)
        self.assertEqual(got['discordant_y_only'], 1)
        self.assertAlmostEqual(got['mcnemar_exact_pvalue'], .625)
        self.assertAlmostEqual(got['paired_mc_se'], (x-y).std(ddof=1)/np.sqrt(6))
        same = paired_summary(x, x, range(6), range(6))
        self.assertEqual(same['mcnemar_exact_pvalue'], 1.)
        self.assertGreater(same['finite_sample_hoeffding_interval'][1], 0.)
        with self.assertRaises(ValueError):
            paired_summary(x, y, range(6), reversed(range(6)))

    def test_boundary_is_structural_not_binomial_point_nine(self):
        qs = np.tile([.01, .2, .6, .8], (20, 1))
        out = fixed_injection_summary(qs, 0., lower_support=0., upper_support=1.)
        self.assertEqual(out['support_to_upper90']['structural_coverage'], 1.)
        self.assertEqual(out['support_to_upper90']['covered'], 20)
        self.assertEqual(out['central_90']['covered'], 0)
        self.assertNotIn('pvalue', out['central_90'])
        self.assertGreater(out['central_90']['exact_interval'][1], 0)

    def test_strict_invalid_and_no_clipping(self):
        for x in [[-.1, .5], [0, 1.01], [.1, np.nan], ['.1', '.5']]:
            with self.assertRaises(ValueError):
                uniformity_summary(x)
        for x in [True, 3.5, '3']:
            with self.assertRaises(ValueError):
                clopper_pearson(1, x)
        with self.assertRaises(ValueError):
            binomial_summary([1, 0, 1])

    def test_campaign_gate_and_expected_sample_count(self):
        args = dict(pit=np.full((1, 16, 1), .5), quantiles=np.tile([.05, .5, .9, .95], (1, 16, 1, 1)),
                    truth=np.full((16, 1), .5), loglikelihood_pit=np.full((1, 16), .5),
                    methods=['toy'], parameters=['theta'], probabilities=[.05, .5, .9, .95],
                    groups={'toy': ['toy']}, replicate_ids=list(range(16)), expected_n=500,
                    numerical_complete=False)
        with self.assertRaises(ValueError):
            diagnose_sbc(**args)
        args['numerical_complete'] = True
        with self.assertRaises(ValueError):
            diagnose_sbc(**args)

    def test_complete_family_has_joint_pit_and_coverage_tests(self):
        u = ((np.arange(20) + .5) / 20)[None, :, None]
        out = diagnose_sbc(u, np.tile([.05, .5, .9, .95], (1, 20, 1, 1)), u[0], u[:, :, 0],
            methods=['toy'], parameters=['theta'], probabilities=[.05, .5, .9, .95],
            groups={'toy': ['toy']}, replicate_ids=list(range(20)), expected_n=20, numerical_complete=True)
        self.assertEqual(len(out['tests']), 7)
        self.assertTrue(all(row['family_size'] == 7 for row in out['tests']))


if __name__ == '__main__':
    unittest.main()
