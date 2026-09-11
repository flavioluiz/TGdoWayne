"""Prototype guarded FFI for the unchanged C07 polynomial/Cholesky kernel.

No compilation or file loading occurs implicitly. Supply the locally compiled
library and a trusted, independently validated reference-model bank. All native
buffers are owned copies, aligned, contiguous, and read-only after construction.
No reference-model arrays or mutable spectral settings are retained.
"""
import ctypes
import numpy as np
from inference.model import YEAR

class NativeLikelihood:
    def __init__(self,model,bounds,library):
        self.bounds=self._owned(bounds,float,'prior bounds')
        if self.bounds.shape!=(5,2) or np.any(self.bounds[:,0]>=self.bounds[:,1]) or not np.array_equal(self.bounds[0],[0,1]):
            raise ValueError('Five proper prior bounds and u support [0,1] required')
        self.nd=self._integer(model.n,1,2**30,'data count')
        self.K=self._integer(len(model.e['f']),1,8,'frequency count')
        self.P=self._integer(len(model.e['points']),1,16,'pulsar count')
        self.D=self._integer(len(model.e['H']),1,16,'statistic count')
        self.frequencies=self._owned(model.e['f'],float,'frequencies')
        self.scale=self._owned(model.e['scale'],float,'data scale')
        dt=np.asarray(model.e['dt'])
        if dt.ndim!=0 or dt.dtype.kind not in 'fiu' or not np.isfinite(dt) or dt<=0:
            raise ValueError('Positive real sampling interval required')
        self.dt=float(dt)
        if self.frequencies.shape!=(self.K,) or self.scale.shape!=(self.K,) or np.any(self.frequencies<=0) or np.any(self.scale<=0):
            raise ValueError('Invalid frequency or normalization arrays')
        self.nodes=self._owned(model.table.nodes,float,'mass nodes')
        if self.nodes.ndim!=1 or len(self.nodes)<2 or self.nodes[0]!=0 or self.nodes[-1]!=1 or np.any(np.diff(self.nodes)<=0):
            raise ValueError('Increasing full-support nodes required')
        self.I=len(self.nodes)-1
        if getattr(model.table,'coordinate_name',None)!='beta':raise ValueError('This wrapper implements only the validated minus-beta spline')
        self.coordinate=self._owned(-np.sqrt((1-self.nodes)*(1+self.nodes)),float,'beta coordinates')
        if np.any(np.diff(self.coordinate)<=0):raise ValueError('Degenerate beta intervals')
        shape=(self.I,4,self.K,self.P,self.P)
        gamma=np.asarray(model.table.coeff)
        if gamma.shape!=shape or gamma.dtype.kind not in 'fc':raise ValueError('Wrong cubic ORF coefficients')
        self.gamma=self._owned(gamma,np.complex128,'cubic ORF coefficients')
        if np.max(abs(self.gamma-self.gamma.swapaxes(-1,-2).conj()))>1e-12:
            raise ValueError('ORF polynomial coefficients are not Hermitian')
        if np.max(abs(np.diagonal(self.gamma,axis1=-2,axis2=-1).imag))>1e-12:
            raise ValueError('Complex ORF diagonal')
        mb=np.asarray(model.meanbank);cb=np.asarray(model.covbank)
        if mb.shape!=(self.I,self.K,6,self.D) or cb.shape!=(self.I,self.K,21,self.D,self.D):
            raise ValueError('Wrong polynomial moment banks')
        if mb.dtype.kind not in 'fiu' or cb.dtype.kind not in 'fiu':raise ValueError('Moment banks must be real')
        if not np.isfinite(cb).all() or np.max(abs(cb-cb.swapaxes(-1,-2)))>1e-12:
            raise ValueError('Nonfinite or nonsymmetric covariance bank')
        self.means=self._owned(mb,float,'mean bank')
        ii,jj=np.tril_indices(self.D)
        self.covpacked=self._owned(cb[...,ii,jj],float,'packed covariance bank')
        red=self._owned(model.e['red'],float,'red pattern');white=self._owned(model.e['sigma'],float,'white noise')
        if red.shape!=(self.P,) or white.shape!=(self.P,) or np.any(red<0) or np.any(white<=0):raise ValueError('Invalid pulsar noise patterns')
        self.red2=self._owned(red**2,float,'squared red pattern');self.white2=self._owned(white**2,float,'white variance')
        self.frequency_weights=self._owned(model.e['weights'],float,'compression weights')
        if self.frequency_weights.shape!=(self.K,):raise ValueError('Invalid frequency weights')
        self.q=self._owned(model.data['q'],np.complex128,'CN observations')
        self.y=self._owned(model.y,float,'normal observations');self.z=self._owned(model.z,float,'compressed observations')
        if self.q.shape!=(self.nd,self.K,self.P) or self.y.shape!=(2,self.nd,self.K,self.D) or self.z.shape!=(2,self.nd,self.D):
            raise ValueError('Wrong observation shapes')
        expected=np.einsum('gmkd,k->gmd',self.y,self.frequency_weights)
        if not np.allclose(self.z,expected,atol=1e-12,rtol=1e-12):raise ValueError('Compressed observations are inconsistent')
        self.library=ctypes.CDLL(str(library));self.function=self.library.full_likelihood_v2
        fp=np.ctypeslib.ndpointer(dtype=np.float64,flags=('C_CONTIGUOUS','ALIGNED'))
        cp=np.ctypeslib.ndpointer(dtype=np.complex128,flags=('C_CONTIGUOUS','ALIGNED'))
        ip=np.ctypeslib.ndpointer(dtype=np.int64,flags=('C_CONTIGUOUS','ALIGNED'))
        self.function.argtypes=[ctypes.c_size_t]*6+[ip,fp,ip]+[fp]*5+[cp]+[fp]*3+[cp]+[fp]*3
        self.function.restype=ctypes.c_int64

    @staticmethod
    def _integer(value,lo,hi,name):
        if isinstance(value,(bool,np.bool_)) or not isinstance(value,(int,np.integer)) or not lo<=value<=hi:raise ValueError('Invalid '+name)
        return int(value)

    @staticmethod
    def _owned(value,dtype,name):
        raw=np.asarray(value)
        kinds='fiu' if np.dtype(dtype).kind=='f' else 'fciu'
        if raw.dtype.kind not in kinds:raise ValueError(name+' must have a numeric compatible dtype')
        a=np.array(raw,dtype=dtype,order='C',copy=True)
        if not np.isfinite(a).all():raise ValueError('Nonfinite '+name)
        a.setflags(write=False)
        return a

    def weights(self,theta):
        u,g,gamma,r,efac=np.asarray(theta).T
        pg=10**(2*g[:,None])*YEAR**3/(12*np.pi*np.pi)*(self.frequencies[None,:]*YEAR)**(-gamma[:,None])/self.scale
        pr=10**(2*r[:,None])*YEAR**3/(12*np.pi*np.pi)*(self.frequencies[None,:]*YEAR)**(-4)/self.scale
        pw=10**(2*efac[:,None])*2*self.dt/self.scale
        return pg,pr,pw

    def __call__(self,theta,targets):
        raw=np.asarray(theta);target=np.asarray(targets)
        if raw.dtype.kind not in 'fiu' or raw.ndim!=2 or raw.shape[1]!=5 or not np.isfinite(raw).all():raise ValueError('Invalid theta batch')
        if target.dtype.kind not in 'iu' or target.shape!=(len(raw),) or np.any(target<0) or np.any(target>=5*self.nd):raise ValueError('Invalid integer target IDs')
        t=np.require(raw,dtype=np.float64,requirements=['C','A'])
        if np.any(t<self.bounds[:,0]) or np.any(t>self.bounds[:,1]):raise ValueError('Parameters outside validated prior support')
        ids=np.require(target,dtype=np.int64,requirements=['C','A'])
        if len(t)==0:return np.empty(0)
        j=np.clip(np.searchsorted(self.nodes,t[:,0],side='right')-1,0,self.I-1)
        coord=-np.sqrt((1-t[:,0])*(1+t[:,0]));f=(coord-self.coordinate[j])/(self.coordinate[j+1]-self.coordinate[j])
        segment=np.require(j,dtype=np.int64,requirements=['C','A']);fraction=np.require(f,dtype=np.float64,requirements=['C','A'])
        weights=self.weights(t)
        if len(weights)!=3:raise ValueError('Three covariance components required')
        weights=[np.require(a,dtype=np.float64,requirements=['C','A']) for a in weights]
        if any(a.shape!=(len(t),self.K) or not np.isfinite(a).all() or np.any(a<=0) for a in weights):raise ValueError('Invalid covariance weights')
        out=np.empty(len(t))
        error=self.function(len(t),self.nd,self.K,self.P,self.D,self.I,segment,fraction,ids,
            *weights,self.means,self.covpacked,self.gamma,self.red2,self.white2,self.frequency_weights,
            self.q,self.y,self.z,out)
        if error<0:raise ValueError(f'Native contract failure {error}')
        if error>0:raise np.linalg.LinAlgError(f'Nonpositive/nonfinite Cholesky pivot at batch index {error-1}; no jitter applied')
        if not np.isfinite(out).all():raise FloatingPointError('Nonfinite native likelihood')
        return out
