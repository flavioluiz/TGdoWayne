"""Exact first/second moments and cumulants of proper-complex Gaussian quadratics.

The quadratic estimators are NOT asserted to have a Gaussian distribution.
There is no inference or calibration acceptance in this module.
"""
from dataclasses import dataclass
import math
import numpy as np


def _hermitian(value, name):
    a=np.asarray(value,dtype=np.complex128)
    if a.ndim<2 or a.shape[-2]!=a.shape[-1] or not np.isfinite(a).all():
        raise ValueError(f'{name} must contain finite square matrices.')
    scale=np.maximum(np.max(np.abs(a),axis=(-2,-1)),np.finfo(float).tiny)
    error=np.max(np.abs(a-a.swapaxes(-1,-2).conj()),axis=(-2,-1))
    if np.any(error>1e-11*scale):raise ValueError(f'{name} is not Hermitian.')
    return a


@dataclass(frozen=True)
class AngularEstimators:
    matrices: np.ndarray
    labels: tuple[str,...]
    metadata: dict


def angular_estimators(directions, nominal_toa_sigma, *, cross_bins, auto_bins):
    """Freeze equal-count angle bins and precision-based auto bins before simulation.

    Re and Im bins use pairs a<b. Precision groups use nominal TOA errors,
    never the truth, observed powers, or a fitted EFAC.
    """
    p=np.asarray(directions,dtype=float);sigma=np.asarray(nominal_toa_sigma,dtype=float)
    if p.ndim!=2 or p.shape[1]!=3 or len(p)<2 or not np.isfinite(p).all():raise ValueError('Unit directions required.')
    if not np.allclose(np.linalg.norm(p,axis=1),1,atol=1e-12,rtol=0):raise ValueError('Directions must be unit vectors.')
    if sigma.shape!=(len(p),) or not np.isfinite(sigma).all() or np.any(sigma<=0):raise ValueError('Positive nominal TOA sigmas required.')
    pairs=np.array([(a,b) for a in range(len(p)) for b in range(a+1,len(p))])
    for value,maximum,name in [(cross_bins,len(pairs),'cross_bins'),(auto_bins,len(p),'auto_bins')]:
        if isinstance(value,bool) or not isinstance(value,(int,np.integer)) or not 1<=value<=maximum:raise ValueError(f'Invalid {name}.')
    cosine=np.array([np.dot(p[a],p[b]) for a,b in pairs])
    groups=np.array_split(np.argsort(cosine,kind='stable'),cross_bins)
    H=[];labels=[]
    for component in ['real','imag']:
        for index,group in enumerate(groups):
            h=np.zeros((len(p),len(p)),complex)
            for a,b in pairs[group]:
                h[a,b]=(0.5 if component=='real' else 0.5j)/len(group)
                h[b,a]=h[a,b].conjugate()
            H.append(h);labels.append(f'cross_{component}_{index}')
    agroups=np.array_split(np.argsort(sigma,kind='stable'),auto_bins)
    for index,group in enumerate(agroups):
        h=np.zeros((len(p),len(p)),complex);h[group,group]=1/len(group)
        H.append(h);labels.append(f'auto_{index}')
    matrices=np.array(H);matrices.flags.writeable=False
    return AngularEstimators(matrices,tuple(labels),{
        'pair_orientation':'a<b; Im(q_a q_b*) changes sign if pair order is swapped',
        'pair_indices':pairs.tolist(),'pair_cosines':cosine.tolist(),
        'cross_bins_pair_indices':[pairs[g].tolist() for g in groups],
        'auto_bins_pulsars':[g.tolist() for g in agroups],
        'weights':'uniform within each bin; bins fixed from directions and nominal sigma only'})


def quadratic_statistics(samples, matrices):
    q=np.asarray(samples,dtype=np.complex128);h=_hermitian(matrices,'matrices')
    if h.ndim!=3 or q.ndim<1 or q.shape[-1]!=h.shape[-1] or not np.isfinite(q).all():raise ValueError('Incompatible samples and estimator matrices.')
    return np.einsum('...a,dab,...b->...d',q.conj(),h,q,optimize=True).real


def quadratic_moments(covariance, matrices):
    """mu_i=tr(H_i C), Sigma_ij=tr(H_i C H_j C), for proper CN only."""
    c=_hermitian(covariance,'covariance');h=_hermitian(matrices,'matrices')
    if h.ndim!=3 or h.shape[-1]!=c.shape[-1]:raise ValueError('Incompatible matrices.')
    hc=np.einsum('dab,...bc->...dac',h,c,optimize=True)
    return (np.einsum('...daa->...d',hc).real,
            np.einsum('...iab,...jba->...ij',hc,hc,optimize=True).real)


def quadratic_cumulants(covariance, matrix, *, maximum_order=4):
    """kappa_r=(r-1)! tr[(HC)^r]; one covariance and one scalar projection."""
    c=_hermitian(covariance,'covariance');h=_hermitian(matrix,'matrix')
    if c.ndim!=2 or h.shape!=c.shape:raise ValueError('Use one covariance and one matching Hermitian matrix.')
    if isinstance(maximum_order,bool) or not isinstance(maximum_order,(int,np.integer)) or not 1<=maximum_order<=12:raise ValueError('maximum_order must be between 1 and 12.')
    factor=np.linalg.cholesky(c)
    eigenvalues=np.linalg.eigvalsh(factor.conj().T@h@factor)
    return np.array([math.factorial(r-1)*np.sum(eigenvalues**r) for r in range(1,maximum_order+1)])


def standardized_cumulants(covariance, matrix):
    k=quadratic_cumulants(covariance,matrix)
    if k[1]<=0:raise ValueError('A zero-variance statistic has no standardized cumulants.')
    return {'mean':float(k[0]),'variance':float(k[1]),
            'skewness':float(k[2]/k[1]**1.5),'excess_kurtosis':float(k[3]/k[1]**2)}


def _weights(weights,n):
    w=np.asarray(weights,dtype=float)
    if w.shape!=(n,) or not np.isfinite(w).all():raise ValueError('One finite, fixed weight per frequency required.')
    return w


def compress_frequencies(statistics,weights):
    y=np.asarray(statistics,dtype=float)
    if y.ndim<2 or not np.isfinite(y).all():raise ValueError('Statistics require frequency and estimator axes.')
    w=_weights(weights,y.shape[-2])
    return np.einsum('k,...kd->...d',w,y,optimize=True)


def compress_independent_moments(mean,covariance,weights):
    """For independent frequency blocks only. Coupled windows require the full operator."""
    mu=np.asarray(mean,dtype=float);cov=np.asarray(covariance,dtype=float)
    if mu.ndim<2 or cov.shape!=mu.shape+(mu.shape[-1],) or not np.isfinite(cov).all():raise ValueError('Expected mean (...,K,d), covariance (...,K,d,d).')
    w=_weights(weights,mu.shape[-2])
    return compress_frequencies(mu,w),np.einsum('k,...kij->...ij',w*w,cov,optimize=True)


def compress_full_moments(mean,covariance,operator):
    """mu_B=W mu and Sigma_B=W Sigma W^T, retaining any inter-frequency covariance."""
    mu=np.asarray(mean,dtype=float);cov=np.asarray(covariance,dtype=float);w=np.asarray(operator,dtype=float)
    if mu.ndim!=1 or cov.shape!=(len(mu),len(mu)) or w.ndim!=2 or w.shape[1]!=len(mu):raise ValueError('Incompatible full moments/operator.')
    if not all(np.isfinite(x).all() for x in (mu,cov,w)):raise ValueError('Finite moments/operator required.')
    return w@mu,w@cov@w.T


def proper_complex_real_covariance(covariance,pseudocovariance=None):
    """Real covariance of (Re q,Im q); includes optional P=E[q q^T].

    A nonzero P means the vector is improper: do not use quadratic_moments
    or a proper-CN likelihood on it without the corresponding correction.
    """
    c=_hermitian(covariance,'covariance')
    if c.ndim!=2:raise ValueError('One full covariance matrix required.')
    p=np.zeros_like(c) if pseudocovariance is None else np.asarray(pseudocovariance,dtype=complex)
    if p.shape!=c.shape or not np.isfinite(p).all() or not np.allclose(p,p.T,atol=1e-12,rtol=1e-11):raise ValueError('Pseudocovariance must be finite and symmetric.')
    return .5*np.block([[(c+p).real,(p-c).imag],[(p+c).imag,(c-p).real]])
