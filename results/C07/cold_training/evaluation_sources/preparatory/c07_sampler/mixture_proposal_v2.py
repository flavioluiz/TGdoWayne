"""Strict input contract around the frozen, independently audited mixture formula.

Weights within 1e-14 of unit row sum are explicitly normalized at machine precision.
No covariance or Cholesky repair is performed. All caller arrays are copied.
"""
import numpy as np
from mixture_proposal import GaussianDefensiveProposal as FrozenV1

def _array(value,name):
    raw=np.asarray(value)
    if np.iscomplexobj(raw) or raw.dtype.kind not in 'fiu':
        raise ValueError(name+' must be real numeric.')
    out=np.array(raw,dtype=float,copy=True)
    if not np.isfinite(out).all():raise ValueError(name+' must be finite.')
    return out

def _scalar(value,name):
    if isinstance(value,(bool,np.bool_)) or not np.isscalar(value) or np.iscomplexobj(value):
        raise ValueError(name+' must be a real scalar.')
    try:value=float(value)
    except (TypeError,ValueError,OverflowError) as error:raise ValueError(name+' must be real.') from error
    if not np.isfinite(value):raise ValueError(name+' must be finite.')
    return value

class GaussianDefensiveProposal(FrozenV1):
    def __init__(self,weights,means,covariances,global_mean,global_cholesky,*,defensive_fraction=.15,student_df=5.,student_scale=3.):
        w,m,c,g,L=[_array(v,n) for v,n in zip([weights,means,covariances,global_mean,global_cholesky],['weights','means','covariances','global_mean','global_cholesky'])]
        if m.ndim!=3 or min(m.shape)<1:raise ValueError('means require nonempty (targets,components,dimension).')
        n,k,d=m.shape
        if w.shape!=(n,k) or c.shape!=(n,k,d,d) or g.shape!=(n,d) or L.shape!=(n,d,d):raise ValueError('Incompatible mixture shapes.')
        if np.any(w<=0) or np.max(abs(w.sum(axis=1)-1))>1e-14:raise ValueError('Positive weights with unit row sums required.')
        self.input_weight_sum_max_error=float(np.max(abs(w.sum(axis=1)-1)))
        w/=w.sum(axis=1)[:,None]
        if not np.array_equal(L,np.tril(L)) or np.any(np.diagonal(L,axis1=-2,axis2=-1)<=0):raise ValueError('global_cholesky must be exactly lower triangular with positive diagonal.')
        if np.max(abs(c-c.swapaxes(-1,-2)))>1e-12*max(1.,float(np.max(abs(c)))):raise ValueError('Covariances must be symmetric.')
        a=_scalar(defensive_fraction,'defensive_fraction');nu=_scalar(student_df,'student_df');s=_scalar(student_scale,'student_scale')
        if not 0<a<1 or nu<=2 or s<=0:raise ValueError('Require 0<defensive_fraction<1, student_df>2, student_scale>0.')
        try:super().__init__(w,m,c,g,L,defensive_fraction=a,student_df=nu,student_scale=s)
        except np.linalg.LinAlgError as error:raise ValueError('Covariances must be positive definite; no repair.') from error
        if not all(np.isfinite(v).all() for v in [self.precision,self.global_precision,self.gaussian_constant,self.student_constant,self.cumulative]):
            raise ValueError('Mixture precision or normalization overflow; unsupported numerical range.')
