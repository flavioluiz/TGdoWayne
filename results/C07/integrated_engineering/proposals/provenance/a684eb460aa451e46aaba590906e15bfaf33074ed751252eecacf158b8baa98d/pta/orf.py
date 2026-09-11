"""Tensor ORF formulae and raw quadratures, with no implicit resolution.

Gamma_ab=(3/8pi) integral sum_A R_a R_b*, e_A:e_B=2 delta_AB.
Analytic references carry the same fixed normalization for every beta.
raw_ routines return numerical values without convergence certification:
use pta.checked_orf to require independent refinement and an explicit budget.
"""
from decimal import Decimal, localcontext
from functools import lru_cache

import numpy as np
from scipy.integrate import quad
from scipy.special import roots_legendre, eval_legendre

from ._domain import (beta_value, cosine_value, phase, positive_integer,
                      real_array, real_scalar, response_arguments)
from .response import transfer


@lru_cache(maxsize=30)
def _gl_nodes(n):
    n = positive_integer(n, 'nmu')
    nodes, weights = roots_legendre(n)
    # Cached quadrature data must not be accidentally mutated by a caller.
    nodes.flags.writeable = weights.flags.writeable = False
    return nodes, weights


def hellings_downs(cosine):
    cosine = real_array(cosine, 'cosine', lower=-1, upper=1)
    x=(1-np.asarray(cosine))/2
    with np.errstate(divide='ignore',invalid='ignore'):
        xlogx=np.where(x==0,0,x*np.log(x))
    return 0.5-0.25*x+1.5*xlogx


def earth_analytic(beta,cosine):
    """Cordes Eq40, same as Liang Eq35 after normalization. Decimal avoids cancellation."""
    beta, cosine = beta_value(beta), cosine_value(cosine)
    if beta<1e-4:
        # Uniform small-beta expansion: omitted absolute term bounded by
        # (3/8)*beta**4*(5-4*beta)/(1-beta)**2 < 1.9e-16 at this cutoff.
        p2=(3*cosine*cosine-1)/2
        p3=(5*cosine**3-3*cosine)/2
        return p2/5+beta*beta*(2*p2+p3)/35
    if beta==1: return float(hellings_downs(cosine))
    with localcontext() as ctx:
        ctx.prec=90
        b=Decimal(str(beta)); d=Decimal(str(cosine)); one=Decimal(1)
        log=((one+b)/(one-b)).ln()
        if cosine==1:
            return float((6*b-4*b**3+3*(b*b-one)*log)/(4*b**5))
        aa=one+2*b*b*(one-2*d)-b**4*(one-2*d*d)
        bb=((one-d)*(2-b*b*(one+d))).sqrt()
        cc=(aa-2*b*(one-b*b*d)*bb)/(b*b-one)**2
        value=(2*b*(3+(6-5*b*b)*d)-6*(one+d+b*b*(one-3*d))*log
               -3*aa/bb*cc.ln())/(16*b**5)
        return float(value)


def raw_direct_orf(beta,cosine,ya=None,yb=None,*,nmu,nphi):
    """2D angular quadrature, TT projector; no polarization-frame singularities.

    ya=yb=None denotes Earth-only; both must be supplied for complete response.
    Returns complex ORF; unequal distances can yield nonzero imaginary parts.
    """
    beta, cosine, ya, yb = response_arguments(beta, cosine, ya, yb)
    nmu = positive_integer(nmu, 'nmu')
    nphi = positive_integer(nphi, 'nphi')
    x,w=_gl_nodes(nmu)
    mu_a=x[:,None]
    da=1+beta*mu_a
    ga=None if ya is None else transfer(ya,da)
    total=np.zeros(nmu,complex)
    # Bounded-memory blocks retain the exact same quadrature rule.
    for start in range(0,nphi,128):
        phi=(np.arange(start,min(start+128,nphi))+0.5)*2*np.pi/nphi
        mu_b=cosine*mu_a+np.sqrt(max(0,1-cosine*cosine))*np.sqrt(1-mu_a*mu_a)*np.cos(phi)
        tensor_sum=2*(cosine-mu_a*mu_b)**2-(1-mu_a*mu_a)*(1-mu_b*mu_b)
        db=1+beta*mu_b
        if ya is None:
            kernel=tensor_sum/(da*db)
        else:
            kernel=tensor_sum*ga*np.conjugate(transfer(yb,db))
        total+=np.sum(kernel,axis=1)
    # 3/(32pi) integral S ga gb*; phi trapezoid gives factor 2pi.
    return complex(3/16*np.dot(w,total/nphi))


def raw_multipoles(beta,y,*,lmax,nmu):
    """Cordes Eq16 with stable transfer; y=None denotes Earth-only.

    Associated Legendre recurrence avoids repeated O(ell) special-function evaluations.
    Output c_l for ell=2..lmax. Finite-distance response is smooth; lmax must resolve beta*y.
    """
    beta = beta_value(beta)
    y = None if y is None else phase(y)
    lmax = positive_integer(lmax, 'lmax', minimum=2)
    nmu = positive_integer(nmu, 'nmu')
    if y is None and beta==1:
        return 4*(-1.)**np.arange(2,lmax+1)
    x,w=_gl_nodes(nmu)
    if y is None: g=1/(1+beta*x)
    else: g=transfer(y,1+beta*x)
    weight=w*(1-x*x)*g
    pprev=np.zeros_like(x)
    p=3*(1-x*x) # P_2^2
    coefficients=[]
    for ell in range(2,lmax+1):
        coefficients.append(np.dot(weight,p))
        pnext=((2*ell+1)*x*p-(ell+2)*pprev)/(ell-1)
        pprev,p=p,pnext
    return np.asarray(coefficients)


def raw_harmonic_orf(beta,cosine,ya=None,yb=None,*,lmax,nmu):
    """Raw complex ORF and multipole terms; explicit resolution is mandatory."""
    beta, cosine, ya, yb = response_arguments(beta, cosine, ya, yb)
    lmax = positive_integer(lmax, 'lmax', minimum=2)
    nmu = positive_integer(nmu, 'nmu')
    ca=raw_multipoles(beta,ya,lmax=lmax,nmu=nmu)
    cb=ca if ya==yb else raw_multipoles(beta,yb,lmax=lmax,nmu=nmu)
    ell=np.arange(2,lmax+1,dtype=float)
    norms=(3/32)*(2*ell+1)/((ell-1)*ell*(ell+1)*(ell+2))
    terms=norms*ca*np.conjugate(cb)*eval_legendre(ell.astype(int),cosine)
    return complex(np.sum(terms)), terms


def gr_auto_exact(y):
    """Cordes Eq25. y=2*pi*f*L/c; sinc here is sin(x)/x."""
    y = phase(y)
    if abs(y)<0.01:
        return y*y/5-2*y**4/105+y**6/945-2*y**8/51975
    return 1-3/(2*y*y)*(1-np.sinc(2*y/np.pi))


def raw_auto_weighted(beta,y,*,small_epsabs,small_epsrel,oscillatory_epsabs,limit):
    """Independent 1D oscillatory adaptive quadrature of Cordes Eq22.

    Separates constant and cosine parts; QAWO resolves high y without an angular grid.
    Returned error estimates only the two quadratures, not an astrophysical/model error.
    """
    beta, y = beta_value(beta), phase(y)
    small_epsabs = real_scalar(small_epsabs, 'small_epsabs')
    small_epsrel = real_scalar(small_epsrel, 'small_epsrel')
    oscillatory_epsabs = real_scalar(oscillatory_epsabs, 'oscillatory_epsabs')
    if min(small_epsabs, small_epsrel, oscillatory_epsabs) <= 0:
        raise ValueError('Quadrature tolerances must be finite and positive.')
    limit = positive_integer(limit, 'limit')
    if beta==1: return gr_auto_exact(y),0.0
    if beta==0: return 4/5*np.sin(y/2)**2,0.0
    if y<0.1:
        # Avoid cancellation between two O(1) terms when the answer is O(y²).
        val,err=quad(lambda x:(1-x*x)**2*abs(transfer(y,1+beta*x))**2,-1,1,
                     epsabs=small_epsabs,epsrel=small_epsrel,limit=limit)
        return 3/16*val,3/16*err
    def weight(x): return (1-x*x)**2/(1+beta*x)**2
    c,ce=quad(weight,-1,1,weight='cos',wvar=y*beta,epsabs=oscillatory_epsabs,limit=limit)
    si,se=quad(weight,-1,1,weight='sin',wvar=y*beta,epsabs=oscillatory_epsabs,limit=limit)
    result=2*earth_analytic(beta,1)-3/8*(np.cos(y)*c-np.sin(y)*si)
    return result,3/8*(abs(np.cos(y))*ce+abs(np.sin(y))*se)


def threshold_full(cosine,ya,yb):
    _, cosine, ya, yb = response_arguments(0, cosine, ya, yb)
    if ya is None:
        raise ValueError('The full threshold formula requires both phases.')
    return -np.expm1(-1j*ya)*(-np.expm1(1j*yb))*(3*cosine*cosine-1)/10
