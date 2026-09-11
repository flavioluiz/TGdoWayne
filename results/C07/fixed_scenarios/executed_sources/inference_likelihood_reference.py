"""Normalized CN and real-normal likelihoods with Cholesky reference solves."""
import numpy as np
from .model import covariance_batch, moment_basis
from pta.statistics import compress_frequencies, compress_independent_moments

def cn_logpdf(c,q):
    """Batch C (N,K,P,P), data (R,K,P), one proper CN coefficient/channel."""
    chol=np.linalg.cholesky(c)
    rhs=np.broadcast_to(q.transpose(1,2,0),(len(c),*q.transpose(1,2,0).shape))
    solved=np.linalg.solve(chol,rhs)
    ld=2*np.log(np.diagonal(chol,axis1=-2,axis2=-1).real).sum(axis=(-2,-1))
    return -np.sum(abs(solved)**2,axis=(1,2))-ld[:,None]-q.shape[1]*q.shape[2]*np.log(np.pi)


def normal_logpdf(mu,cov,y):
    """Batch independent frequency blocks; y=(R,K,d)."""
    chol=np.linalg.cholesky(cov)
    residual=y.transpose(1,2,0)[None]-mu[:,:,:,None]
    solved=np.linalg.solve(chol,residual)
    ld=2*np.log(np.diagonal(chol,axis1=-2,axis2=-1)).sum(axis=(-2,-1))
    return -.5*(np.sum(solved*solved,axis=(1,2))+ld[:,None]+y.shape[1]*y.shape[2]*np.log(2*np.pi))


class Likelihood:
    def __init__(self,e,q,xphysical,xgaussian):
        self.e=e;self.q=q;self.n=len(q)
        self.x=np.concatenate((xphysical,xgaussian),axis=0)
        self.z=compress_frequencies(self.x,e['weights'])[:,None,:]
        self.names=['A0_CN','A_CN','B_CN','A_G','B_G']
    def prepare(self,gamma):
        return moment_basis(gamma,self.e)
    def __call__(self,eta,gamma,basis=None):
        c,w=covariance_batch(eta,gamma,self.e)
        a0=cn_logpdf(c,self.q)
        bm,bs=moment_basis(gamma,self.e) if basis is None else basis
        mu=np.einsum('nks,ksd->nkd',w,bm,optimize=True)
        cov=np.einsum('nks,nkt,kstij->nkij',w,w,bs,optimize=True)
        a=normal_logpdf(mu,cov,self.x)
        mb,cb=compress_independent_moments(mu,cov,self.e['weights'])
        b=normal_logpdf(mb[:,None,:],cb[:,None,:,:],self.z)
        # Result flattened as model-major R. This ordering is frozen in metadata.
        return np.concatenate((a0,a[:,:self.n],b[:,:self.n],a[:,self.n:],b[:,self.n:]),axis=-1)
