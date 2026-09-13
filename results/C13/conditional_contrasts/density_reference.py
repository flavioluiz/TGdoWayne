"""Finite positive density representation; no physical interpolation certificate."""
import numpy as np
from scipy.interpolate import PchipInterpolator
from scipy.optimize import brentq

class Density:
    def __init__(self,u,ell):
        u=np.asarray(u,float);ell=np.asarray(ell,float)
        if u.ndim!=1 or ell.shape!=u.shape or not np.isfinite(ell).all():
            raise ValueError('Finite one-dimensional likelihood required')
        if u[0]!=0 or u[-1]!=1 or not np.all(np.diff(u)>0):
            raise ValueError('Strict ordered full uniform-u support required')
        self.u=u;self.x=np.arcsin(u);self.shift=float(ell.max())
        y=np.exp(ell-self.shift)*np.cos(self.x);y[-1]=0
        self.pdf=PchipInterpolator(self.x,y,extrapolate=False)
        self.primitive=self.pdf.antiderivative()
        self.mass=float(self.primitive(self.x[-1])-self.primitive(0))
        if not self.mass>0 or not np.isfinite(self.pdf.c).all():raise ArithmeticError('Invalid density')
        self.logz=self.shift+np.log(self.mass)
        self.loglike=PchipInterpolator(self.x,ell,extrapolate=False)
    def cdf_alpha(self,x):return (self.primitive(x)-self.primitive(0))/self.mass
    def cdf(self,u):
        if np.any(np.asarray(u)<0) or np.any(np.asarray(u)>1):raise ValueError('Outside support')
        return self.cdf_alpha(np.arcsin(u))
    def quantile(self,p):
        if not 0<=p<=1:raise ValueError('Probability required')
        if p in (0,1):return float(p)
        return float(np.sin(brentq(lambda x:float(self.cdf_alpha(x))-p,0,self.x[-1],xtol=1e-13)))
    def event(self,threshold):
        """Mass for surrogate logL below/equal threshold, preserving atom interval."""
        roots=self.loglike.solve(threshold,extrapolate=False)
        roots=roots[np.isfinite(roots)&(roots>0)&(roots<self.x[-1])]
        cuts=np.unique(np.r_[self.x,roots]);below=equal=0.
        for lo,hi in zip(cuts[:-1],cuts[1:]):
            mid=(lo+hi)/2;idx=min(np.searchsorted(self.x,mid)-1,len(self.x)-2)
            c=self.loglike.c[:,idx]
            mass=float(self.cdf_alpha(hi)-self.cdf_alpha(lo))
            if np.all(c[:-1]==0) and c[-1]==threshold:equal+=mass
            elif self.loglike(mid)<threshold:below+=mass
        return [below,below+equal]

def compare(a,b):
    """Extrema of CDF difference for two fixed piecewise polynomial surrogates."""
    cuts=np.unique(np.r_[a.x,b.x]);stationary=[]
    for lo,hi in zip(cuts[:-1],cuts[1:]):
        mid=(lo+hi)/2
        coeff=np.array([(a.pdf(mid,nu=k)/a.mass-b.pdf(mid,nu=k)/b.mass)/fact
                        for k,fact in enumerate((1,1,2,6))])
        if np.any(coeff):
            roots=np.polynomial.polynomial.polyroots(coeff)
            stationary.extend(mid+r.real for r in roots if abs(r.imag)<1e-12 and lo<mid+r.real<hi)
    nodes=np.unique(np.r_[cuts,stationary]);delta=a.cdf_alpha(nodes)-b.cdf_alpha(nodes)
    return dict(maximum_surrogate_CDF_difference=float(abs(delta).max()),
                at_u=float(np.sin(nodes[abs(delta).argmax()])),
                logZ_difference=abs(float(a.logz-b.logz)),
                scope='Finite surrogate comparison only; independent physical integrals remain required')
