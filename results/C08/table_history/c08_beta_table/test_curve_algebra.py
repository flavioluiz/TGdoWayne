import unittest
import numpy as np
from curve_algebra import evaluate,subdivide,bernstein_eigenvalues
class TestCurve(unittest.TestCase):
 def test_subdivision(self):
  rng=np.random.default_rng(808120203);nodes=np.array([0.,.3,.8,1.]);new=np.unique(np.r_[nodes,np.linspace(0,1,19)])
  c=rng.normal(size=(3,4,1,2,2))+1j*rng.normal(size=(3,4,1,2,2));sub=subdivide(nodes,c,new)
  u=rng.uniform(size=211);np.testing.assert_allclose(evaluate(nodes,c,u),evaluate(new,sub,u),rtol=2e-13,atol=2e-14)
  with self.assertRaises(ValueError):subdivide(nodes,c,np.linspace(0,1,15))
 def test_psd(self):
  c=np.zeros((3,4,1,2,2),complex);c[:,0]=np.eye(2);bernstein_eigenvalues(c)
  c[0,0,0,0,0]=-1
  with self.assertRaises(ValueError):bernstein_eigenvalues(c)
if __name__=='__main__':unittest.main(verbosity=2)
