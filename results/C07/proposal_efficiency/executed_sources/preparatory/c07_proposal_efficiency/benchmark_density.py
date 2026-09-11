"""Frozen fixture equivalence, primary-library cross-check and timings."""
import os
os.environ.setdefault('VECLIB_MAXIMUM_THREADS', '1')
from pathlib import Path
import hashlib, json, sys, time, resource
import numpy as np
from scipy.special import logsumexp
from scipy.stats import multivariate_normal, multivariate_t
ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent
sys.path[:0]=[str(ROOT/'tmp/c07_sampler'),str(HERE)]
from mixture_proposal_v2 import GaussianDefensiveProposal
from multiple_rhs import MultipleRHSGaussianDefensiveProposal

def digest(path): return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    training=ROOT/'tmp/c07_sampler/results/mixture_training.json'
    content=json.loads(training.read_text());records=content['records']
    rng=np.random.default_rng(907103501)
    options=dict(defensive_fraction=content['defensive_student_fraction'],student_df=content['student_df'],student_scale=content['student_scale'])
    reports=[]
    for targets,count in [(16,8192),(1,65536)]:
        rows=records if targets==16 else [next(r for r in records if r['target']==62)]
        args=[np.array([r[k] for r in rows]) for k in ['weights','means','covariances','global_mean','global_cholesky']]
        reference=GaussianDefensiveProposal(*args,**options);fast=MultipleRHSGaussianDefensiveProposal(*args,**options)
        # Wide multivariate draws exercise the Gaussian peaks and Student tails.
        z=reference.global_mean[:,None,:]+rng.normal(size=(targets,count,5))*rng.choice([.1,1.,3.,10.],size=(targets,count,1))
        z=z.reshape(-1,5);baseline=reference.logpdf(z)
        timing={};errors={}
        for name in ['reference','matmul','forward','solve']:
            fn=reference.logpdf if name=='reference' else lambda points, n=name: fast.logpdf(points,method=n)
            values=fn(z);errors[name]=float(np.max(abs(values-baseline)))
            duration=[]
            for _ in range(4):
                start=time.perf_counter();fn(z);duration.append(time.perf_counter()-start)
            timing[name]=dict(seconds=duration,median_seconds=float(np.median(duration)))
        # Independent SciPy formulas including Student shape/covariance distinction.
        check=z.reshape(targets,count,5)[:,:128]
        primary=[]
        for t in range(targets):
            terms=[multivariate_normal.logpdf(check[t],mean=reference.means[t,k],cov=reference.cov[t,k])+np.log((1-reference.alpha)*reference.weights[t,k]) for k in range(reference.k)]
            shape=(reference.nu-2)/reference.nu*reference.scale**2*(reference.global_chol[t]@reference.global_chol[t].T)
            terms.append(multivariate_t.logpdf(check[t],loc=reference.global_mean[t],shape=shape,df=reference.nu)+np.log(reference.alpha))
            primary.append(logsumexp(np.asarray(terms),axis=0))
        scipy_error=float(np.max(abs(fast.logpdf(check.reshape(-1,5)).reshape(targets,-1)-primary)))
        assert max(errors.values())<2e-10 and scipy_error<2e-10
        reports.append(dict(targets=targets,points_per_target=count,maximum_logq_difference=errors,scipy_max_logq_difference=scipy_error,timings=timing))
    sources=[Path(__file__),HERE/'multiple_rhs.py',ROOT/'tmp/c07_sampler/mixture_proposal.py',ROOT/'tmp/c07_sampler/mixture_proposal_v2.py',ROOT/'tmp/c07_sampler/linalg_batch.py',training]
    report=dict(status='EQUIVALENT_DENSITY_BENCHMARK_COMPLETE',seed=907103501,VECLIB_MAXIMUM_THREADS=os.environ.get('VECLIB_MAXIMUM_THREADS'),reports=reports,source_sha256={str(p.relative_to(ROOT)):digest(p) for p in sources},darwin_maxrss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    for p in sources:
        out=HERE/'executed_sources'/p.relative_to(ROOT);out.parent.mkdir(parents=True,exist_ok=True);out.write_bytes(p.read_bytes())
    out=HERE/'density_benchmark.json'
    with out.open('x') as f:json.dump(report,f,indent=2);f.write('\n')
    print(json.dumps(report,indent=2))

if __name__=='__main__':main()
