"""Same Taylor inequalities, with linear algebra batched over channels."""
import numpy as np
from .epsilon_taylor import _domain,_report


def whiten(L,a):
    left=np.linalg.solve(L,a)
    return np.linalg.solve(L.conj(),left.swapaxes(-1,-2)).swapaxes(-1,-2)


def cn_taylor(c,q,left,right,center_loglike,*,roundoff_allowance):
    x,h=_domain(left,right,center_loglike,roundoff_allowance)
    c=np.asarray(c);q=np.asarray(q)
    if c.ndim!=4 or c.shape[0]!=2 or c.shape[-1]!=c.shape[-2] or q.shape!=c.shape[1:3] or not np.isfinite(c).all() or not np.isfinite(q).all():raise ValueError('Finite CN polynomial required')
    L=np.linalg.cholesky(c[0]+x*c[1]);D=whiten(L,c[1]);v=np.linalg.solve(L,q[...,None])[...,0]
    s=np.linalg.norm(D,ord=2,axis=(-2,-1));rho=h*s
    if np.any(rho>=1):return dict(available=False,reason='CN cell has no positive Neumann lower bound')
    a=1/(1-rho);v2=np.sum(abs(v)**2,axis=-1)
    derivative=float(np.sum(-np.trace(D,axis1=-2,axis2=-1)+(v.conj()*(D@v[...,None])[...,0]).sum(axis=-1)).real)
    curvature=float(np.sum(q.shape[-1]*(a*s)**2+2*v2*s*s*a**3))
    return _report(center_loglike,derivative,curvature,h,roundoff_allowance)


def normal_taylor(mu,sigma,y,left,right,center_loglike,*,roundoff_allowance):
    x,h=_domain(left,right,center_loglike,roundoff_allowance)
    mu=np.asarray(mu);sigma=np.asarray(sigma);y=np.asarray(y)
    if mu.ndim!=3 or mu.shape[0]!=2 or sigma.shape!=(3,mu.shape[1],mu.shape[2],mu.shape[2]) or y.shape!=mu.shape[1:]:raise ValueError('Normal polynomial shape')
    if any(np.iscomplexobj(a) or not np.isfinite(a).all() for a in (mu,sigma,y)):raise ValueError('Finite real normal moments required')
    L=np.linalg.cholesky(sigma[0]+x*sigma[1]+x*x*sigma[2])
    V=whiten(L,sigma[1]+2*x*sigma[2]);W=whiten(L,2*sigma[2])
    r=np.linalg.solve(L,(y-mu[0]-x*mu[1])[...,None])[...,0];b=np.linalg.solve(L,mu[1,...,None])[...,0]
    v0=np.linalg.norm(V,ord=2,axis=(-2,-1));w=np.linalg.norm(W,ord=2,axis=(-2,-1));rho=h*v0+.5*h*h*w
    if np.any(rho>=1):return dict(available=False,reason='Normal cell has no positive Neumann lower bound')
    a=1/(1-rho);v=v0+h*w;bn=np.linalg.norm(b,axis=-1);rn=np.linalg.norm(r,axis=-1)+h*bn;d=y.shape[-1]
    derivative=float(np.sum(-.5*np.trace(V,axis1=-2,axis2=-1)+(b*r).sum(axis=-1)+.5*(r*(V@r[...,None])[...,0]).sum(axis=-1)))
    curvature=float(np.sum(.5*d*a*a*v*v+.5*d*a*w+a*bn*bn+2*a*a*bn*v*rn+.5*a*a*w*rn*rn+a**3*v*v*rn*rn))
    return _report(center_loglike,derivative,curvature,h,roundoff_allowance)
