import unittest
import numpy as np
from curve_algebra_v2 import evaluate,subdivide,bernstein_eigenvalues
class TestCurve(unittest.TestCase):
 def test_subdivision(self):
  rng=np.random.default_rng(808120203);nodes=np.array([0.,.3,.8,1.]);new=np.unique(np.r_[nodes,np.linspace(0,1,19)])
  c=rng.normal(size=(3,4,1,2,2))+1j*rng.normal(size=(3,4,1,2,2));sub=subdivide(nodes,c,new)
  u=rng.uniform(size=211);np.testing.assert_allclose(evaluate(nodes,c,u),evaluate(new,sub,u),rtol=2e-13,atol=2e-14)
  with self.assertRaises(ValueError):subdivide(nodes,c,np.linspace(0,1,15))
 def test_invalid_transformed_width_and_integer(self):
  c=np.zeros((2,4,1,2,2),complex)
  with self.assertRaises(ValueError):evaluate([0.,1e-12,1.],c,[.5])
  with self.assertRaises(ValueError):subdivide([0.,.5,1.],c.astype(int),[0.,.25,.5,1.])
 def test_psd(self):
  c=np.zeros((3,4,1,2,2),complex);c[:,0]=np.eye(2);bernstein_eigenvalues(c)
  c[0,0,0,0,0]=-1
  with self.assertRaises(ValueError):bernstein_eigenvalues(c)
if __name__=='__main__':unittest.main(verbosity=2)
