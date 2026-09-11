"""Continuous prior draws with independently computed, checked ORFs at each truth.

This module never interpolates an ORF and never generates a missing cache node.
The caller must construct the exact-node cache separately, with its own budget.
"""
from pathlib import Path
import hashlib
import json
import numpy as np
from pta.simulation import paired_physical_and_gaussian
from .model import experiment, covariance_batch
from .orf_backend import ExactNodeORF
from .orf_table_builder import read_validated_entry


def prior_truths(config):
    if config.get('positive_channels') != [1, 2, 3, 4]:
        raise ValueError('The C07 generator requires the four consecutive channels [1,2,3,4].')
    if config.get('fixed_red_slope') != 4.0:
        raise ValueError('The C07 covariance fixes the red-noise slope at four.')
    bounds = np.asarray(config['prior']['bounds'], float)
    n = config['n_realizations']
    if isinstance(n, bool) or not isinstance(n, int) or n < 1:
        raise ValueError('A positive integer realization count is required.')
    if bounds.shape != (5, 2) or not np.isfinite(bounds).all() or np.any(bounds[:, 1] <= bounds[:, 0]):
        raise ValueError('Five finite nondegenerate prior intervals are required.')
    if config['prior']['kind'] != 'independent uniform in these coordinates':
        raise ValueError('This generator implements the declared independent uniform prior only.')
    if not np.array_equal(bounds[0], [0., 1.]):
        raise ValueError('This experiment preserves every channel with u in [0,1].')
    rng = np.random.default_rng(config['truth_seed'])
    return bounds[:, 0] + rng.uniform(size=(n, 5)) * (bounds[:, 1] - bounds[:, 0])


class StoredExactORF:
    """Read-only numerical payload validation; no silent cache construction."""
    def __init__(self, exp, config, cache):
        self.cache = Path(cache)
        if not self.cache.is_dir():
            raise FileNotFoundError('Construct the exact-node ORF cache before data generation.')
        self.provider = ExactNodeORF(exp, config, self.cache)
        self.config = config
        self.shape = (len(exp['f']), len(exp['points']), len(exp['points']))
        self.records = []

    def evaluate(self, u):
        if not np.ndim(u) == 0 or not np.isfinite(u) or not 0 <= u <= 1:
            raise ValueError('A finite continuous truth u in [0,1] is required.')
        token = hashlib.sha256(self.provider.signature.encode() + float(u).hex().encode()).hexdigest()
        path = self.cache / (token + '.npz')
        if not path.is_file():
            raise FileNotFoundError(f'Exact ORF missing at continuous truth u={u}; interpolation is forbidden here.')
        gamma, record = read_validated_entry(
            path, signature=self.provider.signature, u=u,
            K=self.shape[0], P=self.shape[1],
            tolerance=self.config['maximum_matrix_abs_difference'])
        maximum = record['maximum_coarse_fine_difference']
        self.records.append({'u': float(u), 'file': path.name,
                             'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
                             'maximum_coarse_fine_difference': float(maximum),
                             'interpolation_used': False})
        return gamma


def generate_prior_fixture(config, cache):
    """Same C06 paired generator, one continuous prior truth per realization."""
    exp = experiment(config)
    truths = prior_truths(config)
    provider = StoredExactORF(exp, config['orf'], cache)
    # Verify every required node before drawing any observation.
    matrices = [provider.evaluate(float(theta[0])) for theta in truths]
    rng = np.random.default_rng(config['data_seed'])
    q, physical, gaussian = [], [], []
    for theta, gamma in zip(truths, matrices):
        covariance, _ = covariance_batch(theta[None, 1:], gamma, exp)
        coef, observed, control = paired_physical_and_gaussian(covariance[0], exp['H'], 1, rng)
        q.append(coef[0]); physical.append(observed[0]); gaussian.append(control[0])
    arrays = dict(truth=truths, q=np.asarray(q), x_physical=np.asarray(physical),
                  x_gaussian=np.asarray(gaussian), directions=exp['points'],
                  distances_ly=exp['distance_ly'], sigma=exp['sigma'], red_pattern=exp['red'],
                  frequency_hz=exp['f'], scale=exp['scale'])
    return arrays, provider.records
