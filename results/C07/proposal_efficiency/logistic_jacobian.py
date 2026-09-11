"""Exact logistic log-Jacobian, evaluated with one stable exponential.

For a=|z|, log sigmoid(z)+log sigmoid(-z)=-a-2 log(1+exp(-a)).
The rectangular physical-prior widths cancel its coordinate Jacobian. This
function returns the normalized unit-prior density in logit coordinates.
"""
import numpy as np


def unit_log_prior_jacobian(z):
    raw = np.asarray(z)
    if raw.dtype.kind not in 'fiu' or raw.ndim < 1 or raw.shape[-1] == 0:
        raise ValueError('Expected nonempty real logit coordinates on the last axis.')
    z = np.asarray(raw, float)
    if not np.isfinite(z).all():
        raise ValueError('Finite logit coordinates required.')
    absolute = np.abs(z)
    return (-absolute-2*np.log1p(np.exp(-absolute))).sum(axis=-1)
