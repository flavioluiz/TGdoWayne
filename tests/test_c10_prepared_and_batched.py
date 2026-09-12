from pathlib import Path
import sys
import unittest
import numpy as np
from scipy.stats import multivariate_normal
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from pta.prepared_density import PreparedDensity
from pta import epsilon_taylor as original
from pta import epsilon_taylor_batched as batched


class PreparedAndBatchedTests(unittest.TestCase):
    def setUp(self):
        rng=np.random.default_rng(10012026)
        a=rng.normal(size=(3,4,4))+1j*rng.normal(size=(3,4,4))
        self.c=np.stack((a@a.conj().swapaxes(-1,-2)+np.eye(4),np.broadcast_to(.2*np.eye(4),(3,4,4))))
        self.q=rng.normal(size=(3,4))+1j*rng.normal(size=(3,4))
        self.mu=rng.normal(size=(2,3,4));self.y=rng.normal(size=(3,4))
        self.s=np.stack((self.c[0].real,self.c[1].real,np.broadcast_to(.1*np.eye(4),(3,4,4))))

    def test_normalized_laws_against_independent_scipy(self):
        e=np.array([0.,.1,.5,.95,1.])
        cn=PreparedDensity(self.c,None,self.q);normal=PreparedDensity(self.s,self.mu,self.y)
        ca=cn(e);na=normal(e)
        for j,x in enumerate(e):
            cref=0.;nref=0.
            for k in range(3):
                c=self.c[0,k]+x*self.c[1,k]
                real=.5*np.block([[c.real,-c.imag],[c.imag,c.real]])
                cref+=multivariate_normal.logpdf(np.r_[self.q[k].real,self.q[k].imag],cov=real)
                nref+=multivariate_normal.logpdf(self.y[k],mean=self.mu[0,k]+x*self.mu[1,k],cov=self.s[0,k]+x*self.s[1,k]+x*x*self.s[2,k])
            self.assertAlmostEqual(ca[j],cref,places=11);self.assertAlmostEqual(na[j],nref,places=11)
        self.assertEqual((cn.charged,cn.completed),(5,5))

    def test_batched_inequalities_match_original_channels(self):
        for n in (1,2,4,8,16):
            for j in range(n):
                a,b=j/n,(j+1)/n
                for fn,args in (('cn_taylor',(self.c,self.q)),('normal_taylor',(self.mu,self.s,self.y))):
                    old=getattr(original,fn)(*args,a,b,-15.,roundoff_allowance=1e-10)
                    new=getattr(batched,fn)(*args,a,b,-15.,roundoff_allowance=1e-10)
                    self.assertEqual(old['available'],new['available'])
                    if old['available']:
                        for key in ('lower','upper','derivative','curvature_absolute_bound'):
                            np.testing.assert_allclose(new[key],old[key],rtol=2e-14,atol=1e-13)

    def test_domain_budget_and_failed_charges_preserved(self):
        f=PreparedDensity(self.c,None,self.q,maximum_values=1)
        with self.assertRaises(ValueError):f([-1.])
        self.assertEqual(f.charged,0)
        f([.5])
        with self.assertRaises(RuntimeError):f([.5])
        broken=PreparedDensity(np.zeros((2,1,1,1)),None,np.zeros((1,1)))
        with self.assertRaises(np.linalg.LinAlgError):broken([.5])
        self.assertEqual((broken.charged,broken.completed),(1,0))


if __name__=='__main__':unittest.main()
