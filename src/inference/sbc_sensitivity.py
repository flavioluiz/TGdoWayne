"""Sensitivity of SBC conclusions to interval-valued numerical PITs.

These are deterministic bounds conditional on the input intervals. The intervals
made from importance MCSEs are asymptotic sensitivity intervals, not confidence
certificates. Every simulation remains in the denominator, including unresolved
integrals represented by [0, 1]. No jitter or clipping of PIT estimates is used.
"""
from functools import lru_cache
from numbers import Integral, Real
import numpy as np
from scipy import stats
from .diagnostics import clopper_pearson, holm


def _intervals(lower, upper):
    a, b = np.asarray(lower), np.asarray(upper)
    if a.dtype.kind not in 'fiu' or b.dtype.kind not in 'fiu' or a.ndim != 1 or a.shape != b.shape or not a.size:
        raise ValueError('Two nonempty real interval endpoint vectors required.')
    a, b = a.astype(float), b.astype(float)
    if not np.isfinite(a).all() or not np.isfinite(b).all() or np.any(a < 0) or np.any(b > 1) or np.any(a > b):
        raise ValueError('PIT intervals must lie in [0,1], without reversed endpoints.')
    return a, b


def pit_intervals(pit, mcse, resolved, *, deterministic_component=.002,
                  family_size=15000, alpha_mc=.01):
    p, s, r = np.asarray(pit), np.asarray(mcse), np.asarray(resolved)
    if p.shape != s.shape or p.shape != r.shape or p.size == 0 or p.dtype.kind not in 'fiu' or s.dtype.kind not in 'fiu' or r.dtype.kind != 'b':
        raise ValueError('PIT, MCSE and boolean resolution arrays must have the same shape.')
    if not np.isfinite(p).all() or np.any((p < 0) | (p > 1)):
        raise ValueError('PIT estimates must be finite in [0,1]; never clip them.')
    if np.any(~np.isfinite(s[r])) or np.any(s[r] <= 0):
        raise ValueError('Resolved nonstructural PITs require finite positive MCSE.')
    if isinstance(family_size, (bool,np.bool_)) or not isinstance(family_size, Integral) or family_size < p.size:
        raise ValueError('Invalid simultaneous family size.')
    if any(isinstance(v,(bool,np.bool_)) or not isinstance(v,Real) or not np.isfinite(v)
           for v in (alpha_mc,deterministic_component)) or not 0 < alpha_mc < 1 or not 0 <= deterministic_component <= 1:
        raise ValueError('Invalid simultaneous sensitivity specification.')
    family_size=int(family_size); alpha_mc=float(alpha_mc); deterministic_component=float(deterministic_component)
    z = float(stats.norm.isf(alpha_mc/(2*family_size)))
    lo, hi = np.zeros(p.shape), np.ones(p.shape)
    delta = deterministic_component + z*s[r]
    lo[r] = np.maximum(0., p[r]-delta)
    hi[r] = np.minimum(1., p[r]+delta)
    return lo, hi, dict(z=z, family_size=family_size, alpha_mc=alpha_mc,
        deterministic_component=deterministic_component,
        unresolved_count=int((~r).sum()),
        status='ASYMPTOTIC_NUMERICAL_SENSITIVITY_NOT_EXACT_CONFIDENCE')


def ecdf_envelope(lower, upper, grid):
    a, b = _intervals(lower, upper)
    t = np.asarray(grid)
    if t.ndim != 1 or t.dtype.kind not in 'fiu' or not np.isfinite(t).all():
        raise ValueError('A finite real grid is required.')
    return (np.searchsorted(np.sort(b), t, side='right')/len(a),
            np.searchsorted(np.sort(a), t, side='right')/len(a))


def ks_bounds(lower, upper):
    a, b = _intervals(lower, upper)
    a, b = np.sort(a), np.sort(b)
    n = len(a); right = np.arange(1, n+1)/n; left = np.arange(n)/n
    dmin = float(max(0., np.max(right-b), np.max(a-left)))
    dmax = float(max(np.max(right-a), np.max(b-left)))
    return dict(n=n, statistic_lower_bound=dmin, statistic_upper_bound=dmax,
        pvalue_lower=float(stats.kstwo.sf(dmax, n)),
        pvalue_upper=float(stats.kstwo.sf(dmin, n)),
        bounds_conditional_on_valid_input_intervals=True,
        lower_statistic_bound_not_asserted_attainable=True)


@lru_cache(maxsize=32)
def _binomial_pvalues(n, probability):
    return np.array([stats.binomtest(k, n, probability).pvalue for k in range(n+1)])


def coverage_bounds(lower, upper, *, upper_probability, lower_probability=None,
                    alpha=.05, family_size=1):
    a, b = _intervals(lower, upper)
    if isinstance(family_size, (bool,np.bool_)) or not isinstance(family_size, Integral) or family_size < 1:
        raise ValueError('A positive integer family size is required.')
    high = float(upper_probability)
    if not 0 < high < 1 or (lower_probability is not None and not 0 < lower_probability < high):
        raise ValueError('Interior ordered coverage cutoffs required.')
    if lower_probability is None:
        certain, possible = b <= high, a <= high
        nominal = high
    else:
        low = float(lower_probability)
        certain = (a >= low) & (b <= high)
        possible = (b >= low) & (a <= high)
        nominal = high-low
    n, kmin, kmax = len(a), int(certain.sum()), int(possible.sum())
    values = _binomial_pvalues(n, nominal)[kmin:kmax+1]
    interval = [clopper_pearson(kmin, n, alpha)[0], clopper_pearson(kmax, n, alpha)[1]]
    simultaneous = [clopper_pearson(kmin, n, alpha/family_size)[0],
                    clopper_pearson(kmax, n, alpha/family_size)[1]]
    return dict(n=n, nominal=nominal, certainly_covered=kmin, possibly_covered=kmax,
        ambiguous_count=kmax-kmin, fraction_bounds=[kmin/n,kmax/n],
        pvalue_lower=float(values.min()), pvalue_upper=float(values.max()),
        binomial_interval_union=interval,
        simultaneous_binomial_interval_union=simultaneous), certain, possible


def holm_sensitivity(lower_pvalues, upper_pvalues, *, alpha=.05):
    low, high = np.asarray(lower_pvalues), np.asarray(upper_pvalues)
    if low.shape != high.shape or np.any(low > high):
        raise ValueError('Ordered p-value bounds required.')
    low_adj, _ = holm(low, alpha); high_adj, _ = holm(high, alpha)
    return dict(holm_lower=low_adj, holm_upper=high_adj,
                rejection_for_all_permitted_pvalues=high_adj <= alpha,
                rejection_not_excluded_by_rectangular_bounds=low_adj <= alpha,
                monotonicity_bounds_may_be_conservative=True)


def paired_binary_bounds(certain_x, possible_x, certain_y, possible_y):
    arrays = [np.asarray(v) for v in (certain_x, possible_x, certain_y, possible_y)]
    if any(a.dtype.kind != 'b' or a.ndim != 1 or a.shape != arrays[0].shape for a in arrays) or not arrays[0].size:
        raise ValueError('Equal nonempty boolean vectors required.')
    cx, px, cy, py = arrays
    if np.any(cx & ~px) or np.any(cy & ~py):
        raise ValueError('Certain events must be possible.')
    n = len(cx)
    n10_bounds = [int((cx & ~py).sum()), int((px & ~cy).sum())]
    n01_bounds = [int((cy & ~px).sum()), int((py & ~cx).sum())]
    aa, bb = np.meshgrid(np.arange(n10_bounds[0],n10_bounds[1]+1),
                         np.arange(n01_bounds[0],n01_bounds[1]+1), indexing='ij')
    allowed = aa+bb <= n
    discordant = (aa+bb)[allowed]
    p = np.minimum(1., 2*stats.binom.cdf(np.minimum(aa,bb)[allowed], discordant, .5))
    p[discordant == 0] = 1.
    return dict(n=n, mean_difference_bounds=[float(cx.mean()-py.mean()),float(px.mean()-cy.mean())],
        discordant_x_only_bounds=n10_bounds, discordant_y_only_bounds=n01_bounds,
        pvalue_lower=float(p.min()), pvalue_upper=float(p.max()),
        rectangular_superset_of_attainable_discordance_counts=True)
