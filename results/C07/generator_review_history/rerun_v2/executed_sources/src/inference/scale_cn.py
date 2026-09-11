"""Exact common-scale marginalization for the frozen A0 proper-CN model.

Original independent rectangular log-amplitude priors are retained exactly.
No mass or response approximation is introduced here.
"""
from dataclasses import dataclass
import numpy as np
from scipy.special import gammainc,gammaincc,gammaln

LN10=np.log(10.)


def _log_difference(high,low):
    """log(exp(high)-exp(low)), with high>=low; equality means zero interval."""
    high,low=np.broadcast_arrays(np.asarray(high,float),np.asarray(low,float))
    with np.errstate(divide='ignore',invalid='ignore',over='raise'):
        result=high+np.log(-np.expm1(low-high))
    result=np.where(np.isneginf(low),high,result)
    return result


def _log_lower_gamma_probability(shape,x):
    """Positive-series evaluation of regularized P(shape,x), used for x<=shape."""
    x=np.asarray(x,float);term=np.ones_like(x);total=term.copy()
    for j in range(1,2049):
        term=term*x/(shape+j);total+=term
        ratio=x/(shape+j+1)
        bound=term*ratio/np.maximum(1-ratio,np.finfo(float).eps)
        if np.all(bound<=2e-16*total):break
    else:raise ArithmeticError('Lower gamma series failed its explicit tail criterion.')
    with np.errstate(divide='ignore'):
        return shape*np.log(x)-x-gammaln(shape+1)+np.log(total)


def _log_upper_gamma_integer(shape,x):
    """Exact finite polynomial for integer-shape Q(shape,x), stable for x>=shape."""
    x=np.asarray(x,float);term=np.ones_like(x);total=term.copy()
    for j in range(1,shape):
        term=term*(shape-j)/x;total+=term
    return -x+(shape-1)*np.log(x)-gammaln(shape)+np.log(total)


def log_gamma_interval(shape,lower,upper):
    """log integral_lower^upper v^(shape-1) exp(-v) dv, integer shape>=1.

    Standard incomplete gamma is used when well conditioned; positive series or
    finite upper-tail polynomials retain intervals whose probabilities underflow.
    """
    if isinstance(shape,bool) or not isinstance(shape,(int,np.integer)) or shape<1:raise ValueError('Positive integer gamma shape required.')
    lo,hi=np.broadcast_arrays(np.asarray(lower,float),np.asarray(upper,float))
    if not np.isfinite(lo).all() or not np.isfinite(hi).all() or np.any(lo<0) or np.any(hi<lo):raise ValueError('Finite 0<=lower<=upper required.')
    original_shape=lo.shape;lo=lo.ravel();hi=hi.ravel();result=np.full(len(lo),-np.inf)
    active=hi>lo
    a,b=lo[active],hi[active]
    pl,ph=gammainc(shape,a),gammainc(shape,b)
    ql,qh=gammaincc(shape,a),gammaincc(shape,b)
    use_lower=ph<=.5
    top=np.where(use_lower,ph,ql);bottom=np.where(use_lower,pl,qh)
    delta=top-bottom
    good=(delta>0)&(delta>1e-7*top)
    logs=np.empty_like(a)
    logs[good]=gammaln(shape)+np.log(delta[good])
    if np.any(~good):
        aa,bb=a[~good],b[~good];v=np.empty_like(aa)
        left=bb<=shape;right=aa>=shape;middle=~(left|right)
        if np.any(left):
            v[left]=gammaln(shape)+_log_difference(_log_lower_gamma_probability(shape,bb[left]),_log_lower_gamma_probability(shape,aa[left]))
        if np.any(right):
            v[right]=gammaln(shape)+_log_difference(_log_upper_gamma_integer(shape,aa[right]),_log_upper_gamma_integer(shape,bb[right]))
        if np.any(middle):
            # A crossing interval can only reach this branch when extremely narrow.
            v[middle]=gammaln(shape)+_log_difference(np.log(gammainc(shape,bb[middle])),np.log(gammainc(shape,aa[middle])))
        logs[~good]=v
    result[active]=logs
    return result.reshape(original_shape)


def cn_log_scale_integral(chi,logdet_c0,complex_dimension,low,high,*,conditional_average=True):
    """Integrate the fully normalized CN density in t=log10(s), C=10^(2t)C0.

    M=K*Np complex coordinates, chi=q†C0^-1q summed over frequencies,
    logdet_c0=sum log det C0_n. Low/high may depend on the amplitude ratios.
    conditional_average=True divides by high-low, required when the ratios are
    sampled from their exact induced marginal prior.
    """
    M=complex_dimension
    if isinstance(M,bool) or not isinstance(M,(int,np.integer)) or M<1:raise ValueError('M must count positive complex coordinates.')
    chi,ld,lo,hi=np.broadcast_arrays(np.asarray(chi,float),np.asarray(logdet_c0,float),np.asarray(low,float),np.asarray(high,float))
    if not all(np.isfinite(x).all() for x in [chi,ld,lo,hi]) or np.any(chi<0):raise ValueError('Finite chi>=0, logdet and scale limits required.')
    if np.any(hi<=lo):raise ValueError('A positive conditional scale interval is required.')
    with np.errstate(over='raise'):
        vlow=chi*np.exp(-2*LN10*hi);vhigh=chi*np.exp(-2*LN10*lo)
    small=vhigh<=.1;result=np.empty_like(chi)
    if np.any(~small):
        result[~small]=-ld[~small]-M*np.log(np.pi)-M*np.log(chi[~small])-np.log(2*LN10)+log_gamma_interval(M,vlow[~small],vhigh[~small])
    if np.any(small):
        # A uniformly convergent exp(-v) series avoids subtracting huge log-CDFs
        # when chi is tiny and the allowed log-scale interval is narrow.
        width=hi[small]-lo[small];lam=2*M*LN10
        logden=np.log(-np.expm1(-lam*width))
        base=-ld[small]-M*np.log(np.pi)-lam*lo[small]+logden-np.log(lam)
        correction=np.ones_like(width)
        with np.errstate(divide='ignore'):logv=np.log(vhigh[small])
        for j in range(1,33):
            logmoment=j*logv+np.log(M/(M+j))+np.log(-np.expm1(-2*(M+j)*LN10*width))-logden
            term=np.exp(logmoment-gammaln(j+1))
            correction+=(-1 if j%2 else 1)*term
            bound=np.exp((j+1)*logv-gammaln(j+2))
            if np.all(bound<=1e-16*correction):break
        else:raise ArithmeticError('Small-chi exponential series did not satisfy its explicit remainder bound.')
        result[small]=base+np.log(correction)
    if conditional_average:result-=np.log(hi-lo)
    return result


def cn_conditional_scale_cdf(threshold,chi,complex_dimension,low,high):
    """Posterior P(t<=threshold | amplitude ratios,slope,u,data) for exact A0."""
    threshold,chi,lo,hi=np.broadcast_arrays(np.asarray(threshold,float),np.asarray(chi,float),np.asarray(low,float),np.asarray(high,float))
    if isinstance(complex_dimension,bool) or not isinstance(complex_dimension,(int,np.integer)) or complex_dimension<1:raise ValueError('Positive complex dimension required.')
    if np.isnan(threshold).any() or not all(np.isfinite(x).all() for x in [chi,lo,hi]) or np.any(chi<0):raise ValueError('Valid threshold, chi and finite scale interval required.')
    if np.any(hi<=lo):raise ValueError('A positive conditional scale interval is required.')
    result=np.zeros_like(threshold);result[threshold>=hi]=1
    inside=(threshold>lo)&(threshold<hi)
    if np.any(inside):
        top=cn_log_scale_integral(chi[inside],0.,complex_dimension,lo[inside],threshold[inside],conditional_average=False)
        bottom=cn_log_scale_integral(chi[inside],0.,complex_dimension,lo[inside],hi[inside],conditional_average=False)
        result[inside]=np.exp(top-bottom)
    if np.any(result<0) or np.any(result>1+1e-10):raise ArithmeticError('Conditional CDF outside numerical probability tolerance.')
    return np.minimum(result,1.) # Only removes a possible relative-roundoff excess at the upper endpoint.


def sum_uniforms_ppf(probability,width1,width2):
    """Inverse CDF of U(0,width1)+U(0,width2), including its triangular limits."""
    p,w1,w2=np.broadcast_arrays(np.asarray(probability,float),np.asarray(width1,float),np.asarray(width2,float))
    if not all(np.isfinite(x).all() for x in [p,w1,w2]) or np.any(p<0) or np.any(p>1) or np.any(w1<=0) or np.any(w2<=0):raise ValueError('Require finite p in[0,1] and positive widths.')
    short=np.minimum(w1,w2);long=np.maximum(w1,w2);edge=short/(2*long)
    return np.where(p<edge,np.sqrt(2*short*long*p),
           np.where(p>1-edge,short+long-np.sqrt(2*short*long*(1-p)),long*p+short/2))


@dataclass(frozen=True)
class LogAmplitudeBox:
    gw:tuple=(-16.,-14.)
    red:tuple=(-17.,-14.5)
    efac:tuple=(-np.log10(2.),np.log10(2.))
    slope:tuple=(3.,5.5)

    def __post_init__(self):
        for name in ['gw','red','efac','slope']:
            v=np.asarray(getattr(self,name))
            if v.shape!=(2,) or not np.isfinite(v).all() or v[1]<=v[0]:raise ValueError('Finite positive-width prior intervals required.')

    def conditional_bounds(self,a,b):
        a,b=np.broadcast_arrays(np.asarray(a,float),np.asarray(b,float))
        lo=np.maximum(np.maximum(self.efac[0],self.gw[0]-a),self.red[0]-b)
        hi=np.minimum(np.minimum(self.efac[1],self.gw[1]-a),self.red[1]-b)
        return lo,hi

    def sample_ratio_prior(self,unit):
        """Exact 3D Rosenblatt map; output columns(a,b,slope,low,high).

        a=g-t first follows a difference of uniforms. Given a, t is uniform on
        the gw/efac intersection, so b=r-t is another difference of uniforms.
        This samples the induced ratio density; no rectangular ratio prior is used.
        """
        x=np.asarray(unit,float)
        if x.ndim!=2 or x.shape[1]!=3 or not np.isfinite(x).all() or np.any(x<=0) or np.any(x>=1):raise ValueError('Open-unit-cube points of dimension3 required.')
        G0,G1=self.gw;R0,R1=self.red;E0,E1=self.efac
        a=G0-E1+sum_uniforms_ppf(x[:,0],G1-G0,E1-E0)
        tlo=np.maximum(E0,G0-a);thi=np.minimum(E1,G1-a)
        b=R0-thi+sum_uniforms_ppf(x[:,1],R1-R0,thi-tlo)
        lo,hi=self.conditional_bounds(a,b)
        if np.any(hi<=lo):raise ArithmeticError('The exact ratio-prior map produced an empty conditional interval.')
        slope=self.slope[0]+x[:,2]*(self.slope[1]-self.slope[0])
        return np.column_stack((a,b,slope,lo,hi))

    def ratio_log_density(self,a,b):
        lo,hi=self.conditional_bounds(a,b)
        volume=np.prod([upper-lower for lower,upper in [self.gw,self.red,self.efac]])
        with np.errstate(divide='ignore',invalid='ignore'):
            return np.where(hi>lo,np.log(hi-lo)-np.log(volume),-np.inf)
