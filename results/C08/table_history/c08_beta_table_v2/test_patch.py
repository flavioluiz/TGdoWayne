import unittest
import numpy as np
from patch_curve import stitch,coordinate
class TestPatch(unittest.TestCase):
 def fixture(self):
  b=np.array([1.,.8,.5,.25,0]);n=np.sqrt((1-b)*(1+b));x=coordinate(n);g=(2+x*x)[:,None,None].astype(complex);c=np.zeros((4,4,1,1),complex)
  for j in range(4):
   h=x[j+1]-x[j];c[j,:,0,0]=[2+x[j]**2,2*x[j]*h,h*h,0]
  p=np.unique(np.r_[n[2:],np.sqrt(1-np.array([.4,.1])**2)]);v=(2+coordinate(p)**2)[:,None,None].astype(complex);v[np.searchsorted(p,n[2:])]=g[2:]
  return n,g,c,p,v
 def test_quadratic_exact_and_join(self):
  n,g,c,p,v=self.fixture();nn,gg,cc,r=stitch(n,g,c,p,v);self.assertTrue(np.array_equal(cc[:2],c[:2]));self.assertLess(r['C1_join_error'],1e-12);self.assertLess(r['threshold_derivative_error'],1e-12)
  x=coordinate(nn);t=.37;actual=cc[:,0]+t*(cc[:,1]+t*(cc[:,2]+t*cc[:,3]));expected=(2+(x[:-1]+t*np.diff(x))**2)[:,None,None];np.testing.assert_allclose(actual,expected,atol=1e-14)
 def test_reject_changed_old_knot(self):
  n,g,c,p,v=self.fixture();v[0]+=1e-12
  with self.assertRaises(ValueError):stitch(n,g,c,p,v)
 def test_reject_missing_old_knot(self):
  n,g,c,p,v=self.fixture();p=p[:-1];v=v[:-1]
  with self.assertRaises(ValueError):stitch(n,g,c,p,v)
if __name__=='__main__':unittest.main()
