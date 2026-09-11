import sys
import unittest
from pathlib import Path
import numpy as np
from scipy import stats
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from inference.mcmc_diagnostics import (autocovariance_fft, rank_normalize, rank_rhat,
    effective_sample_size, cdf_summary, quantile_summary, split_chains,
    randomized_exchangeable_rank, ks_interval_sensitivity,
    coverage_interval_sensitivity, compare_independent_cdfs, target_diagnostics,
    central_coverage_interval_sensitivity, holm_decision_sensitivity,
    compare_reference_quantiles, bulk_tail_ess)


class DiagnosticsTests(unittest.TestCase):
    def test_fft_against_direct_lag_products(self):
        x = np.random.default_rng(1501).normal(size=(63, 4))
        centered = x - x.mean(axis=0)
        direct = np.array([(centered[:len(x)-lag] * centered[lag:]).sum(axis=0) / len(x)
                           for lag in range(len(x))])
        np.testing.assert_allclose(autocovariance_fft(x), direct, atol=1e-14)

    def test_rank_scores_ties_and_symmetry(self):
        x = np.arange(24.).reshape(6, 4)
        z = rank_normalize(x)
        np.testing.assert_allclose(np.sort(z.ravel()), -np.sort(z.ravel())[::-1], atol=1e-14)
        expected = stats.norm.ppf((stats.rankdata(x.ravel()) - .375) / (x.size + .25))
        np.testing.assert_allclose(z.ravel(), expected)
        self.assertEqual(rank_normalize(np.ones((8, 4)))[0, 0], 0)

    def test_split_drops_only_middle(self):
        x = np.arange(36.).reshape(9, 4)
        np.testing.assert_array_equal(split_chains(x), np.concatenate((x[:4], x[-4:]), axis=1))

    def test_rhat_detects_location_and_scale(self):
        x = np.random.default_rng(1502).normal(size=(4096, 4))
        shifted = x.copy(); shifted[:, 0] += 2
        scaled = x.copy(); scaled[:, 0] *= .1
        self.assertGreater(rank_rhat(shifted)['maximum'], 1.1)
        self.assertGreater(rank_rhat(scaled)['folded_rank_split'], 1.1)

    def test_constant_and_stuck_cannot_pass(self):
        x = np.ones((64, 4))
        self.assertFalse(np.isfinite(rank_rhat(x)['maximum']))
        self.assertEqual(effective_sample_size(x)['ess'], 0)
        output = cdf_summary(x, 2)
        self.assertFalse(output['precision_pass'])
        self.assertTrue(np.isinf(output['mcse']))

    def test_affine_quantile_mcse(self):
        x = np.random.default_rng(1503).normal(size=(4096, 4))
        a = quantile_summary(x, .9); b = quantile_summary(3*x + 7, .9)
        self.assertAlmostEqual(b['estimate'], 3*a['estimate']+7, 12)
        self.assertAlmostEqual(b['mcse'], 3*a['mcse'], 12)

    def test_randomized_rank_ties(self):
        rng = np.random.default_rng(1504)
        values = [randomized_exchangeable_rank(np.ones(4), 1, rng)['rank'] for _ in range(100)]
        self.assertEqual(set(values), set(range(5)))

    def test_ks_interval_encloses_bruteforce(self):
        lo = np.array([.05,.3,.6]); hi = np.array([.2,.7,.85])
        bound = ks_interval_sensitivity(lo, hi)
        rng = np.random.default_rng(1505)
        for _ in range(100):
            u = rng.uniform(lo, hi)
            d = stats.kstest(u, 'uniform').statistic
            self.assertLessEqual(bound['d_lower'], d+1e-15)
            self.assertGreaterEqual(bound['d_upper'], d-1e-15)

    def test_coverage_bounds(self):
        value = coverage_interval_sensitivity([.01,.3,.8], [.1,.7,.9], .5)
        self.assertEqual((value['count_min'],value['count_max']), (1,2))

    def test_central_coverage_and_holm_sensitivity(self):
        result=central_coverage_interval_sensitivity([0.,.2,.94],[.1,.3,1.])
        self.assertEqual((result['count_min'],result['count_max']),(1,3))
        decisions=holm_decision_sensitivity([.001,.015,.5],[.004,.04,.9])
        self.assertEqual(decisions['certain_rejections'],[True,False,False])
        self.assertEqual(decisions['possible_rejections'],[True,True,False])

    def test_reference_uses_one_twenty_cut_family(self):
        x=np.random.default_rng(1506).uniform(size=(1024,4,5))
        p=np.array([.05,.5,.9,.95]);ref=np.broadcast_to(p,(5,4))
        result=compare_reference_quantiles(x,ref,p,reference_cdf_error=.002)
        self.assertEqual(result['family_size'],20)
        for cut in result['cuts']:
            self.assertAlmostEqual(cut['cdf']['normal_critical_value'],stats.norm.isf(.05/40),14)
        self.assertFalse(result['all_cuts_accepted']) # median precision far above .00335

    def test_minimum_draw_length_works(self):
        x=np.random.default_rng(1507).normal(size=(8,4))
        result=bulk_tail_ess(x)
        self.assertTrue(np.isfinite(result['bulk']))

    def test_independent_mc_errors_add_quadratically(self):
        a={'estimate':.5,'mcse':.003,'precision_pass':True}
        b={'estimate':.51,'mcse':.004,'precision_pass':False}
        result=compare_independent_cdfs(a,b)
        self.assertAlmostEqual(result['mcse_difference'],.005)
        self.assertFalse(result['precision_pass'])

    def test_invalid_inputs_rejected(self):
        x=np.ones((16,4))
        for value in [True, '1', np.nan, np.array([1])]:
            with self.assertRaises((ValueError,TypeError)):
                cdf_summary(x,value)
        with self.assertRaises(ValueError):
            rank_rhat(np.ones((20,1)))
        with self.assertRaises(ValueError):
            target_diagnostics(np.ones((16,3,2)),[.5,.5])


if __name__ == '__main__':
    unittest.main()
