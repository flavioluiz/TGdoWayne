"""Defensive continuous RQMC importance proposal on a unit hypercube.

Data-adapted training is excluded from the production estimates. All mixture
component densities and coordinate Jacobians are known; no support is removed.
"""
from dataclasses import dataclass
import numpy as np
from scipy.special import expit,logit,logsumexp,ndtri
from scipy.stats import qmc


def gaussian_logpdf(z,means,covariances):
    z=np.asarray(z);means=np.asarray(means);covariances=np.asarray(covariances)
    delta=z[:,None,:]-means[None]
    chol=np.linalg.cholesky(covariances)
    solved=np.linalg.solve(chol[None],delta[:,:,:,None])[...,0]
    logdet=2*np.log(np.diagonal(chol,axis1=-2,axis2=-1)).sum(axis=-1)
    return -.5*(np.sum(solved**2,axis=-1)+logdet[None]+z.shape[-1]*np.log(2*np.pi))


@dataclass
class DefensiveLogitMixture:
    component_weights:np.ndarray
    means:np.ndarray
    covariances:np.ndarray
    defensive_fraction:float=.125

    def __post_init__(self):
        self.component_weights=np.asarray(self.component_weights,dtype=float)
        self.means=np.asarray(self.means,dtype=float);self.covariances=np.asarray(self.covariances,dtype=float)
        k,d=self.means.shape
        if self.component_weights.shape!=(k,) or self.covariances.shape!=(k,d,d):raise ValueError('Mixture dimensions do not match.')
        if not 0<self.defensive_fraction<1 or not np.all(self.component_weights>0):raise ValueError('Strictly positive defensive and Gaussian weights required.')
        if not np.isclose(self.component_weights.sum(),1):raise ValueError('Gaussian weights must sum to one.')
        np.linalg.cholesky(self.covariances)

    def log_density(self,x,weights=None):
        x=np.asarray(x)
        if x.ndim!=2 or x.shape[1]!=self.means.shape[1] or np.any(x<=0) or np.any(x>=1) or not np.isfinite(x).all():raise ValueError('Finite open-unit-cube points required.')
        if weights is None:weights=np.r_[self.defensive_fraction,(1-self.defensive_fraction)*self.component_weights]
        z=logit(x)
        log_jacobian=np.log(x).sum(axis=-1)+np.log1p(-x).sum(axis=-1)
        normal=gaussian_logpdf(z,self.means,self.covariances)-log_jacobian[:,None]
        return logsumexp(np.column_stack((np.full(len(x),np.log(weights[0])),normal+np.log(weights[1:]))),axis=1)

    def sample_scramble(self,power,seed):
        """Deterministic-mixture MIS with actual component fractions n_j/N.

        Each component receives an independently scrambled Sobol rule. The
        balance denominator is the mixture with those SAME sample fractions;
        non-power-of-two component counts are prefixes of larger Sobol rules.
        """
        total=2**power;k=len(self.component_weights);d=self.means.shape[1]
        nprior=int(round(total*self.defensive_fraction))
        counts=np.floor((total-nprior)*self.component_weights).astype(int)
        counts[np.argmax(self.component_weights)]+=total-nprior-counts.sum()
        counts=np.r_[nprior,counts]
        if np.any(counts<2):raise ValueError('Every proposal component needs at least two points.')
        actual_weights=counts/total
        children=np.random.SeedSequence(seed).spawn(k+1);points=[]
        for j,(count,child) in enumerate(zip(counts,children)):
            unit=qmc.Sobol(d,scramble=True,seed=np.random.default_rng(child)).random_base2(int(np.ceil(np.log2(count))))[:count]
            if np.any(unit<=0) or np.any(unit>=1):raise FloatingPointError('A digital point hit a transform boundary; use a fresh declared scramble.')
            if j:
                z=ndtri(unit)@np.linalg.cholesky(self.covariances[j-1]).T+self.means[j-1]
                unit=expit(z)
            points.append(unit)
        points=np.concatenate(points)
        return points,self.log_density(points,actual_weights),counts

    def description(self):
        return {'family':'uniform + correlated logit-normal mixture on the open unit hypercube',
                'defensive_fraction':self.defensive_fraction,'component_weights':self.component_weights.tolist(),
                'means_logit':self.means.tolist(),'covariances_logit':self.covariances.tolist(),
                'support':'Full original prior interior; boundaries have zero prior measure. No likelihood, prior or truth is truncated.',
                'density':'q_x(x)=alpha+(1-alpha) sum pi_j N(logit(x);m_j,S_j)/prod[x_i(1-x_i)]',
                'jacobian':'For eta=lo+width*x, prior_eta/q_eta=1/q_x; all prior widths cancel exactly.',
                'production':'Training points excluded. Independent component scrambles, deterministic mixture counts and balance weights.'}


def fit_proposal(unit_points,log_weights,*,components=2,iterations=60,
                 covariance_floor=.03,inflation=1.15,defensive_fraction=.125):
    """Deterministic weighted EM on pilot posterior weights; no truth input."""
    x=np.asarray(unit_points);log_weights=np.asarray(log_weights)
    if x.ndim!=2 or log_weights.shape!=(len(x),):raise ValueError('Pilot shapes mismatch.')
    if not np.isfinite(x).all() or np.any(x<=0) or np.any(x>=1):raise ValueError('Pilot points must be inside unit cube.')
    w=np.exp(log_weights-logsumexp(log_weights));z=logit(x);d=x.shape[1]
    mean=w@z;delta=z-mean;cov=np.einsum('n,ni,nj->ij',w,delta,delta)
    eig,vec=np.linalg.eigh(cov);principal=z@vec[:,-1];order=np.argsort(principal);cum=np.cumsum(w[order])
    indices=[order[min(np.searchsorted(cum,(j+.5)/components),len(x)-1)] for j in range(components)]
    means=z[indices].copy();covs=np.array([cov+covariance_floor*np.eye(d)]*components);pis=np.ones(components)/components
    last=-np.inf
    for iteration in range(iterations):
        logprob=gaussian_logpdf(z,means,covs)+np.log(pis)
        norm=logsumexp(logprob,axis=1);objective=float(w@norm)
        responsibilities=np.exp(logprob-norm[:,None])*w[:,None]
        mass=responsibilities.sum(axis=0)
        if np.min(mass)<1e-8:raise RuntimeError('Pilot mixture collapsed; choose fewer components explicitly.')
        pis=mass/mass.sum();means=responsibilities.T@z/mass[:,None]
        for j in range(components):
            delta=z-means[j]
            covs[j]=np.einsum('n,ni,nj->ij',responsibilities[:,j],delta,delta)/mass[j]+covariance_floor*np.eye(d)
        if abs(objective-last)<1e-8:break
        last=objective
    proposal=DefensiveLogitMixture(pis,means,covs*inflation,defensive_fraction)
    diagnostics={'pilot_weight_concentration_ess':float(1/(w@w)),'maximum_pilot_weight':float(w.max()),
                 'em_iterations':iteration+1,'covariance_floor_logit':covariance_floor,'covariance_inflation':inflation,
                 'note':'Regularization changes only proposal efficiency; exact proposal density remains in all importance weights.'}
    return proposal,diagnostics
