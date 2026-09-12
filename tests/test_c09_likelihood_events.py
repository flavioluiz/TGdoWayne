"""Analytic topology, atom, orientation and resource contracts for event CDFs."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'src'))
import numpy as np
from scipy.integrate import quad
from inference.mass_batch import MassPosteriorBatch
from inference.likelihood_events import likelihood_event_cdf


class LikelihoodEventsTests(unittest.TestCase):
    def test_monotone_columns_both_orientations_and_offsets(self):
        a = np.linspace(0., np.pi/2, 101)
        slope = np.array([2., -3.]); offset = np.array([730., -730.])
        table = MassPosteriorBatch(np.sin(a), a[:, None]*slope+offset)
        cut = .63
        result = likelihood_event_cdf(table, cut*slope+offset)
        expected = []
        for k in slope:
            z = quad(lambda x: np.exp(k*x)*np.cos(x), 0., np.pi/2)[0]
            limits = (0., cut) if k > 0 else (cut, np.pi/2)
            expected.append(quad(lambda x: np.exp(k*x)*np.cos(x), *limits)[0]/z)
        np.testing.assert_allclose(result['strict'].mean(axis=1), expected, atol=2e-11)
        self.assertTrue(np.all(result['strict'][:, 1]-result['strict'][:, 0] < 2e-11))
        np.testing.assert_array_equal(result['crossings'], [1, 1])

    def test_multiple_regions_against_independent_quadrature(self):
        a = np.linspace(0., np.pi/2, 401)
        table = MassPosteriorBatch(np.sin(a), np.cos(8*a)[:, None])
        result = likelihood_event_cdf(table, [0.])
        # Four analytic roots, two disjoint event intervals.
        roots = np.array([1, 3, 5, 7])*np.pi/16
        z = quad(lambda x: np.exp(np.cos(8*x))*np.cos(x), 0., np.pi/2)[0]
        expected = sum(quad(lambda x: np.exp(np.cos(8*x))*np.cos(x), lo, hi)[0]
                       for lo, hi in zip(roots[::2], roots[1::2]))/z
        np.testing.assert_allclose(result['strict'].mean(), expected, atol=2e-7)

    def test_constant_statistic_has_atom_for_every_prior(self):
        for prior, lower in [('uniform_u', 0.), ('uniform_u_squared', 0.), ('log_uniform_u', .001)]:
            u = np.linspace(lower, 1., 101)
            table = MassPosteriorBatch(u, np.full((101, 1), 730.), prior=prior, lower=lower)
            result = likelihood_event_cdf(table, [730.])
            np.testing.assert_allclose(result['strict'], 0.)
            np.testing.assert_allclose(result['inclusive'], 1.)
            np.testing.assert_allclose(result['atom_mass'], 1.)
            np.testing.assert_allclose(likelihood_event_cdf(table, [729.])['inclusive'], 0.)
            np.testing.assert_allclose(likelihood_event_cdf(table, [731.])['strict'], 1.)

    def test_partial_plateau_and_invalid_inputs(self):
        a = np.array([0., .3, .6, 1., np.pi/2])
        table = MassPosteriorBatch(np.sin(a), np.array([0., 1., 1., 0., -1.])[:, None])
        result = likelihood_event_cdf(table, [1.])
        atom = (np.sin(.6)-np.sin(.3))/table.z[0]
        np.testing.assert_allclose(result['atom_mass'], atom, atol=1e-12)
        np.testing.assert_allclose(result['inclusive'], 1., atol=1e-12)
        with self.assertRaises(ValueError): likelihood_event_cdf(table, [np.nan])
        with self.assertRaises(ValueError): likelihood_event_cdf(table, [0., 1.])
        table.maximum_numeric_bytes = 1
        with self.assertRaises(MemoryError): likelihood_event_cdf(table, [0.])


if __name__ == '__main__':
    unittest.main()
