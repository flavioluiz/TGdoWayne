"""Positive nested quadratures for exact cached nodes; no ORF interpolation."""
import math
import numpy as np


def clenshaw_curtis_prior_weights(nodes,*,lower=.001,upper=1.):
    x=np.asarray(nodes,float);N=len(x)-1
    if x.ndim!=1 or N<2 or N%2 or not np.isfinite(x).all() or not lower<upper:
        raise ValueError('Finite even-order Lobatto axis required')
    theta=np.pi*np.arange(N+1)/N
    expected=lower+(upper-lower)*(1-np.cos(theta))/2
    if np.max(abs(x-expected))>32*np.finfo(float).eps*(upper-lower):
        raise ValueError('Axis does not match Chebyshev-Lobatto nodes')
    # Integrate the cosine interpolant. Weights sum to one for the proper
    # uniform measure on the supplied interval, not to its Lebesgue length.
    v=np.ones(N-1)
    for k in range(1,N//2):v-=2*np.cos(2*k*theta[1:-1])/(4*k*k-1)
    v-=np.cos(N*theta[1:-1])/(N*N-1)
    weights=np.r_[1/(2*(N*N-1)),v/N,1/(2*(N*N-1))]
    if np.any(weights<=0) or abs(float(weights.sum())-1)>2e-14:raise ArithmeticError('Invalid positive CC weights')
    return weights


def simpson_union_rule(regions,panels):
    if type(panels)is not int or panels<1 or panels&(panels-1):raise ValueError('Power-of-two panel count required')
    points=[];weights=[];previous=0.
    for a,b in regions:
        if not all(math.isfinite(v) for v in (a,b)) or not 0<=a<b<=1 or a<previous:raise ValueError('Ordered disjoint epsilon regions required')
        previous=b
        inner=np.arange(math.floor(a*panels)+1,math.ceil(b*panels),dtype=float)/panels
        edges=np.r_[a,inner,b];left,right=edges[:-1],edges[1:]
        p=np.stack([left,left+(right-left)/2,right],axis=1).reshape(-1)
        w=((right-left)[:,None]*np.array([1.,4.,1.])[None]/6).reshape(-1)
        points.extend(p);weights.extend(w)
    if not points:return np.array([],float),np.array([],float)
    unique,index=np.unique(points,return_inverse=True);weight=np.bincount(index,weights=weights)
    measure=math.fsum(b-a for a,b in regions)
    if np.any(weight<=0) or abs(float(weight.sum())-measure)>32*np.finfo(float).eps*measure:raise ArithmeticError('Invalid positive Simpson measure')
    return unique,weight


def integrate_regions(cache,regions,shift):
    """Positive composite Simpson 32/64 with explicit ordinary-roundoff model.

    Full-support nodes are the existing 65/129 epsilon nodes. Partial boundary
    panels are scored via the same charged cache. Neither differences nor the
    numerical allowance are rigorous quadrature error bounds.
    """
    estimates=[];counts=[]
    for panels in (32,64):
        points,weights=simpson_union_rule(regions,panels);counts.append(len(points))
        if not len(points):estimates.append(0.);continue
        logs=cache(points)
        with np.errstate(over='raise',invalid='raise'):
            value=float(np.dot(weights,np.exp(logs-shift)))
        if not math.isfinite(value):raise ArithmeticError('Nonfinite Simpson mass')
        estimates.append(value)
    coarse,fine=estimates;difference=abs(fine-coarse)
    operations=2*max(counts,default=0)+2
    gamma=operations*np.finfo(float).eps/(1-operations*np.finfo(float).eps)
    numerical=(1e-10+gamma)*max(coarse,fine)
    error=difference+numerical
    return dict(value=fine,lower=max(0.,fine-error),upper=fine+error,
                coarse=coarse,fine=fine,observed_difference=difference,
                additional_roundoff_allowance=numerical,rule='POSITIVE_COMPOSITE_SIMPSON_32_64',
                sampled_points_per_rule=counts,rigorous_error_bound=False)
