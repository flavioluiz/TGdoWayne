"""Explicit per-target reuse for the unchanged C07 v2 diagnostic method.

The stable public functions remain available. Only target_diagnostics is fused:
normal scores, sorted samples, indicator ESS and quantile interpolation are
reused. No global monkey-patching, shared mutable cache, new criterion or RNG.
"""
from __future__ import annotations
import math
import numpy as np
from scipy import fft, special, stats
from inference.mcmc_diagnostics import *  # Preserve the stable standalone API.
from inference import mcmc_diagnostics as reference

_Z95 = float(stats.norm.isf(.025))
_BETA_PROBS = np.array([.025, .975, *stats.norm.cdf([-1., 1.])])


def _scores_and_sorted(x, *, kind="quicksort", return_order=False):
    """Average tied ranks plus ascending sample, using one indirect sort."""
    flat = x.ravel()
    order = np.argsort(flat, kind=kind)
    ordered = flat[order]
    starts = np.r_[0, np.flatnonzero(ordered[1:] != ordered[:-1]) + 1]
    ends = np.r_[starts[1:], len(flat)]
    sorted_ranks = np.repeat((starts + ends + 1) * .5, ends - starts)
    normal = special.ndtri((sorted_ranks - 3. / 8.) / (len(flat) + 1. / 4.))
    scores = np.empty_like(flat)
    scores[order] = normal
    result = (scores.reshape(x.shape), ordered)
    return (*result, order) if return_order else result


def _quantiles_sorted(ordered, probabilities):
    """NumPy's linear quantile interpolation on an already sorted finite sample.

    The two branches match numpy._lerp, avoiding threshold changes at ties.
    """
    p = np.asarray(probabilities, dtype=float)
    index = (len(ordered) - 1) * p
    lower = np.floor(index).astype(np.intp)
    upper = np.minimum(lower + 1, len(ordered) - 1)
    weight = index - lower
    a, b = ordered[lower], ordered[upper]
    difference = b - a
    return np.where(weight >= .5, b - difference * (1 - weight), a + difference * weight)


def _ess_trusted_split(x):
    """Same Geyer estimator as reference; x is already validated and split."""
    n, m = x.shape
    centered = x - np.mean(x, axis=0)
    size = fft.next_fast_len(2 * n)
    transform = fft.rfft(centered, n=size, axis=0)
    covariance = fft.irfft(transform * np.conjugate(transform), n=size, axis=0)[:n] / n
    within = float(np.mean(covariance[0]) * n / (n - 1))
    variance = float((n - 1) / n * within + np.var(np.mean(x, axis=0), ddof=1))
    if variance <= 0 or within <= 0:
        return {"ess": 0., "ess_raw": 0., "tau": math.inf,
                "status": "constant_or_stuck", "draws": n * m}
    rho = 1 - (within - np.mean(covariance, axis=1)) / variance
    rho[0] = 1.
    count = (len(rho) // 2) * 2
    pairs = rho[:count].reshape(-1, 2).sum(axis=1)
    nonpositive = np.flatnonzero(pairs <= 0)
    stop = int(nonpositive[0]) if len(nonpositive) else len(pairs)
    monotone = np.minimum.accumulate(pairs[:stop])
    tau = max(-1 + 2 * float(monotone.sum()), 1 / math.log10(n * m))
    raw = n * m / tau
    return {"ess": min(float(n * m), raw), "ess_raw": raw, "tau": tau,
            "status": "estimated", "draws": n * m,
            "retained_lag_pairs": stop, "reached_last_pair": not bool(len(nonpositive))}


def _batch_trusted(x):
    n, m = x.shape
    b = math.ceil(math.sqrt(n)); a = n // b
    if a < 2:
        return {"mcse": math.inf, "batches_per_chain": a, "batch_length": b,
                "status": "insufficient_batches"}
    means = x[:a * b].reshape(a, b, m).mean(axis=1)
    variance = float(np.sum(np.var(means, axis=0, ddof=1)) / (a * m * m))
    return {"mcse": math.sqrt(max(variance, 0)), "batch_length": b,
            "batches_per_chain": a, "discarded_draws_per_chain": n - a * b,
            "status": "estimated"}


class _Parameter:
    """All memory is private to one parameter of one target."""
    def __init__(self, x):
        self.x = np.ascontiguousarray(x)
        self.n, self.m = x.shape
        half = self.n // 2
        self.split = np.concatenate((self.x[:half], self.x[-half:]), axis=1)
        normal, ordered_split, raw_order = _scores_and_sorted(self.split, return_order=True)
        self.ordered = ordered_split if self.n % 2 == 0 else np.sort(self.x.ravel())
        size = len(ordered_split)
        if size % 2:
            median = ordered_split[size // 2]
        else:
            median = np.mean(ordered_split[size // 2 - 1:size // 2 + 1])
        # In raw sorted order the folded data are two monotone runs. Stable
        # sorting exploits that structure, then restore the original ordering.
        folded_sorted, _ = _scores_and_sorted(
            np.abs(ordered_split - median).reshape(self.split.shape), kind="stable")
        folded_flat = np.empty(self.split.size)
        folded_flat[raw_order] = folded_sorted.ravel()
        folded = folded_flat.reshape(self.split.shape)
        bulk_rhat = reference._basic_rhat(normal)
        folded_rhat = reference._basic_rhat(folded)
        self.rhat = {"rank_split": bulk_rhat, "folded_rank_split": folded_rhat,
                     "maximum": max(bulk_rhat, folded_rhat),
                     "discarded_middle_draws_per_chain": int(self.n % 2)}
        self.bulk = _ess_trusted_split(normal)
        self.ess_cache = {}
        self.cdf_cache = {}
        self.q05, self.q95 = _quantiles_sorted(self.ordered, [.05, .95])
        tail05 = self.indicator_ess(float(self.q05))[1]
        tail95 = self.indicator_ess(float(self.q95))[1]
        self.ess = {"bulk": self.bulk["ess"], "tail": min(tail05["ess"], tail95["ess"]),
                    "tail_05": tail05["ess"], "tail_95": tail95["ess"]}

    def indicator_ess(self, threshold):
        if threshold not in self.ess_cache:
            indicator = (self.x <= threshold).astype(float)
            half = self.n // 2
            split = np.concatenate((indicator[:half], indicator[-half:]), axis=1)
            self.ess_cache[threshold] = (indicator, _ess_trusted_split(split))
        return self.ess_cache[threshold]

    def cdf(self, threshold):
        threshold = float(threshold)
        if threshold in self.cdf_cache:
            return self.cdf_cache[threshold]
        indicator, ess = self.indicator_ess(threshold)
        estimate = float(indicator.mean())
        if estimate in (0., 1.):
            result = {"estimate": estimate, "ess": 0., "mcse": math.inf,
                      "interval": [0., 1.], "status": "constant_indicator_unresolved",
                      "precision_pass": False, "structural_support_not_inferred": True}
        else:
            batch = _batch_trusted(indicator)
            spectral = math.sqrt(estimate * (1 - estimate) / ess["ess"]) if ess["ess"] > 0 else math.inf
            mcse = max(spectral, batch["mcse"])
            radius = _Z95 * mcse
            adequate = batch["batches_per_chain"] >= 16 and batch["batch_length"] >= 5 * max(1., ess["tau"])
            result = {"estimate": estimate, "ess": ess["ess"], "ess_raw": ess.get("ess_raw"),
                      "tau": ess["tau"], "mcse": mcse, "mcse_spectral": spectral,
                      "mcse_batches": batch["mcse"], "batch": batch, "batch_adequate": adequate,
                      "interval": [max(0., estimate - radius), min(1., estimate + radius)],
                      "normal_critical_value": _Z95, "deterministic_error": 0.,
                      "status": "estimated_asymptotic_not_exact",
                      "precision_pass": bool(mcse <= .00335 and adequate and np.isfinite(mcse))}
        self.cdf_cache[threshold] = result
        return result

    def quantiles(self, probabilities):
        ps = np.array(probabilities)
        if not len(ps):
            return []
        estimates = _quantiles_sorted(self.ordered, ps)
        cdfs = [self.cdf(float(q)) for q in estimates]
        valid = [j for j, c in enumerate(cdfs) if np.isfinite(c["mcse"]) and c["mcse"] != 0]
        mapped = {}; effective = {}
        if valid:
            p = ps[valid]
            eff = np.minimum(self.x.size, p * (1 - p) / np.array([cdfs[j]["mcse"] for j in valid]) ** 2)
            points = stats.beta.ppf(_BETA_PROBS[None, :], (eff * p + 1)[:, None],
                                   (eff * (1 - p) + 1)[:, None])
            mapped_array = _quantiles_sorted(self.ordered, points)
            for i, j in enumerate(valid):
                mapped[j] = mapped_array[i]; effective[j] = float(eff[i])
        out = []
        for j, q in enumerate(estimates):
            if j not in mapped:
                out.append({"estimate": float(q), "mcse": math.inf, "interval": [-math.inf, math.inf],
                            "status": "unresolved", "cdf": cdfs[j]})
            else:
                values = mapped[j]
                out.append({"estimate": float(q), "mcse": float((values[3] - values[2]) / 2),
                            "interval": values[:2].tolist(), "effective_ess_for_error": effective[j],
                            "cdf": cdfs[j], "status": "estimated_asymptotic_not_exact"})
        return out


def target_diagnostics(values, truth, *, loglikelihood=None, loglikelihood_truth=None,
                       names=None, probabilities=(.05, .5, .9, .95)):
    """Same output and v2 decisions as stable target_diagnostics, with local reuse."""
    x = reference._array(values, 3)
    theta = reference._array(truth, 1, "truth")
    if len(theta) != x.shape[2]:
        raise ValueError("truth dimension mismatch")
    if np.any(x < 0) or np.any(x > 1) or np.any(theta < 0) or np.any(theta > 1):
        raise ValueError("target parameters and truth must use the unit prior cube")
    if x.shape[1] != 4:
        raise ValueError("C07 protocol requires exactly four independent chains")
    if x.shape[0] < 8:
        raise ValueError("at least eight draws and two chains required")
    if names is None:
        names = [f"parameter_{j}" for j in range(x.shape[2])]
    if len(names) != x.shape[2] or len(set(names)) != len(names):
        raise ValueError("names must uniquely match the parameter dimension")
    probabilities = tuple(reference._probability(p) for p in probabilities)
    if (loglikelihood is None) != (loglikelihood_truth is None):
        raise ValueError("loglikelihood draws and truth must be supplied together")
    ll = None
    if loglikelihood is not None:
        ll = reference._chains(loglikelihood)
        if ll.shape != x.shape[:2]:
            raise ValueError("loglikelihood shape mismatch")
        reference._real(loglikelihood_truth, "threshold")
    x = np.ascontiguousarray(x)
    convergence = {}; cuts = []; quantiles = []; failures = []
    for j, name in enumerate(names):
        parameter = _Parameter(x[:, :, j])
        passes = bool(parameter.rhat["maximum"] <= 1.01 and parameter.ess["bulk"] >= 400 and parameter.ess["tail"] >= 400)
        convergence[name] = {"rhat": parameter.rhat, "ess": parameter.ess, "diagnostic_floor_pass": passes}
        if not passes:
            failures.append(f"{name}:rhat_or_bulk_tail_ess")
        at_truth = parameter.cdf(theta[j])
        cuts.append({"name": name, "kind": "truth", **at_truth})
        if not at_truth["precision_pass"]:
            failures.append(f"{name}:truth_cdf_precision")
        for p, quantile in zip(probabilities, parameter.quantiles(probabilities)):
            quantiles.append({"name": name, "probability": float(p), **quantile})
            if not quantile["cdf"]["precision_pass"]:
                failures.append(f"{name}:quantile_{p}_cdf_precision")
    if ll is not None:
        parameter = _Parameter(ll)
        passes = bool(parameter.rhat["maximum"] <= 1.01 and parameter.ess["bulk"] >= 400 and parameter.ess["tail"] >= 400)
        convergence["loglikelihood"] = {"rhat": parameter.rhat, "ess": parameter.ess, "diagnostic_floor_pass": passes}
        if not passes:
            failures.append("loglikelihood:rhat_or_bulk_tail_ess")
        cdf = parameter.cdf(loglikelihood_truth)
        cuts.append({"name": "loglikelihood", "kind": "truth", **cdf})
        if not cdf["precision_pass"]:
            failures.append("loglikelihood:truth_cdf_precision")
    else:
        failures.append("loglikelihood:missing")
    return {"draws_per_chain": x.shape[0], "chains": x.shape[1], "convergence": convergence,
            "truth_cdfs": cuts, "quantiles": quantiles, "failures": failures,
            "diagnostic_and_mc_precision_pass": not failures,
            "does_not_approve_deterministic_error_or_sampler_kernel": True}
