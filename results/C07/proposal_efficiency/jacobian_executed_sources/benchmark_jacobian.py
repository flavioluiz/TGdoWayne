"""Equivalent Jacobian identity, numerical extremes, timings and source hashes."""
import os
os.environ.setdefault('VECLIB_MAXIMUM_THREADS','1')
from pathlib import Path
import hashlib,json,sys,time
import numpy as np
from scipy.special import expit
from scipy.stats import logistic
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
from logistic_jacobian import unit_log_prior_jacobian

def reference(z):return (-np.logaddexp(0,-z)-np.logaddexp(0,z)).sum(axis=-1)

def main():
    rng=np.random.default_rng(907103601)
    test=np.r_[np.linspace(-1000,1000,20001),np.nextafter(0.,1.),np.nextafter(0.,-1.),0.,np.logspace(-16,-1,100),-np.logspace(-16,-1,100)][:,None]
    expected=reference(test);actual=unit_log_prior_jacobian(test)
    error=float(np.max(abs(actual-expected)));scipy_error=float(np.max(abs(actual-logistic.logpdf(test[:,0]))))
    assert error<5e-13 and scipy_error<5e-13
    z=rng.normal(size=(65536,5))*3
    rows=[]
    for name,fn in [('reference',reference),('one_exponential',unit_log_prior_jacobian)]:
        duration=[]
        for _ in range(8):
            start=time.perf_counter();expit(z);fn(z);duration.append(time.perf_counter()-start)
        rows.append(dict(implementation=name,seconds=duration,median_seconds=float(np.median(duration))))
    shape_error=float(np.max(abs(unit_log_prior_jacobian(z)-reference(z))))
    assert shape_error<5e-13
    for bad in [np.array([1+2j]),np.array([np.inf]),np.array([np.nan]),np.zeros((2,0)),np.array(['x'])]:
        try:unit_log_prior_jacobian(bad)
        except ValueError:pass
        else:raise AssertionError('Invalid input accepted.')
    sources=[Path(__file__),HERE/'logistic_jacobian.py']
    result=dict(status='PASS_EQUIVALENT_LOGISTIC_JACOBIAN',seed=907103601,extreme_points=len(test),maximum_difference_from_logaddexp=error,maximum_difference_from_scipy_logistic_logpdf=scipy_error,maximum_5d_sum_difference=shape_error,timing_N=65536,timings=rows,source_sha256={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sources})
    for p in sources:
        out=HERE/'jacobian_executed_sources'/p.name;out.parent.mkdir(exist_ok=True);out.write_bytes(p.read_bytes())
    with (HERE/'jacobian_benchmark.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
    print(json.dumps(result,indent=2))

if __name__=='__main__':main()
