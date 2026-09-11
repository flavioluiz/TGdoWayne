"""Algebraic subdivision of PSD-certified cubic curves, no spline refit."""
import numpy as np

def coordinate(u):
 u=np.asarray(u)
 if u.dtype.kind not in 'fiu' or u.ndim!=1 or not np.isfinite(u).all() or np.any((u<0)|(u>1)):raise ValueError('Finite real u vector required')
 return -np.sqrt((1-u)*(1+u))

def evaluate(nodes,coeff,u):
 nodes=np.asarray(nodes);x=coordinate(nodes);t=coordinate(u)
 if nodes.ndim!=1 or len(nodes)<2 or np.any(np.diff(nodes)<=0) or not np.isfinite(coeff).all() or coeff.shape[:2]!=(len(nodes)-1,4):raise ValueError('Malformed polynomial representation')
 if np.any(t<x[0]) or np.any(t>x[-1]):raise ValueError('Outside curve support')
 j=np.minimum(np.searchsorted(x,t,side='right')-1,len(x)-2)
 h=(t-x[j])/(x[j+1]-x[j]);shape=(-1,)+(1,)*(coeff.ndim-2);h=h.reshape(shape);c=coeff[j]
 return c[:,0]+h*(c[:,1]+h*(c[:,2]+h*c[:,3]))

def subdivide(nodes,coeff,new_nodes):
 """Every old knot must occur exactly; polynomial argument a+b*t is exact."""
 old=np.asarray(nodes);new=np.asarray(new_nodes)
 if len(new)<len(old) or new[0]!=old[0] or new[-1]!=old[-1] or not np.isin(old,new).all() or np.any(np.diff(new)<=0):raise ValueError('New knots must refine old knots and preserve endpoints')
 x=coordinate(old);y=coordinate(new);j=np.minimum(np.searchsorted(x,y[:-1],side='right')-1,len(x)-2)
 if np.any(y[1:]>x[j+1]+2*np.spacing(abs(x[j+1]))):raise ValueError('Subdivision crosses an existing breakpoint')
 width=x[j+1]-x[j];shape=(-1,)+(1,)*(coeff.ndim-2);a=((y[:-1]-x[j])/width).reshape(shape);b=((y[1:]-y[:-1])/width).reshape(shape)
 c=coeff[j];v=np.empty((len(new)-1,*coeff.shape[1:]),dtype=coeff.dtype)
 v[:,0]=c[:,0]+a*(c[:,1]+a*(c[:,2]+a*c[:,3]))
 v[:,1]=b*(c[:,1]+a*(2*c[:,2]+3*a*c[:,3]))
 v[:,2]=b*b*(c[:,2]+3*a*c[:,3]);v[:,3]=b*b*b*c[:,3]
 return v

def bernstein_eigenvalues(coeff):
 c=np.asarray(coeff);minimum=np.inf;hermiticity=0.
 for start in range(0,len(c),128):
  a0,a1,a2,a3=np.moveaxis(c[start:start+128],1,0)
  for b in [a0,a0+a1/3,a0+2*a1/3+a2/3,a0+a1+a2+a3]:
   if not np.isfinite(b).all():raise ValueError('Nonfinite control matrix')
   hermiticity=max(hermiticity,float(np.max(abs(b-b.swapaxes(-1,-2).conj()))));minimum=min(minimum,float(np.linalg.eigvalsh(b).min()))
 if hermiticity>1e-11 or minimum< -1e-12:raise ValueError('Polynomial is not Hermitian/PSD within declared roundoff; no eigenvalue clipping')
 return dict(minimum_Bernstein_eigenvalue=minimum,maximum_Bernstein_hermiticity_error=hermiticity)
