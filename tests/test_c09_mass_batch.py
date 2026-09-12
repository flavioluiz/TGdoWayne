"""Analytic multi-column posterior and monotonic W1-envelope checks."""
import unittest,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
import numpy as np
from inference.mass_batch import MassPosteriorBatch

class MassBatchTests(unittest.TestCase):
    def test_constant_likelihood_recovers_each_normalized_prior(self):
        for kind,lower in [('uniform_u',0.),('uniform_u_squared',0.),('log_uniform_u',.001)]:
            u=np.linspace(lower,1.,257);ell=np.tile([0.,730.,-730.],(len(u),1));p=MassPosteriorBatch(u,ell,prior=kind,lower=lower)
            np.testing.assert_allclose(p.summary['logZ'],[0.,730.,-730.],atol=1e-9)
            np.testing.assert_allclose(p.summary['KL'],0.,atol=1e-9)
            cuts=np.array([lower,.2,.7,1.]);truth=cuts if kind=='uniform_u' else (cuts**2 if kind=='uniform_u_squared' else np.log(cuts/lower)/np.log(1/lower))
            np.testing.assert_allclose(p.cdf(cuts),np.broadcast_to(truth[:,None],(4,3)),atol=1e-9)
            q=p.quantile_brackets();expected=p.prior_ppf(q['probabilities'])[:,None]
            self.assertTrue(np.all(q['lower']<=expected+1e-10));self.assertTrue(np.all(q['upper']>=expected-1e-10))
            bounds=p.wasserstein_bounds(cells=256);self.assertTrue(np.all(bounds['lower']<1e-9));self.assertTrue(np.all(bounds['upper']<=bounds['maximum_width']+1e-10))

    def test_distinct_tilted_columns_and_w1_known_solution(self):
        u=np.linspace(0.,1.,1001);tilts=np.array([2.,-3.]);ell=u[:,None]*tilts+[120.,-85.];p=MassPosteriorBatch(u,ell)
        cuts=np.array([0.,.2,.63,1.]);expected=np.expm1(cuts[:,None]*tilts)/np.expm1(tilts)
        np.testing.assert_allclose(p.cdf(cuts),expected,atol=3e-6)
        z=np.expm1(tilts)/tilts;mean=np.exp(tilts)/np.expm1(tilts)-1/tilts
        np.testing.assert_allclose(p.summary['mean'],mean,atol=3e-6)
        np.testing.assert_allclose(p.summary['KL'],tilts*mean-np.log(z),atol=3e-6)
        bounds=p.wasserstein_bounds(cells=256);truth=np.abs(mean-.5)
        self.assertTrue(np.all(bounds['lower']<=truth+3e-6));self.assertTrue(np.all(bounds['upper']>=truth-3e-6))
        self.assertTrue(np.all(bounds['upper']-bounds['lower']<=1/256+1e-10))

    def test_support_and_column_contracts(self):
        with self.assertRaises(ValueError):MassPosteriorBatch([.01,.5,1.],np.zeros((3,2)))
        with self.assertRaises(ValueError):MassPosteriorBatch([0.,.5,1.],np.zeros((3,2)),prior='log_uniform_u')
        p=MassPosteriorBatch([0.,.5,1.],np.zeros((3,2)))
        with self.assertRaises(ValueError):p.cdf_per_curve(np.zeros((2,3)))
        with self.assertRaises(ValueError):p.cdf([-0.01])
        with self.assertRaises(MemoryError):MassPosteriorBatch([0.,.5,1.],np.zeros((3,2)),maximum_numeric_bytes=100)
        p=MassPosteriorBatch([0.,.5,1.],np.zeros((3,2)),maximum_numeric_bytes=100000)
        with self.assertRaises(MemoryError):p.wasserstein_bounds(cells=2048)

if __name__=='__main__':unittest.main(verbosity=2)
