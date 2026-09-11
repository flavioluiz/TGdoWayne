"""Independent numerical diagnostics, not an MCMC sampler.

Arrays are (draw, chain), or (draw, chain, parameter) for summarize_draws.
Based on Vehtari et al. (2021), arXiv:1903.08008v5, sections 3.2 and 4.
No source code from external implementations was copied.
"""
from __future__ import annotations

import math
import numbers
import numpy as np
from scipy import fft, special, stats


def _real(value, name):
    if isinstance(value, (bool, np.bool_)) or not isinstance(value, numbers.Real):
        raise TypeError(f"{name} must be a real scalar")
    value = float(value)
    if not np.isfinite(value):
        raise ValueError(f"{name} must be finite")
    return value


def _integer(value, name, minimum=1):
    if isinstance(value, (bool, np.bool_)) or not isinstance(value, numbers.Integral):
        raise TypeError(f"{name} must be an integer")
    if value < minimum:
        raise ValueError(f"{name} must be >= {minimum}")
    return int(value)


def _probability(value, name="probability", endpoints=False):
    value = _real(value, name)
    if not (0 <= value <= 1 if endpoints else 0 < value < 1):
        raise ValueError(f"{name} outside its allowed interval")
    return value


def _array(values, ndim, name="draws"):
    x = np.asarray(values)
    if x.dtype.kind not in "iuf" or x.ndim != ndim:
        raise ValueError(f"{name} must be a real numeric {ndim}-D array")
    x = np.asarray(x, dtype=float)
    if not np.isfinite(x).all():
        raise ValueError(f"{name} must be finite")
    return x


def _chains(values):
    x = _array(values, 2)
    if x.shape[0] < 8 or x.shape[1] < 2:
        raise ValueError("at least eight draws and two chains required")
    return x


def split_chains(values):
    """Drop the middle draw only when length is odd; preserve time order."""
    x = _chains(values)
    n = x.shape[0] // 2
    return np.concatenate((x[:n], x[-n:]), axis=1)


def rank_normalize(values):
    x = _array(values, 2)
    ranks = stats.rankdata(x.ravel(), method="average").reshape(x.shape)
    return special.ndtri((ranks - 3.0 / 8.0) / (x.size + 1.0 / 4.0))


def _basic_rhat(x):
    n = x.shape[0]
    within = float(np.mean(np.var(x, axis=0, ddof=1)))
    between_over_n = float(np.var(np.mean(x, axis=0), ddof=1))
    if within == 0:
        return math.inf
    return math.sqrt(((n - 1) / n * within + between_over_n) / within)


def rank_rhat(values):
    x = split_chains(values)
    bulk = _basic_rhat(rank_normalize(x))
    folded = _basic_rhat(rank_normalize(np.abs(x - np.median(x))))
    return {"rank_split": bulk, "folded_rank_split": folded,
            "maximum": max(bulk, folded),
            "discarded_middle_draws_per_chain": int(_chains(values).shape[0] % 2)}


def autocovariance_fft(values):
    """Biased lag autocovariance, divisor N, independently centered per chain."""
    x = _array(values, 2)
    if x.shape[0] < 2 or x.shape[1] < 1:
        raise ValueError("at least two draws and one chain required")
    n = x.shape[0]
    centered = x - np.mean(x, axis=0)
    transform = fft.rfft(centered, n=fft.next_fast_len(2 * n), axis=0)
    return fft.irfft(transform * np.conjugate(transform),
                     n=fft.next_fast_len(2 * n), axis=0)[:n] / n


def effective_sample_size(values, *, split=True):
    """Multichain ESS with Geyer initial-positive, initial-monotone paired lags.

    For precision the reported ESS is capped by actual retained draws. This is
    conservative for negatively correlated chains; raw ESS remains available.
    ESS is functional-specific and does not imply independent retained draws.
    """
    x = split_chains(values) if split else _array(values, 2)
    if x.shape[0] < 2 or x.shape[1] < 2:
        raise ValueError("ESS needs at least two draws and two chains")
    n, m = x.shape
    cov = autocovariance_fft(x)
    within = float(np.mean(cov[0]) * n / (n - 1))
    variance = float((n - 1) / n * within + np.var(np.mean(x, axis=0), ddof=1))
    if variance <= 0 or within <= 0:
        return {"ess": 0.0, "ess_raw": 0.0, "tau": math.inf,
                "status": "constant_or_stuck", "draws": n * m}
    rho = 1 - (within - np.mean(cov, axis=1)) / variance
    rho[0] = 1.0
    count = (len(rho) // 2) * 2
    pair = rho[:count].reshape(-1, 2).sum(axis=1)
    nonpositive = np.flatnonzero(pair <= 0)
    truncated = int(nonpositive[0]) if len(nonpositive) else len(pair)
    positive = np.minimum.accumulate(pair[:truncated])
    tau = max(-1 + 2 * float(positive.sum()), 1 / math.log10(n * m))
    raw = n * m / tau
    return {"ess": min(float(n * m), raw), "ess_raw": raw,
            "tau": tau, "status": "estimated",
            "draws": n * m, "retained_lag_pairs": truncated,
            "reached_last_pair": not bool(len(nonpositive))}


def bulk_tail_ess(values):
    x = _chains(values)
    split = split_chains(x)
    bulk = effective_sample_size(rank_normalize(split), split=False)
    quantiles = np.quantile(x, [.05, .95])
    tails = [effective_sample_size((x <= q).astype(float)) for q in quantiles]
    return {"bulk": bulk["ess"], "tail": min(t["ess"] for t in tails),
            "tail_05": tails[0]["ess"], "tail_95": tails[1]["ess"]}


def batch_mean_mcse(values, *, batch_length=None):
    """Independent non-overlapping batch-means estimator, without joining chains.

    Complete batches only; reports discarded draws and adequacy separately.
    Independence between adjacent batches is an approximation to be checked.
    """
    x = _chains(values)
    n, m = x.shape
    b = math.ceil(math.sqrt(n)) if batch_length is None else _integer(batch_length, "batch_length", 2)
    a = n // b
    if a < 2:
        return {"mcse": math.inf, "batches_per_chain": a, "batch_length": b,
                "status": "insufficient_batches"}
    batches = x[:a * b].reshape(a, b, m).mean(axis=1)
    # Each chain's grand mean has variance var(batch means)/a. Chains are independent.
    variance = float(np.sum(np.var(batches, axis=0, ddof=1)) / (a * m * m))
    return {"mcse": math.sqrt(max(variance, 0)), "batch_length": b,
            "batches_per_chain": a, "discarded_draws_per_chain": n - a * b,
            "status": "estimated"}


def cdf_summary(values, threshold, *, alpha=.05, family_size=1,
                deterministic_error=0., mcse_target=.00335):
    x = _chains(values)
    threshold = _real(threshold, "threshold")
    alpha = _probability(alpha, "alpha")
    family_size = _integer(family_size, "family_size")
    deterministic_error = _probability(deterministic_error, "deterministic_error", True)
    mcse_target = _real(mcse_target, "mcse_target")
    if mcse_target <= 0:
        raise ValueError("mcse_target must be positive")
    indicator = (x <= threshold).astype(float)
    estimate = float(indicator.mean())
    if estimate in (0., 1.):
        return {"estimate": estimate, "ess": 0., "mcse": math.inf,
                "interval": [0., 1.], "status": "constant_indicator_unresolved",
                "precision_pass": False, "structural_support_not_inferred": True}
    ess = effective_sample_size(indicator)
    batch = batch_mean_mcse(indicator)
    spectral = math.sqrt(estimate * (1 - estimate) / ess["ess"]) if ess["ess"] > 0 else math.inf
    mcse = max(spectral, batch["mcse"])
    z = float(stats.norm.isf(alpha / (2 * family_size)))
    radius = deterministic_error + z * mcse
    batch_adequate = (batch["batches_per_chain"] >= 16 and
                      batch["batch_length"] >= 5 * max(1., ess["tau"]))
    return {"estimate": estimate, "ess": ess["ess"], "ess_raw": ess.get("ess_raw"),
            "tau": ess["tau"],
            "mcse": mcse, "mcse_spectral": spectral, "mcse_batches": batch["mcse"],
            "batch": batch, "batch_adequate": batch_adequate,
            "interval": [max(0., estimate - radius), min(1., estimate + radius)],
            "normal_critical_value": z, "deterministic_error": deterministic_error,
            "status": "estimated_asymptotic_not_exact", "precision_pass": bool(
                mcse <= mcse_target and batch_adequate and np.isfinite(mcse))}


def quantile_summary(values, probability, *, alpha=.05, family_size=1):
    """ESS-adjusted beta order-statistic error interval, Vehtari section 4.4.

    Finite-MCMC coverage is approximate. No KDE density or independent-draw
    interpretation of ESS is needed; conservative CDF MCSE sets effective ESS.
    """
    x = _chains(values)
    p = _probability(probability)
    alpha = _probability(alpha, "alpha")
    family_size = _integer(family_size, "family_size")
    q = float(np.quantile(x, p))
    cdf = cdf_summary(x, q)
    if not np.isfinite(cdf["mcse"]) or cdf["mcse"] == 0:
        return {"estimate": q, "mcse": math.inf, "interval": [-math.inf, math.inf],
                "status": "unresolved", "cdf": cdf}
    effective = min(x.size, p * (1 - p) / cdf["mcse"] ** 2)
    shape = (effective * p + 1, effective * (1 - p) + 1)
    interval_p = stats.beta.ppf([alpha / (2 * family_size), 1 - alpha / (2 * family_size)], *shape)
    one_sigma_p = stats.beta.ppf(stats.norm.cdf([-1., 1.]), *shape)
    interval_q = np.quantile(x, interval_p)
    one_sigma_q = np.quantile(x, one_sigma_p)
    return {"estimate": q, "mcse": float(np.diff(one_sigma_q)[0] / 2),
            "interval": interval_q.tolist(), "effective_ess_for_error": float(effective),
            "cdf": cdf, "status": "estimated_asymptotic_not_exact"}


def summarize_draws(values, names):
    x = _array(values, 3)
    if len(names) != x.shape[2] or len(set(names)) != len(names):
        raise ValueError("names must uniquely match the parameter dimension")
    if x.shape[1] != 4:
        raise ValueError("C07 protocol requires exactly four independent chains")
    output = {}
    for j, name in enumerate(names):
        rh = rank_rhat(x[:, :, j]); ess = bulk_tail_ess(x[:, :, j])
        output[name] = {"rhat": rh, "ess": ess,
                        "diagnostic_floor_pass": bool(rh["maximum"] <= 1.01 and
                                                       ess["bulk"] >= 400 and ess["tail"] >= 400)}
    return output


def target_diagnostics(values, truth, *, loglikelihood=None,
                       loglikelihood_truth=None, names=None,
                       probabilities=(.05, .5, .9, .95)):
    """Per-target C07 report, with every diagnostic failure retained.

    Parameters must use normalized prior coordinates. The log likelihood must
    use the same data and full target likelihood, not the log posterior/logit
    Jacobian. This function cannot audit those semantic requirements itself.
    """
    x = _array(values, 3)
    theta = _array(truth, 1, "truth")
    if len(theta) != x.shape[2]:
        raise ValueError("truth dimension mismatch")
    if np.any(x < 0) or np.any(x > 1) or np.any(theta < 0) or np.any(theta > 1):
        raise ValueError("target parameters and truth must use the unit prior cube")
    if names is None:
        names = [f"parameter_{j}" for j in range(x.shape[2])]
    convergence = summarize_draws(x, names)
    cuts = []; quantiles = []; failures = []
    for j, name in enumerate(names):
        if not convergence[name]["diagnostic_floor_pass"]:
            failures.append(f"{name}:rhat_or_bulk_tail_ess")
        at_truth = cdf_summary(x[:, :, j], theta[j])
        cuts.append({"name": name, "kind": "truth", **at_truth})
        if not at_truth["precision_pass"]:
            failures.append(f"{name}:truth_cdf_precision")
        for p in probabilities:
            quantile = quantile_summary(x[:, :, j], p)
            quantiles.append({"name": name, "probability": float(p), **quantile})
            if not quantile["cdf"]["precision_pass"]:
                failures.append(f"{name}:quantile_{p}_cdf_precision")
    if (loglikelihood is None) != (loglikelihood_truth is None):
        raise ValueError("loglikelihood draws and truth must be supplied together")
    if loglikelihood is not None:
        ll = _chains(loglikelihood)
        if ll.shape != x.shape[:2]:
            raise ValueError("loglikelihood shape mismatch")
        lr = rank_rhat(ll); le = bulk_tail_ess(ll)
        convergence["loglikelihood"] = {"rhat": lr, "ess": le,
            "diagnostic_floor_pass": bool(lr["maximum"] <= 1.01 and le["bulk"] >= 400 and le["tail"] >= 400)}
        if not convergence["loglikelihood"]["diagnostic_floor_pass"]:
            failures.append("loglikelihood:rhat_or_bulk_tail_ess")
        lcdf = cdf_summary(ll, loglikelihood_truth)
        cuts.append({"name": "loglikelihood", "kind": "truth", **lcdf})
        if not lcdf["precision_pass"]:
            failures.append("loglikelihood:truth_cdf_precision")
    else:
        failures.append("loglikelihood:missing")
    return {"draws_per_chain": x.shape[0], "chains": x.shape[1],
            "convergence": convergence, "truth_cdfs": cuts, "quantiles": quantiles,
            "failures": failures, "diagnostic_and_mc_precision_pass": not failures,
            "does_not_approve_deterministic_error_or_sampler_kernel": True}


def compare_reference_quantiles(values, reference_quantiles, probabilities,
                                *, reference_cdf_error, quantile_tolerance=.001,
                                alpha=.05, cdf_mcse_target=.00335):
    """All normalized-prior coordinates; one simultaneous family over every cut.

    reference_cdf_error must bound/estimate error of F(q_ref) versus p as an
    independent input. A horizontal quantile error alone is insufficient for
    this CDF comparison. Caller must describe the deterministic evidence.
    """
    x = _array(values, 3)
    ref = _array(reference_quantiles, 2, "reference_quantiles")
    probs = [_probability(p) for p in probabilities]
    if ref.shape != (x.shape[2], len(probs)):
        raise ValueError("reference shape must be (parameter, probability)")
    if np.any(x < 0) or np.any(x > 1) or np.any(ref < 0) or np.any(ref > 1):
        raise ValueError("draws and reference quantiles must use unit prior coordinates")
    if np.any(np.diff(probs) <= 0) or np.any(np.diff(ref, axis=1) < 0):
        raise ValueError("ordered probabilities and reference quantiles required")
    tolerance = _real(quantile_tolerance, "quantile_tolerance")
    if tolerance < 0:
        raise ValueError("quantile_tolerance must be nonnegative")
    errors = np.broadcast_to(np.asarray(reference_cdf_error, dtype=float), ref.shape)
    if not np.isfinite(errors).all() or np.any(errors < 0) or np.any(errors > 1):
        raise ValueError("invalid reference_cdf_error")
    cuts = []
    family = ref.size
    for j in range(x.shape[2]):
        for k, p in enumerate(probs):
            cdf = cdf_summary(x[:, :, j], ref[j, k], alpha=alpha, family_size=family,
                              deterministic_error=float(errors[j, k]), mcse_target=cdf_mcse_target)
            quantile = quantile_summary(x[:, :, j], p, alpha=alpha, family_size=family)
            cdf_agrees = cdf["interval"][0] <= p <= cdf["interval"][1]
            q_agrees = quantile["interval"][0] - tolerance <= ref[j, k] <= quantile["interval"][1] + tolerance
            cuts.append({"parameter_index": j, "probability": p, "reference_quantile": float(ref[j, k]),
                         "cdf": cdf, "quantile": quantile,
                         "cdf_agrees": bool(cdf_agrees), "quantile_agrees": bool(q_agrees),
                         "quantile_agreement_is_descriptive_not_second_test_family": True,
                         "accepted": bool(cdf_agrees and cdf["precision_pass"] and
                                          quantile["cdf"]["precision_pass"])})
    return {"family_size": family, "alpha": alpha, "cuts": cuts,
            "all_cuts_accepted": all(c["accepted"] for c in cuts),
            "does_not_replace_global_rhat_ess_or_deterministic_checks": True}


def compare_independent_cdfs(first, second, *, deterministic_tolerance=.002,
                             alpha=.05, family_size=1):
    """Assumes independent productions; correlated/common-random draws need covariance."""
    tol = _real(deterministic_tolerance, "deterministic_tolerance")
    if tol < 0:
        raise ValueError("deterministic_tolerance must be nonnegative")
    z = float(stats.norm.isf(_probability(alpha, "alpha") / (2 * _integer(family_size, "family_size"))))
    difference = float(first["estimate"] - second["estimate"])
    se = math.hypot(first["mcse"], second["mcse"])
    return {"difference": difference, "mcse_difference": se,
            "acceptance_radius": tol + z * se,
            "agrees": bool(np.isfinite(se) and abs(difference) <= tol + z * se),
            "precision_pass": bool(first["precision_pass"] and second["precision_pass"])}


def randomized_exchangeable_rank(draws, truth, rng):
    """Randomized rank valid under exchangeability, NOT made valid by autocorrelation ESS.

    Does not inspect or certify independence. With ties, randomly place the
    truth among equal entries before uniformizing the discrete rank cell.
    """
    x = _array(draws, 1)
    if x.size < 1:
        raise ValueError("at least one posterior draw required")
    truth = _real(truth, "truth")
    if not isinstance(rng, np.random.Generator):
        raise TypeError("an explicitly seeded NumPy Generator is required")
    smaller = int(np.count_nonzero(x < truth))
    tied = int(np.count_nonzero(x == truth))
    rank = smaller + int(rng.integers(tied + 1))
    return {"rank": rank, "posterior_draws": int(x.size), "ties": tied,
            "randomized_pit": float((rank + rng.random()) / (x.size + 1)),
            "exchangeability_required_not_verified": True}


def ks_interval_sensitivity(lower, upper):
    """Bounds on KS D over every vector u_i in supplied intervals, without resampling.

    The bounds rely on externally valid intervals. MCMC CLT intervals are
    approximate; this routine cannot upgrade them to exact finite-sample bounds.
    """
    lo = _array(lower, 1, "lower"); hi = _array(upper, 1, "upper")
    if lo.shape != hi.shape or len(lo) == 0 or np.any(lo < 0) or np.any(hi > 1) or np.any(lo > hi):
        raise ValueError("invalid PIT intervals")
    a, b = np.sort(lo), np.sort(hi); n = len(a)
    grid0 = np.arange(n) / n; grid1 = np.arange(1, n + 1) / n
    dmin = max(0., float(np.max(grid1 - b)), float(np.max(a - grid0)))
    dmax = max(float(np.max(grid1 - a)), float(np.max(b - grid0)))
    return {"d_lower": dmin, "d_upper": dmax,
            "pvalue_lower": float(stats.kstwo.sf(dmax, n)),
            "pvalue_upper": float(stats.kstwo.sf(dmin, n)),
            "interval_validity_is_external": True}


def coverage_interval_sensitivity(cdf_lower, cdf_upper, probability):
    """Bounds on coverage theta_true <= Q_p, equivalently F(theta_true)<=p in continuous cases."""
    lo = _array(cdf_lower, 1, "cdf_lower"); hi = _array(cdf_upper, 1, "cdf_upper")
    p = _probability(probability)
    if lo.shape != hi.shape or len(lo) == 0 or np.any(lo < 0) or np.any(hi > 1) or np.any(lo > hi):
        raise ValueError("invalid CDF intervals")
    certain = int(np.sum(hi <= p)); possible = int(np.sum(lo <= p))
    return {"count_min": certain, "count_max": possible,
            "fraction_min": certain / len(lo), "fraction_max": possible / len(lo),
            "ambiguous_count": possible - certain,
            "interval_validity_is_external": True}


def central_coverage_interval_sensitivity(cdf_lower, cdf_upper, lower_probability=.05,
                                          upper_probability=.95):
    lo = _array(cdf_lower, 1, "cdf_lower"); hi = _array(cdf_upper, 1, "cdf_upper")
    a = _probability(lower_probability); b = _probability(upper_probability)
    if a >= b or lo.shape != hi.shape or len(lo) == 0 or np.any(lo < 0) or np.any(hi > 1) or np.any(lo > hi):
        raise ValueError("invalid intervals")
    certain = int(np.sum((lo >= a) & (hi <= b)))
    possible = int(np.sum((hi >= a) & (lo <= b)))
    return {"count_min": certain, "count_max": possible,
            "fraction_min": certain / len(lo), "fraction_max": possible / len(lo),
            "ambiguous_count": possible - certain,
            "interval_validity_is_external": True}


def holm_decision_sensitivity(pvalue_lower, pvalue_upper, *, alpha=.05):
    """Monotone Holm decisions at simultaneous lower/upper p-value bounds."""
    lo = _array(pvalue_lower, 1, "pvalue_lower"); hi = _array(pvalue_upper, 1, "pvalue_upper")
    alpha = _probability(alpha, "alpha")
    if lo.shape != hi.shape or len(lo) == 0 or np.any(lo < 0) or np.any(hi > 1) or np.any(lo > hi):
        raise ValueError("invalid p-value bounds")
    def rejected(p):
        order = np.argsort(p); adjusted = np.maximum.accumulate(p[order] * np.arange(len(p), 0, -1))
        result = np.empty(len(p), dtype=bool); result[order] = adjusted <= alpha
        return result
    possible = rejected(lo); certain = rejected(hi)
    return {"certain_rejections": certain.tolist(), "possible_rejections": possible.tolist(),
            "decision_stable": (certain == possible).tolist(), "family_size": len(lo), "alpha": alpha}
