"""Own and evaluate validated C08 polynomial coefficients; NEVER fit a spline.

This checks the representation, not the astrophysical response or inference.
A C08 response-specific finite-gate manifest is still required by a runtime.
"""
import numpy as np

class FrozenCoefficientORF:
 def __init__(self,nodes,matrices,coeff,*,maximum_owned_numeric_bytes,require_threshold_parity=True):
  n=np.asarray(nodes);m=np.asarray(matrices);c=np.asarray(coeff)
  if n.dtype.kind not in 'fiu' or n.ndim!=1 or len(n)<2 or not np.isfinite(n).all() or n[0]!=0 or n[-1]!=1 or np.any(np.diff(n)<=0):raise ValueError('Increasing full-support finite u nodes required')
  if m.dtype.kind not in 'fc' or m.ndim!=4 or m.shape[0]!=len(n) or m.shape[-1]!=m.shape[-2] or not m.shape[1] or not m.shape[2]:raise ValueError('Floating matrix nodes[N,K,P,P] required')
  if c.dtype.kind not in 'fc' or c.shape!=(len(n)-1,4,*m.shape[1:]) or not np.isfinite(c).all() or not np.isfinite(m).all():raise ValueError('Finite floating matching cubic coefficients required')
  coordinate=-np.sqrt((1-n)*(1+n))
  if np.any(np.diff(coordinate)<=0):raise ValueError('Degenerate transformed beta interval')
  if isinstance(maximum_owned_numeric_bytes,bool) or not isinstance(maximum_owned_numeric_bytes,(int,np.integer)) or maximum_owned_numeric_bytes<=0:raise ValueError('Explicit positive owned-array budget required')
  owned=2*n.size*8+(m.size+c.size)*16
  temporary=min(len(c),128)*4*int(np.prod(m.shape[1:]))*16
  if owned+temporary>maximum_owned_numeric_bytes:raise MemoryError('Owned arrays/control buffers exceed declared budget; caller input arrays need a separate runtime allowance')
  self.nodes=np.array(n,float,copy=True);self.matrices=np.array(m,complex,copy=True);self.coeff=np.array(c,complex,copy=True);self.alpha=np.array(coordinate,float,copy=True);self.coordinate_name='beta'
  herm=max(float(np.max(abs(self.matrices-self.matrices.swapaxes(-1,-2).conj()))),float(np.max(abs(self.coeff-self.coeff.swapaxes(-1,-2).conj()))))
  if herm>1e-12:raise ValueError('Non-Hermitian matrix polynomial')
  continuity=max(float(np.max(abs(self.coeff[:,0]-self.matrices[:-1]))),float(np.max(abs(self.coeff.sum(axis=1)-self.matrices[1:]))))
  if continuity>1e-11:raise ValueError('Polynomial endpoints do not match stored matrix nodes')
  minimum=np.inf
  for start in range(0,len(c),128):
   a0,a1,a2,a3=np.moveaxis(self.coeff[start:start+128],1,0)
   for b in [a0,a0+a1/3,a0+2*a1/3+a2/3,a0+a1+a2+a3]:minimum=min(minimum,float(np.linalg.eigvalsh(b).min()))
  if minimum< -1e-12:raise ValueError('Bernstein controls not PSD; no clipping')
  derivative=-(self.coeff[-1,1]+2*self.coeff[-1,2]+3*self.coeff[-1,3])/(self.alpha[-1]-self.alpha[-2]);parity=float(np.max(abs(derivative)))
  if require_threshold_parity and parity>1e-7:raise ValueError('Nonzero beta derivative at the tensor threshold')
  for a in [self.nodes,self.matrices,self.coeff,self.alpha]:a.flags.writeable=False
  self.representation_checks=dict(owned_and_temporary_estimate_bytes=owned+temporary,maximum_owned_numeric_bytes=int(maximum_owned_numeric_bytes),maximum_Hermiticity_error=herm,maximum_endpoint_error=continuity,minimum_Bernstein_eigenvalue=minimum,threshold_derivative_error=parity,source_coefficients_used_directly=True,spline_fit_performed=False,scientific_response_validation_claimed=False)
 def coordinate(self,u):
  x=np.asarray(u)
  if x.dtype.kind not in 'fiu' or x.ndim!=1 or not np.isfinite(x).all() or np.any((x<0)|(x>1)):raise ValueError('Finite real u vector in[0,1] required')
  return -np.sqrt((1-x)*(1+x))
 def location(self,u):
  beta=self.coordinate(u);j=np.minimum(np.searchsorted(self.nodes,u,side='right')-1,len(self.nodes)-2);fraction=(beta-self.alpha[j])/(self.alpha[j+1]-self.alpha[j]);return j,fraction
 def __call__(self,u):
  j,f=self.location(u);c=self.coeff[j];f=f[:,None,None,None]
  return c[:,0]+f*(c[:,1]+f*(c[:,2]+f*c[:,3]))
