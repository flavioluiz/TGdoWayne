"""Common strict input contracts; validation does not certify convergence."""
from numbers import Integral, Real

import numpy as np


def real_scalar(value, name):
    if isinstance(value, (bool, np.bool_)) or not isinstance(value, Real):
        raise ValueError(f'{name} must be a finite real scalar.')
    try:
        result = float(value)
    except (ValueError, OverflowError) as exc:
        raise ValueError(f'{name} must be a finite real scalar.') from exc
    if not np.isfinite(result):
        raise ValueError(f'{name} must be finite.')
    return result


def positive_integer(value, name, *, minimum=1, ceiling=None):
    if isinstance(value, (bool, np.bool_)) or not isinstance(value, Integral):
        raise ValueError(f'{name} must be an integer >= {minimum}.')
    result = int(value)
    if result < minimum or (ceiling is not None and result > ceiling):
        raise ValueError(f'{name} is outside the allowed integer range.')
    return result


def real_array(value, name, *, lower=None, upper=None):
    array = np.asarray(value)
    if array.dtype.kind not in 'iuf' or not np.all(np.isfinite(array)):
        raise ValueError(f'{name} must contain finite real numbers.')
    if lower is not None and np.any(array < lower):
        raise ValueError(f'{name} must be >= {lower}.')
    if upper is not None and np.any(array > upper):
        raise ValueError(f'{name} must be <= {upper}.')
    return array


def phase(value, name='y'):
    result = real_scalar(value, name)
    if result < 0:
        raise ValueError(f'{name}=2*pi*f*L/c must be nonnegative.')
    return result


def beta_value(value):
    result = real_scalar(value, 'beta')
    if not 0 <= result <= 1:
        raise ValueError('Travelling tensor response requires 0<=beta<=1.')
    return result


def cosine_value(value):
    result = real_scalar(value, 'cosine')
    if not -1 <= result <= 1:
        raise ValueError('cosine must be in [-1,1].')
    return result


def response_arguments(beta, cosine, ya, yb):
    beta, cosine = beta_value(beta), cosine_value(cosine)
    if (ya is None) != (yb is None):
        raise ValueError('Supply both pulsar phases, or neither for Earth-only.')
    if ya is not None:
        ya, yb = phase(ya, 'ya'), phase(yb, 'yb')
    return beta, cosine, ya, yb
