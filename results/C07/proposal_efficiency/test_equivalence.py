"""Portable tests for the algebraic optimizations, independent synthetic fixture."""
from pathlib import Path
import sys, unittest
import numpy as np
from scipy.special import logsumexp
from scipy.stats import multivariate_normal, multivariate_t
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
sys.path[:0]=[str(ROOT/'tmp/c07_sampler'),str(HERE)]
from multiple_rhs import MultipleRHSGaussianDefensiveProposal
from mixture_proposal_v2 import GaussianDefensiveProposal
from vector_sample import sample_single_target


class EquivalentOptimization(unittest.TestCase):
    def setUp(self):
        rng=np.random.default_rng(89172)
        self.args=[np.array([[.2,.8],[.7,.3]]),rng.normal(size=(2,2,3))]
        matrix=rng.normal(size=(2,2,3,3))
        cov=matrix@matrix.swapaxes(-1,-2)+.2*np.eye(3)
        global_chol=np.array([[[1,0,0],[.2,2,0],[-.3,.4,1]],[[2,0,0],[-.5,1,0],[.7,-.1,.8]]])
        self.args.extend([cov,rng.normal(size=(2,3)),global_chol])
        self.q=MultipleRHSGaussianDefensiveProposal(*self.args)

    def test_all_whitening_paths_and_target_axis(self):
        z=np.random.default_rng(299).normal(size=(2*129,3))*7
        expected=GaussianDefensiveProposal(*self.args).logpdf(z)
        for method in ['matmul','forward','solve']:
            np.testing.assert_allclose(self.q.logpdf(z,method=method),expected,rtol=1e-13,atol=1e-12)

    def test_scipy_joint_density(self):
        z=np.random.default_rng(230).normal(size=(2,65,3))*4
        expected=[]
        for target in range(2):
            terms=[multivariate_normal.logpdf(z[target],self.q.means[target,k],self.q.cov[target,k])+np.log(.85*self.q.weights[target,k]) for k in range(2)]
            shape=5.4*self.q.global_chol[target]@self.q.global_chol[target].T
            terms.append(multivariate_t.logpdf(z[target],loc=self.q.global_mean[target],shape=shape,df=5)+np.log(.15))
            expected.append(logsumexp(terms,axis=0))
        np.testing.assert_allclose(self.q.logpdf(z.reshape(-1,3)).reshape(2,-1),expected,rtol=1e-13,atol=1e-12)

    def test_invalid_points_and_preserved_constructor_guard(self):
        for points in [np.zeros((0,3)),np.zeros((3,3)),np.zeros((2,4)),np.ones((2,3))*np.nan,np.zeros((2,3),complex),[['x']*3]*2]:
            with self.assertRaises(ValueError):self.q.logpdf(points)
        with self.assertRaises(ValueError):self.q.logpdf(np.zeros((2,3)),method='unregistered')
        bad=[a.copy() for a in self.args];bad[-1][0,0,2]=.1
        with self.assertRaises(ValueError):MultipleRHSGaussianDefensiveProposal(*bad)
        bad=[a.copy() for a in self.args];bad[0][0]*=1.000001
        with self.assertRaises(ValueError):MultipleRHSGaussianDefensiveProposal(*bad)

    def test_grouped_sampler_against_scalar_formula_same_rng_arrays(self):
        q=MultipleRHSGaussianDefensiveProposal(*[a[:1] for a in self.args]);seed=90822;N=128
        a=np.random.default_rng(seed);b=np.random.default_rng(seed)
        z,components=sample_single_target(q,a,N)
        u=b.random(N);which=np.sum(u[:,None]>q.cumulative[0],axis=1)
        noise=b.normal(size=(N,3));chi=b.chisquare(q.nu,size=N)
        reference=[]
        for i,k in enumerate(which):
            if k<q.k:point=q.means[0,k]+q.chol[0,k]@noise[i]
            else:point=q.global_mean[0]+q.global_chol[0]@noise[i]*np.sqrt((q.nu-2)/chi[i])*q.scale
            reference.append(point)
        np.testing.assert_allclose(z,reference,rtol=1e-14,atol=1e-14)
        np.testing.assert_array_equal(which,components)
        self.assertEqual(a.bit_generator.state,b.bit_generator.state)
        with self.assertRaises(ValueError):sample_single_target(self.q,a,128)


if __name__=='__main__':unittest.main()
