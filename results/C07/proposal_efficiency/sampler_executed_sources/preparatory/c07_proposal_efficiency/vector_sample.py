"""Same per-target RNG recipe with component-grouped matrix products."""
import numpy as np


def sample_single_target(proposal, rng, count):
    if proposal.n != 1:
        raise ValueError('One explicitly identified target per IID stream required.')
    if isinstance(count, (bool, np.bool_)) or not isinstance(count, (int, np.integer)) or count <= 0:
        raise ValueError('IID count must be a positive explicit integer.')
    # Keep EXACT draw order and array sizes of the portable vectorized producer.
    u = rng.random(count)
    which = np.sum(u[:, None] > proposal.cumulative[0], axis=1)
    noise = rng.normal(size=(count, proposal.d))
    chi = rng.chisquare(proposal.nu, size=count)
    if np.any(chi <= 0) or not np.isfinite(chi).all():
        raise ArithmeticError('Unrepresentable Student scale; no replacement draw.')
    z = np.empty_like(noise)
    for component in range(proposal.k):
        selected = which == component
        z[selected] = (proposal.means[0, component]
                       + noise[selected] @ proposal.chol[0, component].T)
    selected = which == proposal.k
    z[selected] = (proposal.global_mean[0]
                   + (noise[selected] @ proposal.global_chol[0].T)
                   * np.sqrt((proposal.nu-2)/chi[selected])[:, None] * proposal.scale)
    if not np.isfinite(z).all():
        raise ArithmeticError('Nonfinite logit sample; no clipping or replacement.')
    return z, which
