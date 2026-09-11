import json,unittest
import numpy as np
from scipy.stats import multivariate_normal
from beta_builder import HERE
from inference.model import experiment
from gate_kernel import compressed_moments,direct_trace_moments,compressed_logpdf
class TestKernel(unittest.TestCase):
 def test_trace_and_normalization(self):
  cfg=json.loads((HERE/'inputs/experiment.json').read_text());e=experiment(cfg);rng=np.random.default_rng(808120200)
  z=rng.normal(size=(4,12,12))+1j*rng.normal(size=(4,12,12));g=z@z.swapaxes(-1,-2).conj()/24
  bounds=np.array(cfg['prior']['bounds'])[1:];eta=bounds[:,0]+rng.uniform(size=(3,4))*np.diff(bounds)[:,0]
  mu,c=compressed_moments(eta,g,e);md,cd=direct_trace_moments(eta,g,e)
  np.testing.assert_allclose(mu,md,rtol=5e-13,atol=1e-12);np.testing.assert_allclose(c,cd,rtol=5e-13,atol=1e-10)
  y=rng.normal(size=(4,10));ll=compressed_logpdf(mu,c,y)
  ref=np.array([multivariate_normal.logpdf(y,mean=m,cov=v) for m,v in zip(mu,c)])
  np.testing.assert_allclose(ll,ref,rtol=1e-12,atol=1e-10)
if __name__=='__main__':unittest.main(verbosity=2)
