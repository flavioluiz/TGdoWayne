from pathlib import Path
import sys,unittest
import numpy as np
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE/'src'));sys.path.insert(0,str(ROOT/'src'));sys.path.insert(0,str(ROOT/'tmp/c08_beta_table'))
from frozen_coefficient_orf import FrozenCoefficientORF
from curve_algebra_v2 import subdivide,evaluate
from inference.orf_interpolation import EvenThresholdCubicORF
class Tests(unittest.TestCase):
 def make(self):
  n=np.array([0.,.5,1.]);m=np.array([1.,1.2,2.])[:,None,None,None]*np.eye(2)[None,None];c=np.zeros((2,4,1,2,2),complex);c[:,0]=m[:-1];c[0,1]=.2*np.eye(2);c[1,1]=1.6*np.eye(2);c[1,2]=-.8*np.eye(2);return n,m.astype(complex),c
 def test_subdivision_no_refit(self):
  n,m,c=self.make();new=np.unique(np.r_[n,[.2,.8]]);sub=subdivide(n,c,new);values=evaluate(n,c,new);t=FrozenCoefficientORF(new,values,sub,maximum_owned_numeric_bytes=10**6);x=np.linspace(0,1,113)
  np.testing.assert_allclose(t(x),evaluate(n,c,x),rtol=1e-13,atol=1e-13)
  refit=EvenThresholdCubicORF(new,values,coordinate='beta');self.assertGreater(np.max(abs(refit(x)-t(x))),1e-4)
 def test_owned(self):
  n,m,c=self.make();t=FrozenCoefficientORF(n,m,c,maximum_owned_numeric_bytes=10**6);v=t([.1]);n[1]=.7;m[:]=0;c[:]=0;np.testing.assert_array_equal(v,t([.1]));self.assertFalse(t.coeff.flags.writeable)
 def test_guards(self):
  n,m,c=self.make()
  with self.assertRaises(MemoryError):FrozenCoefficientORF(n,m,c,maximum_owned_numeric_bytes=1)
  with self.assertRaises(ValueError):FrozenCoefficientORF(np.array([0.,1e-12,1.]),m,c,maximum_owned_numeric_bytes=10**6)
  with self.assertRaises(ValueError):FrozenCoefficientORF(n,m,c.real.astype(int),maximum_owned_numeric_bytes=10**6)
  bad=c.copy();bad[0,1]*=2
  with self.assertRaises(ValueError):FrozenCoefficientORF(n,m,bad,maximum_owned_numeric_bytes=10**6)
 def test_negative_between_positive_endpoints(self):
  n=np.array([0.,1.]);m=np.ones((2,1,1,1),complex);c=np.array([1.,-8.,8.,0.],complex)[None,:,None,None,None]
  with self.assertRaises(ValueError):FrozenCoefficientORF(n,m,c,maximum_owned_numeric_bytes=10**6,require_threshold_parity=False)
if __name__=='__main__':unittest.main(verbosity=2)
