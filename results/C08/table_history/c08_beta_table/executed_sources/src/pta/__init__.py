"""Tensor PTA response with explicit empirical convergence checks.

The recommended ORF entry point is checked_orf. Low-level quadratures live
in pta.orf, are prefixed raw_, and require explicit numerical resolutions.
"""
from .response import beta_from_frequency, transfer
from .validation import ConvergenceError, Resolution, ResourceBudget, checked_orf

__all__ = [
    'beta_from_frequency', 'transfer', 'checked_orf',
    'Resolution', 'ResourceBudget', 'ConvergenceError',
]
