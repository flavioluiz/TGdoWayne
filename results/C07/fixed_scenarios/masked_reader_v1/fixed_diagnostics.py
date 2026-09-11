"""Prospective fixed96 masked reader, separate from immutable campaign diagnostics v1.

No posterior sampler is implemented here. Undefined truths are never converted
to CDF cutoffs. The only exact structural CDF is the continuous mass endpoint u=0.
"""
from pathlib import Path
from time import perf_counter
import itertools
import numpy as np
from inference.campaign_io import read_json,sha256,write_json_new,write_npz_new
from inference.campaign_diagnostic_io import load_target_levels
from inference.iid_optimized import TargetIIDContext
from inference.iid_diagnostics import simultaneous_differences,json_safe

PROBABILITIES=np.array([.05,.5,.9,.95])
PIT_INDICES=np.array([0,5,10,15,20,25])
PAIRS=tuple(itertools.combinations(range(4),2))


def _truth_contract(truth_unit,truth_defined,truth_logl,logl_defined,bounds,structural):
    truth=np.asarray(truth_unit);defined=np.asarray(truth_defined);bounds=np.asarray(bounds)
    structural=np.asarray(structural)
    if (truth.shape!=(5,) or truth.dtype.kind not in 'fiu' or defined.shape!=(5,) or defined.dtype.kind!='b' or
        structural.shape!=(5,) or structural.dtype.kind!='b' or bounds.shape!=(5,2) or
        bounds.dtype.kind not in 'fiu' or not np.isfinite(bounds).all() or np.any(bounds[:,1]<=bounds[:,0]) or
        not np.array_equal(bounds[0],[0,1])):
        raise ValueError('Five C07 coordinates, finite bounds and explicit boolean masks required.')
    if (not np.isfinite(truth[defined]).all() or np.any((truth[defined]<0)|(truth[defined]>1)) or
        not np.isnan(truth[~defined]).all()):
        raise ValueError('Defined truths must be finite in the unit cube; missing truths must be NaN.')
    if not isinstance(logl_defined,(bool,np.bool_)) or not np.isscalar(truth_logl):
        raise ValueError('Explicit scalar logL applicability flag required.')
    if (bool(logl_defined)!=bool(defined[:3].all()) or not defined[3:].all() or
       (not defined[:3].all() and defined[:3].any())):
        raise ValueError('Fixed96 has either five defined coordinates or only the two noise coordinates.')
    if (logl_defined and not np.isfinite(truth_logl)) or (not logl_defined and not np.isnan(truth_logl)):
        raise ValueError('Undefined signal-model logL truth must remain NaN; finite substitute forbidden.')
    expected=np.zeros(5,bool);expected[0]=bool(defined[0] and truth[0]==0)
    if not np.array_equal(structural,expected):
        raise ValueError('Only the analytically proven continuous u=0 endpoint is structural.')
    return truth.astype(float),defined,bounds.astype(float),structural


def _placeholder(structural):
    value=0. if structural else np.nan
    return dict(estimate=value,mcse=value,precision_pass=bool(structural),
        replication_estimates=[value]*4,replication_mcse=[value]*4,
        positive_weight_counts_below_above=[-1,-1])


def _contrasts(rows,global_size,alpha):
    """Keep the prospectively fixed denominator when structural/undefined tests are omitted."""
    values=np.asarray(rows,float)
    if values.ndim!=2 or values.shape[1]!=4 or not 0<len(values)<=global_size:
        raise ValueError('Nonempty contrast list below fixed family bound required.')
    return simultaneous_differences(*values.T,alpha=alpha*len(values)/global_size)


def fixed_numerical_statistics(low,high,truth_unit,truth_defined,truth_logl,logl_defined,bounds,
                               structural_lower_boundary,*,mcse_target=.00335,
                               alpha_replicates=.05,alpha_refinement=.05,
                               global_replicate_contrasts=204*96,global_refinement_contrasts=7*96,
                               continuous_uniform_mass_prior_no_atom=True):
    """SNIS diagnostics only; arrays retain 26 slots, with applicability/structural masks.

    All20 independent low-selected quantile cuts remain applicable. The global
    numerical families are fixed96 maxima, never reduced to the tests executed.
    """
    if (continuous_uniform_mass_prior_no_atom is not True or global_replicate_contrasts!=204*96 or
        global_refinement_contrasts!=7*96 or mcse_target!=.00335 or alpha_replicates!=.05 or alpha_refinement!=.05):
        raise ValueError('Fixed96 prospectively frozen prior/numerical protocol required.')
    truth,defined,bounds,structural=_truth_contract(truth_unit,truth_defined,truth_logl,logl_defined,bounds,structural_lower_boundary)
    applicable=np.ones(26,bool);applicable[PIT_INDICES]=np.r_[defined,logl_defined]
    exact=np.zeros(26,bool);exact[PIT_INDICES[:5]]=structural
    numerical=applicable & ~exact
    contexts=[]
    for data in (low,high):
        x=np.asarray(data['x_unit']);lw=np.asarray(data['log_weights']);ll=np.asarray(data['log_likelihood'])
        if (x.shape!=lw.shape+(5,) or lw.ndim!=2 or lw.shape[0]!=4 or ll.shape!=lw.shape or
            not np.isfinite(x).all() or np.any((x<0)|(x>1)) or not np.isfinite(ll).all()):
            raise ValueError('Four aligned finite IID replicate arrays in the original unit prior cube required.')
        contexts.append(TargetIIDContext(lw))
    if np.shape(high['log_weights'])[1]<=np.shape(low['log_weights'])[1]:
        raise ValueError('Two increasing independent IID levels required.')
    cuts=np.array([contexts[0].quantiles(low['x_unit'][:,:,j],PROBABILITIES) for j in range(5)])
    quantiles=np.array([contexts[1].quantiles(high['x_unit'][:,:,j],PROBABILITIES) for j in range(5)])
    levels=[];weights=[];contrasts=[];specifications=[]
    for level,(data,context) in enumerate(zip((low,high),contexts)):
        rows=[]
        for j in range(5):
            if numerical[j*5]:
                rows.extend(context.cdf(data['x_unit'][:,:,j],np.r_[truth[j],cuts[j]],mcse_target=mcse_target))
            else:
                rows.append(_placeholder(bool(exact[j*5])))
                rows.extend(context.cdf(data['x_unit'][:,:,j],cuts[j],mcse_target=mcse_target))
        rows.extend(context.cdf(data['log_likelihood'],[truth_logl],mcse_target=mcse_target)
                    if numerical[25] else [_placeholder(False)])
        weight=context.weights();levels.append(rows);weights.append(weight)
        for measure in (PIT_INDICES if level==0 else range(26)):
            if not numerical[measure]:continue
            row=rows[measure]
            for a,b in PAIRS:
                contrasts.append([row['replication_estimates'][a],row['replication_mcse'][a],row['replication_estimates'][b],row['replication_mcse'][b]])
                specifications.append([level,measure,a,b])
        for a,b in PAIRS:
            wa,wb=weight['replications'][a],weight['replications'][b]
            contrasts.append([wa['log_evidence'],wa['log_evidence_delta_mcse'],wb['log_evidence'],wb['log_evidence_delta_mcse']])
            specifications.append([level,26,a,b])
    refinement=[];refine_spec=[]
    for measure in PIT_INDICES:
        if not numerical[measure]:continue
        a,b=levels[0][measure],levels[1][measure]
        refinement.append([a['estimate'],a['mcse'],b['estimate'],b['mcse']]);refine_spec.append(int(measure))
    a,b=weights
    refinement.append([a['log_evidence'],a['log_evidence_delta_mcse'],b['log_evidence'],b['log_evidence_delta_mcse']]);refine_spec.append(26)
    rep=_contrasts(contrasts,global_replicate_contrasts,alpha_replicates)
    refine=_contrasts(refinement,global_refinement_contrasts,alpha_refinement)
    estimates=np.array([[r['estimate'] for r in level] for level in levels])
    mcse=np.array([[r['mcse'] for r in level] for level in levels])
    resolved=np.isfinite(mcse)&applicable[None,:]
    precision=np.array([[r['precision_pass'] for r in level] for level in levels],bool)&applicable[None,:]
    cut_indices=np.array([[j*5+k for k in range(1,5)] for j in range(5)])
    output=dict(probabilities=PROBABILITIES.copy(),pit=estimates[1,PIT_INDICES],pit_mcse=mcse[1,PIT_INDICES],
        pit_applicable=applicable[PIT_INDICES],pit_structural_exact=exact[PIT_INDICES],
        pit_resolved=resolved[1,PIT_INDICES],pit_precision_pass=precision[1,PIT_INDICES],
        quantiles_unit=quantiles,quantiles_physical=bounds[:,0,None]+np.diff(bounds,axis=1)*quantiles,
        independent_cuts_unit=cuts,cut_cdf=estimates[1,cut_indices],cut_mcse=mcse[1,cut_indices],
        cut_resolved=resolved[1,cut_indices],cut_precision_pass=precision[1,cut_indices],
        cdf_applicable=applicable,cdf_structural_exact=exact,cdf_numerically_evaluated=numerical,
        cdf_estimates_by_level=estimates,cdf_mcse_by_level=mcse,cdf_resolved_by_level=resolved,cdf_precision_by_level=precision,
        cdf_replicate_estimates=np.array([[r['replication_estimates'] for r in level] for level in levels]),
        cdf_replicate_mcse=np.array([[r['replication_mcse'] for r in level] for level in levels]),
        cdf_positive_weight_counts=np.array([[r['positive_weight_counts_below_above'] for r in level] for level in levels]),
        log_evidence=np.asarray(weights[1]['log_evidence']),log_evidence_mcse=np.asarray(weights[1]['log_evidence_delta_mcse']),
        log_evidence_by_level=np.array([w['log_evidence'] for w in weights]),
        log_evidence_mcse_by_level=np.array([w['log_evidence_delta_mcse'] for w in weights]),
        log_evidence_by_replicate=np.array([[r['log_evidence'] for r in w['replications']] for w in weights]),
        log_evidence_mcse_by_replicate=np.array([[r['log_evidence_delta_mcse'] for r in w['replications']] for w in weights]),
        weight_ess=np.asarray(weights[1]['weight_ess_concentration_only']),maximum_weight=np.asarray(weights[1]['maximum_normalized_weight']),
        single_deletion_bound=np.asarray(weights[1]['single_deletion_cdf_bound']),
        weight_deletion_guard_by_level=np.array([w['single_deletion_guard_pass'] for w in weights]),
        replication_specification=np.asarray(specifications,int),replication_difference=rep['difference'],
        replication_mcse=rep['difference_mcse'],replication_resolved=rep['resolved'],replication_pass=rep['consistent'],
        refinement_specification=np.array(refine_spec,int),refinement_difference=refine['difference'],
        refinement_mcse=refine['difference_mcse'],refinement_resolved=refine['resolved'],refinement_pass=refine['consistent'])
    summary=dict(scope='FIXED_TRUTH_NUMERICAL_DIAGNOSTICS_NOT_SBC',mcse_target=mcse_target,
        high_cdf_applicable=int(applicable.sum()),high_cdf_numerically_evaluated=int(numerical.sum()),
        high_cdf_structural_exact=int(exact.sum()),high_cdf_precision_pass=int(precision[1].sum()),
        high_pit_applicable=int(output['pit_applicable'].sum()),high_pit_structural_exact=int(output['pit_structural_exact'].sum()),
        high_pit_precision_pass=int(output['pit_precision_pass'].sum()),high_cut_precision_pass=int(output['cut_precision_pass'].sum()),
        high_unresolved_applicable=int((applicable&~resolved[1]).sum()),
        cdf_precision_pass=bool(precision[1,applicable].all()),
        pooled_weight_guard_pass=bool(output['weight_deletion_guard_by_level'].all()),
        replication_pass=rep['all_consistent'],refinement_pass=refine['all_consistent'],
        replication_family=dict(executed=len(contrasts),maximum_per_target=204,global_size=global_replicate_contrasts,alpha=alpha_replicates,z=rep['z']),
        refinement_family=dict(executed=len(refinement),maximum_per_target=7,global_size=global_refinement_contrasts,alpha=alpha_refinement,z=refine['z']),
        weights_by_level=json_safe(weights),undefined_truth_is_not_numerical_failure=True,
        structural_zero_is_not_unresolved_sample_tail=True,no_automatic_approval=True,
        no_unseen_tail_certificate=True,low_quantile_cdfs_descriptive_only=True)
    return output,summary


def load_fixed_truth(report_path,truth_data_path,generation_path,bounds):
    """Read fixed truth only in this diagnostic, against producer/data/generator identities."""
    record=read_json(report_path);generation=read_json(generation_path);digest=sha256(truth_data_path)
    if (record['model']!='A0_CN' or record['target']!=record['datum'] or not 0<=record['datum']<96 or
        digest!=record['input_sha256']['data'] or digest!=generation['data_sha256'] or
        generation['status']!='FIXED_DATA_GENERATED_NOT_POSTERIOR_INFERENCE' or
        generation['preflight']['experiment_sha256']!=record['input_sha256']['experiment']):
        raise RuntimeError('Fixed truth/generation/producer identity mismatch.')
    datum=record['datum'];bounds=np.asarray(bounds,float)
    with np.load(truth_data_path,allow_pickle=False) as p:
        if p['truth'].shape!=(96,5) or p['truth_defined'].shape!=(96,5) or p['log_likelihood_at_truth'].shape!=(96,):
            raise ValueError('Fixed96 truth schema required.')
        truth=p['truth'][datum].copy();defined=p['truth_defined'][datum].copy()
        structural=p['structural_lower_boundary_pit'][datum].copy()
        logl=float(p['log_likelihood_at_truth'][datum]);logl_defined=bool(p['log_likelihood_at_truth_defined'][datum])
        scenario=int(p['scenario_index'][datum]);replicate=int(p['replicate_within_scenario'][datum])
        if scenario!=datum//32 or replicate!=datum%32 or int(p['target'][datum])!=datum:
            raise RuntimeError('Fixed target/scenario/replication mapping changed.')
    unit=np.full(5,np.nan);unit[defined]=(truth[defined]-bounds[defined,0])/np.diff(bounds,axis=1)[defined,0]
    _truth_contract(unit,defined,logl,logl_defined,bounds,structural)
    return dict(truth=truth,unit=unit,defined=defined,logl=logl,logl_defined=logl_defined,
                structural=structural,scenario=scenario,replicate=replicate)


def diagnose_fixed_target(runtime,report_path,raw_root,truth_data_path,generation_path,protocol_path,output_root,*,resume=False):
    """Separate masked adapter; computes no likelihood and authorizes no raw deletion."""
    start=perf_counter();protocol=read_json(protocol_path);record=read_json(report_path)
    if (record.get('identity')!=runtime.identity or runtime.n!=96 or
        not np.array_equal(runtime.targets,np.arange(96)) or runtime.cfg['prior']['kind']!='independent uniform in these coordinates'):
        raise RuntimeError('Fixed96 runtime/target/prior identity mismatch.')
    if (protocol['population_targets']!=96 or protocol['models']!=['A0_CN'] or
        protocol['levels']!=record['levels'] or protocol['independent_replications']!=4):
        raise ValueError('Prospective fixed96 protocol differs from the production.')
    source_paths={'fixed_diagnostics':Path(__file__)}
    import importlib.util
    for name in ['iid_optimized','iid_diagnostics','campaign_diagnostic_io','campaign_io']:
        source_paths[name]=Path(importlib.util.find_spec('inference.'+name).origin)
    hashes={name:sha256(path) for name,path in source_paths.items()}
    identity=dict(producer_report_sha256=sha256(report_path),truth_data_sha256=sha256(truth_data_path),
        generation_sha256=sha256(generation_path),protocol_sha256=sha256(protocol_path),source_sha256=hashes)
    output=Path(output_root);destination=output/f'fixed_diagnostic_target_{record["target"]:06d}.json'
    if destination.exists():
        if not resume:raise FileExistsError('A fixed diagnostic exists; explicit resume required.')
        existing=read_json(destination)
        if existing['diagnostic_inputs']!=identity or sha256(output/existing['numeric_file'])!=existing['numeric_sha256']:
            raise RuntimeError('Completed fixed diagnostic provenance changed.')
        return existing
    record,loaded=load_target_levels(report_path,raw_root)
    t=load_fixed_truth(report_path,truth_data_path,generation_path,runtime.bounds)
    low,high=[loaded[n] for n in record['levels']]
    arrays,summary=fixed_numerical_statistics(low,high,t['unit'],t['defined'],t['logl'],t['logl_defined'],runtime.bounds,t['structural'],
        mcse_target=protocol['cdf_mcse_target'],alpha_replicates=protocol['alpha_replicate_family'],
        alpha_refinement=protocol['alpha_refinement_family'],global_replicate_contrasts=protocol['global_replicate_contrasts'],
        global_refinement_contrasts=protocol['global_refinement_contrasts'])
    saturated_rows=[];saturated_weight=[]
    for level in record['levels']:
        reps=sorted([r for r in record['replicates'] if r['level']==level],key=lambda r:r['replicate'])
        saturated_rows.append([r['saturated_rows'] for r in reps]);saturated_weight.append([r['saturated_normalized_target_weight'] for r in reps])
    arrays.update(target=np.asarray(record['target']),datum=np.asarray(record['datum']),model_index=np.asarray(0),
        truth_unit=t['unit'],truth_physical=t['truth'],truth_defined=t['defined'],truth_log_likelihood=np.asarray(t['logl']),
        truth_log_likelihood_defined=np.asarray(t['logl_defined']),scenario_index=np.asarray(t['scenario']),
        replicate_within_scenario=np.asarray(t['replicate']),saturated_rows=np.asarray(saturated_rows,int),saturated_weight=np.asarray(saturated_weight,float))
    saturation=np.asarray(saturated_weight,float)
    if saturation.shape!=(2,4) or not np.isfinite(saturation).all() or np.any((saturation<0)|(saturation>1)):
        raise ValueError('Finite saturation-weight fractions from all eight production files required.')
    limit=protocol['maximum_saturated_target_weight']
    if limit!=1e-12:raise ValueError('Fixed saturation guard cannot be relaxed.')
    summary['saturation_guard_pass']=bool(np.all(saturation<=limit))
    summary['maximum_saturated_normalized_weight']=float(saturation.max())
    numeric=output/f'fixed_diagnostic_target_{record["target"]:06d}.npz'
    if numeric.exists():
        if not resume:raise FileExistsError('Incomplete fixed arrays exist; explicit resume required.')
        with np.load(numeric,allow_pickle=False) as old:
            if set(old.files)!=set(arrays) or any(not np.array_equal(old[k],v,equal_nan=True) for k,v in arrays.items()):
                raise RuntimeError('Resumed fixed diagnostic arrays differ.')
    else:write_npz_new(numeric,**arrays)
    runtime.verify_unchanged()
    if any(sha256(path)!=hashes[name] for name,path in source_paths.items()):raise RuntimeError('Masked diagnostic source changed.')
    meta=dict(status='FIXED_NUMERICAL_DIAGNOSTICS_COMPLETE',schema='C07_FIXED_MASKED_IID_DIAGNOSTICS_v1',
        identity=runtime.identity,target=record['target'],datum=record['datum'],model=record['model'],
        numeric_file=numeric.name,numeric_sha256=sha256(numeric),numeric_bytes=numeric.stat().st_size,
        diagnostic_inputs=identity,raw_sha256={r['raw_file']:r['raw_sha256'] for r in record['replicates']},
        proposal_sha256=record['proposal_sha256'],levels=record['levels'],truth_read_only_for_diagnostic=True,
        truth_likelihood_evaluations_this_reader=0,truth_likelihood_source='checked exact-node generation for signal scenarios; undefined when signal absent',
        summary=summary,seconds=perf_counter()-start,raw_release_authorized=False)
    write_json_new(destination,json_safe(meta));return meta
