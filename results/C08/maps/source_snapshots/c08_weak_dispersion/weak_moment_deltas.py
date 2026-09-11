"""Algebra of the first variation of independent proper-complex moments."""
import numpy as np


def first_variation(c0, dc, h, weights, *, maximum_numeric_bytes):
    if not all(isinstance(a,np.ndarray) for a in (c0,dc,h,weights)):
        raise TypeError('Existing arrays required before allocation')
    if c0.ndim != 3 or dc.shape != c0.shape or h.ndim != 3:
        raise ValueError('C0 and deltaC[K,P,P], H[D,P,P]')
    k,p,p2 = c0.shape; d,hp,hp2 = h.shape
    if p != p2 or (hp,hp2) != (p,p) or weights.shape != (k,) or not (1<=k<=8 and 1<=p<=16 and 1<=d<=16):
        raise ValueError('Bounded consistent shapes required')
    estimate = 16*(2*k*p*p+d*p*p+4*k*d*p*p) + 8*(k*d+3*k*d*d+4*d*d)
    if type(maximum_numeric_bytes) is not int or maximum_numeric_bytes < estimate:
        raise MemoryError('First-variation allowance exceeded before products')
    if not all(a.dtype in (np.dtype('float64'),np.dtype('complex128')) and np.isfinite(a).all()
               for a in (c0,dc,h)) or weights.dtype != np.float64 or not np.isfinite(weights).all():
        raise ValueError('Finite double-precision inputs required')
    for a in (c0,dc,h):
        error=np.max(abs(a-a.swapaxes(-1,-2).conj()))
        if error > 1e-11*max(float(np.max(abs(a))),np.finfo(float).tiny):
            raise ValueError('Hermitian matrices required')
    hc=np.einsum('iab,kbc->kiac',h,c0,optimize=False)
    hd=np.einsum('iab,kbc->kiac',h,dc,optimize=False)
    mu=np.trace(hd,axis1=-2,axis2=-1)
    cov=(np.einsum('kiab,kjba->kij',hd,hc,optimize=False)
         +np.einsum('kiab,kjba->kij',hc,hd,optimize=False))
    for a in (mu,cov):
        if np.max(abs(a.imag))>1e-11*max(float(np.max(abs(a))),np.finfo(float).tiny):
            raise ArithmeticError('Unexpected complex moment variation')
    return (np.einsum('k,ki->i',weights,mu.real),
            np.einsum('k,kij->ij',weights**2,cov.real))


def backward_derivatives(f0, fh, f2h, f4h, h):
    if not isinstance(h,(int,float)) or isinstance(h,bool) or not np.isfinite(h) or h<=0:
        raise ValueError('Positive finite step')
    return ((3*f0-4*fh+f2h)/(2*h), (3*f0-4*f2h+f4h)/(4*h))


def normalized_max(a,b):
    return float(np.max(abs(a-b))/max(1.,float(np.max(abs(b)))))
