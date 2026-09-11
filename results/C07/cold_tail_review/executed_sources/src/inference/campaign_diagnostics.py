"""Compact per-target diagnostics; deliberately distinct from campaign approval."""
from pathlib import Path
from time import perf_counter
import itertools
import numpy as np
from .campaign_io import read_json, sha256, write_json_new, write_npz_new, positive_int
from .campaign_diagnostic_io import load_target_levels, load_truth_for_diagnostics
from .iid_optimized import TargetIIDContext
from .iid_diagnostics import simultaneous_differences, json_safe

PROBABILITIES = np.array([.05, .5, .9, .95])
PIT_INDICES = np.array([0, 5, 10, 15, 20, 25])
PAIRS = tuple(itertools.combinations(range(4), 2))


def numerical_statistics(low, high, truth_unit, truth_logl, bounds, *,
                         population_targets=2500, mcse_target=.00335,
                         alpha_replicates=.05, alpha_refinement=.05):
    """Compute v1 SNIS formulas, retaining every indicator and numerical failure.

    The truth is consumed only by this explicitly separate diagnostic function.
    Low-level quantiles fix thresholds before evaluating high-level CDF errors.
    Neither posterior resampling nor a binomial ESS substitution is used.
    """
    count = positive_int(population_targets, 'population target count')
    bounds = np.asarray(bounds, float); truth = np.asarray(truth_unit, float)
    if bounds.shape != (5, 2) or truth.shape != (5,) or not np.isfinite(bounds).all() or not np.isfinite(truth).all() or not np.isfinite(truth_logl):
        raise ValueError('Finite bounds, five truths and truth log likelihood required.')
    if np.any(bounds[:, 1] <= bounds[:, 0]) or np.any((truth < 0) | (truth > 1)):
        raise ValueError('Truth/bounds outside the registered prior domain.')
    contexts = []
    for data in (low, high):
        x = np.asarray(data['x_unit']); lw = np.asarray(data['log_weights']); ll = np.asarray(data['log_likelihood'])
        if x.shape != lw.shape+(5,) or lw.ndim != 2 or lw.shape[0] != 4 or ll.shape != lw.shape or not np.isfinite(x).all() or np.any((x < 0) | (x > 1)):
            raise ValueError('Four aligned IID replicates in the unit prior cube required.')
        contexts.append(TargetIIDContext(lw))
    if high['log_weights'].shape[1] <= low['log_weights'].shape[1]:
        raise ValueError('Two increasing independent IID levels required.')
    cuts = np.array([contexts[0].quantiles(low['x_unit'][:, :, j], PROBABILITIES) for j in range(5)])
    quantiles = np.array([contexts[1].quantiles(high['x_unit'][:, :, j], PROBABILITIES) for j in range(5)])
    levels = []; weights = []; contrasts = []; specifications = []
    for level, (data, context) in enumerate(zip((low, high), contexts)):
        rows = []
        for j in range(5):
            rows.extend(context.cdf(data['x_unit'][:, :, j], np.r_[truth[j], cuts[j]], mcse_target=mcse_target))
        rows.extend(context.cdf(data['log_likelihood'], [truth_logl], mcse_target=mcse_target))
        weight = context.weights(); levels.append(rows); weights.append(weight)
        selected = PIT_INDICES if level == 0 else range(26)
        for measure in selected:
            row = rows[measure]
            for a, b in PAIRS:
                contrasts.append([row['replication_estimates'][a], row['replication_mcse'][a], row['replication_estimates'][b], row['replication_mcse'][b]])
                specifications.append([level, measure, a, b])
        for a, b in PAIRS:
            wa, wb = weight['replications'][a], weight['replications'][b]
            contrasts.append([wa['log_evidence'], wa['log_evidence_delta_mcse'], wb['log_evidence'], wb['log_evidence_delta_mcse']])
            specifications.append([level, 26, a, b])
    refinement = []
    for j in PIT_INDICES:
        a, b = levels[0][j], levels[1][j]
        refinement.append([a['estimate'], a['mcse'], b['estimate'], b['mcse']])
    a, b = weights
    refinement.append([a['log_evidence'], a['log_evidence_delta_mcse'], b['log_evidence'], b['log_evidence_delta_mcse']])
    if len(contrasts) != 204 or len(refinement) != 7:
        raise AssertionError('The frozen contrast family count changed.')
    rep = simultaneous_differences(*np.asarray(contrasts).T, alpha=alpha_replicates/count)
    refine = simultaneous_differences(*np.asarray(refinement).T, alpha=alpha_refinement/count)
    estimates = np.array([[r['estimate'] for r in level] for level in levels])
    mcse = np.array([[r['mcse'] for r in level] for level in levels])
    resolved = np.isfinite(mcse)
    precision = np.array([[r['precision_pass'] for r in level] for level in levels], bool)
    cut_indices = np.array([[j*5+k for k in range(1,5)] for j in range(5)])
    output = dict(
        probabilities=PROBABILITIES.copy(), pit=estimates[1,PIT_INDICES],
        pit_mcse=mcse[1,PIT_INDICES], pit_resolved=resolved[1,PIT_INDICES], pit_precision_pass=precision[1,PIT_INDICES],
        quantiles_unit=quantiles, quantiles_physical=bounds[:,0,None]+np.diff(bounds,axis=1)*quantiles,
        independent_cuts_unit=cuts, cut_cdf=estimates[1,cut_indices], cut_mcse=mcse[1,cut_indices],
        cut_resolved=resolved[1,cut_indices], cut_precision_pass=precision[1,cut_indices],
        cdf_estimates_by_level=estimates, cdf_mcse_by_level=mcse,
        cdf_resolved_by_level=resolved, cdf_precision_by_level=precision,
        cdf_replicate_estimates=np.array([[r['replication_estimates'] for r in level] for level in levels]),
        cdf_replicate_mcse=np.array([[r['replication_mcse'] for r in level] for level in levels]),
        cdf_positive_weight_counts=np.array([[r['positive_weight_counts_below_above'] for r in level] for level in levels]),
        log_evidence=np.asarray(weights[1]['log_evidence']), log_evidence_mcse=np.asarray(weights[1]['log_evidence_delta_mcse']),
        log_evidence_by_level=np.array([w['log_evidence'] for w in weights]),
        log_evidence_mcse_by_level=np.array([w['log_evidence_delta_mcse'] for w in weights]),
        log_evidence_by_replicate=np.array([[r['log_evidence'] for r in w['replications']] for w in weights]),
        log_evidence_mcse_by_replicate=np.array([[r['log_evidence_delta_mcse'] for r in w['replications']] for w in weights]),
        weight_ess=np.asarray(weights[1]['weight_ess_concentration_only']),
        maximum_weight=np.asarray(weights[1]['maximum_normalized_weight']),
        single_deletion_bound=np.asarray(weights[1]['single_deletion_cdf_bound']),
        weight_deletion_guard_by_level=np.array([w['single_deletion_guard_pass'] for w in weights]),
        replication_specification=np.asarray(specifications, int),
        replication_difference=rep['difference'], replication_mcse=rep['difference_mcse'],
        replication_resolved=rep['resolved'], replication_pass=rep['consistent'],
        refinement_difference=refine['difference'], refinement_mcse=refine['difference_mcse'],
        refinement_resolved=refine['resolved'], refinement_pass=refine['consistent'],
    )
    summary = dict(
        mcse_target=mcse_target, high_cdf_precision_pass=int(precision[1].sum()), high_cdf_count=26,
        high_pit_precision_pass=int(output['pit_precision_pass'].sum()),
        high_cut_precision_pass=int(output['cut_precision_pass'].sum()),
        high_unresolved=int((~resolved[1]).sum()),
        maximum_finite_high_mcse=float(mcse[1,np.isfinite(mcse[1])].max()) if np.isfinite(mcse[1]).any() else None,
        cdf_precision_pass=bool(precision[1].all()),
        pooled_weight_guard_pass=bool(output['weight_deletion_guard_by_level'].all()),
        replication_pass=rep['all_consistent'], refinement_pass=refine['all_consistent'],
        replication_family=dict(local=204, global_size=204*count, alpha=alpha_replicates, z=rep['z']),
        refinement_family=dict(local=7, global_size=7*count, alpha=alpha_refinement, z=refine['z']),
        weights_by_level=json_safe(weights), no_unseen_tail_certificate=True,
        no_automatic_approval=True, low_quantile_cdfs_descriptive_only=True,
    )
    return output, summary


def diagnose_target(runtime, report_path, raw_root, truth_data_path, protocol_path,
                    output_root, *, truth_loglikelihood_path=None, resume=False):
    """Write a compact diagnostic, never a raw-deletion authorization."""
    start = perf_counter(); protocol = read_json(protocol_path); record = read_json(report_path)
    if record.get('identity') != runtime.identity:
        raise RuntimeError('Diagnostic runtime differs from the production identity.')
    population = positive_int(protocol['population_targets'], 'population targets')
    if population != len(runtime.targets) or record['target'] not in runtime.targets:
        raise ValueError('Target or global numerical family differs from the campaign.')
    if protocol['levels'] != record['levels'] or protocol['independent_replications'] != 4:
        raise ValueError('IID levels differ from the diagnostic protocol.')
    output = Path(output_root); destination = output/f'diagnostic_target_{record["target"]:06d}.json'
    sources = {name:sha256(Path(__file__).parent/name) for name in ('campaign_diagnostics.py','campaign_diagnostic_io.py','iid_optimized.py','iid_diagnostics.py')}
    if truth_loglikelihood_path is None:raise ValueError('An explicit independently calculated direct-ORF truth likelihood record is required.')
    identity = dict(truth_loglikelihood_sha256=sha256(truth_loglikelihood_path), producer_report_sha256=sha256(report_path), protocol_sha256=sha256(protocol_path), truth_data_sha256=sha256(truth_data_path), source_sha256=sources)
    if destination.exists():
        if not resume:raise FileExistsError('A diagnostic exists; explicit resume required.')
        existing=read_json(destination)
        if existing['diagnostic_inputs'] != identity or sha256(output/existing['numeric_file']) != existing['numeric_sha256']:
            raise RuntimeError('Completed diagnostic identity or array hash differs.')
        return existing
    record, loaded = load_target_levels(report_path, raw_root)
    truth, truth_unit = load_truth_for_diagnostics(report_path, truth_data_path, runtime.bounds)
    truth_record=read_json(truth_loglikelihood_path)
    if truth_record.get('status')!='DIRECT_ORF_TRUTH_LOGL_DIAGNOSTIC_ONLY' or truth_record['data_sha256']!=record['input_sha256']['data'] or truth_record['config_sha256']!=record['input_sha256']['experiment'] or truth_record['models']!=runtime.cfg['models'] or truth_record['shape']!=[5,runtime.n]:
        raise RuntimeError('Independent direct-ORF truth likelihood identity mismatch.')
    truth_logl=float(truth_record['log_likelihood'][record['target']//runtime.n][record['datum']])
    low, high = [loaded[n] for n in record['levels']]
    arrays, summary = numerical_statistics(low, high, truth_unit, truth_logl, runtime.bounds,
        population_targets=population, mcse_target=protocol['cdf_mcse_target'],
        alpha_replicates=protocol['alpha_replicate_family'], alpha_refinement=protocol['alpha_refinement_family'])
    saturated_rows=[]; saturated_weight=[]
    for level in record['levels']:
        reps=sorted([r for r in record['replicates'] if r['level']==level],key=lambda r:r['replicate'])
        saturated_rows.append([r['saturated_rows'] for r in reps]); saturated_weight.append([r['saturated_normalized_target_weight'] for r in reps])
    arrays.update(target=np.asarray(record['target']),datum=np.asarray(record['datum']),model_index=np.asarray(record['target']//runtime.n),truth_unit=truth_unit,truth_physical=truth,truth_log_likelihood=np.asarray(truth_logl),saturated_rows=np.asarray(saturated_rows,int),saturated_weight=np.asarray(saturated_weight,float))
    maximum_saturation=float(np.max(saturated_weight)); limit=protocol.get('maximum_saturated_target_weight')
    summary['saturation_guard_pass']=None if limit is None else maximum_saturation<=limit
    summary['maximum_saturated_normalized_weight']=maximum_saturation
    numeric=output/f'diagnostic_target_{record["target"]:06d}.npz'
    if numeric.exists():
        if not resume:raise FileExistsError('Incomplete diagnostic arrays exist; explicit resume required.')
        from .campaign_iid import verify_arrays
        verify_arrays(numeric,arrays)
    else:write_npz_new(numeric,**arrays)
    runtime.verify_unchanged()
    meta=dict(status='NUMERICAL_DIAGNOSTICS_COMPLETE',schema='C07_TARGET_IID_DIAGNOSTICS_v1',identity=runtime.identity,target=record['target'],datum=record['datum'],model=record['model'],numeric_file=numeric.name,numeric_sha256=sha256(numeric),numeric_bytes=numeric.stat().st_size,diagnostic_inputs=identity,raw_sha256={r['raw_file']:r['raw_sha256'] for r in record['replicates']},proposal_sha256=record['proposal_sha256'],levels=record['levels'],truth_read_only_for_diagnostic=True,truth_likelihood_evaluations_this_reader=0,truth_likelihood_source='independent direct ORFs',summary=summary,seconds=perf_counter()-start,raw_release_authorized=False)
    write_json_new(destination,json_safe(meta));return meta
