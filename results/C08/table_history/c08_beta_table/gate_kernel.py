"""Only the compressed real-normal likelihood; no posterior evaluation bank.

Frequencies remain independent before fixed compression. H are the actual
C06 Hermitian estimators, including the imaginary cross components.
"""
import numpy as np
from beta_builder import ROOT
from inference.model import covariance_batch,moment_basis

def compressed_moments(eta,gamma,e):
 _,weight=covariance_batch(eta,gamma,e)
 bm,bs=moment_basis(gamma,e)
 mu=np.einsum('nks,ksd,k->nd',weight,bm,e['weights'],optimize=True)
 cov=np.einsum('nks,nkt,kstij,k->nij',weight,weight,bs,e['weights']**2,optimize=True)
 if not np.isfinite(mu).all() or not np.isfinite(cov).all():raise ValueError('Nonfinite normal moments')
 if np.max(abs(cov-cov.swapaxes(-1,-2)))>1e-10*max(1.,np.max(abs(cov))):raise ValueError('Asymmetric covariance')
 return mu,cov

def compressed_logpdf(mu,cov,observations):
 chol=np.linalg.cholesky(cov)
 delta=observations.T[None]-mu[:,:,None]
 # Solve all observed datasets as columns, no density normalization omitted.
 solved=np.linalg.solve(chol,delta)
 ld=2*np.log(np.diagonal(chol,axis1=-2,axis2=-1)).sum(axis=-1)
 return -.5*(np.sum(solved*solved,axis=1)+ld[:,None]+mu.shape[-1]*np.log(2*np.pi))

def direct_trace_moments(eta,gamma,e):
 c,_=covariance_batch(eta,gamma,e)
 hc=np.einsum('iab,nkbc->nkiac',e['H'],c,optimize=True)
 mu=np.einsum('nki aa->nki',hc).real
 cov=np.einsum('nkiab,nkjba->nkij',hc,hc,optimize=True).real
 return np.einsum('nki,k->ni',mu,e['weights']),np.einsum('nkij,k->nij',cov,e['weights']**2)
