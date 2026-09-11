"""Optional deterministic batch parallelism; random-number generation stays outside."""
from concurrent.futures import ThreadPoolExecutor
import numpy as np
from .campaign_io import positive_int

class ThreadedLikelihood:
 def __init__(self,likelihood,workers=6):
  self.likelihood=likelihood;self.maximum_workers=positive_int(workers,'workers');self.workers=self.maximum_workers;self.pool=ThreadPoolExecutor(max_workers=self.maximum_workers)
 def set_workers(self,workers):
  n=positive_int(workers,'active workers')
  if n>self.maximum_workers:raise ValueError('Active worker count exceeds the frozen executor size.')
  self.workers=n
 def __call__(self,theta,targets):
  t=np.asarray(theta);ids=np.asarray(targets)
  if t.ndim!=2 or ids.shape!=(len(t),):raise ValueError('Aligned theta/target batch required.')
  if self.workers==1 or len(t)<64:return self.likelihood(theta,targets)
  bounds=np.linspace(0,len(t),min(self.workers,len(t))+1,dtype=int);jobs=[self.pool.submit(self.likelihood,t[a:b],ids[a:b]) for a,b in zip(bounds[:-1],bounds[1:])]
  return np.concatenate([job.result() for job in jobs])
 def close(self):self.pool.shutdown(wait=True)
