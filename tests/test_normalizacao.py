"""Auditoria independente de Einstein linear, sinais e unidades históricas.

Não altera as equações históricas ou identifica suas massas por convenção.
Executar com SymPy 1.14.0; apenas identidades simbólicas, sem dados observacionais.
"""
from itertools import product
import unittest

import sympy as s
from polarizacoes.foundations import ETA, Q, DELTA, symmetric, riemann, visser_amplitude, fp_amplitude


def zero(value):
    if isinstance(value, s.MatrixBase):
        return all(s.cancel(component) == 0 for component in value)
    return s.cancel(value) == 0


def connection(h, eta, q):
    """Gamma^a_bc com a derivada de Fourier partial_a -> i q_a."""
    return {(a, b, c): s.I * sum(
        eta[a, r] * (q[b] * h[r, c] + q[c] * h[r, b] - q[r] * h[b, c])
        for r in range(4)) / 2 for a, b, c in product(range(4), repeat=3)}


def ricci_and_einstein(h, eta, q, historical=False):
    """Contração da conexão; historical reproduz Eq.10 de Paula (2004).

    Aqui: R_mn = partial_a Gamma^a_nm - partial_n Gamma^a_am.
    Artigo: a ordem das duas parcelas é invertida.
    """
    gamma = connection(h, eta, q)
    sign = -1 if historical else 1
    ricci = s.Matrix(4, 4, lambda m, n: s.expand(sign * s.I * sum(
        q[a] * gamma[a, n, m] - q[n] * gamma[a, a, m] for a in range(4))))
    scalar = s.trace(eta * ricci)
    return ricci, s.simplify(ricci - eta * scalar / 2)


def trace_reverse(h, eta):
    return h - eta * s.trace(eta * h) / 2


class EinsteinNormalization(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.h = symmetric(s.symbols('h00 h01 h02 h03 h11 h12 h13 h22 h23 h33'))
        cls.q = s.Matrix(s.symbols('q0 q1 q2 q3', real=True))

    def test_connection_ricci_matches_prototype_contraction_both_signatures(self):
        # All ten independent h components and four q components are free.
        curvature = riemann(self.h, self.q)
        for eta in (ETA, -ETA):
            ricci, _ = ricci_and_einstein(self.h, eta, self.q)
            contracted = s.Matrix(4, 4, lambda b, d: sum(
                eta[a, c] * curvature[a, b, c, d] for a, c in product(range(4), repeat=2)))
            self.assertTrue(zero(ricci - contracted))

    def test_general_einstein_lorenz_identity_and_bianchi(self):
        for eta in (ETA, -ETA):
            _, einstein = ricci_and_einstein(self.h, eta, self.q)
            bar = trace_reverse(self.h, eta)
            divergence = bar * eta * self.q
            box = -(self.q.T * eta * self.q)[0]
            # Exact off-shell identity. Lorenz sets divergence to zero, not h trace.
            remainder = -(self.q * divergence.T + divergence * self.q.T) / 2
            remainder += eta * (self.q.T * eta * divergence)[0] / 2
            self.assertTrue(zero(einstein + box * bar / 2 - remainder))
            self.assertTrue(zero(einstein * eta * self.q))

    def test_visser_einstein_sign_both_signatures_and_historical_ricci(self):
        h = visser_amplitude()
        for eta in (ETA, -ETA):
            bar = trace_reverse(h, eta)
            self.assertTrue(zero(bar * eta * Q))
            _, here = ricci_and_einstein(h, eta, Q)
            _, historical = ricci_and_einstein(h, eta, Q, historical=True)
            box = -(Q.T * eta * Q)[0]
            self.assertTrue(zero(here + box * bar / 2))
            self.assertTrue(zero(historical - box * bar / 2))
            self.assertTrue(zero(here + historical))

    def test_fp_mass_equation_divergence_trace_and_reduced_dispersion(self):
        mu = s.symbols('mu', positive=True)
        h, q, eta = self.h, self.q, ETA
        _, einstein = ricci_and_einstein(h, eta, q)
        tr = s.trace(eta * h)
        constraint = h * eta * q - q * tr
        equation = einstein - mu**2 * (h - eta * tr) / 2
        self.assertTrue(zero(equation * eta * q + mu**2 * constraint / 2))
        self.assertTrue(zero(s.trace(eta * equation)
                             - (q.T * eta * constraint)[0] - 3 * mu**2 * tr / 2))
        # mu!=0 first imposes constraint=0, then tr=0. Check the reduced system.
        hf = fp_amplitude()
        _, gf = ricci_and_einstein(hf, ETA, Q)
        reduced = gf - mu**2 * hf / 2
        self.assertTrue(zero(reduced - (DELTA - mu**2) * hf / 2))

    def test_literal_tg_and_article_coefficients(self):
        mass, c, hbar, grav, box = s.symbols('mass c hbar G box', positive=True)
        kappa = 8 * s.pi * grav / c**4
        tau_tg = -mass**2 * c**2 / (8 * s.pi * grav * hbar**2)
        tau_article = -mass**2 * c**6 / (8 * s.pi * grav * hbar**2)
        # Historical Einstein = box*hbar_metric/2. Signs of the source differ.
        tg_normalized_equation = box - 2 * kappa * tau_tg
        article_normalized_equation = box + 2 * kappa * tau_article
        mu2 = mass**2 * c**2 / hbar**2
        self.assertTrue(zero(tg_normalized_equation - box - 2 * mass**2 / (hbar**2 * c**2)))
        self.assertTrue(zero(article_normalized_equation - box + 2 * mu2))
        printed_article_equation = box - mu2
        self.assertTrue(zero(article_normalized_equation - printed_article_equation + mu2))
        self.assertNotEqual(s.simplify(article_normalized_equation - printed_article_equation), 0)

    def test_si_dimensions_expose_tg_c_power(self):
        # M,L,T are independent dimension generators, not numerical unit values.
        dim_m, dim_l, dim_t = s.symbols('M L T', positive=True)
        mass = dim_m
        c = dim_l / dim_t
        hbar = dim_m * dim_l**2 / dim_t
        grav = dim_l**3 / (dim_m * dim_t**2)
        physical_mu2 = mass**2 * c**2 / hbar**2
        tg_mu2 = mass**2 / (hbar**2 * c**2)
        self.assertTrue(zero(physical_mu2 - dim_l**-2))
        self.assertTrue(zero(tg_mu2 - dim_t**4 / dim_l**6))
        self.assertTrue(zero(tg_mu2 * c**4 - physical_mu2))
        tg_stress = mass**2 * c**2 / (grav * hbar**2)
        article_stress = mass**2 * c**6 / (grav * hbar**2)
        energy_density = dim_m / (dim_l * dim_t**2)
        self.assertTrue(zero(article_stress - energy_density))
        self.assertTrue(zero(tg_stress * c**4 - energy_density))

    def test_operational_dispersion_mass_and_article_factor_two(self):
        mass_article, mass_disp, c, hbar, w_si, k = s.symbols(
            'm_article m_disp c hbar omega_SI k', positive=True)
        delta = w_si**2 / c**2 - k**2
        literal_article = delta - 2 * mass_article**2 * c**2 / hbar**2
        operational = delta - mass_disp**2 * c**2 / hbar**2
        self.assertTrue(zero(literal_article - operational.subs(mass_disp, s.sqrt(2) * mass_article)))
        frequency_equation = w_si**2 - c**2 * k**2 - (mass_disp * c**2 / hbar)**2
        self.assertTrue(zero(c**2 * operational - frequency_equation))


if __name__ == '__main__':
    unittest.main()
