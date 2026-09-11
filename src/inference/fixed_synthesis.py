"""Conditional fixed96 summaries; no uniformity test or posterior calculation."""
from pathlib import Path
import itertools
import numpy as np
from scipy.stats import norm
from inference.campaign_io import read_json, sha256
from inference.campaign_archive import verify_archive_receipt
from inference.diagnostics import clopper_pearson
from inference.sbc_sensitivity import pit_intervals, ecdf_envelope

PIT = np.array([0, 5, 10, 15, 20, 25])
PROBS = np.array([.05, .5, .9, .95])
PARAMETERS = ['u', 'log10_Agw', 'gamma_gw', 'log10_Ar', 'log10_EFAC']
SCENARIOS = ['mass_zero_signal_present', 'near_kinematic_edge', 'no_gravitational_signal']
SCHEMA = 'C07_FIXED_MASKED_IID_DIAGNOSTICS_v2_OPERATIONAL'
SCOPE = 'FIXED_TRUTH96_NOT_SBC'


def check_protocol(config, numerical, scientific):
    expected = dict(population_targets=96, models=['A0_CN'], levels=[16384, 65536],
                    independent_replications=4, cdf_mcse_target=.00335,
                    alpha_replicate_family=.05, alpha_refinement_family=.05,
                    global_replicate_contrasts=19584, global_refinement_contrasts=672,
                    maximum_saturated_target_weight=1e-12)
    if any(numerical.get(k) != v for k, v in expected.items()):
        raise ValueError('Frozen fixed96 numerical protocol differs.')
    if (config.get('protocol') != 'C07_FIXED96_SYNTHESIS_v1_BEFORE_POSTERIORS' or
            config.get('population_targets') != 96 or config.get('models') != ['A0_CN'] or
            config.get('discard_realizations') is not False or config.get('pointwise_cp_alpha') != .05 or
            config.get('quantile_probabilities') != PROBS.tolist() or
            config.get('numerical_sensitivity') != dict(family_size=576, alpha_mc=.01,
                deterministic_component=.002, cdf_mcse_target=.00335)):
        raise ValueError('Prospective fixed synthesis configuration differs.')
    if (scientific.get('protocol_id') != 'C07-fixed-scenarios-v1-before-generation' or
            scientific.get('repetitions_per_scenario') != 32 or scientific.get('models') != ['A0_CN'] or
            scientific.get('parameter_order') != PARAMETERS or
            [r['id'] for r in scientific['scenarios']] != SCENARIOS or
            scientific.get('quantile_probabilities') != PROBS.tolist()):
        raise ValueError('The original scientific fixed-scenario protocol differs.')


def arr(a, key, shape, kind=None, finite=False):
    v = np.asarray(a[key])
    if v.shape != shape or (kind and v.dtype.kind not in kind) or (finite and not np.isfinite(v).all()):
        raise ValueError('Shape/type/finitude mismatch: ' + key)
    return v


def masks(target):
    defined = np.ones(6, bool)
    if target >= 64:
        defined[[0, 1, 2, 5]] = False
    structural = np.zeros(6, bool)
    structural[0] = target < 32
    applicable = np.ones(26, bool)
    applicable[PIT] = defined
    exact = np.zeros(26, bool)
    exact[PIT] = structural
    return defined, structural, applicable, exact


def contrast_specifications(target):
    _, _, applicable, exact = masks(target)
    numerical = applicable & ~exact
    pairs = list(itertools.combinations(range(4), 2))
    reps = [[level, measure, a, b] for level, candidates in
            [(0, PIT), (1, range(26))] for measure in
            [int(j) for j in candidates if numerical[j]] + [26] for a, b in pairs]
    refinement = [int(j) for j in PIT if numerical[j]] + [26]
    return np.asarray(reps, int), np.asarray(refinement, int)


def check_numeric(a, target, truth, truth_logl, bounds, protocol):
    for k, v in [('target', target), ('datum', target), ('model_index', 0),
                 ('scenario_index', target // 32), ('replicate_within_scenario', target % 32)]:
        if arr(a, k, (), 'iu').item() != v:
            raise ValueError('Numeric target identity differs: ' + k)
    defined, structural, applicable, exact = masks(target)
    unit = (truth - bounds[:, 0]) / np.diff(bounds, axis=1)[:, 0]
    for k, expected in [('truth_physical', truth), ('truth_unit', unit),
                         ('truth_defined', defined[:5]), ('pit_applicable', defined),
                         ('pit_structural_exact', structural), ('cdf_applicable', applicable),
                         ('cdf_structural_exact', exact), ('cdf_numerically_evaluated', applicable & ~exact)]:
        value = arr(a, k, expected.shape, 'b' if expected.dtype.kind == 'b' else 'f')
        if not np.array_equal(value, expected, equal_nan=True):
            raise ValueError('Truth/mask identity differs: ' + k)
    if (arr(a, 'truth_log_likelihood_defined', (), 'b').item() != defined[5] or
            not np.array_equal(arr(a, 'truth_log_likelihood', (), 'f'), truth_logl, equal_nan=True)):
        raise ValueError('Undefined logL must be NaN; defined logL must match generation.')
    if not np.array_equal(arr(a, 'probabilities', (4,), 'f', True), PROBS):
        raise ValueError('Quantile probabilities changed.')
    q = arr(a, 'quantiles_unit', (5, 4), 'f', True)
    if (np.any((q < 0) | (q > 1)) or np.any(np.diff(q, axis=1) < 0) or
            not np.array_equal(arr(a, 'quantiles_physical', (5, 4), 'f', True),
                               bounds[:, 0, None] + np.diff(bounds, axis=1) * q)):
        raise ValueError('Quantile support/order/units changed.')
    estimates = arr(a, 'cdf_estimates_by_level', (2, 26), 'f')
    errors = arr(a, 'cdf_mcse_by_level', (2, 26), 'f')
    numeric = applicable & ~exact
    if (not np.isnan(estimates[:, ~applicable]).all() or not np.isnan(errors[:, ~applicable]).all() or
            not np.isfinite(estimates[:, applicable]).all() or
            np.any((estimates[:, applicable] < 0) | (estimates[:, applicable] > 1)) or
            not np.all(estimates[:, exact] == 0) or not np.all(errors[:, exact] == 0) or
            np.isnan(errors[:, numeric]).any() or np.any(errors[:, numeric] <= 0)):
        raise ValueError('CDF values/uncertainties violate applicability or structural rules.')
    resolution = np.isfinite(errors) & applicable[None, :]
    precision = resolution & (errors <= protocol['cdf_mcse_target'])
    for key, expected in [('cdf_resolved_by_level', resolution), ('cdf_precision_by_level', precision),
            ('pit', estimates[1, PIT]), ('pit_mcse', errors[1, PIT]),
            ('pit_resolved', resolution[1, PIT]), ('pit_precision_pass', precision[1, PIT])]:
        actual = arr(a, key, expected.shape, 'b' if expected.dtype.kind == 'b' else 'f')
        if not np.array_equal(actual, expected, equal_nan=True):
            raise ValueError('CDF value/flag inconsistency: ' + key)
    indices = np.array([[5*j+k for k in range(1, 5)] for j in range(5)])
    for key, expected in [('cut_cdf', estimates[1, indices]), ('cut_mcse', errors[1, indices]),
                          ('cut_resolved', resolution[1, indices]), ('cut_precision_pass', precision[1, indices])]:
        if not np.array_equal(arr(a, key, expected.shape, 'b' if expected.dtype.kind == 'b' else 'f'), expected):
            raise ValueError('Cut/full-CDF inconsistency: ' + key)
    specs, refspec = contrast_specifications(target)
    for key, expected in [('replication_specification', specs), ('refinement_specification', refspec)]:
        if not np.array_equal(arr(a, key, expected.shape, 'iu'), expected):
            raise ValueError('Missing/duplicate/undefined contrast: ' + key)
    for prefix, size, family in [('replication', len(specs), 19584), ('refinement', len(refspec), 672)]:
        difference = arr(a, prefix + '_difference', (size,), 'f', True)
        error = arr(a, prefix + '_mcse', (size,), 'f')
        if np.isnan(error).any() or np.any(error < 0):
            raise ValueError('Invalid contrast MCSE.')
        resolved = np.isfinite(error) & (error > 0)
        passed = resolved & (abs(difference) <= norm.isf(.05/(2*family))*error)
        for suffix, expected in [('resolved', resolved), ('pass', passed)]:
            if not np.array_equal(arr(a, prefix+'_'+suffix, (size,), 'b'), expected):
                raise ValueError('Contrast flags contradict frozen multiplicity.')
    arr(a, 'weight_deletion_guard_by_level', (2,), 'b')
    saturated = arr(a, 'saturated_weight', (2, 4), 'f', True)
    if np.any((saturated < 0) | (saturated > 1)):
        raise ValueError('Invalid saturation weight.')
    return resolved_by_function(a)


def resolved_by_function(a):
    """Structural proof is separate; other functions require their own MC checks."""
    applicable = np.asarray(a['pit_applicable'])
    structural = np.asarray(a['pit_structural_exact'])
    reps = np.asarray(a['replication_specification'])
    refs = np.asarray(a['refinement_specification'])
    rep_pass = np.asarray(a['replication_pass'])
    ref_pass = np.asarray(a['refinement_pass'])
    common = (np.asarray(a['weight_deletion_guard_by_level']).all() and
              (np.asarray(a['saturated_weight']) <= 1e-12).all() and
              rep_pass[reps[:, 1] == 26].all() and ref_pass[refs == 26].all())
    resolved = structural.copy()
    for j, index in enumerate(PIT):
        if not applicable[j] or structural[j]:
            continue
        selected, selected_ref = reps[:, 1] == index, refs == index
        if selected.sum() != 12 or selected_ref.sum() != 1:
            raise ValueError('Two levels of six PIT contrasts and one refinement required.')
        resolved[j] = bool(common and a['pit_resolved'][j] and a['pit_precision_pass'][j]
                           and rep_pass[selected].all() and ref_pass[selected_ref].all())
    return resolved


def conditional_coverage(pit, lower, upper, *, central=False, structural=False):
    """No null p-value: binomial intervals are pointwise conditional stress summaries."""
    p, a, b = np.asarray(pit), np.asarray(lower), np.asarray(upper)
    if (p.shape != (32,) or a.shape != p.shape or b.shape != p.shape or
            not np.isfinite([p, a, b]).all() or np.any((p < 0) | (p > 1)) or
            np.any(a < 0) or np.any(b > 1) or np.any(a > b)):
        raise ValueError('Exactly32 finite ordered conditional intervals required.')
    nominal = (p >= .05) & (p <= .95) if central else p <= .9
    certain = (a >= .05) & (b <= .95) if central else b <= .9
    possible = (b >= .05) & (a <= .95) if central else a <= .9
    k, kmin, kmax = int(nominal.sum()), int(certain.sum()), int(possible.sum())
    return dict(n=32, calculated_count=k, calculated_fraction=k/32,
        pointwise_cp95=clopper_pearson(k, 32), certainly_covered=kmin, possibly_covered=kmax,
        coverage_fraction_sensitivity=[kmin/32, kmax/32],
        pointwise_cp95_union_over_count_range=[clopper_pearson(kmin, 32)[0], clopper_pearson(kmax, 32)[1]],
        approximate_numerical_sensitivity_not_exact_confidence=True,
        interval='central_equal_tail_90' if central else 'prior_lower_bound_to_upper90',
        structural_population_coverage=(0. if central else 1.) if structural else None,
        structural_exception=bool(structural), no_test_of_universal_nominal_coverage=True)


def synthesize(arrays, config):
    p, s, applicable, structural, resolved = [np.asarray(arrays[k]) for k in
        ['pit', 'pit_mcse', 'pit_applicable', 'pit_structural_exact', 'resolved_for_function']]
    if any(v.shape != (96, 6) for v in (p, s, applicable, structural, resolved)):
        raise ValueError('All96 targets and six PIT slots must remain.')
    expected = [masks(t)[:2] for t in range(96)]
    if (not np.array_equal(applicable, [a for a, _ in expected]) or
            not np.array_equal(structural, [b for _, b in expected]) or
            np.any(resolved & ~applicable) or not resolved[structural].all()):
        raise ValueError('Fixed96 masks or structural resolution differ.')
    lo, hi = np.full(p.shape, np.nan), np.full(p.shape, np.nan)
    numeric = applicable & ~structural
    lower, upper, numerical = pit_intervals(p[numeric], s[numeric], resolved[numeric],
        family_size=576, alpha_mc=.01, deterministic_component=.002)
    lo[numeric], hi[numeric] = lower, upper
    lo[structural] = hi[structural] = 0.
    grid = np.linspace(0, 1, 101)
    rows, quantile_rows, scenarios = [], [], []
    for scenario, name in enumerate(SCENARIOS):
        sl = slice(32*scenario, 32*(scenario+1))
        scenarios.append(dict(id=name, targets=list(range(32*scenario, 32*(scenario+1))), n=32,
            applicable_pits=int(applicable[sl].sum()), structural_pits=int(structural[sl].sum()),
            numerically_resolved_nonstructural_pits=int((resolved[sl] & ~structural[sl]).sum()),
            unresolved_nonstructural_pits=int((applicable[sl] & ~resolved[sl]).sum())))
        for j, parameter in enumerate(PARAMETERS + ['logL_at_truth']):
            if not applicable[sl, j].all():
                rows.append(dict(scenario=name, parameter=parameter, applicable=False,
                    reason='No generating truth for this signal parameter/statistic; all32 retained as masked.'))
                continue
            ecdf_lo, ecdf_hi = ecdf_envelope(lo[sl, j], hi[sl, j], grid)
            row = dict(scenario=name, parameter=parameter, applicable=True, n=32,
                target_ids=list(range(32*scenario, 32*(scenario+1))),
                resolved_count=int(resolved[sl, j].sum()), structural_count=int(structural[sl, j].sum()),
                calculated_pit_quantiles=np.quantile(p[sl, j], [.05, .5, .95]),
                ecdf_lower=ecdf_lo, ecdf_upper=ecdf_hi,
                conditional_distribution_not_expected_to_be_uniform=True)
            if j < 5:
                row['upper90'] = conditional_coverage(p[sl, j], lo[sl, j], hi[sl, j],
                    structural=bool(structural[sl, j].all()))
                row['central90'] = conditional_coverage(p[sl, j], lo[sl, j], hi[sl, j], central=True,
                    structural=bool(structural[sl, j].all()))
            rows.append(row)
        for j, parameter in enumerate(PARAMETERS):
            q = arrays['quantiles_physical'][sl, j]
            quantile_rows.append(dict(scenario=name, parameter=parameter,
                probabilities=PROBS, across32_quantiles_min_median_max=np.stack([q.min(0), np.median(q, 0), q.max(0)]),
                precise_independent_cut_counts=np.asarray(arrays['cut_precision_pass'][sl, j]).sum(0),
                descriptive_only=True, no_recovery_bias_if_truth_undefined=not bool(applicable[sl, j].all()),
                CDF_precision_does_not_certify_horizontal_quantile_error=True))
    report = dict(scope='FIXED96_CONDITIONAL_STRESS_SUMMARY_NOT_SBC', population_targets=96,
        models=['A0_CN'], scenarios=scenarios, functions=rows, quantiles=quantile_rows,
        numerical_sensitivity=numerical, all_ids_retained=True, no_KS_or_uniformity_test=True,
        pointwise_CP_only_no_familywise_claim=True, no_Bayes_factors=True,
        numerical_failures_do_not_trigger_target_selection=True,
        sensitivity_is_conditional_on_valid_asymptotic_MC_and_deterministic_error_estimates=True)
    return report, dict(pit_lower=lo, pit_upper=hi, ecdf_grid=grid)


def safe_child(root, name):
    relative = Path(name)
    path = (Path(root)/relative).resolve()
    if relative.is_absolute() or Path(root).resolve() not in path.parents:
        raise ValueError('Unsafe relative artifact path.')
    return path


def verify_sources(campaign, plan):
    runtime = campaign/'provenance'/plan['identity']
    manifest = read_json(runtime/'manifest.json')
    if manifest['identity'] != plan['identity'] or manifest['input_sha256'] != plan['input_sha256']:
        raise RuntimeError('Runtime provenance identity mismatch.')
    for name, digest in manifest['source_sha256'].items():
        base = runtime/name.replace('.', '/')
        paths = list(base.parent.glob(base.name+'.*'))
        if len(paths) != 1 or sha256(paths[0]) != digest:
            raise RuntimeError('Frozen producer source missing/changed: '+name)
    driver = campaign/'driver_provenance'/plan['driver_identity']
    for name, digest in plan['driver_source_sha256'].items():
        if sha256(driver/(name+'.py')) != digest:
            raise RuntimeError('Frozen masked driver source changed: '+name)
    for name in ['protocol', 'generation']:
        if sha256(driver/(name+'.json')) != plan['extra_input_sha256'][name]:
            raise RuntimeError('Frozen fixed diagnostic input changed: '+name)
    return manifest


def evidence_manifest(path):
    record = read_json(path)
    entries = record.get('entries', [])
    roles = []
    for entry in entries:
        p = Path(entry['path'])
        p = p if p.is_absolute() else Path(path).resolve().parent/p
        if not p.is_file() or sha256(p) != entry['sha256']:
            raise RuntimeError('Independent numerical evidence changed.')
        roles.append(entry['role'])
    if not {'orf_interpolation', 'likelihood_kernel', 'external_posterior_reference'} <= set(roles):
        raise ValueError('ORF/kernel/reference evidence roles required.')
    return dict(record, manifest_sha256=sha256(path),
        integrity_does_not_assert_universal_fixed_scenario_validation=True)


def load_campaign(campaign, experiment, data, generation, numerical_protocol, scientific_protocol,
                  synthesis_config, evidence):
    campaign = Path(campaign).resolve()
    cfg, exp, gen, num, sci = [read_json(p) for p in
        [synthesis_config, experiment, generation, numerical_protocol, scientific_protocol]]
    check_protocol(cfg, num, sci)
    hashes = {k: sha256(v) for k, v in dict(data=data, experiment=experiment, generation=generation,
        protocol=numerical_protocol, scientific_protocol=scientific_protocol, synthesis_config=synthesis_config).items()}
    for name, key in [('data', 'data'), ('experiment', 'experiment'), ('generation', 'generation'),
                      ('numerical_protocol', 'protocol'), ('scientific_protocol', 'scientific_protocol')]:
        if cfg['sources'][name]['sha256'] != hashes[key]:
            raise RuntimeError('Frozen synthesis input differs: '+name)
    plan = read_json(campaign/'campaign_plan.json')
    complete = read_json(campaign/'campaign_complete.json')
    if (plan.get('scope') != SCOPE or plan.get('all_target_ids') != list(range(96)) or
            plan.get('models') != ['A0_CN'] or complete.get('scope') != SCOPE or
            complete.get('status') != 'ALL_TARGET_PRODUCTS_ARCHIVED' or complete.get('targets') != list(range(96)) or
            complete.get('driver_identity') != plan['driver_identity'] or
            plan['input_sha256']['data'] != hashes['data'] or plan['input_sha256']['experiment'] != hashes['experiment'] or
            plan['extra_input_sha256'] != dict(protocol=hashes['protocol'], truth_data=hashes['data'], generation=hashes['generation'])):
        raise ValueError('Complete exact96 A0 campaign with matching fixed provenance required.')
    source_manifest = verify_sources(campaign, plan)
    if (exp['n_realizations'] != 96 or exp['parameters'] != PARAMETERS or
            gen['status'] != 'FIXED_DATA_GENERATED_NOT_POSTERIOR_INFERENCE' or gen['data_sha256'] != hashes['data'] or
            gen['preflight']['experiment_sha256'] != hashes['experiment'] or
            gen['absent_signal_covariance_exactly_zero'] is not True):
        raise ValueError('Fixed generation/configuration differs.')
    proof = evidence_manifest(evidence)
    bounds = np.asarray(exp['prior']['bounds'], float)
    with np.load(data, allow_pickle=False) as f:
        truth, ll = f['truth'], f['log_likelihood_at_truth']
        expected_defined = np.array([masks(t)[0][:5] for t in range(96)])
        if (truth.shape != (96, 5) or ll.shape != (96,) or
                not np.array_equal(f['truth_defined'], expected_defined) or
                not np.array_equal(f['log_likelihood_at_truth_defined'], np.arange(96) < 64) or
                not np.array_equal(f['structural_lower_boundary_pit'],
                                   np.array([masks(t)[1][:5] for t in range(96)])) or
                not np.array_equal(f['target'], np.arange(96)) or
                not np.array_equal(f['scenario_index'], np.repeat(np.arange(3), 32)) or
                not np.array_equal(f['replicate_within_scenario'], np.tile(np.arange(32), 3))):
            raise ValueError('Fixed generation mask/target inventory changed.')
    expected_truth = np.repeat(np.array([[np.nan if v is None else v for v in s['truth']]
                                        for s in sci['scenarios']]), 32, axis=0)
    if (not np.array_equal(truth, expected_truth, equal_nan=True) or bounds.shape != (5, 2) or
            not np.isfinite(bounds).all() or np.any(np.diff(bounds, axis=1) <= 0) or
            not np.array_equal(bounds[0], [0, 1]) or not np.isfinite(ll[:64]).all() or not np.isnan(ll[64:]).all()):
        raise ValueError('Scientific fixed truths or prior support differ.')
    paths = sorted((campaign/'diagnostics').glob('diagnostic_target_*.json'))
    if len(paths) != 96 or len(list((campaign/'diagnostics').glob('diagnostic_target_*.npz'))) != 96:
        raise ValueError('Missing/extra targets; no intersection or approved-subset selection.')
    arrays = {k: [] for k in ['pit', 'pit_mcse', 'pit_applicable', 'pit_structural_exact',
        'resolved_for_function', 'quantiles_unit', 'quantiles_physical', 'cut_precision_pass']}
    inventory, seen = [], set()
    for path in paths:
        meta = read_json(path)
        t = meta['target']
        if type(t) is not int or not 0 <= t < 96 or t in seen or path.name != f'diagnostic_target_{t:06d}.json':
            raise ValueError('Duplicate/noninteger/unplanned target identity.')
        if (meta['status'] != 'NUMERICAL_DIAGNOSTICS_COMPLETE' or meta['schema'] != SCHEMA or meta['scope'] != SCOPE or
                meta['identity'] != plan['identity'] or meta['datum'] != t or meta['model'] != 'A0_CN' or
                meta.get('raw_release_authorized') is not False):
            raise ValueError('Wrong diagnostic identity/status/masked schema.')
        producer_path = campaign/'production'/f'target_{t:06d}.json'
        producer = read_json(producer_path)
        inputs = meta['diagnostic_inputs']
        if (producer['status'] != 'IID_COMPLETE_AWAITING_DIAGNOSTICS' or producer['identity'] != plan['identity'] or
                producer['target'] != t or producer['datum'] != t or producer['model'] != 'A0_CN' or
                producer['input_sha256'] != plan['input_sha256'] or producer.get('uses_truth') is not False or
                inputs['producer_report_sha256'] != sha256(producer_path) or
                inputs['truth_data_sha256'] != hashes['data'] or inputs['generation_sha256'] != hashes['generation'] or
                inputs['protocol_sha256'] != hashes['protocol'] or meta['proposal_sha256'] != producer['proposal_sha256']):
            raise RuntimeError('Producer/generation/protocol/input digest mismatch.')
        for name, digest in inputs['source_sha256'].items():
            expected = (plan['driver_source_sha256']['fixed_masked_reader'] if name == 'fixed_diagnostics'
                        else source_manifest['source_sha256'].get(name, plan['driver_source_sha256'].get(name)))
            if digest != expected:
                raise RuntimeError('Masked diagnostic source digest mismatch.')
        if set(inputs['source_sha256']) != {'fixed_diagnostics', 'iid_optimized', 'iid_diagnostics', 'campaign_diagnostic_io', 'campaign_io'}:
            raise ValueError('Incomplete masked diagnostic source inventory.')
        reps = producer['replicates']
        expected = {(n, r) for n in num['levels'] for r in range(4)}
        if (producer['levels'] != num['levels'] or meta['levels'] != num['levels'] or len(reps) != 8 or
                {(r['level'], r['replicate']) for r in reps} != expected or
                meta['raw_sha256'] != {r['raw_file']: r['raw_sha256'] for r in reps}):
            raise ValueError('Two independent levels/four-replica raw hashes required.')
        numeric = safe_child(path.parent, meta['numeric_file'])
        if numeric.name != f'diagnostic_target_{t:06d}.npz' or sha256(numeric) != meta['numeric_sha256']:
            raise RuntimeError('Numeric path/digest mismatch.')
        with np.load(numeric, allow_pickle=False) as f:
            a = {k: f[k] for k in f.files}
        resolved = check_numeric(a, t, truth[t], ll[t], bounds, num)
        expected_flags = dict(cdf_precision_pass=bool(a['cdf_precision_by_level'][1, a['cdf_applicable']].all()),
            pooled_weight_guard_pass=bool(a['weight_deletion_guard_by_level'].all()),
            saturation_guard_pass=bool((a['saturated_weight'] <= 1e-12).all()),
            replication_pass=bool(a['replication_pass'].all()), refinement_pass=bool(a['refinement_pass'].all()))
        if any(meta['summary'].get(k) is not v for k, v in expected_flags.items()):
            raise ValueError('Summary flags contradict numeric arrays.')
        for level, n in enumerate(num['levels']):
            rep_rows = sorted([r for r in reps if r['level'] == n], key=lambda r: r['replicate'])
            if not np.array_equal(a['saturated_weight'][level],
                                  [r['saturated_normalized_target_weight'] for r in rep_rows]):
                raise ValueError('Saturation fractions differ from production.')
        receipt = verify_archive_receipt(campaign/'production'/f'archive_receipt_target_{t:06d}.json',
            campaign/'production', plan['identity'], t, meta['raw_sha256'])
        artifact_hashes = {r['role']: r['sha256'] for r in receipt['artifacts']}
        if (artifact_hashes['producer'] != sha256(producer_path) or artifact_hashes['diagnostic'] != sha256(path) or
                artifact_hashes['numeric'] != meta['numeric_sha256'] or artifact_hashes['proposal'] != meta['proposal_sha256']):
            raise RuntimeError('Archived and live producer/diagnostic/numeric/proposal differ.')
        expected_status = 'RECORDED_NUMERICAL_CHECKS_PASSED' if all(expected_flags.values()) else 'NUMERICALLY_UNRESOLVED'
        if receipt['numerical_flags'] != expected_flags or receipt['numerical_status'] != expected_status:
            raise ValueError('Archived numerical flags differ from retained diagnostics.')
        for k in arrays:
            arrays[k].append(resolved if k == 'resolved_for_function' else a[k])
        seen.add(t)
        inventory.append(dict(target=t, scenario=t//32, replicate=t%32, diagnostic_sha256=sha256(path),
            producer_sha256=sha256(producer_path), numeric_sha256=meta['numeric_sha256'],
            archive_sha256=sha256(campaign/'production'/f'archive_receipt_target_{t:06d}.json'),
            numerical_status=receipt['numerical_status'], numerical_flags=receipt['numerical_flags']))
    if seen != set(range(96)):
        raise ValueError('Incomplete exact96 inventory.')
    if complete['numerically_unresolved_targets'] != [r['target'] for r in inventory
                                                    if r['numerical_status'] == 'NUMERICALLY_UNRESOLVED']:
        raise ValueError('Complete campaign omitted or changed numerical failures.')
    arrays = {k: np.asarray(v) for k, v in arrays.items()}
    arrays.update(targets=np.arange(96), truth=truth, bounds=bounds, probabilities=PROBS)
    provenance = dict(input_sha256=hashes, runtime_identity=plan['identity'], driver_identity=plan['driver_identity'],
        campaign_complete_sha256=sha256(campaign/'campaign_complete.json'), validation_evidence=proof,
        inventory=inventory, source_manifest_sha256=sha256(campaign/'provenance'/plan['identity']/'manifest.json'),
        all96_ids_retained=True)
    return arrays, cfg, provenance
