"""Whole-cell Taylor bounds for affine CN and quadratic normal covariances.

The inequalities hold in exact arithmetic for the supplied polynomial model.
Ordinary float64 evaluation and the explicit roundoff allowance do not constitute
an interval-arithmetic or physical ORF error certificate.
"""
import math
import numpy as np


def _whiten(L, matrix):
    return np.linalg.solve(L.conj(),np.linalg.solve(L,matrix).T).T


def _norm(matrix):
    return float(np.linalg.norm(matrix,ord=2))


def _report(center,derivative,curvature,halfwidth,allowance):
    radius=abs(derivative)*halfwidth+.5*curvature*halfwidth**2
    numerical=allowance+64*np.finfo(float).eps*(1+abs(center)+radius)
    return dict(available=True,lower=center-radius-numerical,upper=center+radius+numerical,
                derivative=derivative,curvature_absolute_bound=curvature,
                explicit_roundoff_allowance=allowance,additional_arithmetic_allowance=numerical-allowance,
                rigorous_floatingpoint_certificate=False,physical_uniform_certificate=False)


def _domain(left,right,center_loglike,roundoff_allowance):
    if not all(math.isfinite(float(x)) for x in (left,right,center_loglike,roundoff_allowance)):
        raise ValueError('Finite cell, center density and explicit roundoff allowance required')
    if not 0<=left<right<=1 or roundoff_allowance<0:raise ValueError('Invalid epsilon domain/allowance')
    return left+(right-left)/2,(right-left)/2


def cn_taylor(coefficients,observations,left,right,center_loglike,*,roundoff_allowance):
    x,h=_domain(left,right,center_loglike,roundoff_allowance)
    c=np.asarray(coefficients);q=np.asarray(observations)
    if c.ndim!=4 or c.shape[0]!=2 or c.shape[2]!=c.shape[3] or q.shape!=c.shape[1:3]:raise ValueError('CN polynomial shape')
    if not np.isfinite(c).all() or not np.isfinite(q).all():raise ValueError('Nonfinite CN inputs')
    derivative=0.;curvature=0.
    for c0,c1,z in zip(c[0],c[1],q):
        L=np.linalg.cholesky(c0+x*c1);D=_whiten(L,c1);v=np.linalg.solve(L,z)
        s=_norm(D);rho=h*s
        if rho>=1:return dict(available=False,reason='CN cell has no positive Neumann lower bound')
        a=1/(1-rho);v2=float(np.vdot(v,v).real)
        derivative+=float((-np.trace(D)+np.vdot(v,D@v)).real)
        curvature+=len(z)*(a*s)**2+2*v2*s*s*a**3
    return _report(center_loglike,derivative,curvature,h,roundoff_allowance)


def normal_taylor(mean_coefficients,covariance_coefficients,observations,left,right,center_loglike,*,roundoff_allowance):
    x,h=_domain(left,right,center_loglike,roundoff_allowance)
    mu=np.asarray(mean_coefficients);sigma=np.asarray(covariance_coefficients);y=np.asarray(observations)
    if mu.ndim!=3 or mu.shape[0]!=2 or sigma.shape!=(3,mu.shape[1],mu.shape[2],mu.shape[2]) or y.shape!=mu.shape[1:]:raise ValueError('Normal polynomial shape')
    if any(np.iscomplexobj(v) or not np.isfinite(v).all() for v in (mu,sigma,y)):raise ValueError('Finite real normal moments required')
    derivative=0.;curvature=0.
    for k,observation in enumerate(y):
        S=sigma[0,k]+x*sigma[1,k]+x*x*sigma[2,k]
        L=np.linalg.cholesky(S)
        V=_whiten(L,sigma[1,k]+2*x*sigma[2,k]);W=_whiten(L,2*sigma[2,k])
        r=np.linalg.solve(L,observation-mu[0,k]-x*mu[1,k]);b=np.linalg.solve(L,mu[1,k])
        v0=_norm(V);w=_norm(W);rho=h*v0+.5*h*h*w
        if rho>=1:return dict(available=False,reason='Normal cell has no positive Neumann lower bound')
        a=1/(1-rho);v=v0+h*w;bn=float(np.linalg.norm(b));rn=float(np.linalg.norm(r))+h*bn;d=len(observation)
        derivative+=float(-.5*np.trace(V)+np.dot(b,r)+.5*np.dot(r,V@r))
        curvature+=(.5*d*a*a*v*v+.5*d*a*w+a*bn*bn+2*a*a*bn*v*rn
                    +.5*a*a*w*rn*rn+a**3*v*v*rn*rn)
    return _report(center_loglike,derivative,curvature,h,roundoff_allowance)
