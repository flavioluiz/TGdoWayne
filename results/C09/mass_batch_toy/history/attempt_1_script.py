#!/usr/bin/env python3
"""500 analytic truncated-normal columns validate batch integration; no PTA data."""
from pathlib import Path
import os,sys,json,time,resource,hashlib
for k in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','VECLIB_MAXIMUM_THREADS'):os.environ[k]='1'
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'src'))
import numpy as np
from scipy.stats import truncnorm,norm
from inference.mass_batch import MassPosteriorBatch
def main():
 start=time.process_time();n=500;mu=np.linspace(.05,.95,n);sigma=np.linspace(.07,.3,n);a=-mu/sigma;b=(1-mu)/sigma;shifts=np.linspace(-730,730,n)
 mean=truncnorm.mean(a,b,loc=mu,scale=sigma);var=truncnorm.var(a,b,loc=mu,scale=sigma);logz=np.log(sigma*np.sqrt(2*np.pi)*(norm.cdf(b)-norm.cdf(a)))
 KL=-.5*(var+(mean-mu)**2)/sigma**2-logz
 p=np.array([.05,.5,.9,.95]);quantiles=truncnorm.ppf(p[:,None],a,b,loc=mu,scale=sigma)
 runs=[]
 for nodes in (321,641):
  u=np.sin(np.linspace(0,np.pi/2,nodes));u[-1]=1.;ell=-.5*((u[:,None]-mu)/sigma)**2+shifts
  table=MassPosteriorBatch(u,ell);q=table.quantile_brackets();w=table.wasserstein_bounds()
  cuts=np.vstack((mu,np.full(n,.2),np.full(n,.7)));cdf=table.cdf_per_curve(cuts);exact=truncnorm.cdf(cuts,a,b,loc=mu,scale=sigma)
  delta=dict(logZ=float(np.max(abs(table.summary['logZ']-(logz+shifts)))),mean=float(np.max(abs(table.summary['mean']-mean))),second=float(np.max(abs(table.summary['second']-(var+mean**2)))),KL=float(np.max(abs(table.summary['KL']-KL))),CDF=float(np.max(abs(cdf-exact))))
  assert all(v<1e-5 for v in delta.values()),delta
  assert np.all(q['lower']<=quantiles+1e-5) and np.all(q['upper']>=quantiles-1e-5)
  assert np.max(q['upper']-q['lower'])<=.00049
  # Independent dense trapezoid of the analytic CDF, with its grid error kept
  # much smaller than the monotonic envelope width for this numerical check.
  grid=np.linspace(0,1,20001);reference=np.trapezoid(abs(truncnorm.cdf(grid[:,None],a,b,loc=mu,scale=sigma)-grid[:,None]),grid,axis=0)
  assert np.all(w['lower']<=reference+1e-5) and np.all(w['upper']>=reference-1e-5)
  runs.append(dict(nodes=nodes,columns=n,max_deltas=delta,max_quantile_bracket=float(np.max(q['upper']-q['lower'])),max_W1_envelope_width=float(np.max(w['upper']-w['lower'])),all_analytic_W1_inside=True))
 out=R/'results/C09/mass_batch_toy';out.mkdir(parents=True,exist_ok=True)
 result=dict(status='PASS',runs=runs,CPU=time.process_time()-start,RSS=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,source_sha256={str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [Path(__file__),R/'src/inference/mass_batch.py']},PTA_observations=0,physical_likelihood_evaluations=0,scope='Analytic algorithm/array benchmark; not calibration of the physical PTA posterior')
 (out/'audit.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
