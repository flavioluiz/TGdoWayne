"""Direct physical spectral covariance plus Hermitian traces, independent of component bases."""
import numpy as np
YEAR=365.25*86400

def moments(eta,gamma,e):
 ag,slope,ar,efac=map(float,eta);H=e['H'];mu=np.zeros(len(H));cov=np.zeros((len(H),len(H)))
 for k,f in enumerate(e['f']):
  signal=10**(2*ag)*YEAR**3/(12*np.pi**2)*(f*YEAR)**(-slope)/e['scale'][k]
  red=10**(2*ar)*YEAR**3/(12*np.pi**2)*(f*YEAR)**(-4)/e['scale'][k]
  white=10**(2*efac)*2*e['dt']/e['scale'][k]
  C=signal*gamma[k]+np.diag(red*e['red']**2+white*e['sigma']**2)
  HC=H@C
  mk=np.trace(HC,axis1=-2,axis2=-1)
  sk=np.einsum('iab,jba->ij',HC,HC)
  if np.max(abs(mk.imag))>1e-10*max(1.,np.max(abs(mk.real))) or np.max(abs(sk.imag))>1e-10*max(1.,np.max(abs(sk.real))):raise ValueError('Nonreal Hermitian trace beyond declared roundoff')
  mu+=e['weights'][k]*mk.real;cov+=e['weights'][k]**2*sk.real
 return mu,cov
