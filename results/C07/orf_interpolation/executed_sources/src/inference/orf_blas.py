"""An explicitly budgeted alternative construction of the SAME harmonic ORF.

No C05 source/cache modifications. Build one frequency/resolution basis at a
time; reuse it over beta batches using real BLAS for real/imaginary weights.
"""
from dataclasses import dataclass
import numpy as np
from scipy.special import roots_legendre
from pta import transfer

@dataclass(frozen=True)
class TableBudget:
    maximum_estimated_memory_bytes:int=768*1024**2
    maximum_multiplications_per_batch:int=50_000_000_000
    maximum_batch_size:int=16

def estimate(lmax,nmu,npulsars,batch):
    L=lmax-1
    # Real associated basis, geometry kernel, nodes/recurrence temporaries.
    fixed=8*nmu*L+8*npulsars*npulsars*L+64*nmu
    # Real and imaginary W, transfer temporaries, all coefficient products and
    # conservative einsum/BLAS scratch. This is an estimate, not an RSS promise.
    buffers=16*batch*npulsars*nmu+96*batch*nmu+64*batch*npulsars*L+64*batch*npulsars*npulsars
    return dict(basis_bytes=8*nmu*L,geometry_bytes=8*npulsars*npulsars*L,
                estimated_memory_bytes=int(fixed+buffers),
                real_multiplications_per_batch=int(2*batch*npulsars*nmu*L),
                recurrence_elements=int(nmu*L),batch_size=batch)

class RealHarmonicBasis:
    def __init__(self,points,*,lmax,nmu,budget=TableBudget(),planned_batch=8):
        points=np.asarray(points,float)
        if points.ndim!=2 or points.shape[1]!=3 or not np.isfinite(points).all():raise ValueError('Finite3D unit directions required.')
        if np.max(abs(np.sum(points*points,axis=1)-1))>1e-12:raise ValueError('Directions must be unit length; no normalization repair.')
        if lmax<2 or nmu<2:raise ValueError('Positive harmonic and angular resolution required.')
        self.points=points;self.lmax=int(lmax);self.nmu=int(nmu);self.budget=budget
        self.preflight(planned_batch)
        self.x,self.w=roots_legendre(self.nmu)
        self.angular_weight=self.w*(1-self.x*self.x)
        self.P=np.empty((self.nmu,self.lmax-1),float,order='F')
        self.geometry=np.empty((len(points),len(points),self.lmax-1),float)
        # This clipping only repairs unit-vector dot-product roundoff.
        delta=np.clip(points@points.T,-1.,1.)
        previous=np.zeros_like(self.x);associated=3*(1-self.x*self.x)
        leg_previous=np.ones_like(delta);leg=delta.copy()
        for ell in range(2,self.lmax+1):
            self.P[:,ell-2]=associated
            previous,associated=associated,((2*ell+1)*self.x*associated-(ell+2)*previous)/(ell-1)
            new=((2*ell-1)*delta*leg-(ell-1)*leg_previous)/ell
            norm=3/32*(2*ell+1)/((ell-1)*ell*(ell+1)*(ell+2))
            self.geometry[:,:,ell-2]=norm*new
            leg_previous,leg=leg,new
        self.P.flags.writeable=False;self.geometry.flags.writeable=False
    def preflight(self,batch):
        if not 1<=batch<=self.budget.maximum_batch_size:raise ValueError('Batch outside declared budget.')
        report=estimate(self.lmax,self.nmu,len(self.points),batch)
        if report['estimated_memory_bytes']>self.budget.maximum_estimated_memory_bytes:raise RuntimeError('Basis/buffer estimate exceeds the NEW backend memory budget.')
        if report['real_multiplications_per_batch']>self.budget.maximum_multiplications_per_batch:raise RuntimeError('BLAS batch work estimate exceeds the NEW backend budget.')
        return report
    def evaluate(self,betas,y):
        betas=np.asarray(betas,float);y=np.asarray(y,float)
        if betas.ndim!=1 or not np.isfinite(betas).all() or np.any(betas<0) or np.any(betas>1):raise ValueError('Real beta batch in[0,1] required.')
        if y.shape!=(len(self.points),):raise ValueError('One phase per pulsar required.')
        self.preflight(len(betas));B=len(betas);P=len(y)
        real=np.empty((B,P,self.nmu));imag=np.empty_like(real)
        d=1+betas[:,None]*self.x[None]
        # The same audited transfer function is reused. Each temporary holds
        # only one pulsar's B×nmu values, not B×P×nmu complex values.
        for j,yy in enumerate(y):
            t=transfer(float(yy),d)*self.angular_weight[None]
            real[:,j]=t.real;imag[:,j]=t.imag
        rc=real.reshape(B*P,self.nmu)@self.P
        ic=imag.reshape(B*P,self.nmu)@self.P
        coefficients=(rc+1j*ic).reshape(B,P,self.lmax-1)
        # optimize=False executes the contraction without constructing a
        # B×P×P×ell outer-product array. Budget includes coefficient conjugate.
        g=np.einsum('bal,bcl,acl->bac',coefficients,coefficients.conj(),self.geometry,optimize=False)
        return (g+g.swapaxes(-1,-2).conj())/2
