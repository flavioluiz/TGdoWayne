"""Checked conditional common-scale integral for normal A/B/G likelihoods.

Let t=log10(s), mu=s² mu0, Sigma=s⁴ Sigma0. With z=s^-2,
L(t)=exp[-(ld+c+d log(2pi))/2] z^d exp[-chi*z²/2+b*z].
The dt measure supplies dz/(2 ln(10) z): the integral uses z^(d-1).
All likelihood determinants and the induced conditional prior are retained.
"""
from functools import lru_cache
import numpy as np
from scipy.special import roots_legendre

LN10=np.log(10.)


@lru_cache(maxsize=16)
def _rule(order):
    if isinstance(order,(bool,np.bool_)) or not isinstance(order,(int,np.integer)) or order<2:raise ValueError('A Gauss order must be an integer >=2.')
    return roots_legendre(int(order))


def _inputs(chi,linear,constant,logdet,dimension,low,high):
    if isinstance(dimension,(bool,np.bool_)):raise ValueError('The real dimension must be a positive integer.')
    arrays=np.broadcast_arrays(*[np.asarray(a,float) for a in (chi,linear,constant,logdet,dimension,low,high)])
    chi,b,c,ld,d,lo,hi=arrays
    if not all(np.isfinite(a).all() for a in arrays):raise ValueError('Finite coefficients and limits required.')
    if np.any(chi<0) or np.any(c<0) or np.any(d<1) or np.any(d!=np.floor(d)) or np.any(hi<=lo):raise ValueError('Require chi,c>=0, integer d>=1, and high>low.')
    bound=np.sqrt(chi)*np.sqrt(c)
    if np.any(abs(b)>bound+1e-10*np.maximum(1,bound)):raise ValueError('Coefficients violate the Cauchy bound |linear|<=sqrt(chi*constant).')
    if np.any((chi==0)&(b!=0)):raise ValueError('Zero data norm requires zero linear coefficient, exactly.')
    return arrays


def _positive_mode(A,B,power):
    """Maximizer r>0 of power*log r-A*r²/2+B*r, before clipping."""
    A,B,power=np.broadcast_arrays(A,B,power);out=np.full_like(A,np.inf)
    active=A>0
    aa,bb,pp=A[active],B[active],power[active]
    root=np.hypot(bb,2*np.sqrt(aa)*np.sqrt(pp))
    rr=np.empty_like(aa);positive=bb>=0
    rr[positive]=.5*(bb[positive]/aa[positive]+root[positive]/aa[positive])
    negative=~positive
    rr[negative]=2*pp[negative]/(root[negative]-bb[negative])
    out[active]=rr
    out[(A==0)&(B==0)&(power==0)]=1
    return out


def _piece(chi,b,c,ld,d,lo,hi,coarse_order,fine_order,tail_log_drop):
    # Use z=zlow*(1+x), x in[0,expm1(2ln10*(hi-lo))]. This retains tiny intervals.
    with np.errstate(over='raise',invalid='raise'):
        zlow=np.exp(-2*LN10*hi)
        xmax=np.expm1(2*LN10*(hi-lo))
        A=chi*zlow*zlow;B=b*zlow;power=d-1
    peak=np.clip(_positive_mode(A,B,power)-1,0,xmax)
    rpeak=1+peak
    peak_value=power*np.log1p(peak)-.5*A*rpeak*rpeak+B*rpeak

    def delta(x):
        dx=x-peak
        return power*np.log1p(dx/rpeak)+dx*(B-A*rpeak-.5*A*dx)

    left=np.zeros_like(peak);right=xmax.copy()
    trim_left=delta(left)<-tail_log_drop
    trim_right=delta(right)<-tail_log_drop
    # Log-concavity gives one root on each side of the constrained maximum.
    al=np.zeros_like(peak);bl=peak.copy()
    ar=peak.copy();br=xmax.copy()
    for _ in range(80):
        mid=(al+bl)/2;far=delta(mid)<-tail_log_drop
        al=np.where(trim_left&far,mid,al);bl=np.where(trim_left&~far,mid,bl)
        mid=(ar+br)/2;far=delta(mid)<-tail_log_drop
        br=np.where(trim_right&far,mid,br);ar=np.where(trim_right&~far,mid,ar)
    left=np.where(trim_left,(al+bl)/2,left)
    right=np.where(trim_right,(ar+br)/2,right)
    half=(right-left)/2;middle=(right+left)/2
    if np.any(half<=0):raise ArithmeticError('No representable integration interval remained.')

    def quadrature(order):
        nodes,weights=_rule(order);x=middle[:,None]+half[:,None]*nodes
        dx=x-peak[:,None]
        exponent=power[:,None]*np.log1p(dx/rpeak[:,None])+dx*(B[:,None]-A[:,None]*rpeak[:,None]-.5*A[:,None]*dx)
        if np.any(exponent>1e-8):raise ArithmeticError('Constrained mode did not bound the quadrature integrand.')
        return half*np.sum(np.exp(exponent)*weights,axis=1)

    coarse=quadrature(coarse_order);fine=quadrature(fine_order)
    if np.any(fine<=0) or not np.isfinite(fine).all():raise ArithmeticError('Non-positive finite scale integral.')
    refinement=abs(fine-coarse)/fine
    tail=np.zeros_like(fine)
    if np.any(trim_left):
        x=left[trim_left];der=power[trim_left]/(1+x)-A[trim_left]*(1+x)+B[trim_left]
        if np.any(der<=0):raise ArithmeticError('Left tangent does not bound the discarded tail.')
        tail[trim_left]+=np.exp(delta(left)[trim_left])*(-np.expm1(-der*x))/der
    if np.any(trim_right):
        x=right[trim_right];der=power[trim_right]/(1+x)-A[trim_right]*(1+x)+B[trim_right]
        if np.any(der>=0):raise ArithmeticError('Right tangent does not bound the discarded tail.')
        tail[trim_right]+=np.exp(delta(right)[trim_right])*(-np.expm1(der*(xmax[trim_right]-x)))/(-der)
    tail_relative=tail/fine
    value=-.5*(ld+c+d*np.log(2*np.pi))-np.log(2*LN10)+d*np.log(zlow)+peak_value+np.log(fine)
    return value,refinement,tail_relative


def gaussian_log_scale_integral(chi,linear,constant,logdet_sigma0,real_dimension,low,high,*,
        coarse_order,fine_order,conditional_average=True,relative_tolerance=1e-8,
        tail_log_drop=40.,maximum_evaluations=20_000_000,chunk_size=1024,return_diagnostics=False):
    """Integral of the fully normalized normal density in t=log10(s).

    With exact induced ratio-prior sampling, conditional_average MUST be True.
    Two Gauss orders and tangent tail bounds are checked; no silent refinement.
    relative_tolerance bounds those two numerical components. Final floating-point
    arithmetic is reported separately as a conservative magnitude-based proxy.
    This is a deterministic reference, not a replacement of the physical family.
    """
    _rule(coarse_order);_rule(fine_order)
    if fine_order<=coarse_order:raise ValueError('The fine Gauss order must exceed the coarse one.')
    for val,name in [(maximum_evaluations,'maximum_evaluations'),(chunk_size,'chunk_size')]:
        if isinstance(val,(bool,np.bool_)) or not isinstance(val,(int,np.integer)) or val<1:raise ValueError(f'{name} must be a positive integer.')
    if not np.isfinite(relative_tolerance) or relative_tolerance<=0 or not np.isfinite(tail_log_drop) or tail_log_drop<=0:raise ValueError('Positive finite quadrature/tail tolerances required.')
    arrays=_inputs(chi,linear,constant,logdet_sigma0,real_dimension,low,high);shape=arrays[0].shape
    flat=[a.reshape(-1) for a in arrays];size=len(flat[0]);active=np.flatnonzero(flat[0]>0);zero=flat[0]==0
    evaluations=len(active)*(coarse_order+fine_order)
    if evaluations>maximum_evaluations:raise ValueError(f'Scale quadrature budget exceeded before computation: {evaluations}>{maximum_evaluations}.')
    values=np.empty(size);errors=np.zeros(size);tails=np.zeros(size)
    if np.any(zero):
        _,_,c,ld,d,lo,hi=[a[zero] for a in flat];lam=2*d*LN10
        values[zero]=-.5*(ld+c+d*np.log(2*np.pi))-lam*lo+np.log(-np.expm1(-lam*(hi-lo)))-np.log(lam)
    for start in range(0,len(active),chunk_size):
        indices=active[start:start+chunk_size]
        vals,err,tail=_piece(*[a[indices] for a in flat],coarse_order,fine_order,tail_log_drop)
        if np.any(err+tail>relative_tolerance):raise ArithmeticError(f'Conditional scale integral unresolved: max refinement+tail={np.max(err+tail):.6g}, tolerance={relative_tolerance}.')
        values[indices]=vals;errors[indices]=err;tails[indices]=tail
    if conditional_average:values-=np.log(flat[-1]-flat[-2])
    values=values.reshape(shape)
    if not return_diagnostics:return values
    with np.errstate(over='ignore'):
        zmax=np.exp(-2*LN10*flat[-2])
        roundoff_proxy=64*np.finfo(float).eps*(1+abs(flat[3])+flat[2]+abs(flat[0])*zmax*zmax+2*abs(flat[1])*zmax+2*flat[4]*LN10*np.maximum(abs(flat[-2]),abs(flat[-1])))
    return values,dict(maximum_relative_refinement_error=float(errors.max(initial=0)),maximum_relative_tail_bound=float(tails.max(initial=0)),maximum_absolute_log_roundoff_proxy=float(roundoff_proxy.max(initial=0)),roundoff_proxy_exceeds_quadrature_tolerance_count=int(np.sum(roundoff_proxy>relative_tolerance)),roundoff_note='Magnitude-based conservative proxy, not a rigorous bound; extreme tails require the separately tested floating-point accuracy statement.',coarse_order=int(coarse_order),fine_order=int(fine_order),quadrature_evaluations=int(evaluations),zero_data_analytic_cases=int(zero.sum()),tangent_bisection_iterations=80,maximum_vectorized_cells=int(min(len(active),chunk_size)),conditional_average=bool(conditional_average),integration_variable='z=10^(-2t), measure dz/(2ln(10) z)',mass_or_prior_approximation=False)


def gaussian_scale_loglike(t,chi,linear,constant,logdet_sigma0,real_dimension):
    t,chi,b,c,ld,d=np.broadcast_arrays(*[np.asarray(v,float) for v in (t,chi,linear,constant,logdet_sigma0,real_dimension)])
    z=np.exp(-2*LN10*t)
    return -.5*(ld+c+d*np.log(2*np.pi))+d*np.log(z)-.5*chi*z*z+b*z


def gaussian_conditional_scale_cdf(threshold,chi,linear,constant,logdet_sigma0,real_dimension,low,high,*,
        coarse_order,fine_order,log_denominator=None,**kwargs):
    """Continuous CDF of t conditional on ratios, slope, u and the chosen data family."""
    fields=np.broadcast_arrays(*[np.asarray(v,float) for v in (threshold,chi,linear,constant,logdet_sigma0,real_dimension,low,high)])
    threshold,chi,b,c,ld,d,lo,hi=fields
    _inputs(chi,b,c,ld,d,lo,hi)
    result=np.zeros_like(threshold);result[threshold>=hi]=1
    inside=(threshold>lo)&(threshold<hi)
    if np.any(inside):
        params=[a[inside] for a in (chi,b,c,ld,d,lo)]
        top=gaussian_log_scale_integral(*params,threshold[inside],coarse_order=coarse_order,fine_order=fine_order,conditional_average=False,**kwargs)
        if log_denominator is None:
            bottom=gaussian_log_scale_integral(*params,hi[inside],coarse_order=coarse_order,fine_order=fine_order,conditional_average=False,**kwargs)
        else:bottom=np.broadcast_to(log_denominator,result.shape)[inside]
        result[inside]=np.exp(top-bottom)
    if np.any(result>1+2e-8) or np.any(result<0):raise ArithmeticError('Conditional scale CDF outside its numerical probability tolerance.')
    return np.minimum(result,1.)


def gaussian_conditional_loglike_cdf(threshold,chi,linear,constant,logdet_sigma0,real_dimension,low,high,*,
        coarse_order,fine_order,under_prior=False,**kwargs):
    """Conditional P(logL(t)<=threshold), needed for data-dependent SBC diagnostics.

    The superlevel set of logL is an interval in z (and hence in t). Its endpoints
    are solved continuously. under_prior=True supplies the ignored-data control.
    """
    fields=np.broadcast_arrays(*[np.asarray(v,float) for v in (threshold,chi,linear,constant,logdet_sigma0,real_dimension,low,high)])
    threshold,chi,b,c,ld,d,lo,hi=fields;_inputs(chi,b,c,ld,d,lo,hi)
    zlo=np.exp(-2*LN10*hi);xmax=np.expm1(2*LN10*(hi-lo))
    mode_ratio=np.clip(_positive_mode(chi*zlo*zlo,b*zlo,d),1,1+xmax)
    mode=hi-np.log(mode_ratio)/(2*LN10)
    zm=np.exp(-2*LN10*mode)
    peak=gaussian_scale_loglike(mode,chi,b,c,ld,d)
    target=threshold-peak
    def delta(t):
        dt=t-mode
        return -2*d*LN10*dt-.5*chi*zm*zm*np.expm1(-4*LN10*dt)+b*zm*np.expm1(-2*LN10*dt)
    left_needed=(threshold<peak)&(delta(lo)<target)
    right_needed=(threshold<peak)&(delta(hi)<target)
    a=lo.copy();bnd=mode.copy();cnd=mode.copy();z=hi.copy()
    for _ in range(80):
        mid=(a+bnd)/2;outside=delta(mid)<target
        a=np.where(left_needed&outside,mid,a);bnd=np.where(left_needed&~outside,mid,bnd)
        mid=(cnd+z)/2;outside=delta(mid)<target
        z=np.where(right_needed&outside,mid,z);cnd=np.where(right_needed&~outside,mid,cnd)
    left=np.where(left_needed,(a+bnd)/2,lo)
    right=np.where(right_needed,(cnd+z)/2,hi)
    if under_prior:result=(left-lo+hi-right)/(hi-lo)
    else:
        den=gaussian_log_scale_integral(chi,b,c,ld,d,lo,hi,coarse_order=coarse_order,fine_order=fine_order,conditional_average=False,**kwargs)
        lf=gaussian_conditional_scale_cdf(left,chi,b,c,ld,d,lo,hi,coarse_order=coarse_order,fine_order=fine_order,log_denominator=den,**kwargs)
        rf=gaussian_conditional_scale_cdf(right,chi,b,c,ld,d,lo,hi,coarse_order=coarse_order,fine_order=fine_order,log_denominator=den,**kwargs)
        result=lf+1-rf
    result=np.where(threshold>=peak,1.,result)
    if np.any(result < -2e-8) or np.any(result>1+2e-8):raise ArithmeticError('Conditional log-likelihood CDF outside probability tolerance.')
    return np.clip(result,0.,1.) # Remove only validated probability-roundoff excess.
