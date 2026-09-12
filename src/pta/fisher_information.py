"""Local Fisher information for proper CN and real Gaussian experiments.

The supplied derivatives define the experiment. This module does not assign
Gaussian Fisher information to misspecified quadratic physical observations.
"""
import numpy as np


def _whiten(covariance, derivatives):
    c = np.asarray(covariance)
    d = np.asarray(derivatives)
    if c.ndim != 3 or c.shape[-1] != c.shape[-2] or d.ndim != 4 or d.shape[1:] != c.shape:
        raise ValueError('Expected C[channel,n,n] and dC[parameter,channel,n,n]')
    if not np.isfinite(c).all() or not np.isfinite(d).all():
        raise ValueError('Finite covariance and derivatives required')
    for a in (c, d):
        scale = max(float(np.max(np.abs(a))), np.finfo(float).tiny)
        if np.max(np.abs(a-a.conj().swapaxes(-1,-2))) > 64*np.finfo(float).eps*scale:
            raise ValueError('Hermitian covariance and derivatives required')
    L = np.linalg.cholesky(c)
    left = np.linalg.solve(L[None], d)
    white = np.linalg.solve(L[None], left.conj().swapaxes(-1,-2)).conj().swapaxes(-1,-2)
    return L, white


def proper_cn_features(covariance, derivatives):
    """Fisher = F.T @ F; no real-normal factor 1/2 for proper CN."""
    _, white = _whiten(covariance, derivatives)
    return np.concatenate((white.real.reshape(len(white),-1),
                           white.imag.reshape(len(white),-1)), axis=1).T


def real_gaussian_features(covariance, derivatives, mean_derivatives):
    """Independent channels with parameter-dependent mean and covariance."""
    if any(np.iscomplexobj(x) for x in (covariance, derivatives, mean_derivatives)):
        raise ValueError('Real Gaussian inputs must be real')
    L, white = _whiten(covariance, derivatives)
    dm = np.asarray(mean_derivatives)
    if dm.shape != (len(white), *L.shape[:-1]) or not np.isfinite(dm).all():
        raise ValueError('Expected dmu[parameter,channel,n]')
    mean = np.linalg.solve(L[None], dm[..., None])[...,0]
    return np.concatenate((mean.reshape(len(white),-1),
                           white.reshape(len(white),-1)/np.sqrt(2)), axis=1).T


def local_diagnostics(features, coordinate_scales, *, interest=(0,1), rank_relative=1e-8):
    """Project nuisance score span by SVD; never invert a singular direction.

    Rank threshold is relative to Fisher eigenvalues, hence its square root
    applies to singular values of the score feature matrix.
    """
    f = np.asarray(features, float); scales = np.asarray(coordinate_scales, float)
    if f.ndim != 2 or scales.shape != (f.shape[1],) or not np.isfinite(f).all() or not np.isfinite(scales).all() or np.any(scales <= 0):
        raise ValueError('Finite features and positive coordinate scales required')
    if not 0 < rank_relative < 1 or len(set(interest)) != len(interest) or not set(interest) <= set(range(f.shape[1])):
        raise ValueError('Invalid rank threshold or interest coordinates')
    score = f * scales[None]
    information = score.T @ score
    eigenvalues = np.linalg.eigvalsh(information)
    threshold = rank_relative * max(float(eigenvalues[-1]), 0.)
    rank = int(np.count_nonzero(eigenvalues > threshold))
    nuisance = [i for i in range(f.shape[1]) if i not in interest]
    target = score[:,list(interest)]
    if nuisance:
        u, s, _ = np.linalg.svd(score[:,nuisance], full_matrices=False)
        keep = s > np.sqrt(rank_relative) * (s[0] if len(s) else 0.)
        basis = u[:,keep]
        residual = target - basis @ (basis.T @ target)
        nuisance_rank = int(np.count_nonzero(keep))
    else:
        residual = target; nuisance_rank = 0
    schur = residual.T @ residual
    conditional = target.T @ target
    ce = np.linalg.eigvalsh(conditional)
    generalized = None
    if len(ce) and ce[0] > rank_relative*ce[-1]:
        l = np.linalg.cholesky(conditional)
        left = np.linalg.solve(l, schur)
        normalized = np.linalg.solve(l, left.T).T
        generalized = np.linalg.eigvalsh((normalized+normalized.T)/2).tolist()
    correlation = None
    if rank == len(scales):
        inverse = np.linalg.solve(information, np.eye(len(scales)))
        std = np.sqrt(np.diag(inverse))
        correlation = (inverse/std[:,None]/std[None,:]).tolist()
    return dict(information=information.tolist(), eigenvalues=eigenvalues.tolist(), rank=rank,
                rank_relative_threshold=rank_relative, nuisance_rank=nuisance_rank,
                condition_number=float(eigenvalues[-1]/eigenvalues[0]) if rank==len(scales) else None,
                correlation=correlation, interest=list(interest), schur_information=schur.tolist(),
                conditional_interest_information=conditional.tolist(),
                generalized_schur_eigenvalues=generalized, singular_direction_clipping=False)


def derivative_stencil(point, step, lower=-np.inf, upper=np.inf):
    """Second-order three-point derivative, with one-sided physical boundaries."""
    if not np.isfinite(point) or not np.isfinite(step) or step <= 0 or not lower <= point <= upper:
        raise ValueError('Invalid derivative point or step')
    if point-step >= lower and point+step <= upper:
        return np.array([point-step,point,point+step]), np.array([-1.,0.,1.])/(2*step)
    if point+2*step <= upper:
        return np.array([point,point+step,point+2*step]), np.array([-3.,4.,-1.])/(2*step)
    if point-2*step >= lower:
        return np.array([point,point-step,point-2*step]), np.array([3.,-4.,1.])/(2*step)
    raise ValueError('No supported second-order stencil at requested step')
