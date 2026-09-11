"""Guarded algebraic subdivision, retaining the executed v1 separately."""
import numpy as np

def coordinate(u):
 u=np.asarray(u)
 if u.dtype.kind not in 'fiu' or u.ndim!=1 or not np.isfinite(u).all() or np.any((u<0)|(u>1)):raise ValueError('Finite real u vector required')
 return -np.sqrt((1-u)*(1+u))

def _nodes(nodes):
 n=np.asarray(nodes);x=coordinate(n)
 if len(n)<2 or np.any(np.diff(n)<=0) or np.any(np.diff(x)<=0):raise ValueError('At least two strictly increasing u AND transformed nodes required')
 return n,x

def _curve(nodes,coeff):
 n,x=_nodes(nodes);c=np.asarray(coeff)
 if c.dtype.kind not in 'fc' or c.ndim<3 or c.shape[:2]!=(len(n)-1,4) or not np.isfinite(c).all():raise ValueError('Finite floating real/complex polynomial coefficients with matching shape required')
 return n,x,c

def evaluate(nodes,coeff,u):
 nodes,x,c=_curve(nodes,coeff);t=coordinate(u)
 if np.any(t<x[0]) or np.any(t>x[-1]):raise ValueError('Outside curve support')
 j=np.minimum(np.searchsorted(x,t,side='right')-1,len(x)-2)
 h=(t-x[j])/(x[j+1]-x[j]);shape=(-1,)+(1,)*(c.ndim-2);h=h.reshape(shape);picked=c[j]
 return picked[:,0]+h*(picked[:,1]+h*(picked[:,2]+h*picked[:,3]))

def subdivide(nodes,coeff,new_nodes):
 """Every old knot must occur exactly; polynomial argument a+b*t is exact."""
 old,x,c=_curve(nodes,coeff);new,y=_nodes(new_nodes)
 if len(new)<len(old) or new[0]!=old[0] or new[-1]!=old[-1] or not np.isin(old,new).all():raise ValueError('New knots must refine old knots and preserve endpoints')
 j=np.minimum(np.searchsorted(x,y[:-1],side='right')-1,len(x)-2)
 if np.any(y[1:]>x[j+1]):raise ValueError('Subdivision crosses an existing breakpoint')
 width=x[j+1]-x[j];shape=(-1,)+(1,)*(c.ndim-2);a=((y[:-1]-x[j])/width).reshape(shape);b=((y[1:]-y[:-1])/width).reshape(shape)
 picked=c[j];v=np.empty((len(new)-1,*c.shape[1:]),dtype=c.dtype)
 v[:,0]=picked[:,0]+a*(picked[:,1]+a*(picked[:,2]+a*picked[:,3]))
 v[:,1]=b*(picked[:,1]+a*(2*picked[:,2]+3*a*picked[:,3]))
 v[:,2]=b*b*(picked[:,2]+3*a*picked[:,3]);v[:,3]=b*b*b*picked[:,3]
 return v

def bernstein_eigenvalues(coeff):
 c=np.asarray(coeff)
 if c.dtype.kind not in 'fc' or c.ndim<4 or c.shape[1]!=4 or c.shape[-1]!=c.shape[-2] or not len(c) or not np.isfinite(c).all():raise ValueError('Nonempty finite floating matrix polynomial required')
 minimum=np.inf;hermiticity=0.
 for start in range(0,len(c),128):
  a0,a1,a2,a3=np.moveaxis(c[start:start+128],1,0)
  for b in [a0,a0+a1/3,a0+2*a1/3+a2/3,a0+a1+a2+a3]:
   hermiticity=max(hermiticity,float(np.max(abs(b-b.swapaxes(-1,-2).conj()))));minimum=min(minimum,float(np.linalg.eigvalsh(b).min()))
 if hermiticity>1e-11 or minimum< -1e-12:raise ValueError('Polynomial is not Hermitian/PSD within declared roundoff; no eigenvalue clipping')
 return dict(minimum_Bernstein_eigenvalue=minimum,maximum_Bernstein_hermiticity_error=hermiticity)
