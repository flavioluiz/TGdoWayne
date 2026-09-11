"""Normalized logit-space Gaussian mixture with a wide Student-t safeguard."""
import numpy as np
from scipy.special import gammaln,logsumexp
from linalg_batch import forward_substitution
class GaussianDefensiveProposal:
    def __init__(self,weights,means,covariances,global_mean,global_cholesky,*,defensive_fraction=.15,student_df=5.,student_scale=3.):
        self.weights=np.asarray(weights,float);self.means=np.asarray(means,float);self.cov=np.asarray(covariances,float);self.global_mean=np.asarray(global_mean,float);self.global_chol=np.asarray(global_cholesky,float)
        self.n,self.k,self.d=self.means.shape
        if self.weights.shape!=(self.n,self.k) or self.cov.shape!=(self.n,self.k,self.d,self.d) or self.global_mean.shape!=(self.n,self.d) or self.global_chol.shape!=(self.n,self.d,self.d):raise ValueError('Incompatible mixture shapes.')
        if not all(np.isfinite(x).all() for x in [self.weights,self.means,self.cov,self.global_mean,self.global_chol]) or np.any(self.weights<=0) or not np.allclose(self.weights.sum(axis=1),1) or not 0<defensive_fraction<1 or student_df<=2 or not np.isfinite(student_scale) or student_scale<=0:raise ValueError('Invalid normalized defensive mixture.')
        self.alpha=defensive_fraction;self.nu=student_df;self.scale=student_scale
        self.chol=np.linalg.cholesky(self.cov);eye=np.broadcast_to(np.eye(self.d),self.chol.shape);invL=forward_substitution(self.chol,eye);self.precision=invL.swapaxes(-1,-2)@invL
        self.gaussian_constant=-.5*(2*np.log(np.diagonal(self.chol,axis1=-2,axis2=-1)).sum(axis=-1)+self.d*np.log(2*np.pi))
        invG=forward_substitution(self.global_chol,np.broadcast_to(np.eye(self.d),self.global_chol.shape));self.global_precision=invG.swapaxes(-1,-2)@invG
        self.student_constant=gammaln((self.nu+self.d)/2)-gammaln(self.nu/2)-self.d/2*np.log(np.pi*(self.nu-2))-np.log(np.diagonal(self.global_chol,axis1=-2,axis2=-1)).sum(axis=-1)-self.d*np.log(self.scale)
        self.cumulative=np.cumsum(np.column_stack(((1-self.alpha)*self.weights,np.full(self.n,self.alpha))),axis=1);self.cumulative[:,-1]=1.
    def logpdf(self,z):
        z=np.asarray(z,float)
        if z.ndim!=2 or z.shape[1]!=self.d or len(z)%self.n or not np.isfinite(z).all():raise ValueError('Logit points must have complete ordered target batches.')
        z=z.reshape(self.n,-1,self.d);delta=z[:,:,None,:]-self.means[:,None,:,:]
        mahal=np.einsum('ncki,nkij,nckj->nck',delta,self.precision,delta)
        normal=self.gaussian_constant[:,None,:]-.5*mahal+np.log((1-self.alpha)*self.weights)[:,None,:]
        delta=z-self.global_mean[:,None,:];mahal=np.einsum('nci,nij,ncj->nc',delta,self.global_precision,delta)
        student=self.student_constant[:,None]-.5*(self.nu+self.d)*np.log1p(mahal/((self.nu-2)*self.scale**2))+np.log(self.alpha)
        return logsumexp(np.concatenate((normal,student[:,:,None]),axis=-1),axis=-1).ravel()
    def sample(self,rngs):
        c=len(rngs);u=np.stack([r.random(self.n) for r in rngs],axis=1);which=np.sum(u[:,:,None]>self.cumulative[:,None,:],axis=-1)
        noise=np.stack([r.normal(size=(self.n,self.d)) for r in rngs],axis=1);ix=np.arange(self.n)[:,None];jj=np.minimum(which,self.k-1)
        z=self.means[ix,jj]+np.einsum('ncij,ncj->nci',self.chol[ix,jj],noise)
        mask=which==self.k
        chi=np.stack([r.chisquare(self.nu,size=self.n) for r in rngs],axis=1)
        t=self.global_mean[:,None,:]+np.einsum('nij,ncj->nci',self.global_chol,noise)*np.sqrt((self.nu-2)/chi[:,:,None])*self.scale
        z[mask]=t[mask];return z.reshape(-1,self.d)
