"""Standard Cholesky and forward substitution, vectorized over small matrices."""
import numpy as np

def forward_substitution(L,b):
    if L.shape[-1]!=L.shape[-2] or b.shape[-2]!=L.shape[-1]:raise ValueError('Incompatible triangular system.')
    x=np.empty_like(b,dtype=np.result_type(L,b))
    for i in range(L.shape[-1]):
        x[...,i,:]=(b[...,i,:]-np.einsum('...i,...ij->...j',L[...,i,:i],x[...,:i,:]))/L[...,i,i,None]
    return x

def cholesky_batch(c):
    if c.shape[-1]!=c.shape[-2]:raise ValueError('Matrix must be square.')
    L=np.zeros_like(c)
    for j in range(c.shape[-1]):
        diag=(c[...,j,j]-np.einsum('...i,...i->...',L[...,j,:j],L[...,j,:j].conj())).real
        if np.any(~np.isfinite(diag)) or np.any(diag<=0):raise np.linalg.LinAlgError('Covariance is not positive definite; no clipping or jitter.')
        L[...,j,j]=np.sqrt(diag)
        col=c[...,j+1:,j]-np.einsum('...ik,...k->...i',L[...,j+1:,:j],L[...,j,:j].conj())
        L[...,j+1:,j]=col/L[...,j,j,None]
    return L
