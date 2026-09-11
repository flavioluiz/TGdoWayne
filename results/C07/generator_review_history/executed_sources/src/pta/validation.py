"""Interface C05: validação obrigatória antes de retornar uma ORF.

Requer resoluções e orçamento
explícitos. As comparações são critérios empíricos de convergência, não limites
matemáticos rigorosos de erro. Não usa clipping de autovalores ou renormalização.
"""
from dataclasses import asdict, dataclass
from math import isfinite, pi
from . import orf as core
from ._domain import real_scalar as _scalar, positive_integer, response_arguments

MAX_VALIDATED_PHASE = 2 * pi * 1000.125 + 1  # Includes the unequal-distance coherence campaign.
MAX_QUADRATURE_ORDER = 20000


@dataclass(frozen=True)
class Resolution:
    lmax: int
    nmu_harmonic: int
    nmu_direct: int
    nphi_direct: int


@dataclass(frozen=True)
class ResourceBudget:
    max_work_units: int
    max_estimated_memory_bytes: int


class ConvergenceError(RuntimeError):
    def __init__(self, report):
        self.report = report
        super().__init__('ORF failed explicit refinement/cross-method convergence: ' + str(report['errors']))


def _preflight(beta, cosine, ya, yb, coarse, fine, budget, atol, rtol):
    beta, cosine, ya, yb = response_arguments(beta, cosine, ya, yb)
    if ya is not None and max(ya, yb) > MAX_VALIDATED_PHASE:
        raise ValueError('Phases outside the audited envelope [0, 2*pi*1000.125+1]. Extend benchmarks first.')
    atol, rtol = _scalar(atol, 'atol'), _scalar(rtol, 'rtol')
    if atol <= 0 or rtol < 0:
        raise ValueError('Require atol>0 and rtol>=0; absolute tolerance is necessary near zeros.')
    if not isinstance(coarse, Resolution) or not isinstance(fine, Resolution):
        raise TypeError('Explicit coarse and fine Resolution objects required.')
    def normalized(level):
        return Resolution(**{
            field: positive_integer(value, field, minimum=2 if field == 'lmax' else 1,
                                    ceiling=MAX_QUADRATURE_ORDER)
            for field, value in asdict(level).items()})
    coarse, fine = normalized(coarse), normalized(fine)
    if any(asdict(fine)[field] <= value for field, value in asdict(coarse).items()):
        raise ValueError('Every fine resolution must strictly exceed its coarse counterpart.')
    if not isinstance(budget, ResourceBudget):
        raise TypeError('Explicit ResourceBudget required.')
    budget = ResourceBudget(**{field: positive_integer(value, field)
                               for field, value in asdict(budget).items()})
    # Explicitly a proxy, not a promised CPU time or a rigorous RSS upper bound.
    distinct = 1 if ya == yb else 2
    harmonic_work = distinct * (coarse.lmax * coarse.nmu_harmonic
                    + coarse.lmax * fine.nmu_harmonic + fine.lmax * fine.nmu_harmonic)
    angular_work = 0 if ya is None else (coarse.nmu_direct * coarse.nphi_direct
                                       + fine.nmu_direct * fine.nphi_direct)
    orders = {coarse.nmu_harmonic, fine.nmu_harmonic}
    if ya is not None:
        orders.update((coarse.nmu_direct, fine.nmu_direct))
    # roots_legendre can require quadratic work; its cached result is only O(n).
    roots_work = sum(n * n for n in orders)
    work = harmonic_work + angular_work + roots_work
    max_n = max(orders)
    # 24 complex-size work arrays in the 128-column block, plus recurrence/cache allowance.
    memory = 24 * 16 * fine.nmu_direct * 128 + 30 * 16 * max_n + 64 * max_n
    estimate = {'work_units_proxy': work, 'estimated_memory_bytes': memory,
                'includes_harmonic_refinement': True, 'includes_direct_refinement': ya is not None,
                'hard_max_order': MAX_QUADRATURE_ORDER,
                'warning': 'Resource estimates are conservative proxies, not measured runtime or guaranteed RSS limits.'}
    if work > budget.max_work_units or memory > budget.max_estimated_memory_bytes:
        raise ValueError('Resource budget exceeded before any quadrature: ' + str(estimate))
    return beta, cosine, ya, yb, atol, rtol, estimate, coarse, fine


def checked_orf(beta, cosine, ya=None, yb=None, *, coarse, fine, budget, atol, rtol):
    """Return (complex Gamma, report) only if ALL empirical criteria pass.

    There is no automatic growth after a failed check: caller must review the report,
    request larger explicit resolutions, and pass resource preflight again. A matrix
    caller should use common harmonic cutoffs/resolutions for all pulsars and verify
    its Hermitian spectrum; pairwise acceptance does not certify matrix conditioning.
    """
    beta, cosine, ya, yb, atol, rtol, estimate, coarse, fine = _preflight(
        beta, cosine, ya, yb, coarse, fine, budget, atol, rtol)
    h0 = core.raw_harmonic_orf(beta, cosine, ya, yb,
                          lmax=coarse.lmax, nmu=coarse.nmu_harmonic)[0]
    hn = core.raw_harmonic_orf(beta, cosine, ya, yb,
                          lmax=coarse.lmax, nmu=fine.nmu_harmonic)[0]
    hf = core.raw_harmonic_orf(beta, cosine, ya, yb,
                          lmax=fine.lmax, nmu=fine.nmu_harmonic)[0]
    errors = {'harmonic_nodes': abs(hn - h0), 'harmonic_truncation': abs(hf - hn)}
    if ya is None:
        reference = core.earth_analytic(beta, cosine)
        errors['analytic_crosscheck'] = abs(hf - reference)
    else:
        d0 = core.raw_direct_orf(beta, cosine, ya, yb,
                            nmu=coarse.nmu_direct, nphi=coarse.nphi_direct)
        df = core.raw_direct_orf(beta, cosine, ya, yb,
                            nmu=fine.nmu_direct, nphi=fine.nphi_direct)
        errors['direct_refinement'] = abs(df - d0)
        errors['independent_crosscheck'] = abs(hf - df)
    limit = atol + rtol * abs(hf)
    if not isfinite(limit):
        raise ValueError('atol+rtol*abs(Gamma) must remain finite.')
    report = {'status': 'PASS', 'errors': {k: float(v) for k, v in errors.items()},
              'acceptance_limit': float(limit), 'atol': atol, 'rtol': rtol,
              'coarse': asdict(coarse), 'fine': asdict(fine), 'resources': estimate,
              'domain': {'beta': beta, 'cosine': cosine, 'ya': ya, 'yb': yb},
              'criterion': 'Empirical refinement and independent-method agreement, not a rigorous error bound.'}
    if not isfinite(hf.real) or not isfinite(hf.imag) or any(
            not isfinite(error) or error > limit for error in errors.values()):
        report['status'] = 'FAIL'
        raise ConvergenceError(report)
    return complex(hf), report
