"""Positive one-dimensional posterior tables for many likelihood columns.

This interpolates log likelihood, never an ORF. Agreement between tables and
independent physical references must be assessed externally before inference
claims. Wasserstein bounds below concern this normalized positive table only.
"""
import numpy as np
from scipy.interpolate import PchipInterpolator


class MassPosteriorBatch:
    def __init__(self, u, log_likelihood, *, prior='uniform_u', lower=0.,
                 order=32, interval_batch=8, maximum_numeric_bytes=1024**3):
        u=np.asarray(u,float);ell=np.asarray(log_likelihood,float)
        if prior not in ('uniform_u','uniform_u_squared','log_uniform_u'):
            raise ValueError('Registered normalized prior required')
        if u.ndim!=1 or len(u)<3 or ell.ndim!=2 or ell.shape[0]!=len(u) or ell.shape[1]<1:
            raise ValueError('Increasing nodes and likelihood(node,curve) required')
        if not np.isfinite(u).all() or not np.isfinite(ell).all() or np.any(np.diff(u)<=0):
            raise ValueError('Finite increasing nodes and finite likelihoods required')
        if prior=='log_uniform_u':
            if not 0<lower<1:raise ValueError('Explicit positive logarithmic cutoff required')
        elif lower!=0:raise ValueError('Uniform priors here have support [0,1]')
        if u[0]!=lower or u[-1]!=1:raise ValueError('Exact support endpoints required; extrapolation forbidden')
        if not isinstance(order,int) or order<4 or not isinstance(interval_batch,int) or interval_batch<1:
            raise ValueError('Positive quadrature settings required')
        if not isinstance(maximum_numeric_bytes,int) or maximum_numeric_bytes<1:
            raise ValueError('Positive numeric-array budget required')
        self.estimated_base_bytes=int(8*ell.shape[1]*(9*len(u)+8*order*interval_batch))
        self.maximum_numeric_bytes=maximum_numeric_bytes
        if self.estimated_base_bytes>maximum_numeric_bytes:raise MemoryError('Posterior array estimate exceeds budget before interpolation')
        self.u=u.copy();self.alpha=np.arcsin(u);self.prior=prior;self.lower=lower
        self.order=order;self.interval_batch=interval_batch;self.ncurves=ell.shape[1]
        self.shift=ell.max(axis=0);self.interpolator=PchipInterpolator(self.alpha,ell-self.shift,axis=0,extrapolate=False)
        self.coeff=self.interpolator.c
        x,w=np.polynomial.legendre.leggauss(order);self.x=x;self.w=w
        parts=[];moments=np.zeros((3,self.ncurves))
        for first in range(0,len(u)-1,interval_batch):
            lo=self.alpha[first:min(first+interval_batch,len(u)-1)];hi=self.alpha[first+1:first+1+len(lo)]
            a=(lo[:,None]+hi[:,None])/2+(hi-lo)[:,None]*x/2
            y=self.interpolator(a);weights=(hi-lo)[:,None]*w/2
            mass=np.exp(y)*self.prior_alpha_density(a)[...,None]*weights[...,None]
            parts.append(mass.sum(axis=1));v=np.sin(a)[...,None]
            moments[0]+=(mass*v).sum(axis=(0,1));moments[1]+=(mass*v*v).sum(axis=(0,1));moments[2]+=(mass*y).sum(axis=(0,1))
        self.segment_mass=np.concatenate(parts);self.cumulative=np.vstack((np.zeros(self.ncurves),np.cumsum(self.segment_mass,axis=0)))
        self.z=self.cumulative[-1]
        if not np.isfinite(self.z).all() or np.any(self.z<=0):raise ArithmeticError('Invalid normalizer')
        self.summary=dict(logZ=self.shift+np.log(self.z),mean=moments[0]/self.z,second=moments[1]/self.z,KL=moments[2]/self.z-np.log(self.z))

    def prior_alpha_density(self,a):
        u=np.sin(a)
        if self.prior=='uniform_u':return np.cos(a)
        if self.prior=='uniform_u_squared':return 2*u*np.cos(a)
        return np.cos(a)/(u*np.log(1/self.lower))

    def prior_ppf(self,p):
        if self.prior=='uniform_u':return p
        if self.prior=='uniform_u_squared':return np.sqrt(p)
        return self.lower**(1-p)

    def prior_cdf_primitive(self,u):
        if self.prior=='uniform_u':return u*u/2
        if self.prior=='uniform_u_squared':return u*u*u/3
        return (u*np.log(u/self.lower)-u)/np.log(1/self.lower)

    def cdf_per_curve(self,cuts):
        """CDF at cuts(point,curve), integrated inside each containing interval."""
        cuts=np.asarray(cuts,float)
        if cuts.ndim!=2 or cuts.shape[1]!=self.ncurves or not np.isfinite(cuts).all():
            raise ValueError('Finite cuts(point,curve) required')
        if np.any(cuts<self.lower) or np.any(cuts>1):raise ValueError('Cuts outside support')
        outputs=[];columns=np.arange(self.ncurves)[None,None,:]
        for first in range(0,len(cuts),self.interval_batch):
            a=np.arcsin(cuts[first:first+self.interval_batch]);idx=np.minimum(np.searchsorted(self.alpha,a,side='right')-1,len(self.alpha)-2)
            lo=self.alpha[idx];points=(lo[:,None,:]+a[:,None,:])/2+(a-lo)[:,None,:]*self.x[None,:,None]/2
            dx=points-lo[:,None,:];c=self.coeff[:,idx[:,None,:],columns]
            y=((c[0]*dx+c[1])*dx+c[2])*dx+c[3]
            partial=(np.exp(y)*self.prior_alpha_density(points)*self.w[None,:,None]*(a-lo)[:,None,:]/2).sum(axis=1)
            result=(self.cumulative[idx,np.arange(self.ncurves)[None,:]]+partial)/self.z
            if np.any(result < -1e-12) or np.any(result>1+1e-12):raise ArithmeticError('CDF outside numeric range')
            result=np.clip(result,0.,1.);result[cuts[first:first+len(a)]==self.lower]=0.;result[cuts[first:first+len(a)]==1.]=1.;outputs.append(result)
        return np.concatenate(outputs) if outputs else np.empty((0,self.ncurves))

    def cdf(self,common_cuts):
        cuts=np.asarray(common_cuts,float)
        if cuts.ndim!=1:raise ValueError('One-dimensional common cuts required')
        return self.cdf_per_curve(np.broadcast_to(cuts[:,None],(len(cuts),self.ncurves)))

    def quantile_brackets(self,probabilities=(.05,.5,.9,.95),width=0.00049):
        p=np.asarray(probabilities,float)
        if p.ndim!=1 or np.any((p<=0)|(p>=1)) or not np.isfinite(p).all() or not 0<width<1:
            raise ValueError('Interior probabilities and positive width required')
        lo=np.full((len(p),self.ncurves),self.lower);hi=np.ones_like(lo)
        while float(np.max(hi-lo))>width:
            mid=(lo+hi)/2;below=self.cdf_per_curve(mid)<p[:,None];lo=np.where(below,mid,lo);hi=np.where(below,hi,mid)
        return dict(probabilities=p,lower=lo,upper=hi,cdf_lower=self.cdf_per_curve(lo),cdf_upper=self.cdf_per_curve(hi),scope='Quantiles of the positive interpolated table; physical validation is separate')

    def wasserstein_bounds(self,cells=2048):
        """Monotone-CDF envelopes bound W1 of this table without CDF interpolation.

        On [x0,x1], a<=F_post<=b. Integrate distance of F_prior to [a,b]
        for the lower bound and the farther endpoint for the upper bound.
        Their total width is at most max step * sum(b-a) = max step.
        Quadrature error in the evaluated CDF is not included in this bound.
        """
        if not isinstance(cells,int) or cells<2:raise ValueError('At least two cells required')
        if self.estimated_base_bytes+20*(cells+1)*self.ncurves*8>self.maximum_numeric_bytes:
            raise MemoryError('W1 array estimate exceeds budget; split likelihood columns')
        grid=np.linspace(self.lower,1.,cells+1);F=self.cdf(grid)
        if np.min(np.diff(F,axis=0)) < -1e-12:raise ArithmeticError('Nonmonotone CDF')
        a,b=F[:-1],F[1:];x0,x1=grid[:-1,None],grid[1:,None];A=self.prior_cdf_primitive
        ta=np.clip(self.prior_ppf(a),x0,x1);tb=np.clip(self.prior_ppf(b),x0,x1);tm=np.clip(self.prior_ppf((a+b)/2),x0,x1)
        lower=(a*(ta-x0)-(A(ta)-A(x0))+(A(x1)-A(tb))-b*(x1-tb)).sum(axis=0)
        upper=(b*(tm-x0)-(A(tm)-A(x0))+(A(x1)-A(tm))-a*(x1-tm)).sum(axis=0)
        if np.any(lower < -1e-10) or np.any(upper < lower-1e-10) or np.any(upper-lower > (1-self.lower)/cells+1e-10):raise ArithmeticError('Invalid W1 envelope')
        return dict(lower=np.maximum(lower,0),upper=np.maximum(upper,0),maximum_width=(1-self.lower)/cells,scope='Positive posterior table only; excludes CDF quadrature and physical backend error')
