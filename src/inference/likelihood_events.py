"""Continuous likelihood-event integrals of a positive PCHIP posterior table.

Root envelopes exclude quadrature and physical likelihood interpolation error.
Flat segments at the threshold are atoms, reported separately without an
implicit random draw or an unjustified continuous-statistic SBC assumption.
"""
import numpy as np


def likelihood_event_cdf(table, thresholds, *, alpha_width=1e-11, block_size=4096):
    """Return strict/inclusive CDF envelopes for actual (unshifted) logL cuts."""
    thresholds = np.asarray(thresholds, float)
    if thresholds.shape != (table.ncurves,) or not np.isfinite(thresholds).all():
        raise ValueError('One finite log-likelihood threshold per curve required')
    if not 0 < alpha_width < 1 or not isinstance(block_size, int) or block_size < 1:
        raise ValueError('Positive root width and integer block size required')
    estimate = table.estimated_base_bytes + 80 * table.segment_mass.size + 128 * block_size * table.order
    if estimate > table.maximum_numeric_bytes:
        raise MemoryError('Event integration estimate exceeds budget; split columns')
    h = thresholds - table.shift
    values = table.interpolator(table.alpha)
    left, right = values[:-1], values[1:]
    atom = (left == h) & (right == h)
    full = (np.maximum(left, right) <= h) & ~atom
    total = np.sum(np.where(full, table.segment_mass, 0.), axis=0)
    lower, upper = total.copy(), total.copy()
    atom_mass = np.sum(np.where(atom, table.segment_mass, 0.), axis=0)
    intervals, columns = np.nonzero((np.minimum(left, right) < h) & (h < np.maximum(left, right)))
    for first in range(0, len(intervals), block_size):
        ii, cc = intervals[first:first+block_size], columns[first:first+block_size]
        c = table.coeff[:, ii, cc]
        span = table.alpha[ii+1] - table.alpha[ii]
        lo, hi = np.zeros(len(ii)), span.copy()
        increasing = right[ii, cc] > left[ii, cc]
        while np.max(hi-lo) > alpha_width:
            mid = (lo+hi)/2
            y = ((c[0]*mid+c[1])*mid+c[2])*mid+c[3]
            before = np.where(increasing, y < h[cc], y > h[cc])
            lo, hi = np.where(before, mid, lo), np.where(before, hi, mid)

        def integrate(a, b):
            dx = (a[:, None]+b[:, None])/2 + (b-a)[:, None]*table.x/2
            y = ((c[0, :, None]*dx+c[1, :, None])*dx+c[2, :, None])*dx+c[3, :, None]
            return np.sum(np.exp(y)*table.prior_alpha_density(table.alpha[ii, None]+dx)
                          *table.w*(b-a)[:, None]/2, axis=1)

        # Integrate the selected region directly, avoiding cancellation in tails.
        low_mass = integrate(np.where(increasing, 0., hi), np.where(increasing, lo, span))
        high_mass = integrate(np.where(increasing, 0., lo), np.where(increasing, hi, span))
        np.add.at(lower, cc, low_mass)
        np.add.at(upper, cc, high_mass)
    strict = np.stack((lower, upper), axis=1)/table.z[:, None]
    inclusive = strict + (atom_mass/table.z)[:, None]
    if np.any(strict[:, 0] > strict[:, 1]+1e-12) or np.any(inclusive > 1+1e-10):
        raise ArithmeticError('Invalid event CDF envelope')
    return dict(strict=np.clip(strict, 0., 1.), inclusive=np.clip(inclusive, 0., 1.),
                atom_mass=atom_mass/table.z, crossings=np.bincount(columns, minlength=table.ncurves),
                scope='Positive interpolated table only; excludes quadrature and physical interpolation error')
