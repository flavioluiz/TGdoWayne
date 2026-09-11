"""Independent analytic and t-coordinate adaptive-quadrature checks."""
from pathlib import Path
import json
import warnings
from time import perf_counter
import numpy as np
from scipy.integrate import quad
from scipy.special import logsumexp
from scipy.stats import multivariate_normal
import sys
from pathlib import Path
REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
OUTPUT = REPO / "results/C07/validation"
OUTPUT.mkdir(parents=True, exist_ok=True)

from inference.scale_gaussian import gaussian_log_scale_integral,gaussian_conditional_scale_cdf,gaussian_scale_loglike

ROOT=OUTPUT
LOW=-np.log10(2);HIGH=np.log10(2);LN10=np.log(10.)


def independent_reference(chi,b,c,ld,d,lo,hi):
    # Independent integration in t=log10(s); no z-Jacobian/panel code is reused.
    if chi:
        root=np.hypot(b,2*np.sqrt(chi*d))
        v=(b+root)/(2*chi) if b>=0 else 2*d/(root-b)
        mode=np.clip(-np.log10(v)/2,lo,hi)
    else:mode=lo
    def ll(t):
        s=10**t
        return -.5*(chi/s**4-2*b/s**2+c+ld+d*np.log(2*np.pi))-2*d*np.log(s)
    peak=ll(mode);v=10**(-2*mode)
    gradient=2*LN10*(-d+chi*v*v-b*v)
    curvature=4*LN10*LN10*(b*v-2*chi*v*v)
    width=1/max(abs(gradient),np.sqrt(abs(curvature)),1.)
    edges=np.unique(np.r_[lo,hi,np.clip(mode+width*np.array([-64,-16,-8,-4,-2,-1,0,1,2,4,8,16,64]),lo,hi)])
    total=0.;error=0.;warning_messages=[]
    for a,z in zip(edges[:-1],edges[1:]):
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter('always')
            value,err=quad(lambda x:np.exp(ll(x)-peak),a,z,epsabs=1e-13*min(1,width),epsrel=2e-11,limit=200)
        warning_messages.extend(str(item.message) for item in caught)
        total+=value;error+=err
    return peak+np.log(total)-np.log(hi-lo),error/max(total,np.finfo(float).tiny),warning_messages


def main():
    start=perf_counter();records=[]
    # Zero-data limit: retains normalization and nonzero mean (constant term).
    for d in [1,10,40]:
        for lo,hi in [(LOW,HIGH),(.123,.123000001)]:
            c=7.3;ld=-2.1;lam=2*d*LN10
            exact=-.5*(c+ld+d*np.log(2*np.pi))-lam*lo+np.log(-np.expm1(-lam*(hi-lo)))-np.log(lam)-np.log(hi-lo)
            got=gaussian_log_scale_integral(0.,0.,c,ld,d,lo,hi,coarse_order=32,fine_order=64)
            assert abs(got-exact)<1e-9
            records.append(dict(case='zero_data_analytic',dimension=d,low=lo,high=hi,log_error=float(got-exact)))
    # d=2,b=0 has an elementary integral even in the extreme, underflowing tail.
    for chi in [1e-8,.1,10.,1e4,1e9]:
        lo,hi=LOW,HIGH;vlo=10**(-2*hi);vhi=10**(-2*lo);c=0.;ld=.7
        exact=-.5*(ld+2*np.log(2*np.pi))-np.log(2*LN10)-.5*chi*vlo*vlo+np.log(-np.expm1(-.5*chi*(vhi*vhi-vlo*vlo)))-np.log(chi)-np.log(hi-lo)
        got,diag=gaussian_log_scale_integral(chi,0.,c,ld,2,lo,hi,coarse_order=32,fine_order=64,return_diagnostics=True)
        assert abs(got-exact)<1e-7
        records.append(dict(case='dimension2_elementary',chi=chi,log_error=float(got-exact),diagnostics=diag))
    # Negative/zero/positive linear term; full, narrow, and edge intervals.
    adaptive=[]
    for d in [1,10,40]:
        for chi in [1e-7,.01,1.,50.,1e4,1e8]:
            for rho in [-.9,0,.9]:
                c=15.;b=rho*np.sqrt(chi*c);ld=-.7
                for lo,hi in [(LOW,HIGH),(.2,.201),(-.25,-.24999999)]:
                    got,diag=gaussian_log_scale_integral(chi,b,c,ld,d,lo,hi,coarse_order=32,fine_order=64,return_diagnostics=True)
                    ref,referr,reference_warnings=independent_reference(chi,b,c,ld,d,lo,hi)
                    error=float(got-ref)
                    # Absolute log tolerance in extreme tails acknowledges floating-point subtraction.
                    tolerance=2e-6 if abs(ref)>1e5 else 2e-8
                    assert abs(error)<tolerance,(d,chi,rho,lo,hi,got,ref,error)
                    adaptive.append(dict(dimension=d,chi=chi,rho=rho,low=lo,high=hi,log_error=error,reference_log_value=ref,reference_relative_error=referr,reference_warnings=reference_warnings,**diag))
    records.append(dict(case='independent_t_quadrature',count=len(adaptive),maximum_abs_log_error=max(abs(a['log_error']) for a in adaptive),maximum_abs_log_error_above_minus1e5=max(abs(a['log_error']) for a in adaptive if a['reference_log_value']>-1e5),records=adaptive))
    # End-to-end scalar checks from independent scipy multivariate-normal densities.
    rng=np.random.default_rng(78011);cases=[]
    for d in [3,10]:
        m=rng.normal(size=d);z=rng.normal(size=(d,d));cov=z@z.T+np.eye(d);y=rng.normal(size=d)
        inv=np.linalg.inv(cov);chi=y@inv@y;b=m@inv@y;c=m@inv@m;ld=np.linalg.slogdet(cov)[1]
        f=lambda t:multivariate_normal.logpdf(y,mean=10**(2*t)*m,cov=10**(4*t)*cov)
        grid=np.linspace(LOW,HIGH,201);shift=max(map(f,grid))
        norm=quad(lambda t:np.exp(f(t)-shift),LOW,HIGH,epsabs=1e-12,epsrel=1e-11)[0]
        exact=np.log(norm)+shift-np.log(HIGH-LOW)
        got=gaussian_log_scale_integral(chi,b,c,ld,d,LOW,HIGH,coarse_order=32,fine_order=64)
        assert abs(got-exact)<1e-10
        cdf_errors=[]
        for point in np.linspace(LOW,HIGH,11):
            expected=quad(lambda t:np.exp(f(t)-shift),LOW,point,epsabs=1e-12,epsrel=1e-11)[0]/norm
            value=gaussian_conditional_scale_cdf(point,chi,b,c,ld,d,LOW,HIGH,coarse_order=32,fine_order=64)
            cdf_errors.append(float(value-expected))
        assert max(abs(x) for x in cdf_errors)<1e-10
        cases.append(dict(dimension=d,log_error=float(got-exact),maximum_cdf_error=max(abs(x) for x in cdf_errors)))
    records.append(dict(case='scipy_multivariate_normal_end_to_end',records=cases))
    output=dict(status='PASS_conditional_gaussian_scale_reference',seconds=perf_counter()-start,records=records,production_executed=False)
    (ROOT/'validation_integral.json').write_text(json.dumps(output,indent=2)+'\n')
    print(json.dumps({'status':output['status'],'seconds':output['seconds'],'adaptive_cases':len(adaptive),'max_log_error':max(abs(a['log_error']) for a in adaptive)},indent=2))


if __name__=='__main__':main()
