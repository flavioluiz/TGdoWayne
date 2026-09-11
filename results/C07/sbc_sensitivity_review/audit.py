"""Independent deterministic audit of the frozen SBC sensitivity candidate.

No PTA truth or posterior files are loaded. All examples are algebraic fixtures.
"""
from __future__ import annotations
import hashlib
import importlib.util
import itertools
import json
import math
from pathlib import Path
import sys
import types

import numpy as np
from scipy import optimize, stats

HERE = Path(__file__).resolve().parent
PACKAGE = types.ModuleType('frozen_sensitivity_review')
PACKAGE.__path__ = [str(HERE/'snapshot')]
sys.modules[PACKAGE.__name__] = PACKAGE
spec = importlib.util.spec_from_file_location(
    PACKAGE.__name__+'.sbc_sensitivity', HERE/'snapshot/sbc_sensitivity.py')
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)


def check(condition, message):
    if not condition:
        raise AssertionError(message)


def exact_ks_direct(values):
    # Independent ECDF formula; no call to candidate order-statistic routine.
    x = np.asarray(values)
    candidates = []
    for t in np.unique(x):
        candidates.extend([abs(np.mean(x <= t)-t), abs(np.mean(x < t)-t)])
    return max(candidates)


def closed_holm(p):
    p = np.asarray(p)
    out = np.zeros(len(p))
    for mask in itertools.product([False, True], repeat=len(p)):
        mask = np.asarray(mask)
        if mask.any():
            local = min(1., mask.sum()*p[mask].min())
            out[mask] = np.maximum(out[mask], local)
    return out


def exact_binomial_probability_order(k, n, probability):
    masses = np.array([math.comb(n, j)*probability**j*(1-probability)**(n-j)
                       for j in range(n+1)])
    return min(1., float(masses[masses <= masses[k]*(1+1e-12)].sum()))


def cp_by_tail_inversion(k, n, alpha):
    low = 0. if k == 0 else optimize.brentq(
        lambda p: stats.binom.sf(k-1, n, p)-alpha/2, 0, 1, xtol=1e-14)
    high = 1. if k == n else optimize.brentq(
        lambda p: stats.binom.cdf(k, n, p)-alpha/2, 0, 1, xtol=1e-14)
    return np.array([low, high])


def run():
    result = {'scope': 'DETERMINISTIC_ALGEBRAIC_FIXTURES_NO_PTA_CAMPAIGN',
              'seed': 707511801, 'checks': {}, 'findings': []}
    rng = np.random.default_rng(result['seed'])
    grid = [0., .2, .5, .8, 1.]
    intervals = [(a, b) for a in grid for b in grid if a <= b]
    boxes = list(itertools.product(intervals, repeat=2))
    boxes += [tuple(intervals[i] for i in rng.integers(len(intervals), size=4))
              for unused in range(100)]
    ks_assignments = 0
    ks_max_excess = 0.
    for box in boxes:
        lower, upper = np.array(box).T
        bound = module.ks_bounds(lower, upper)
        grid_ecdf = np.array([-.1, 0., .1, .2, .5, .8, .9, 1., 1.1])
        gl, gu = module.ecdf_envelope(lower, upper, grid_ecdf)
        for point in itertools.product(*[np.unique([a, (a+b)/2, b]) for a,b in box]):
            x = np.array(point)
            d = exact_ks_direct(x)
            ks_max_excess = max(ks_max_excess,
                bound['statistic_lower_bound']-d, d-bound['statistic_upper_bound'])
            check(bound['statistic_lower_bound'] <= d+1e-15 and
                  d <= bound['statistic_upper_bound']+1e-15, 'KS containment')
            ecdf = (x[:, None] <= grid_ecdf).mean(axis=0)
            check(np.all(gl <= ecdf) and np.all(ecdf <= gu), 'ECDF containment')
            p = stats.kstwo.sf(d, len(x))
            check(bound['pvalue_lower'] <= p+1e-15 <= bound['pvalue_upper']+2e-15,
                  'KS p-value containment')
            ks_assignments += 1
    result['checks']['ks_ecdf'] = dict(boxes=len(boxes), assignments=ks_assignments,
        maximum_roundoff_excess=ks_max_excess, status='PASS',
        known_loose_lower_example=module.ks_bounds([0.], [1.]),
        actual_minimum_statistic_for_that_example=.5)

    holm_vectors = 0
    max_holm_error = 0.
    for unused in range(80):
        low = rng.choice([0., .0001, .01, .04, .2, .5, 1.], 4)
        high = low + rng.uniform(size=4)*(1-low)
        bound = module.holm_sensitivity(low, high)
        for fraction in itertools.product([0., .5, 1.], repeat=4):
            p = low + np.array(fraction)*(high-low)
            actual = closed_holm(p)
            candidate = module.holm_sensitivity(p, p)['holm_lower']
            max_holm_error = max(max_holm_error, np.max(abs(actual-candidate)))
            check(np.all(actual >= bound['holm_lower']-1e-15) and
                  np.all(actual <= bound['holm_upper']+1e-15), 'Holm monotonicity')
            holm_vectors += 1
    result['checks']['holm'] = dict(boxes=80, vectors=holm_vectors,
        maximum_closed_testing_difference=float(max_holm_error), status='PASS')

    coverage_cases = 0
    coverage_assignments = 0
    max_binomial_error = 0.
    for n in [1, 2, 5, 12]:
        for unused in range(10):
            lower = rng.uniform(0, 1, n)
            upper = lower + rng.uniform(size=n)*(1-lower)
            # Include exact thresholds and unresolved intervals.
            if unused == 0:
                lower[:] = 0.; upper[:] = 1.
            if unused == 1:
                lower[:] = .05; upper[:] = .95
            for low, high in [(None, .05), (None, .5), (None, .9), (None, .95), (.05, .95)]:
                out, certain, possible = module.coverage_bounds(lower, upper,
                    upper_probability=high, lower_probability=low, family_size=93)
                for k in range(out['certainly_covered'], out['possibly_covered']+1):
                    p = exact_binomial_probability_order(k, n, out['nominal'])
                    max_binomial_error = max(max_binomial_error,
                        out['pvalue_lower']-p, p-out['pvalue_upper'])
                    check(out['pvalue_lower'] <= p+2e-13 and p <= out['pvalue_upper']+2e-13,
                          'Coverage exact p-value extrema')
                    for alpha, field in [(.05, 'binomial_interval_union'),
                                         (.05/93, 'simultaneous_binomial_interval_union')]:
                        cp = cp_by_tail_inversion(k, n, alpha)
                        check(out[field][0] <= cp[0]+1e-12 and cp[1] <= out[field][1]+1e-12,
                              'Coverage Clopper-Pearson union')
                if n <= 5:
                    choices = []
                    for a,b in zip(lower,upper):
                        c = [a, b, (a+b)/2]
                        for cutoff in [low, high]:
                            if cutoff is not None and a <= cutoff <= b:
                                c.append(cutoff)
                        choices.append(np.unique(c))
                    for x in itertools.product(*choices):
                        x = np.array(x)
                        hit = x <= high if low is None else (x >= low)&(x <= high)
                        check(np.all(~certain | hit) and np.all(~hit | possible),
                              'Coverage classifications with equality')
                        coverage_assignments += 1
                coverage_cases += 1
    result['checks']['coverage'] = dict(cases=coverage_cases,
        assignments=coverage_assignments, maximum_pvalue_roundoff_excess=max_binomial_error,
        status='PASS')

    # Each Boolean event is impossible, ambiguous, or certain.
    states = [(False, False), (False, True), (True, True)]
    paired_cases = paired_assignments = 0
    rectangular_gap_example = None
    for pattern in itertools.product(list(itertools.product(states, states)), repeat=3):
        cx = np.array([s[0][0] for s in pattern]); px = np.array([s[0][1] for s in pattern])
        cy = np.array([s[1][0] for s in pattern]); py = np.array([s[1][1] for s in pattern])
        out = module.paired_binary_bounds(cx, px, cy, py)
        actual_p = []
        for x in itertools.product([False, True], repeat=3):
            x = np.array(x)
            if np.any(cx & ~x) or np.any(x & ~px): continue
            for y in itertools.product([False, True], repeat=3):
                y = np.array(y)
                if np.any(cy & ~y) or np.any(y & ~py): continue
                a, b = int((x & ~y).sum()), int((y & ~x).sum())
                p = 1. if a+b == 0 else exact_binomial_probability_order(a,a+b,.5)
                actual_p.append(p)
                delta = float(x.mean()-y.mean())
                check(out['mean_difference_bounds'][0] <= delta+1e-15 and
                      delta <= out['mean_difference_bounds'][1]+1e-15, 'Paired difference')
                check(out['pvalue_lower'] <= p+1e-15 <= out['pvalue_upper']+2e-15,
                      'McNemar p-value containment')
                paired_assignments += 1
        if (out['pvalue_lower'] < min(actual_p)-1e-14 or
            max(actual_p) < out['pvalue_upper']-1e-14) and rectangular_gap_example is None:
            rectangular_gap_example = dict(pattern=pattern, out=out,
                attainable_pvalue_extrema=[min(actual_p), max(actual_p)])
        paired_cases += 1
    result['checks']['mcnemar'] = dict(cases=paired_cases, assignments=paired_assignments,
        conservative_gap_example=rectangular_gap_example, status='PASS')
    result['checks']['mcnemar']['unattainable_count_example'] = dict(
        certain_x=[True,False], possible_x=[True,True],
        certain_y=[True,False], possible_y=[True,True],
        rectangle_permits=[1,1],
        actual_attainable_counts=[[0,0],[1,0],[0,1]],
        reason='First pair is forced agreement; only the second can be discordant.')

    p=np.array([.1,.5,.9]); s=np.array([.001,np.inf,np.nan]); r=np.array([True,False,False])
    lower,upper,out=module.pit_intervals(p,s,r)
    check(np.array_equal(lower[1:],[0,0]) and np.array_equal(upper[1:],[1,1]), 'Unresolved')
    check(out['family_size']==15000 and out['alpha_mc']==.01 and
          out['deterministic_component']==.002, 'Protocol envelope defaults')
    result['checks']['envelope_defaults'] = dict(status='PASS', output=out,
        lower=lower.tolist(), upper=upper.tolist())

    invalid_family = module.coverage_bounds(np.linspace(.05,.95,20), np.linspace(.05,.95,20),
                                           upper_probability=.9, family_size=.5)[0]
    check(invalid_family['simultaneous_binomial_interval_union'][0] >
          invalid_family['binomial_interval_union'][0], 'Reproduce family-size missing guard')
    result['findings'].append(dict(id='F1', severity='guard_defect',
        finding='coverage_bounds accepts family_size=.5 and returns narrower simultaneous interval',
        example=invalid_family))

    invalid_controls = {}
    for name, kwargs in [
        ('boolean_deterministic',dict(deterministic_component=True)),
        ('array_alpha',dict(alpha_mc=np.array([.01]))),
        ('array_deterministic',dict(deterministic_component=np.array([.002]))),
    ]:
        try:
            _,_,out=module.pit_intervals([.5],[.001],[True], **kwargs)
            invalid_controls[name] = {'accepted': True,
                'metadata_types': {k:type(v).__name__ for k,v in out.items()}}
        except Exception as exc:
            invalid_controls[name] = {'accepted':False, 'exception':type(exc).__name__}
    result['findings'].append(dict(id='F2', severity='guard_contract',
        finding='Numeric scalar controls are not uniformly strict; shape-1 arrays can leak into metadata',
        examples=invalid_controls))
    allowed = np.array([[.026,.9],[.06,.01]])
    result['findings'].append(dict(id='F3', severity='interpretation',
        finding='The lower Holm corner means rejection not excluded by marginal bounds; it need not be jointly attainable under extra dependence constraints.',
        feasible_pvalue_vectors=allowed.tolist(),
        actual_adjusted_pvalues=[closed_holm(p).tolist() for p in allowed],
        marginal_lower=allowed.min(axis=0).tolist(),
        marginal_upper=allowed.max(axis=0).tolist(),
        lower_corner_adjusted=closed_holm(allowed.min(axis=0)).tolist(),
        first_hypothesis_rejected_for_any_feasible_vector=False,
        first_hypothesis_rejected_at_marginal_lower_corner=True))
    result['sources']={str(p.relative_to(HERE)): hashlib.sha256(p.read_bytes()).hexdigest()
                       for p in sorted((HERE/'snapshot').glob('*.py'))}
    result['script_sha256']=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    (HERE/'results/audit.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'checks': result['checks'], 'findings': result['findings']},indent=2))


if __name__=='__main__':run()
