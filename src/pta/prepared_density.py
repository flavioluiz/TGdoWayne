"""Normalized single-observation densities from fixed covariance polynomials."""
import numpy as np


class PreparedDensity:
    def __init__(self, covariance, mean, observation, *, maximum_values=256):
        self.c=np.array(covariance,copy=True);self.y=np.array(observation,copy=True)
        self.mu=None if mean is None else np.array(mean,copy=True)
        degree=2 if mean is None else 3
        if self.c.ndim!=4 or self.c.shape[0]!=degree or self.c.shape[-1]!=self.c.shape[-2] or self.y.shape!=self.c.shape[1:3]:
            raise ValueError('Invalid polynomial dimensions')
        if self.mu is not None and (self.mu.shape!=(2,*self.y.shape) or any(np.iscomplexobj(a) for a in (self.c,self.mu,self.y))):
            raise ValueError('Real affine mean and real covariance required')
        if any(not np.isfinite(a).all() for a in (self.c,self.y) if a is not None) or (self.mu is not None and not np.isfinite(self.mu).all()):
            raise ValueError('Finite polynomial and observations required')
        scale=max(float(np.max(abs(self.c))),np.finfo(float).tiny)
        if np.max(abs(self.c-self.c.conj().swapaxes(-1,-2)))>64*np.finfo(float).eps*scale:raise ValueError('Non-Hermitian coefficients')
        if type(maximum_values)is not int or maximum_values<1:raise ValueError('Positive explicit value cap required')
        self.maximum=maximum_values;self.charged=0;self.completed=0
        for a in (self.c,self.y,self.mu):
            if a is not None:a.setflags(write=False)

    def __call__(self, epsilon):
        e=np.asarray(epsilon,float)
        if e.ndim!=1 or not len(e) or not np.isfinite(e).all() or np.any((e<0)|(e>1)):raise ValueError('Finite nonempty epsilon batch within support required')
        if self.charged+len(e)>self.maximum:raise RuntimeError('Prepared density value cap')
        if len(e)*self.c.shape[1]*self.c.shape[2]**2*128>256*1024**2:raise MemoryError('Prepared numeric workspace cap')
        self.charged+=len(e) # Durable accounting belongs to caller's GlobalLedger.
        x=e[:,None,None,None];cov=self.c[0]+x*self.c[1]
        if self.mu is not None:cov=cov+x*x*self.c[2]
        chol=np.linalg.cholesky(cov)
        rhs=np.broadcast_to(self.y,(len(e),*self.y.shape))
        if self.mu is not None:rhs=rhs-self.mu[0]-e[:,None,None]*self.mu[1]
        z=np.linalg.solve(chol,rhs[...,None])[...,0]
        ld=2*np.log(np.diagonal(chol,axis1=-2,axis2=-1).real).sum(axis=(1,2))
        quad=np.sum(abs(z)**2,axis=(1,2))
        n=self.y.size
        result=-quad-ld-n*np.log(np.pi) if self.mu is None else -.5*(quad+ld+n*np.log(2*np.pi))
        if not np.isfinite(result).all():raise ArithmeticError('Nonfinite normalized density')
        self.completed+=len(e)
        return result
