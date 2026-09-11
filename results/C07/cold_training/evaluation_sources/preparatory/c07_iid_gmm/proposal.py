"""Fully normalized Student mixture in logit coordinates for IID importance draws."""
import numpy as np
from scipy.special import gammaln,logsumexp,expit

class StudentLogitMixture:
    def __init__(self,mean,cholesky,*,df=5.,scales=(1.,3.),weights=(.75,.25)):
        self.mean=np.asarray(mean,float);self.L=np.asarray(cholesky,float)
        self.df=float(df);self.scales=np.asarray(scales,float);self.weights=np.asarray(weights,float)
        if self.mean.ndim!=2:raise ValueError('Mean must have target,coordinate axes.')
        self.targets,self.d=self.mean.shape
        if self.L.shape!=(self.targets,self.d,self.d) or not np.isfinite(self.mean).all() or not np.isfinite(self.L).all():raise ValueError('Finite mean and matching Cholesky matrices required.')
        if np.any(np.diagonal(self.L,axis1=-2,axis2=-1)<=0) or np.any(np.triu(self.L,1)!=0):raise ValueError('Positive lower-triangular Cholesky factors required.')
        if not np.isfinite(self.df) or self.df<=2 or self.scales.ndim!=1 or self.weights.shape!=self.scales.shape or not np.isfinite(self.scales).all() or not np.isfinite(self.weights).all() or np.any(self.scales<=0) or np.any(self.weights<=0) or not np.isclose(self.weights.sum(),1,rtol=0,atol=1e-14):raise ValueError('Invalid full-support Student mixture.')
        self.logdetL=np.log(np.diagonal(self.L,axis1=-2,axis2=-1)).sum(axis=-1)
        self.constant=gammaln((self.df+self.d)/2)-gammaln(self.df/2)-.5*self.d*np.log(np.pi*(self.df-2))-self.logdetL
    def sample(self,rng,count):
        if not isinstance(rng,np.random.Generator) or not isinstance(count,int) or isinstance(count,bool) or count<1:raise ValueError('Explicit RNG and positive count required.')
        component=rng.choice(len(self.scales),size=(count,self.targets),p=self.weights)
        normal=rng.standard_normal((count,self.targets,self.d));chi=rng.chisquare(self.df,size=(count,self.targets))
        z=self.mean[None]+np.einsum('tij,ntj->nti',self.L,normal)*np.sqrt((self.df-2)/chi)[:,:,None]*self.scales[component][:,:,None]
        return z,component
    def logpdf(self,z):
        z=np.asarray(z,float)
        if z.ndim!=3 or z.shape[1:]!=self.mean.shape or not np.isfinite(z).all():raise ValueError('Finite sample,target,coordinate array required.')
        rhs=(z-self.mean[None]).transpose(1,2,0)
        whitened=np.linalg.solve(self.L,rhs).transpose(2,0,1)
        r2=np.sum(whitened**2,axis=-1)
        components=self.constant[None,:,None]+np.log(self.weights)[None,None,:]-self.d*np.log(self.scales)[None,None,:]-.5*(self.df+self.d)*np.log1p(r2[:,:,None]/((self.df-2)*self.scales[None,None,:]**2))
        return logsumexp(components,axis=-1)

def unit_log_prior_jacobian(z):
    """log[uniform physical prior * |d theta/dz|]; physical widths cancel."""
    z=np.asarray(z,float)
    return (-np.logaddexp(0,-z)-np.logaddexp(0,z)).sum(axis=-1)
