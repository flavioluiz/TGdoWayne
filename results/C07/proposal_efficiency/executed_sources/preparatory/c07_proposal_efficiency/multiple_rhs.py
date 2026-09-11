"""Equivalent Gaussian/Student density using several RHS per Cholesky factor.

The guarded v2 input contract and mixture distribution are unchanged. The
flattened API is target-major, just like the audited reference. No RNG here.
"""
import numpy as np
from mixture_proposal_v2 import GaussianDefensiveProposal
from linalg_batch import forward_substitution


class MultipleRHSGaussianDefensiveProposal(GaussianDefensiveProposal):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.inverse_chol = forward_substitution(
            self.chol, np.broadcast_to(np.eye(self.d), self.chol.shape))
        self.inverse_global_chol = forward_substitution(
            self.global_chol, np.broadcast_to(np.eye(self.d), self.global_chol.shape))

    def logpdf(self, z, *, method='matmul'):
        raw = np.asarray(z)
        if raw.dtype.kind not in 'fiu' or raw.ndim != 2 or raw.shape[1] != self.d:
            raise ValueError('Real logit points with flattened target-major axes required.')
        z = np.asarray(raw, float)
        if len(z) == 0 or len(z) % self.n or not np.isfinite(z).all():
            raise ValueError('Need nonempty finite complete target batches.')
        if method not in ('matmul', 'forward', 'solve'):
            raise ValueError('Unknown equivalent whitening implementation.')
        z = z.reshape(self.n, -1, self.d)
        result = np.full(z.shape[:2], -np.inf)

        def mahalanobis(delta, chol, inverse):
            rhs = np.swapaxes(delta, -1, -2)
            if method == 'matmul':
                whitened = inverse @ rhs
            elif method == 'forward':
                whitened = forward_substitution(chol, rhs)
            else:
                whitened = np.linalg.solve(chol, rhs)
            return np.sum(whitened * whitened, axis=-2)

        for component in range(self.k):
            delta = z - self.means[:, component, None, :]
            mahal = mahalanobis(delta, self.chol[:, component], self.inverse_chol[:, component])
            term = (self.gaussian_constant[:, component, None] - .5 * mahal
                    + np.log((1-self.alpha)*self.weights[:, component, None]))
            np.logaddexp(result, term, out=result)
        delta = z - self.global_mean[:, None, :]
        mahal = mahalanobis(delta, self.global_chol, self.inverse_global_chol)
        term = (self.student_constant[:, None]
                - .5 * (self.nu+self.d) * np.log1p(mahal/((self.nu-2)*self.scale**2))
                + np.log(self.alpha))
        np.logaddexp(result, term, out=result)
        return result.ravel()
