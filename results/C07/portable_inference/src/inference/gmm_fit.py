"""Same weighted EM as the frozen proposal fit; reuse each Cholesky across points."""
import numpy as np
from scipy.special import logsumexp,logit
from .gmm_fit_reference import DefensiveLogitMixture

def gaussian_logpdf(z,means,covariances):
    z=np.asarray(z);means=np.asarray(means);covariances=np.asarray(covariances)
    delta=z[:,None,:]-means[None]
    chol=np.linalg.cholesky(covariances)
    # One small factor per component, many right-hand sides; no repeated LU per point.
    rhs=delta.transpose(1,2,0)
    solved=np.linalg.solve(chol,rhs).transpose(2,0,1)
    logdet=2*np.log(np.diagonal(chol,axis1=-2,axis2=-1)).sum(axis=-1)
    return -.5*(np.sum(solved**2,axis=-1)+logdet[None]+z.shape[-1]*np.log(2*np.pi))

def fit_proposal(unit_points, log_weights, *, components=2, iterations=60, covariance_floor=0.03, inflation=1.15, defensive_fraction=0.125):
    """Deterministic weighted EM on pilot posterior weights; no truth input."""
    x = np.asarray(unit_points)
    log_weights = np.asarray(log_weights)
    if x.ndim != 2 or log_weights.shape != (len(x),):
        raise ValueError('Pilot shapes mismatch.')
    if not np.isfinite(x).all() or np.any(x <= 0) or np.any(x >= 1):
        raise ValueError('Pilot points must be inside unit cube.')
    w = np.exp(log_weights - logsumexp(log_weights))
    z = logit(x)
    d = x.shape[1]
    mean = w @ z
    delta = z - mean
    cov = np.einsum('n,ni,nj->ij', w, delta, delta)
    eig, vec = np.linalg.eigh(cov)
    principal = z @ vec[:, -1]
    order = np.argsort(principal)
    cum = np.cumsum(w[order])
    indices = [order[min(np.searchsorted(cum, (j + 0.5) / components), len(x) - 1)] for j in range(components)]
    means = z[indices].copy()
    covs = np.array([cov + covariance_floor * np.eye(d)] * components)
    pis = np.ones(components) / components
    last = -np.inf
    for iteration in range(iterations):
        logprob = gaussian_logpdf(z, means, covs) + np.log(pis)
        norm = logsumexp(logprob, axis=1)
        objective = float(w @ norm)
        responsibilities = np.exp(logprob - norm[:, None]) * w[:, None]
        mass = responsibilities.sum(axis=0)
        if np.min(mass) < 1e-08:
            raise RuntimeError('Pilot mixture collapsed; choose fewer components explicitly.')
        pis = mass / mass.sum()
        means = responsibilities.T @ z / mass[:, None]
        for j in range(components):
            delta = z - means[j]
            covs[j] = np.einsum('n,ni,nj->ij', responsibilities[:, j], delta, delta) / mass[j] + covariance_floor * np.eye(d)
        if abs(objective - last) < 1e-08:
            break
        last = objective
    proposal = DefensiveLogitMixture(pis, means, covs * inflation, defensive_fraction)
    diagnostics = {'pilot_weight_concentration_ess': float(1 / (w @ w)), 'maximum_pilot_weight': float(w.max()), 'em_iterations': iteration + 1, 'covariance_floor_logit': covariance_floor, 'covariance_inflation': inflation, 'note': 'Regularization changes only proposal efficiency; exact proposal density remains in all importance weights.'}
    return (proposal, diagnostics)
