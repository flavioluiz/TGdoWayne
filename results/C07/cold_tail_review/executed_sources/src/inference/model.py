"""Frozen C07 Fourier experiment, spectral covariance and exact moment coefficients."""
import numpy as np
from pta.simulation import JULIAN_YEAR_SECONDS as YEAR, residual_power_spectrum
from pta.statistics import angular_estimators

def experiment(config):
    n=config['n_pulsars'];i=np.arange(n)
    z=1-2*(i+.5)/n;phi=np.pi*(3-np.sqrt(5))*i
    p=np.column_stack((np.sqrt(1-z*z)*np.cos(phi),np.sqrt(1-z*z)*np.sin(phi),z))
    seeds=config['geometry_seeds'];lo,hi=config['distance_range_light_years']
    d=np.linspace(lo,hi,n)[np.random.default_rng(seeds[0]).permutation(n)]
    sigma=np.geomspace(1e-7,5e-7,n)[np.random.default_rng(seeds[1]).permutation(n)]
    red=np.geomspace(.5,2,n)[np.random.default_rng(seeds[2]).permutation(n)]
    T=config['duration_years']*YEAR
    dt=T/int(np.ceil(T/(config['cadence_days']*86400)))
    f=np.asarray(config['positive_channels'])/T
    scale=residual_power_spectrum(f,-14.7,13/3)+2*np.median(sigma)**2*dt
    H=angular_estimators(p,sigma,cross_bins=4,auto_bins=2)
    return dict(points=p,distance_ly=d,sigma=sigma,red=red,T=T,dt=dt,f=f,scale=scale,H=H.matrices,labels=H.labels,weights=np.asarray(config['frequency_weights']))


def covariance_batch(eta,gamma,e):
    eta=np.atleast_2d(eta);ag,slope,ar,efac=eta.T
    sg=10**(2*ag[:,None])*YEAR**3/(12*np.pi*np.pi)*(e['f'][None,:]*YEAR)**(-slope[:,None])/e['scale']
    sr=10**(2*ar[:,None])*YEAR**3/(12*np.pi*np.pi)*(e['f'][None,:]*YEAR)**(-4)/e['scale']
    sw=10**(2*efac[:,None])*2*e['dt']/e['scale']
    weights=np.stack((sg,sr,sw),axis=-1)
    c=sg[:,:,None,None]*gamma[None]
    ii=np.arange(c.shape[-1])
    c[:,:,ii,ii]+=sr[:,:,None]*e['red'][None,None,:]**2+sw[:,:,None]*e['sigma'][None,None,:]**2
    return c,weights


def moment_basis(gamma,e):
    k,p,_=gamma.shape
    components=np.stack((gamma,np.broadcast_to(np.diag(e['red']**2),(k,p,p)),np.broadcast_to(np.diag(e['sigma']**2),(k,p,p))),axis=1)
    hc=np.einsum('dab,ksbc->ksdac',e['H'],components,optimize=True)
    mu=np.einsum('ksdaa->ksd',hc).real
    sigma=np.einsum('ksiab,ktjba->kstij',hc,hc,optimize=True).real
    return mu,sigma
