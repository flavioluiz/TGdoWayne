from pathlib import Path
import sys
import unittest
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'src'))
from pta.fisher_information import proper_cn_features, real_gaussian_features, local_diagnostics, derivative_stencil


def real_embedding(c):
    return .5*np.concatenate((np.concatenate((c.real,-c.imag),axis=-1),
                             np.concatenate((c.imag,c.real),axis=-1)),axis=-2)


class FisherTests(unittest.TestCase):
    def test_complex_experiment_equals_doubled_real_experiment(self):
        c=np.array([[[2,.2+.3j],[.2-.3j,1]]])
        d=np.array([c, [[[.3,.1j],[-.1j,.4]]]])
        a=proper_cn_features(c,d)
        b=real_gaussian_features(real_embedding(c),real_embedding(d),np.zeros((2,1,4)))
        np.testing.assert_allclose(a.T@a,b.T@b,rtol=2e-14,atol=2e-14)
        self.assertAlmostEqual((a.T@a)[0,0],2.)

    def test_real_mean_and_variance_have_known_information(self):
        f=real_gaussian_features(np.array([[[4.]]]),np.array([[[[0.]]],[[[4.]]]]),np.array([[[1.]],[[0.]]]))
        np.testing.assert_allclose(f.T@f, np.diag([.25,.5]),atol=1e-15)

    def test_schur_matches_inverse_and_detects_exact_degeneracy(self):
        f=np.array([[1.,0.,1.],[0.,2.,0.],[0.,0.,1.],[1.,1.,0.]])
        report=local_diagnostics(f,[1.,2.,.5])
        info=np.array(report['information'])
        expected=info[:2,:2]-info[:2,2:]@np.linalg.solve(info[2:,2:],info[2:,:2])
        np.testing.assert_allclose(report['schur_information'],expected,atol=2e-14)
        singular=local_diagnostics(np.array([[1.,0.,1.],[0.,1.,0.]]),[1.,1.,1.])
        self.assertEqual(singular['rank'],2);self.assertIsNone(singular['correlation'])
        np.testing.assert_allclose(singular['schur_information'],[[0.,0.],[0.,1.]],atol=1e-15)
        self.assertEqual(singular['generalized_schur_eigenvalues'],[0.,1.])

    def test_boundary_stencils_and_rejections(self):
        for x in (.001,.2,1.):
            nodes,weights=derivative_stencil(x,.000999,.001,1.)
            self.assertTrue(np.all((nodes>=.001)&(nodes<=1)))
            self.assertAlmostEqual(float(weights@nodes**2),2*x,places=11)
        with self.assertRaises(ValueError): derivative_stencil(.5,1.,0.,1.)
        with self.assertRaises(ValueError): proper_cn_features(np.array([[[1.,1.],[0.,1.]]]),np.zeros((1,1,2,2)))
        with self.assertRaises(np.linalg.LinAlgError): proper_cn_features(np.zeros((1,1,1)),np.zeros((1,1,1,1)))


if __name__=='__main__':unittest.main()
