"""Prospective C07 diagnostics. This module does not run any PTA inference."""
from __future__ import annotations

from numbers import Integral, Real
import numpy as np
from scipy import stats


def _integer(x, name, minimum=1):
    if isinstance(x, (bool, np.bool_)) or not isinstance(x, Integral) or x < minimum:
        raise ValueError(f"{name} must be an integer >= {minimum}")
    return int(x)


def _probability(x, name="alpha", endpoints=False):
    if isinstance(x, (bool, np.bool_)) or not isinstance(x, Real) or not np.isfinite(x):
        raise ValueError(f"{name} must be a finite real scalar")
    if not ((0 <= x <= 1) if endpoints else (0 < x < 1)):
        raise ValueError(f"{name} outside probability domain")
    return float(x)


def _array(x, name, ndim=None):
    x = np.asarray(x)
    if x.dtype.kind not in "fiu" or (ndim is not None and x.ndim != ndim):
        raise ValueError(f"{name} must be a real numerical array of dimension {ndim}")
    x = x.astype(float, copy=False)
    if x.size == 0 or not np.all(np.isfinite(x)):
        raise ValueError(f"{name} must be nonempty and finite")
    return x


def holm(pvalues, alpha=0.05):
    """Holm adjusted p-values; controls FWER under arbitrary test dependence."""
    alpha = _probability(alpha)
    p = _array(pvalues, "pvalues", 1)
    if np.any((p < 0) | (p > 1)):
        raise ValueError("pvalues must lie in [0,1]")
    order = np.argsort(p, kind="stable")
    adjusted_sorted = np.minimum(1, np.maximum.accumulate((len(p) - np.arange(len(p))) * p[order]))
    adjusted = np.empty_like(p)
    adjusted[order] = adjusted_sorted
    return adjusted, adjusted <= alpha


def clopper_pearson(k, n, alpha=0.05):
    n = _integer(n, "n")
    k = _integer(k, "k", 0)
    alpha = _probability(alpha)
    if k > n:
        raise ValueError("k cannot exceed n")
    lo = 0.0 if k == 0 else float(stats.beta.ppf(alpha / 2, k, n - k + 1))
    hi = 1.0 if k == n else float(stats.beta.ppf(1 - alpha / 2, k + 1, n - k))
    return [lo, hi]


def binomial_summary(hit, p_null=None, alpha=0.05, family_size=1):
    """Uncertainty for IID replicate coverage indicators, not posterior probability."""
    x = np.asarray(hit)
    if x.ndim != 1 or x.size == 0 or x.dtype.kind != "b":
        raise ValueError("hit must be a nonempty boolean vector")
    alpha = _probability(alpha)
    family_size = _integer(family_size, "family_size")
    n, k = x.size, int(x.sum())
    phat = k / n
    out = dict(n=int(n), covered=k, fraction=phat,
               plugin_mc_se=float(np.sqrt(phat * (1 - phat) / n)),
               exact_interval=clopper_pearson(k, n, alpha),
               simultaneous_bonferroni_interval=clopper_pearson(k, n, alpha / family_size),
               interval_alpha=alpha, simultaneous_family_size=family_size)
    if p_null is not None:
        p_null = _probability(p_null, "p_null", endpoints=True)
        out.update(nominal=p_null, pvalue=float(stats.binomtest(k, n, p_null).pvalue),
                   null_mc_se=float(np.sqrt(p_null * (1 - p_null) / n)),
                   central_null_count_interval=stats.binom.ppf([alpha / 2, 1 - alpha / 2], n, p_null).astype(int).tolist())
    return out


def uniformity_summary(pit, alpha=0.05, family_size=1, pit_error_sensitivity=0.0):
    u = _array(pit, "pit", 1)
    if np.any((u < 0) | (u > 1)):
        raise ValueError("PIT values must lie in [0,1]; no clipping allowed")
    alpha = _probability(alpha)
    family_size = _integer(family_size, "family_size")
    delta = _probability(pit_error_sensitivity, "pit_error_sensitivity", endpoints=True)
    ordered = np.sort(u)
    n = len(u)
    dplus = float(np.max(np.arange(1, n + 1) / n - ordered))
    dminus = float(np.max(ordered - np.arange(n) / n))
    d = max(dplus, dminus)
    pvalue = float(stats.kstwo.sf(d, n))
    return dict(n=n, statistic=d, dplus=dplus, dminus=dminus,
                pvalue=pvalue, pvalue_numerical_underflow=(pvalue == 0.),
                log10_dkw_tail_upper_bound=float(min(0., np.log10(2.) - 2 * n * d**2 / np.log(10.))),
                test_method="two-sided exact finite-n KS continuous null",
                mean=float(u.mean()), minimum=float(u.min()), maximum=float(u.max()),
                exact_zero_count=int(np.count_nonzero(u == 0)), exact_one_count=int(np.count_nonzero(u == 1)),
                unique_count=int(np.unique(u).size),
                dkw_simultaneous_half_width=float(np.sqrt(np.log(2 * family_size / alpha) / (2 * n))),
                pit_error_sensitivity=delta,
                sensitivity_pvalue_lower=float(stats.kstwo.sf(min(1., d + delta), n)),
                sensitivity_pvalue_upper=float(stats.kstwo.sf(max(0., d - delta), n)),
                sensitivity_is_not_a_certified_integration_error_bound=True)


def paired_summary(x, y, ids_x, ids_y, alpha=0.05):
    """Compare x-y on identical ordered replicate IDs; no silent intersection."""
    x, y = _array(x, "x", 1), _array(y, "y", 1)
    alpha = _probability(alpha)
    ids_x, ids_y = list(ids_x), list(ids_y)
    if x.shape != y.shape or len(x) < 2 or len(ids_x) != len(x) or ids_x != ids_y:
        raise ValueError("paired arrays need same shape, at least two rows and identical ordered IDs")
    if len(set(ids_x)) != len(ids_x):
        raise ValueError("duplicate replicate IDs")
    d = x - y
    mean, se = float(d.mean()), float(d.std(ddof=1) / np.sqrt(len(d)))
    half = float(stats.t.ppf(1 - alpha / 2, len(d) - 1) * se)
    out = dict(n=len(d), difference_direction="x_minus_y", mean_difference=mean,
               paired_mc_se=se, approximate_t_interval=[mean - half, mean + half],
               interval_is_asymptotic_not_exact=True)
    if np.all(np.isin(x, [0., 1.])) and np.all(np.isin(y, [0., 1.])):
        n10 = int(np.count_nonzero((x == 1) & (y == 0)))
        n01 = int(np.count_nonzero((x == 0) & (y == 1)))
        disc = n10 + n01
        out.update(discordant_x_only=n10, discordant_y_only=n01,
                   mcnemar_exact_pvalue=1.0 if disc == 0 else float(stats.binomtest(n10, disc, 0.5).pvalue),
                   finite_sample_hoeffding_interval=[max(-1., mean - np.sqrt(2 * np.log(2 / alpha) / len(d))),
                                                    min(1., mean + np.sqrt(2 * np.log(2 / alpha) / len(d)))])
    return out


def prior_return_summary(quantiles, prior_quantiles, prior_scale):
    """Descriptive necessary check; equality of four quantiles is not posterior equality."""
    q = _array(quantiles, "quantiles", 3)
    pq = _array(prior_quantiles, "prior_quantiles", 2)
    scale = _array(prior_scale, "prior_scale", 1)
    if q.shape[1:] != pq.shape or len(scale) != pq.shape[0] or np.any(scale <= 0):
        raise ValueError("inconsistent prior diagnostic shapes/scales")
    distance = np.max(np.abs(q - pq) / scale[None, :, None], axis=(1, 2))
    return dict(maximum_scaled_quantile_distance=float(distance.max()),
                median_scaled_quantile_distance=float(np.median(distance)),
                identical_quantiles_every_replication=bool(np.all(q == pq)),
                equality_of_four_quantiles_does_not_prove_full_posterior_equality=True)


def diagnose_sbc(pit, quantiles, truth, loglikelihood_pit, *, methods, parameters,
                 probabilities, groups, replicate_ids, expected_n,
                 numerical_complete, alpha=0.05, pit_error_sensitivity=0.0):
    """Historical input order M,N,P[,Q]. Groups must partition method names.

    `numerical_complete` is an explicit prerequisite, never inferred from uniformity.
    This function only handles continuous-prior SBC; fixed injections use separate routines.
    """
    if numerical_complete is not True:
        raise ValueError("numerical convergence not approved; SBC interpretation blocked")
    alpha = _probability(alpha)
    expected_n = _integer(expected_n, "expected_n", 2)
    u = _array(pit, "pit", 3)
    q = _array(quantiles, "quantiles", 4)
    theta = _array(truth, "truth", 2)
    ll = _array(loglikelihood_pit, "loglikelihood_pit", 2)
    probs = _array(probabilities, "probabilities", 1)
    if not np.array_equal(probs, np.array([.05, .5, .9, .95])):
        raise ValueError("protocol requires probabilities [.05,.5,.9,.95] in this order")
    methods, parameters, ids = list(methods), list(parameters), list(replicate_ids)
    if len(set(methods)) != len(methods) or len(set(parameters)) != len(parameters):
        raise ValueError("duplicate method or parameter name")
    m, n, p = u.shape
    if n != expected_n or (m, p) != (len(methods), len(parameters)) or q.shape != (m, n, p, 4) or theta.shape != (n, p) or ll.shape != (m, n):
        raise ValueError("input shape or planned replicate count mismatch")
    if len(ids) != n or len(set(ids)) != n:
        raise ValueError("replicate IDs must be unique with one per planned row")
    if np.any(np.diff(q, axis=-1) < 0):
        raise ValueError("quantiles are not monotone")
    grouped = [name for names in groups.values() for name in names]
    if len(grouped) != m or set(grouped) != set(methods):
        raise ValueError("groups must partition all methods exactly once")
    records = []
    for group, names in groups.items():
        family_size = len(names) * ((p + 1) + p * 5)
        group_rows = []
        for name in names:
            j = methods.index(name)
            for k, parameter in enumerate(parameters + ["logL_at_truth"]):
                vals = u[j, :, k] if k < p else ll[j]
                group_rows.append(dict(group=group, method=name, target=parameter, diagnostic="PIT",
                    **uniformity_summary(vals, alpha, family_size, pit_error_sensitivity)))
            for k, parameter in enumerate(parameters):
                for l, prob in enumerate(probs):
                    hit = theta[:, k] <= q[j, :, k, l]
                    group_rows.append(dict(group=group, method=name, target=parameter, diagnostic=f"below_q{prob:.2f}",
                                           **binomial_summary(hit, float(prob), alpha, family_size)))
                hit = (q[j, :, k, 0] <= theta[:, k]) & (theta[:, k] <= q[j, :, k, 3])
                group_rows.append(dict(group=group, method=name, target=parameter, diagnostic="central_90",
                                       **binomial_summary(hit, .9, alpha, family_size)))
        adjusted, rejected = holm([row['pvalue'] for row in group_rows], alpha)
        assert len(group_rows) == family_size
        for row, padj, reject in zip(group_rows, adjusted, rejected, strict=True):
            row.update(family_size=family_size, holm_pvalue=float(padj), reject=bool(reject))
        records.extend(group_rows)
    return dict(scope="continuous_prior_predictive_SBC", n=n, methods=methods, parameters=parameters,
                numerical_complete=True, alpha=alpha, groups=groups, tests=records,
                nonrejection_does_not_prove_correctness=True,
                approximate_family_rejection_does_not_alone_identify_numerical_failure=True)


def fixed_injection_summary(quantiles, truth, probabilities=(.05, .5, .9, .95), *,
                            alpha=.05, lower_support=None, upper_support=None):
    """One scalar parameter, one fixed scenario; no automatic 90% null hypothesis."""
    q = _array(quantiles, "quantiles", 2)
    probs = _array(probabilities, "probabilities", 1)
    if q.shape[1] != 4 or not np.array_equal(probs, [.05, .5, .9, .95]) or np.any(np.diff(q, axis=-1) < 0):
        raise ValueError("expected monotone .05/.5/.9/.95 quantiles")
    if isinstance(truth, (bool, np.bool_)) or not isinstance(truth, Real) or not np.isfinite(truth):
        raise ValueError("truth must be one finite real fixed parameter value")
    if lower_support is not None:
        if not isinstance(lower_support, Real) or not np.isfinite(lower_support) or truth < lower_support or np.any(q < lower_support):
            raise ValueError("truth or quantiles outside lower support")
    if upper_support is not None:
        if not isinstance(upper_support, Real) or not np.isfinite(upper_support) or truth > upper_support or np.any(q > upper_support):
            raise ValueError("truth or quantiles outside upper support")
    central = (q[:, 0] <= truth) & (truth <= q[:, 3])
    out = dict(scope="fixed_truth_coverage_not_SBC", truth=float(truth),
               nominal_frequentist_coverage_not_assumed=True,
               central_90=binomial_summary(central, alpha=alpha),
               upper_quantile_90=binomial_summary(truth <= q[:, 2], alpha=alpha),
               median_bias=float(np.mean(q[:, 1] - truth)),
               median_bias_mc_se=float(np.std(q[:, 1] - truth, ddof=1) / np.sqrt(len(q))) if len(q) > 1 else None)
    if lower_support is not None:
        out['support_to_upper90'] = binomial_summary((lower_support <= truth) & (truth <= q[:, 2]), alpha=alpha)
        if truth == lower_support:
            out['support_to_upper90'].update(structural_coverage=1.0,
                explanation="the fixed lower boundary belongs to [lower_support,U90] for every admissible realization; 90% is not the null")
    return out
