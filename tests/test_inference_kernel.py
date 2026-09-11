"""Independent distribution/density checks; run via staged harness."""
from pathlib import Path
import json
import unittest
import numpy as np
from numpy.testing import assert_allclose
from scipy.integrate import quad
from scipy.stats import multivariate_normal
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from inference.model import experiment, covariance_batch, moment_basis
from inference.likelihood_reference import cn_logpdf, normal_logpdf
from inference.quadrature import continuous_cdf, continuous_ppf
from pta.simulation import SpectralParameters,residual_covariances
from pta.statistics import quadratic_moments,proper_complex_real_covariance

HERE=Path(__file__).resolve().parents[1]


class IndependentKernelChecks(unittest.TestCase):
    def setUp(self):
        self.e=experiment(json.loads((ROOT/'configs/calibration/pilot_initial.json').read_text()))
        rng=np.random.default_rng(70709)
        z=rng.normal(size=(4,12,12))+1j*rng.normal(size=(4,12,12))
        self.g=z@z.swapaxes(-1,-2).conj()/12
        self.eta=np.array([[-15,4.3,-15.5,.1],[-14.1,3.1,-16.5,-.2]])
        self.c,self.w=covariance_batch(self.eta,self.g,self.e)

    def test_batch_covariance_matches_declared_physical_psd(self):
        for eta,got in zip(self.eta,self.c):
            expected=residual_covariances(self.e['f'],self.g,self.e['sigma'],self.e['red'],self.e['dt'],SpectralParameters(eta[0],eta[1],eta[2],4,10**eta[3]))/self.e['scale'][:,None,None]
            assert_allclose(got,expected,rtol=4e-15,atol=1e-14)

    def test_moment_polynomial_equals_direct_trace(self):
        bm,bs=moment_basis(self.g,self.e)
        m=np.einsum('nks,ksd->nkd',self.w,bm)
        s=np.einsum('nks,nkt,kstij->nkij',self.w,self.w,bs)
        expected=quadratic_moments(self.c,self.e['H'])
        assert_allclose(m,expected[0],atol=2e-13,rtol=2e-13)
        assert_allclose(s,expected[1],atol=2e-12,rtol=3e-13)

    def test_complex_density_against_independent_real_normal(self):
        rng=np.random.default_rng(11);q=rng.normal(size=(3,4,12))+1j*rng.normal(size=(3,4,12))
        got=cn_logpdf(self.c,q)
        for i,c in enumerate(self.c):
            for j,data in enumerate(q):
                expected=sum(multivariate_normal.logpdf(np.r_[qq.real,qq.imag],cov=proper_complex_real_covariance(cc)) for cc,qq in zip(c,data))
                self.assertAlmostEqual(got[i,j],expected,places=10)

    def test_real_normal_density_against_scipy(self):
        mu,sig=quadratic_moments(self.c,self.e['H']);rng=np.random.default_rng(31);x=rng.normal(size=(3,4,10))
        got=normal_logpdf(mu,sig,x)
        for i in range(2):
            for j in range(3):
                expected=sum(multivariate_normal.logpdf(xx,mean=mm,cov=ss) for xx,mm,ss in zip(x[j],mu[i],sig[i]))
                self.assertAlmostEqual(got[i,j],expected,places=8)

    def test_continuous_density_not_discrete_atoms(self):
        nodes=np.array([0,.23,.61,1]);density=2+3*nodes
        norm=3.5
        for x in [.011,.118,.529,.833,1]:
            expected=(2*x+1.5*x*x)/norm
            self.assertAlmostEqual(continuous_cdf(nodes,density,x),expected,places=14)
        for p in [.0003,.142857,.8173,.99991]:
            x=continuous_ppf(nodes,density,p)
            self.assertGreater(np.min(abs(nodes-x)),1e-6)
            self.assertAlmostEqual((2*x+1.5*x*x)/norm,p,places=12)


if __name__=='__main__':unittest.main(verbosity=2)
