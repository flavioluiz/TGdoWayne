"""Raw self-normalized IID importance diagnostics, not exact MC certificates.

All proposal parameters must be frozen before independent production draws.
Full log weights, including likelihood and prior/proposal constants, are needed
for evidence. No smoothing, clipping, rejection or posterior resampling occurs.
"""
import math
import numpy as np
from scipy.special import logsumexp
from scipy.stats import norm


def json_safe(x):
    if isinstance(x, dict):
        return {k: json_safe(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [json_safe(v) for v in x]
    if isinstance(x, np.ndarray):
        return json_safe(x.tolist())
    if isinstance(x, (bool, np.bool_)):
        return bool(x)
    if isinstance(x, (int, np.integer)):
        return int(x)
    if isinstance(x, (float, np.floating)):
        return float(x) if math.isfinite(x) else None
    return x


def _real_array(x, ndim, name):
    a = np.asarray(x)
    if a.dtype.kind not in 'fiu' or a.ndim != ndim:
        raise ValueError(f'{name} must be a real numeric array of dimension {ndim}')
    a = a.astype(float)
    return a


def _weights(log_weights):
    lw = _real_array(log_weights, 1, 'log_weights')
    if len(lw) < 2 or np.isnan(lw).any() or np.isposinf(lw).any() or not np.isfinite(lw).any():
        raise ValueError('Need at least two weights, some positive target mass, no NaN/+inf')
    ls = logsumexp(lw)
    return lw, np.exp(lw-ls), float(ls-np.log(len(lw)))


def weight_summary(log_weights, *, deletion_bound_target=.00335):
    if not 0 < deletion_bound_target < 1:
        raise ValueError('Invalid single-deletion tolerance')
    lw, p, logz = _weights(log_weights)
    n = len(p); sq = float(p@p); pmax = float(p.max())
    order = np.sort(p)[::-1]
    entropy = float(-np.sum(p[p > 0]*np.log(p[p > 0])))
    # s_w / (sqrt(N) * mean_w): delta MCSE for log Z.
    relative_se = float(np.sqrt(max(0., (n*sq-1)/(n-1))))
    deletion = pmax/(1-pmax) if pmax < 1 else math.inf
    return {
        'n': n, 'log_evidence': logz, 'log_evidence_delta_mcse': relative_se,
        'evidence_relative_mcse': relative_se,
        'weight_ess_concentration_only': 1/sq,
        'entropy_effective_count': math.exp(entropy),
        'maximum_normalized_weight': pmax,
        'largest_ten_weight_fraction': float(order[:10].sum()),
        'largest_one_percent_weight_fraction': float(order[:max(1, math.ceil(n*.01))].sum()),
        'log_weight_range_finite': float(np.ptp(lw[np.isfinite(lw)])),
        'exact_zero_target_weights': int(np.isneginf(lw).sum()),
        'floating_point_weight_underflows': int(((p == 0)&np.isfinite(lw)).sum()),
        'single_deletion_cdf_bound': deletion,
        'single_deletion_guard_pass': deletion <= deletion_bound_target,
        'no_unseen_tail_certificate': True,
    }


def iid_cdf(values, log_weights, thresholds, *, mcse_target=.00335):
    """Delta-method SNIS CDFs. Constants return unresolved, never MCSE=0 pass."""
    x = _real_array(values, 1, 'values')
    t = _real_array(thresholds, 1, 'thresholds')
    lw, p, _ = _weights(log_weights)
    if len(x) != len(lw) or not np.isfinite(x).all() or not np.isfinite(t).all() or not 0 < mcse_target < 1:
        raise ValueError('Invalid values/thresholds/precision')
    n = len(x); indicator = x[:, None] <= t[None, :]
    estimate = p@indicator
    influence = n*p[:, None]*(indicator-estimate)
    # Bessel correction applied to centered influence, not a binomial ESS.
    se = np.std(influence, axis=0, ddof=1)/np.sqrt(n)
    rows = []
    for k, cutoff in enumerate(t):
        positive = p > 0
        a = int(np.count_nonzero(indicator[:, k]&positive))
        b = int(np.count_nonzero(~indicator[:, k]&positive))
        resolved = bool(a and b and np.isfinite(se[k]) and se[k] > 0)
        rows.append({'threshold': float(cutoff), 'estimate': float(estimate[k]),
            'mcse': float(se[k]) if resolved else math.inf,
            'raw_delta_mcse': float(se[k]),
            'status': 'asymptotic_influence' if resolved else 'constant_indicator_unresolved',
            'positive_weight_counts_below_above': [a, b],
            'precision_pass': bool(resolved and se[k] <= mcse_target)})
    return rows


def weighted_quantiles(values, log_weights, probabilities):
    x = _real_array(values, 1, 'values'); probs = _real_array(probabilities, 1, 'probabilities')
    lw, p, _ = _weights(log_weights)
    if len(x) != len(lw) or not np.isfinite(x).all() or not np.isfinite(probs).all() or np.any((probs <= 0)|(probs >= 1)):
        raise ValueError('Invalid quantile inputs')
    order = np.argsort(x, kind='stable'); cumulative = np.cumsum(p[order]); cumulative[-1] = 1
    return x[order][np.searchsorted(cumulative, probs, side='left')]


def replicated_cdf(values, log_weights, thresholds, *, mcse_target=.00335):
    """Pool complete weights; estimate between-replication influence separately.

    Equal N and the same frozen proposal are required. The block influence uses
    Z_r/Z_pool; simply averaging independently self-normalized CDFs differs.
    """
    x = _real_array(values, 2, 'values'); lw = _real_array(log_weights, 2, 'log_weights')
    if x.shape != lw.shape or x.shape[0] < 2:
        raise ValueError('Expected equally sized independent replications (R,N), R>=2')
    r, n = x.shape
    each = [iid_cdf(x[j], lw[j], thresholds, mcse_target=mcse_target) for j in range(r)]
    pooled = iid_cdf(x.ravel(), lw.ravel(), thresholds, mcse_target=mcse_target)
    logz = np.array([_weights(a)[2] for a in lw]); logz_pool = logsumexp(logz)-np.log(r)
    z_ratio = np.exp(logz-logz_pool)
    for k, row in enumerate(pooled):
        f = np.array([a[k]['estimate'] for a in each])
        block_influence = z_ratio*(f-row['estimate'])
        between = float(np.std(block_influence, ddof=1)/np.sqrt(r))
        row['pooled_iid_influence_mcse'] = row['mcse']
        row['between_replications_influence_mcse'] = between
        row['replication_estimates'] = f.tolist()
        row['replication_mcse'] = [a[k]['mcse'] for a in each]
        row['replication_status'] = [a[k]['status'] for a in each]
        row['all_replications_resolved'] = all(a[k]['precision_pass'] or a[k]['status'] == 'asymptotic_influence' for a in each)
        row['mcse'] = max(row['mcse'], between) if row['all_replications_resolved'] else math.inf
        row['precision_pass'] = bool(np.isfinite(row['mcse']) and row['mcse'] <= mcse_target)
    return pooled


def replicated_weights(log_weights):
    lw = _real_array(log_weights, 2, 'log_weights')
    if lw.shape[0] < 2:
        raise ValueError('Need independent replicated weights')
    each = [weight_summary(a) for a in lw]; pooled = weight_summary(lw.ravel())
    r = len(lw); logz = np.array([a['log_evidence'] for a in each])
    ratios = np.exp(logz-pooled['log_evidence'])
    between = float(np.std(ratios, ddof=1)/np.sqrt(r))
    pooled['pooled_iid_evidence_relative_mcse'] = pooled['evidence_relative_mcse']
    pooled['between_replications_evidence_relative_mcse'] = between
    pooled['evidence_relative_mcse'] = max(pooled['evidence_relative_mcse'], between)
    pooled['log_evidence_delta_mcse'] = pooled['evidence_relative_mcse']
    pooled['replications'] = each
    return pooled


def simultaneous_differences(estimates_a, mcse_a, estimates_b, mcse_b, *, alpha=.05):
    """Approximate two-sided independent MC contrasts, explicit Bonferroni."""
    aa = [np.asarray(v, float).ravel() for v in (estimates_a, mcse_a, estimates_b, mcse_b)]
    if not aa[0].size or any(a.shape != aa[0].shape for a in aa) or not 0 < alpha < 1:
        raise ValueError('Invalid contrast family')
    a, sa, b, sb = aa; z = float(norm.isf(alpha/(2*len(a))))
    sd = np.hypot(sa, sb); finite = np.isfinite(a)&np.isfinite(b)&np.isfinite(sd)&(sd > 0)&(sa >= 0)&(sb >= 0)
    passed = finite&(np.abs(a-b) <= z*sd)
    return {'family_size': len(a), 'alpha': alpha, 'z': z,
        'difference': a-b, 'difference_mcse': sd, 'consistent': passed,
        'resolved': finite, 'all_consistent': bool(passed.all()),
        'method': 'asymptotic_normal_Bonferroni_not_exact'}


def compare_brackets(values, log_weights, brackets, probabilities, reference_cdf,
                     resolution_spread, omission_bound, *, alpha=.05,
                     deterministic_error=.002, quantile_width=.001, mcse_target=.00335):
    """A0d14: forty one-sided checks, no assumed midpoint CDF."""
    x = _real_array(values, 3, 'values'); lw = _real_array(log_weights, 2, 'log_weights')
    br = _real_array(brackets, 3, 'brackets'); p = _real_array(probabilities, 1, 'probabilities')
    ref, spread, omitted = [np.asarray(a, float) for a in (reference_cdf, resolution_spread, omission_bound)]
    if x.shape[:2] != lw.shape or x.shape[2] != 5 or br.shape != (5,4,2) or p.shape != (4,) or any(a.shape != br.shape for a in (ref, spread, omitted)):
        raise ValueError('Invalid 20-bracket reference shapes')
    if not all(np.isfinite(a).all() for a in (x,br,p,ref,spread,omitted)) or np.any(x < 0) or np.any(x > 1) or np.any(br < 0) or np.any(br > 1) or np.any(br[:,:,0] > br[:,:,1]) or np.any(spread < 0) or np.any(omitted < 0) or np.any((p <= 0)|(p >= 1)) or not 0 < alpha < 1:
        raise ValueError('Invalid normalized reference/domain')
    z = float(norm.isf(alpha/40)); rows = []
    for j in range(5):
        cdfs = replicated_cdf(x[:,:,j], lw, br[j].ravel(), mcse_target=mcse_target)
        for k, prob in enumerate(p):
            ends = []
            for side in (0,1):
                c = cdfs[2*k+side]; violation = (c['estimate']-prob)*(1 if side == 0 else -1)
                radius = deterministic_error+z*c['mcse']
                ends.append({'side': 'lower' if side == 0 else 'upper', 'cdf': c,
                    'signed_inequality_violation': float(violation), 'allowed_error': radius,
                    'inequality_consistent': bool(np.isfinite(radius) and violation <= radius),
                    'reference_cdf': float(ref[j,k,side]),
                    'reference_resolution_spread': float(spread[j,k,side]),
                    'reference_omission_bound': float(omitted[j,k,side]),
                    'reference_refinement_pass': bool(spread[j,k,side]+omitted[j,k,side] <= deterministic_error),
                    'difference_MC_minus_quadrature_descriptive': float(c['estimate']-ref[j,k,side])})
            rows.append({'parameter_index': j, 'probability': float(prob), 'ends': ends,
                'horizontal_width': float(br[j,k,1]-br[j,k,0]),
                'horizontal_refinement_pass': bool(br[j,k,1]-br[j,k,0] <= quantile_width+1e-14),
                'bracket_consistent': all(e['inequality_consistent'] for e in ends),
                'mc_precision_pass': all(e['cdf']['precision_pass'] for e in ends)})
    return {'z': z, 'alpha': alpha, 'one_sided_inequalities': 40, 'rows': rows,
        'consistent_brackets': sum(a['bracket_consistent'] for a in rows),
        'brackets_passing_mc_precision': sum(a['mc_precision_pass'] for a in rows),
        'no_midpoint_CDF_assumption': True, 'no_automatic_inference_approval': True}
