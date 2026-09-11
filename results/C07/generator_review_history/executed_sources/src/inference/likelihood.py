"""Equivalent batched likelihood using reusable quadratic forms, with reference retained.

Small precision matrices are obtained by triangular-factor solves, never by fitting,
diagonal covariance approximations, or changing the probability family.
"""
import numpy as np
from .likelihood_reference import Likelihood
from .model import covariance_batch, moment_basis
from pta.statistics import compress_independent_moments


def precision_and_logdet(c):
    factor=np.linalg.cholesky(c)
    invfactor=np.linalg.solve(factor,np.broadcast_to(np.eye(c.shape[-1]),c.shape))
    precision=invfactor.swapaxes(-1,-2).conj()@invfactor
    logdet=2*np.log(np.diagonal(factor,axis1=-2,axis2=-1).real).sum(axis=(-2,-1))
    return precision,logdet


def normal_quadratic_logpdf(mu,cov,y,outer):
    precision,ld=precision_and_logdet(cov)
    v=np.einsum('nkab,nkb->nka',precision,mu,optimize=True)
    term0=np.einsum('nkab,rkba->nr',precision,outer,optimize=True)
    term1=np.einsum('nka,rka->nr',v,y,optimize=True)
    term2=np.einsum('nka,nka->n',mu,v,optimize=True)
    quadratic=term0-2*term1+term2[:,None]
    return -.5*(quadratic+ld[:,None]+y.shape[1]*y.shape[2]*np.log(2*np.pi))


class FastLikelihood(Likelihood):
    def __init__(self,e,q,xphysical,xgaussian):
        super().__init__(e,q,xphysical,xgaussian)
        self.qouter=q[:,:,:,None]*q[:,:,None,:].conj()
        self.xouter=self.x[:,:,:,None]*self.x[:,:,None,:]
        self.zouter=self.z[:,:,:,None]*self.z[:,:,None,:]

    def __call__(self,eta,gamma,basis=None):
        c,w=covariance_batch(eta,gamma,self.e)
        precision,ld=precision_and_logdet(c)
        quad=np.einsum('nkab,rkba->nr',precision,self.qouter,optimize=True).real
        a0=-quad-ld[:,None]-self.q.shape[1]*self.q.shape[2]*np.log(np.pi)
        bm,bs=self.prepare(gamma) if basis is None else basis
        mu=np.einsum('nks,ksd->nkd',w,bm,optimize=True)
        cov=np.einsum('nks,nkt,kstij->nkij',w,w,bs,optimize=True)
        a=normal_quadratic_logpdf(mu,cov,self.x,self.xouter)
        mb,cb=compress_independent_moments(mu,cov,self.e['weights'])
        b=normal_quadratic_logpdf(mb[:,None,:],cb[:,None,:,:],self.z,self.zouter)
        return np.concatenate((a0,a[:,:self.n],b[:,:self.n],a[:,self.n:],b[:,self.n:]),axis=-1)
