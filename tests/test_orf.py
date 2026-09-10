"""Eight original C05 tests, four independent physical tests and API controls.

Scientific formula checks keep the audited configurations and thresholds.
No report files are written by test discovery.
"""
import unittest
import numpy as np
from functools import partial
from unittest.mock import patch

from pta.response import beta_from_frequency, transfer
from pta.orf import (raw_direct_orf as direct_orf,
                     raw_harmonic_orf as harmonic_orf,
                     raw_multipoles, raw_auto_weighted,
                     earth_analytic, hellings_downs, gr_auto_exact, threshold_full)
from pta import validation as checked

# Reproduce exactly the original adaptive-quadrature configuration.
auto_weighted = partial(raw_auto_weighted, small_epsabs=1e-13,
                        small_epsrel=1e-12, oscillatory_epsabs=1e-12, limit=300)


class TensorResponseTests(unittest.TestCase):
    def test_domain_and_transfer(self):
        self.assertEqual(beta_from_frequency(1,1),0)
        self.assertEqual(beta_from_frequency(1,0),1)
        self.assertEqual(beta_from_frequency(1e-300,0),1)
        with self.assertRaises(ValueError): beta_from_frequency(0.99,1)
        with self.assertRaises(ValueError): direct_orf(1.01,0,nmu=20,nphi=40)
        self.assertEqual(transfer(10,0),10j)
        self.assertAlmostEqual(abs(transfer(3,1e-14)-3j),0,places=12)

    def test_earth_analytic_and_direct(self):
        for b in [0,1e-25,1e-5,0.2,0.6,0.9,0.99,1]:
            for angle in [0,np.pi/8,np.pi/2,np.pi]:
                d=float(np.cos(angle))
                result=direct_orf(b,d,nmu=360,nphi=720).real
                exact=earth_analytic(b,d)
                self.assertLess(abs(result-exact),1e-5,(b,angle,result,exact))

    def test_earth_harmonic(self):
        for b in [0,0.2,0.9,1]:
            for d in [-1,0,1]:
                numerical,_=harmonic_orf(b,d,lmax=500,nmu=1200)
                self.assertLess(abs(numerical-earth_analytic(b,d)),7e-6,(b,d))

    def test_exact_threshold_and_low_phase(self):
        for d in [-1,-0.2,0,0.8,1]:
            for ya,yb in [(0,0),(0.1,0.2),(5,7),(200,345)]:
                exact=threshold_full(d,ya,yb)
                direct=direct_orf(0,d,ya,yb,nmu=30,nphi=60)
                harmonic,_=harmonic_orf(0,d,ya,yb,lmax=20,nmu=60)
                self.assertLess(abs(direct-exact),1e-12)
                self.assertLess(abs(harmonic-exact),1e-12)
        for b in [0,0.5,1]:
            y=1e-4
            result,_=auto_weighted(b,y)
            self.assertLess(abs(result/(y*y)-0.2),1e-8)

    def test_gr_autocorrelation_exact(self):
        for y in [0,0.001,0.1,1,10,100,300]:
            expected=gr_auto_exact(y)
            direct=direct_orf(1,1,y,y,nmu=max(100,int(2*y)),nphi=4).real
            harmonic,_=harmonic_orf(1,1,y,y,lmax=max(50,int(y+40)),nmu=max(200,int(2*y+100)))
            self.assertLess(abs(direct-expected),1e-10,(y,direct,expected))
            self.assertLess(abs(harmonic-expected),1e-10,(y,harmonic,expected))

    def test_finite_direct_harmonic(self):
        for b in [0.1,0.6,0.99,1]:
            for d in [0,0.95,1]:
                for ya,yb in [(2,4),(30,35),(100,150)]:
                    lmax=int(b*max(ya,yb)+60)
                    nmu=int(2*b*max(ya,yb)+150)
                    direct=direct_orf(b,d,ya,yb,nmu=nmu,nphi=2*nmu)
                    harmonic,_=harmonic_orf(b,d,ya,yb,lmax=lmax,nmu=nmu)
                    self.assertLess(abs(direct-harmonic),1e-9,(b,d,ya,yb,direct,harmonic))

    def test_autocorrelation_weighted(self):
        for b in [0.001,0.2,0.8,0.99,0.9999]:
            for y in [0.01,2,100,500]:
                ref,err=auto_weighted(b,y)
                direct=direct_orf(b,1,y,y,nmu=int(2*b*y+250),nphi=4)
                self.assertLess(abs(direct.real-ref),max(1e-10,10*err),(b,y,ref,direct,err))

    def test_reciprocity_and_positive_matrix(self):
        vectors=np.array([[0,0,1],[1,0,0],[0.6,0.8,0],[-0.7,0,np.sqrt(0.51)]])
        distances=[10,20,30,40]
        for beta in [0,0.3,0.99,1]:
            gamma=np.zeros((4,4),complex)
            for a in range(4):
                for b in range(4):
                    gamma[a,b]=direct_orf(beta,float(np.dot(vectors[a],vectors[b])),
                                  distances[a],distances[b],nmu=180,nphi=360)
            self.assertLess(np.max(np.abs(gamma-gamma.T.conj())),1e-12)
            self.assertGreaterEqual(np.linalg.eigvalsh(gamma).min(),-1e-12)



from scipy.special import roots_legendre as independent_roots_legendre

METRICS = {}


def explicit_polarization_gram(beta, directions, phases, nmu=120, nphi=240):
    """One fixed sky for all pulsars, explicit e+/ex; no TT projector or target transfer.

    Signed phases are allowed here solely to check the real-field negative-frequency
    extension. Production positive-frequency functions should retain their domain.
    """
    x, wx = independent_roots_legendre(nmu)
    phi = 2 * np.pi * (np.arange(nphi) + 0.25) / nphi
    xx, pp = np.meshgrid(x, phi, indexing='ij')
    xx, pp = xx.ravel(), pp.ravel()
    rr = np.sqrt(1 - xx * xx)
    omega = np.column_stack((rr * np.cos(pp), rr * np.sin(pp), xx))
    etheta = np.column_stack((xx * np.cos(pp), xx * np.sin(pp), -rr))
    ephi = np.column_stack((-np.sin(pp), np.cos(pp), np.zeros_like(xx)))
    pt, pf = etheta @ directions.T, ephi @ directions.T
    contractions = np.stack((pt * pt - pf * pf, 2 * pt * pf), axis=2)
    denom = 1 + beta * (omega @ directions.T)
    numer = -np.expm1(-1j * denom * np.asarray(phases)[None, :])
    factor = np.divide(numer, denom, out=np.broadcast_to(
        1j * np.asarray(phases)[None, :], denom.shape).copy(), where=denom != 0)
    response = contractions * factor[:, :, None] / 2
    weight = np.repeat(wx, nphi) * (2 * np.pi / nphi) * (3 / (8 * np.pi))
    return np.einsum('npa,nqa,n->pq', response, response.conj(), weight, optimize=True)


def directions():
    vectors = np.array([[0, 0, 1], [1e-7, 0, 1], [0, 0, -1],
                        [1, 2, 3], [-2, 1, 0.3], [0.4, -0.5, 0.7]], dtype=float)
    return vectors / np.linalg.norm(vectors, axis=1)[:, None]


class IndependentResponse(unittest.TestCase):
    def test_explicit_polarizations_gram_vs_harmonics_psd_and_complex_phase(self):
        pulsars = directions()
        phases = [19, 19.7, 31, 50, 77, 90]
        records = []
        for beta in [0, 0.2, np.nextafter(1., 0.), 1]:
            gram = explicit_polarization_gram(beta, pulsars, phases)
            harmonic = np.empty_like(gram)
            for a in range(len(phases)):
                for b in range(len(phases)):
                    cosine = float(np.clip(pulsars[a] @ pulsars[b], -1, 1))
                    harmonic[a, b] = harmonic_orf(
                        beta, cosine, phases[a], phases[b], lmax=170, nmu=300)[0]
            err = np.max(np.abs(gram - harmonic))
            mineig = np.linalg.eigvalsh(gram).min()
            hmineig = np.linalg.eigvalsh(harmonic).min()
            self.assertLess(err, 2e-11)
            self.assertLess(np.max(np.abs(gram - gram.conj().T)), 1e-13)
            self.assertGreaterEqual(mineig, -1e-13)
            self.assertGreaterEqual(hmineig, -1e-13)
            # Unequal radial positions in a nearly common direction retain a complex CSD.
            self.assertGreater(abs(gram[0, 1].imag), 1e-3)
            records.append({'beta': beta, 'max_abs_difference': float(err),
                            'gram_min_eigenvalue': float(mineig),
                            'harmonic_min_eigenvalue': float(hmineig),
                            'near_pair_imaginary': float(gram[0, 1].imag)})
        METRICS['explicit_gram'] = records

    def test_global_rotation_with_fixed_quadrature_sky(self):
        pulsars = directions()
        phases = [19, 19.7, 31, 50, 77, 90]
        rotation, _ = np.linalg.qr(np.array([[1., 2., -1.], [3., 0.2, 4.], [-2., 1., 1.]]))
        if np.linalg.det(rotation) < 0:
            rotation[:, 0] *= -1
        errors = []
        for beta in [0, np.nextafter(1., 0.), 1]:
            original = explicit_polarization_gram(beta, pulsars, phases)
            rotated = explicit_polarization_gram(beta, pulsars @ rotation.T, phases)
            error = np.max(np.abs(original - rotated))
            self.assertLess(error, 2e-11)
            errors.append({'beta': beta, 'max_abs_difference': float(error)})
        METRICS['global_rotation'] = errors

    def test_negative_frequency_reality_and_real_time_covariance(self):
        pulsars, phases = directions(), np.array([19, 19.7, 31, 50, 77, 90])
        positive = explicit_polarization_gram(0.8, pulsars, phases)
        negative = explicit_polarization_gram(0.8, pulsars, -phases)
        self.assertLess(np.max(np.abs(negative - positive.conj())), 1e-13)
        # One finite frequency band, arbitrary positive weight, independent sample times.
        # This tests a physical consequence of the complex cross spectrum, not only G_ab=G_ba*.
        time = np.array([0., 0.4, 1.2, 1.7, 2.9, 4.2])
        phasor = np.exp(0.73j * (time[:, None] - time[None, :]))
        time_cov = positive * phasor + negative * phasor.conj()
        self.assertLess(np.max(np.abs(time_cov.imag)), 1e-13)
        self.assertLess(np.max(np.abs(time_cov - time_cov.T)), 1e-13)
        self.assertGreaterEqual(np.linalg.eigvalsh(time_cov.real).min(), -1e-13)
        # Erasing Im(G) changes nonzero-lag correlations in this coherent example.
        discarded = 2 * positive.real * phasor.real
        changed = np.max(np.abs(time_cov.real - discarded))
        self.assertGreater(changed, 1e-3)
        METRICS['frequency_reality'] = {
            'max_conjugacy_error': float(np.max(np.abs(negative - positive.conj()))),
            'time_cov_min_eigenvalue': float(np.linalg.eigvalsh(time_cov.real).min()),
            'max_time_cov_change_if_imaginary_discarded': float(changed)}

    def test_exact_coincident_positions_and_continuity_without_diagonal_switch(self):
        base = np.array([[0., 0., 1.], [0., 0., 1.]])
        y = 27.1
        records = []
        for beta in [0, 0.99, 1]:
            same = explicit_polarization_gram(beta, base, [y, y])
            self.assertLess(abs(same[0, 1] - same[0, 0]), 1e-13)
            near = base.copy()
            near[1] = [np.sin(1e-6), 0., np.cos(1e-6)]
            almost = explicit_polarization_gram(beta, near, [y, y + 1e-6])
            difference = abs(almost[0, 1] - same[0, 0])
            self.assertLess(difference, 1e-6)
            self.assertLess(np.linalg.eigvalsh(same).min(), 1e-13)
            records.append({'beta': beta, 'near_vs_coincident_difference': float(difference)})
        METRICS['coincidence'] = records


class CheckedResponseTests(unittest.TestCase):
    def setUp(self):
        self.options = dict(
            coarse=checked.Resolution(80, 160, 100, 200),
            fine=checked.Resolution(120, 260, 180, 360),
            budget=checked.ResourceBudget(500_000_000, 512_000_000),
            atol=1e-8, rtol=1e-8)

    def test_converged_complex_threshold_coincident_and_earth_cases(self):
        for args in [(0.9, 0.4, 30, 31), (0, 1, 27.1, 27.1),
                     (1, 0.999999999999, 30, 30.7), (0.8, 0.4, None, None)]:
            with self.subTest(args=args):
                value, report = checked.checked_orf(*args, **self.options)
                self.assertEqual(report['status'], 'PASS')
                self.assertTrue(np.isfinite(value))
                self.assertTrue(all(error <= report['acceptance_limit']
                                    for error in report['errors'].values()))

    def test_invalid_physics_and_audited_phase_envelope(self):
        for args in [(0.9, 1.1, 30, 31), (0.9, float('nan'), 30, 31),
                     (0.9, 0, 30, None), (0.9, 0, None, 30),
                     (1, 0, 10000, 10000), (0.8, 0, -1, 1)]:
            with self.subTest(args=args), self.assertRaises(ValueError):
                checked.checked_orf(*args, **self.options)

    def test_missing_resolution_and_nonincreasing_refinement(self):
        with self.assertRaises(TypeError):
            checked.checked_orf(1, 0, 30, 31)
        options = dict(self.options, fine=self.options['coarse'])
        with self.assertRaises(ValueError):
            checked.checked_orf(0.9, 0, 30, 31, **options)

    def test_budget_rejected_before_any_quadrature(self):
        options = dict(self.options, budget=checked.ResourceBudget(1, 1))
        with patch.object(checked.core, 'raw_harmonic_orf',
                          side_effect=AssertionError('Quadrature must not start')):
            with self.assertRaises(ValueError):
                checked.checked_orf(0.9, 0, 30, 31, **options)

    def test_underresolved_large_phase_auto_fails(self):
        options = dict(self.options,
            coarse=checked.Resolution(200, 6400, 200, 400),
            fine=checked.Resolution(250, 6600, 300, 600), atol=1e-5, rtol=1e-5)
        with self.assertRaises(checked.ConvergenceError) as error:
            checked.checked_orf(1, 1, 6283.970705342984, 6283.970705342984, **options)
        self.assertEqual(error.exception.report['status'], 'FAIL')
        self.assertGreater(error.exception.report['errors']['independent_crosscheck'],
                           error.exception.report['acceptance_limit'])

    def test_tolerances_are_finite_positive_and_limit_cannot_overflow(self):
        for change in [dict(atol=0), dict(atol=np.inf), dict(rtol=-1), dict(rtol=np.nan)]:
            with self.subTest(change=change), self.assertRaises(ValueError):
                checked.checked_orf(0.9, 0, 30, 31, **dict(self.options, **change))
        # This isolates arithmetic overflow of a tolerance from any physical model.
        with patch.object(checked.core, 'raw_harmonic_orf', return_value=(2+0j, None)), \
             patch.object(checked.core, 'earth_analytic', return_value=2):
            with self.assertRaises(ValueError):
                checked.checked_orf(0.9, 0, **dict(self.options, atol=1e308, rtol=1e308))


class StrictInputTests(unittest.TestCase):
    def test_scalar_contract_rejects_strings_booleans_complex_and_arrays(self):
        for bad in ['0.9', True, np.bool_(True), 0.9+0j, np.array(0.9), [0.9], np.nan, np.inf]:
            with self.subTest(bad=repr(bad)):
                for call in [lambda: beta_from_frequency(bad, 0),
                             lambda: transfer(bad, 1),
                             lambda: harmonic_orf(bad, 0, lmax=4, nmu=10),
                             lambda: earth_analytic(0.9, bad)]:
                    with self.assertRaises(ValueError):
                        call()

    def test_raw_orf_domain_is_shared_and_requires_both_phases(self):
        for beta, cosine, ya, yb in [(0.9, 1.1, 1, 2), (0.9, np.nan, 1, 2),
                                     (0.9, 0, 1, None), (0.9, 0, None, 1),
                                     (0.9, 0, -1, 1), (0.9, 0, 1, np.inf),
                                     (-0.1, 0, None, None)]:
            with self.subTest(beta=beta, cosine=cosine, ya=ya, yb=yb):
                with self.assertRaises(ValueError):
                    harmonic_orf(beta, cosine, ya, yb, lmax=4, nmu=10)
                with self.assertRaises(ValueError):
                    direct_orf(beta, cosine, ya, yb, nmu=10, nphi=20)

    def test_raw_resolution_arguments_are_required_and_integral(self):
        for operation in [lambda: harmonic_orf(1, 0), lambda: direct_orf(1, 0),
                          lambda: raw_multipoles(1, None, lmax=4),
                          lambda: raw_auto_weighted(0.9, 1)]:
            with self.assertRaises(TypeError):
                operation()
        for bad in [True, np.bool_(True), 1.5, 2.0, '10', 0, -1, np.nan]:
            with self.subTest(bad=repr(bad)), self.assertRaises(ValueError):
                harmonic_orf(0.9, 0, lmax=4, nmu=bad)
        with self.assertRaises(ValueError):
            harmonic_orf(0.9, 0, lmax=1, nmu=10)
        self.assertTrue(np.isfinite(harmonic_orf(np.float64(0.9), np.float64(0),
                             lmax=np.int64(4), nmu=np.int64(10))[0]))

    def test_transfer_array_and_analytic_reference_domains(self):
        result = transfer(3, np.array([0., 1e-14, 1., 2.]))
        self.assertEqual(result[0], 3j)
        for bad in [np.array([1, np.nan]), np.array([1+0j]), ['1'], True]:
            with self.subTest(bad=repr(bad)), self.assertRaises(ValueError):
                transfer(3, bad)
        with self.assertRaises(ValueError):
            transfer(1e308, 2.)
        with self.assertRaises(ValueError):
            hellings_downs(np.array([0., 1.1]))
        with self.assertRaises(ValueError):
            gr_auto_exact(-1)
        with self.assertRaises(ValueError):
            threshold_full(0, None, None)

    def test_numpy_integer_wrapper_resolution_serializes_as_native_int(self):
        options = dict(
            coarse=checked.Resolution(*(np.int64(v) for v in (80, 160, 100, 200))),
            fine=checked.Resolution(*(np.int64(v) for v in (120, 260, 180, 360))),
            budget=checked.ResourceBudget(np.int64(500_000_000), np.int64(512_000_000)),
            atol=1e-8, rtol=1e-8)
        _, report = checked.checked_orf(0, 0, 27.1, 28.1, **options)
        import json
        json.dumps(report, allow_nan=False)
        self.assertIs(type(report['coarse']['lmax']), int)


if __name__ == '__main__':
    unittest.main(verbosity=2)
