"""Small synthetic coefficient tests; no ORF integral, bank, or likelihood."""
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / 'src'))
from frozen_coefficient_orf import FrozenCoefficientORF as V1
from frozen_coefficient_orf_v2 import FrozenCoefficientORF as V2, loader_memory_estimate


def c0_toy():
    n = np.array([0., .5, 1.])
    m = np.array([1., 1.2, 2.])[:, None, None, None] * np.eye(2)[None, None]
    c = np.zeros((2, 4, 1, 2, 2), complex)
    c[:, 0] = m[:-1]
    c[0, 1] = .2 * np.eye(2)
    c[1, 1] = 1.6 * np.eye(2)
    c[1, 2] = -.8 * np.eye(2)
    return n, m.astype(complex), c


def smooth_toy(count=9):
    n = np.linspace(0., 1., count)
    x = -np.sqrt((1-n)*(1+n))
    h = np.diff(x)
    base = np.array([[2., .1j], [-.1j, 2.]], complex)[None]
    base = np.repeat(base, 2, axis=0)
    m = (1+x*x)[:, None, None, None]*base
    c = np.zeros((count-1, 4, 2, 2, 2), complex)
    c[:, 0] = m[:-1]
    c[:, 1] = (2*x[:-1]*h)[:, None, None, None]*base
    c[:, 2] = (h*h)[:, None, None, None]*base
    return n, m, c


class Tests(unittest.TestCase):
    def construct(self, payload, **kwargs):
        return V2(*payload, maximum_owned_numeric_bytes=10**6, **kwargs)

    def test_v1_parity_and_native_table_api(self):
        payload = c0_toy()
        old = V1(*payload, maximum_owned_numeric_bytes=10**6)
        new = self.construct(payload, validation_tile_size=1)
        u = np.unique(np.r_[np.linspace(0., 1., 31), payload[0]])
        np.testing.assert_array_equal(new(u), old(u))
        for name in ('nodes', 'matrices', 'coeff', 'alpha'):
            np.testing.assert_array_equal(getattr(new, name), getattr(old, name))
        self.assertEqual(new.coordinate_name, 'beta')
        for a, b in zip(new.location(u), old.location(u)):
            np.testing.assert_array_equal(a, b)
        self.assertEqual(new.representation_checks['continuity_order_checked'], 'C0')
        self.assertFalse(new.representation_checks['spline_fit_performed'])
        self.assertFalse(new.representation_checks['clipping_or_fallback_performed'])

    def test_budget_precedes_copies_coercion_and_value_checks(self):
        payload = smooth_toy()
        estimate = loader_memory_estimate(*payload, validation_tile_size=2)
        # Any eager coercion, allocation, or isfinite would fail this test
        # instead of the expected metadata-only MemoryError.
        with patch.object(np, 'asarray', side_effect=AssertionError('early coercion')), \
             patch.object(np, 'array', side_effect=AssertionError('early copy')), \
             patch.object(np, 'empty', side_effect=AssertionError('early allocation')), \
             patch.object(np, 'isfinite', side_effect=AssertionError('early numeric check')):
            with self.assertRaises(MemoryError):
                V2(*payload, validation_tile_size=2,
                   maximum_owned_numeric_bytes=estimate['owned_and_temporary_estimate_bytes']-1)

    def test_exact_budget_and_separate_caller_scope(self):
        payload = smooth_toy()
        estimate = loader_memory_estimate(*payload, validation_tile_size=2)
        cap = estimate['owned_and_temporary_estimate_bytes']
        new = V2(*payload, maximum_owned_numeric_bytes=cap, validation_tile_size=2)
        owned = sum(getattr(new, name).nbytes for name in ('nodes', 'matrices', 'coeff', 'alpha'))
        self.assertEqual(owned, estimate['persistent_owned_numeric_bytes'])
        self.assertEqual(estimate['simultaneous_loader_numeric_bytes_excluding_backend'],
                         cap+sum(a.nbytes for a in payload))
        self.assertFalse(estimate['backend_workspace_included'])
        self.assertFalse(estimate['RSS_guarantee'])

    def test_validation_operations_are_bounded_by_tile(self):
        payload = smooth_toy(19)
        tile = 2
        ceiling = tile*np.prod(payload[1].shape[1:])
        original_finite, original_conjugate = np.isfinite, np.conjugate
        original_eig, original_empty = np.linalg.eigvalsh, np.empty
        allocation_sizes, eigen_sizes = [], []

        def finite(a, *args, **kwargs):
            self.assertLessEqual(a.size, ceiling)
            return original_finite(a, *args, **kwargs)

        def conjugate(a, *args, **kwargs):
            self.assertLessEqual(a.size, ceiling)
            return original_conjugate(a, *args, **kwargs)

        def eig(a, *args, **kwargs):
            self.assertLessEqual(a.size, ceiling)
            result = original_eig(a, *args, **kwargs)
            eigen_sizes.append(result.nbytes)
            return result

        def empty(*args, **kwargs):
            result = original_empty(*args, **kwargs)
            allocation_sizes.append(result.nbytes)
            return result

        with patch.object(np, 'isfinite', side_effect=finite), \
             patch.object(np, 'conjugate', side_effect=conjugate), \
             patch.object(np.linalg, 'eigvalsh', side_effect=eig), \
             patch.object(np, 'empty', side_effect=empty):
            new = self.construct(payload, validation_tile_size=tile, require_C1=True)
        estimate = new.representation_checks
        self.assertEqual(sum(allocation_sizes), estimate['persistent_owned_numeric_bytes']
                         + estimate['reusable_validation_workspace_bytes'])
        self.assertLessEqual(max(eigen_sizes), estimate['maximum_eigenvalue_result_bytes'])

    def test_c1_guard_optional_for_valid_c0_toy(self):
        self.construct(c0_toy(), require_C1=False)
        with self.assertRaisesRegex(ValueError, 'C1 derivative'):
            self.construct(c0_toy(), validation_tile_size=1, require_C1=True)

    def test_c1_guard_on_analytic_polynomial_and_tile_seams(self):
        payload = smooth_toy()
        new = self.construct(payload, validation_tile_size=2, require_C1=True)
        self.assertLess(new.representation_checks['maximum_C1_derivative_error'], 1e-12)
        u = np.linspace(0., 1., 17)
        expected = (2-u*u)[:, None, None, None]*payload[1][-1]
        np.testing.assert_allclose(new(u), expected, atol=2e-15, rtol=2e-15)
        # Interior bump has zero endpoint values but changes join derivatives;
        # its index is at a tile seam. Endpoints and PSD still pass.
        n, m, c = payload
        c[2, 1] += .001*np.eye(2)
        c[2, 2] -= .001*np.eye(2)
        self.construct((n, m, c), validation_tile_size=2, require_C1=False)
        with self.assertRaisesRegex(ValueError, 'C1 derivative'):
            self.construct((n, m, c), validation_tile_size=2, require_C1=True)

    def test_owned_readonly_and_noncontiguous_sources(self):
        n, m, c = smooth_toy()
        n = np.repeat(n, 2)[::2]
        m, c = m[..., ::-1, ::-1], c[..., ::-1, ::-1]
        new = self.construct((n, m, c), validation_tile_size=2)
        value = new([.1, .9])
        n[1], m[:], c[:] = .99, 0., 0.
        np.testing.assert_array_equal(value, new([.1, .9]))
        for name in ('nodes', 'matrices', 'coeff', 'alpha'):
            array = getattr(new, name)
            self.assertFalse(array.flags.writeable)
            self.assertTrue(array.flags.c_contiguous)

    def test_nonfinite_inputs_in_final_tiles(self):
        for target, bad in ((0, np.nan), (1, np.nan), (2, np.inf)):
            with self.subTest(target=target):
                payload = list(smooth_toy())
                payload[target].flat[-1] = bad
                with self.assertRaisesRegex(ValueError, 'Nonfinite'):
                    self.construct(payload, validation_tile_size=2)

    def test_hermiticity_and_endpoint_checks_in_final_tiles(self):
        for kind in ('matrix_hermiticity', 'coefficient_hermiticity', 'endpoint'):
            with self.subTest(kind=kind):
                n, m, c = smooth_toy()
                if kind == 'matrix_hermiticity':
                    m[-1, 0, 0, 0] += 1e-5j
                elif kind == 'coefficient_hermiticity':
                    c[-1, 3, 0, 0, 0] += 1e-5j
                else:
                    c[-1, 3, 0, 0, 0] += 1e-5
                with self.assertRaisesRegex(ValueError, 'Hermitian|endpoints'):
                    self.construct((n, m, c), validation_tile_size=2)

    def test_negative_bernstein_with_positive_endpoints(self):
        n = np.array([0., 1.])
        m = np.ones((2, 1, 1, 1), complex)
        c = np.array([1., -8., 8., 0.], complex)[None, :, None, None, None]
        with self.assertRaisesRegex(ValueError, 'Bernstein'):
            self.construct((n, m, c), require_threshold_parity=False)

    def test_threshold_parity_guard_remains_optional(self):
        n = np.array([0., 1.])
        m = np.array([1., 2.], complex)[:, None, None, None]
        c = np.array([1., 1., 0., 0.], complex)[None, :, None, None, None]
        self.construct((n, m, c), require_threshold_parity=False)
        with self.assertRaisesRegex(ValueError, 'tensor threshold'):
            self.construct((n, m, c))

    def test_node_support_order_and_transform_guards(self):
        for case in ('seam', 'transform', 'support'):
            with self.subTest(case=case):
                n, m, c = smooth_toy()
                if case == 'seam':
                    n[2] = n[1]
                elif case == 'transform':
                    n[1] = 1e-12
                else:
                    n[0] = .01
                with self.assertRaisesRegex(ValueError, 'Increasing|support'):
                    self.construct((n, m, c), validation_tile_size=2)

    def test_metadata_rejects_unbudgeted_sequences_and_bad_options(self):
        n, m, c = smooth_toy()
        with self.assertRaises(TypeError):
            self.construct((n.tolist(), m, c))
        with self.assertRaises(ValueError):
            self.construct((n, m, c.real.astype(int)))
        for options in ({'validation_tile_size': 0}, {'validation_tile_size': True},
                        {'require_C1': 'yes'}, {'C1_absolute_tolerance': np.nan}):
            with self.subTest(options=options), self.assertRaises(ValueError):
                self.construct((n, m, c), **options)

    def test_empty_queries_and_query_guards(self):
        new = self.construct(c0_toy())
        self.assertEqual(new([]).shape, (0, 1, 2, 2))
        for bad in ([np.nan], [-.1], [1.1], [[.2]]):
            with self.assertRaises(ValueError):
                new(bad)


if __name__ == '__main__':
    unittest.main(verbosity=2)
