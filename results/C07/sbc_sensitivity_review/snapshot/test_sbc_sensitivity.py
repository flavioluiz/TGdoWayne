import itertools
import unittest
import numpy as np
from scipy import stats
from inference.sbc_sensitivity import (pit_intervals, ecdf_envelope, ks_bounds,
    coverage_bounds, holm_sensitivity, paired_binary_bounds)
from inference.diagnostics import holm


class SensitivityTests(unittest.TestCase):
    def test_point_intervals_reproduce_exact_statistics(self):
        x = np.array([.02,.15,.48,.68,.99])
        result = ks_bounds(x,x)
        exact = stats.kstest(x,'uniform',method='exact')
        self.assertAlmostEqual(result['statistic_lower_bound'],exact.statistic)
        self.assertAlmostEqual(result['statistic_upper_bound'],exact.statistic)
        self.assertAlmostEqual(result['pvalue_lower'],exact.pvalue)
        result, certain, possible = coverage_bounds(x,x,upper_probability=.9,lower_probability=.05)
        self.assertEqual(result['certainly_covered'],3)
        np.testing.assert_array_equal(certain,possible)
        self.assertAlmostEqual(result['pvalue_lower'],stats.binomtest(3,5,.85).pvalue)

    def test_unresolved_keeps_full_denominator(self):
        p=np.array([.1,.5,.9]);s=np.array([.001,np.inf,np.nan]);r=np.array([True,False,False])
        lo,hi,report=pit_intervals(p,s,r,family_size=3)
        np.testing.assert_array_equal(lo[1:],[0,0]);np.testing.assert_array_equal(hi[1:],[1,1])
        a,b=ecdf_envelope(lo,hi,np.array([.5]))
        self.assertEqual(a[0],1/3);self.assertEqual(b[0],1.)
        self.assertEqual(report['unresolved_count'],2)

    def test_ks_envelope_contains_independent_assignments(self):
        rng=np.random.default_rng(707510101)
        lo=rng.uniform(0,.6,12);hi=lo+rng.uniform(0,.4,12)
        bound=ks_bounds(lo,hi);grid=np.linspace(0,1,101)
        gl,gu=ecdf_envelope(lo,hi,grid)
        for unused in range(128):
            x=lo+rng.uniform(size=12)*(hi-lo)
            d=stats.kstest(x,'uniform',method='exact').statistic
            self.assertLessEqual(bound['statistic_lower_bound']-1e-15,d)
            self.assertGreaterEqual(bound['statistic_upper_bound']+1e-15,d)
            ecdf=(x[:,None]<=grid).mean(axis=0)
            self.assertTrue(np.all((gl<=ecdf)&(ecdf<=gu)))

    def test_coverage_and_paired_bounds_contain_exhaustive_events(self):
        cx=np.array([True,False,False,False]);px=np.array([True,True,True,False])
        cy=np.array([False,False,True,False]);py=np.array([True,True,True,False])
        bound=paired_binary_bounds(cx,px,cy,py)
        for xx in itertools.product([False,True],repeat=4):
            x=np.array(xx)
            if np.any(cx&~x) or np.any(x&~px):continue
            for yy in itertools.product([False,True],repeat=4):
                y=np.array(yy)
                if np.any(cy&~y) or np.any(y&~py):continue
                a=int((x&~y).sum());b=int((y&~x).sum())
                p=1. if a+b==0 else stats.binomtest(a,a+b,.5).pvalue
                self.assertLessEqual(bound['pvalue_lower'],p)
                self.assertGreaterEqual(bound['pvalue_upper'],p)
                delta=float(x.mean()-y.mean())
                self.assertLessEqual(bound['mean_difference_bounds'][0],delta)
                self.assertGreaterEqual(bound['mean_difference_bounds'][1],delta)

    def test_holm_bounds_include_correlated_choices(self):
        lower=np.array([.0001,.01,.03,.25]);upper=np.array([.02,.3,.04,.5])
        bounds=holm_sensitivity(lower,upper)
        for choice in itertools.product([0.,.5,1.],repeat=4):
            p=lower+np.array(choice)*(upper-lower);adjusted,_=holm(p)
            self.assertTrue(np.all(adjusted>=bounds['holm_lower']))
            self.assertTrue(np.all(adjusted<=bounds['holm_upper']))

    def test_input_guards_preserve_invalid_observations(self):
        with self.assertRaises(ValueError):pit_intervals(np.array([1.1]),np.array([.1]),np.array([True]))
        with self.assertRaises(ValueError):pit_intervals(np.array([.1]),np.array([0.]),np.array([True]))
        with self.assertRaises(ValueError):ks_bounds([.8],[.2])
        with self.assertRaises(ValueError):holm_sensitivity([.2],[.1])
        with self.assertRaises(ValueError):paired_binary_bounds([True],[False],[False],[True])


if __name__=='__main__':unittest.main()
