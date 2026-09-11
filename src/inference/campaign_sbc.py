"""SBC synthesis for all registered realizations, with numerical sensitivity.

The scientific families are frozen separately from integration diagnostics.
Nominal tests remain conditional on computed PITs; interval analyses show how
their conclusions depend on numerical uncertainty. This module cannot approve
an integrator from an attractive calibration plot.
"""
import numpy as np
from .diagnostics import (uniformity_summary, binomial_summary, holm,
                          paired_summary, prior_return_summary)
from .sbc_sensitivity import (pit_intervals, ks_bounds, coverage_bounds,
                             holm_sensitivity, paired_binary_bounds)

PIT_INDICES=np.array([0,5,10,15,20,25])


def resolved_by_function(arrays, *, saturation_limit=1e-12):
    """Apply the prospective purpose-specific rule, not just finite MCSE."""
    specs=np.asarray(arrays['replication_specification'])
    rep=np.asarray(arrays['replication_pass'])
    refinement=np.asarray(arrays['refinement_pass'])
    if specs.shape!=(204,4) or rep.shape!=(204,) or refinement.shape!=(7,) or rep.dtype.kind!='b' or refinement.dtype.kind!='b':
        raise ValueError('Frozen 204 replication and seven refinement checks required.')
    weight=bool(np.asarray(arrays['weight_deletion_guard_by_level']).all())
    saturation=np.asarray(arrays['saturated_weight'])
    if saturation.shape!=(2,4) or not np.isfinite(saturation).all() or np.any(saturation<0):
        raise ValueError('Both levels and all four saturation records required.')
    common=weight and bool(np.max(saturation)<=saturation_limit) and bool(refinement[6])
    zchecks=specs[:,1]==26
    if np.count_nonzero(zchecks)!=12:raise ValueError('Two levels of six logZ contrasts required.')
    common=common and bool(rep[zchecks].all())
    precision=np.asarray(arrays['pit_precision_pass'])
    finite=np.asarray(arrays['pit_resolved'])
    if precision.shape!=(6,) or finite.shape!=(6,) or precision.dtype.kind!='b' or finite.dtype.kind!='b':
        raise ValueError('Six explicit PIT flags required.')
    resolved=np.zeros(6,bool)
    for j,index in enumerate(PIT_INDICES):
        selected=specs[:,1]==index
        if np.count_nonzero(selected)!=12:raise ValueError('Two levels of six PIT contrasts required.')
        resolved[j]=common and precision[j] and finite[j] and refinement[j] and rep[selected].all()
    return resolved


def synthesize(pit, mcse, resolved, quantiles, config, parameters):
    """Shapes M,N,6 and M,N,5,4; no missing models or dropped simulation IDs."""
    models=config['models'];n=config['n_realizations'];parameters=list(parameters)
    p=np.asarray(pit);s=np.asarray(mcse);r=np.asarray(resolved);q=np.asarray(quantiles)
    if p.shape!=(len(models),n,6) or s.shape!=p.shape or r.shape!=p.shape or q.shape!=(len(models),n,5,4) or len(parameters)!=5:
        raise ValueError('All registered models/realizations and five parameters are required.')
    if not np.isfinite(q).all() or np.any(np.diff(q,axis=-1)<0):
        raise ValueError('Finite monotone quantiles required, without repair.')
    numerical=config['numerical_sensitivity'];alpha=config['scientific_alpha']
    lower,upper,sensitivity=pit_intervals(p,s,r,
        deterministic_component=numerical['deterministic_component'],
        family_size=numerical['family_size'],alpha_mc=numerical['alpha_mc'])
    records=[];coverage_events={}
    for group in ['correct','approximate']:
        family=config['families'][group];rows=[];size=family['hypotheses']
        for name in family['models']:
            m=models.index(name)
            for j,parameter in enumerate(parameters+['logL_at_truth']):
                nominal=uniformity_summary(p[m,:,j],alpha,size)
                bounds=ks_bounds(lower[m,:,j],upper[m,:,j])
                rows.append(dict(group=group,method=name,target=parameter,diagnostic='PIT',
                    nominal=nominal,sensitivity=bounds,
                    numerical_resolved=int(r[m,:,j].sum())))
            for j,parameter in enumerate(parameters):
                for probability in config['probabilities']:
                    hit=p[m,:,j]<=probability
                    bounds,certain,possible=coverage_bounds(lower[m,:,j],upper[m,:,j],
                        upper_probability=probability,alpha=alpha,family_size=size)
                    rows.append(dict(group=group,method=name,target=parameter,
                        diagnostic=f'below_q{probability:.2f}',
                        nominal=binomial_summary(hit,probability,alpha,size),sensitivity=bounds,
                        numerical_resolved=int(r[m,:,j].sum())))
                hit=(p[m,:,j]>=.05)&(p[m,:,j]<=.95)
                bounds,certain,possible=coverage_bounds(lower[m,:,j],upper[m,:,j],
                    lower_probability=.05,upper_probability=.95,alpha=alpha,family_size=size)
                coverage_events[name,j]=(hit,certain,possible)
                rows.append(dict(group=group,method=name,target=parameter,diagnostic='central_90',
                    nominal=binomial_summary(hit,.9,alpha,size),sensitivity=bounds,
                    numerical_resolved=int(r[m,:,j].sum())))
        if len(rows)!=size:raise ValueError('The registered scientific family size changed.')
        adjusted,rejected=holm([row['nominal']['pvalue'] for row in rows],alpha)
        bounds=holm_sensitivity([row['sensitivity']['pvalue_lower'] for row in rows],
                               [row['sensitivity']['pvalue_upper'] for row in rows],alpha=alpha)
        for i,row in enumerate(rows):
            row.update(family_size=size,nominal_holm_pvalue=float(adjusted[i]),
                nominal_reject=bool(rejected[i]),
                sensitivity_holm_pvalue_bounds=[float(bounds['holm_lower'][i]),float(bounds['holm_upper'][i])],
                rejection_robust_to_sensitivity=bool(bounds['rejection_for_all_permitted_pvalues'][i]),
                rejection_not_excluded_by_sensitivity=bool(bounds['rejection_not_excluded_by_rectangular_bounds'][i]))
        records.extend(rows)
    pairs=[];descriptive=[];ids=list(range(n))
    for name_a,name_b in config['families']['paired_central90']['pairs']:
        a,b=models.index(name_a),models.index(name_b)
        for j,parameter in enumerate(parameters):
            hit_a,certain_a,possible_a=coverage_events[name_a,j]
            hit_b,certain_b,possible_b=coverage_events[name_b,j]
            pairs.append(dict(method_a=name_a,method_b=name_b,parameter=parameter,
                nominal=paired_summary(hit_a.astype(float),hit_b.astype(float),ids,ids,alpha),
                sensitivity=paired_binary_bounds(certain_a,possible_a,certain_b,possible_b)))
            for k,probability in enumerate(config['probabilities']):
                descriptive.append(dict(method_a=name_a,method_b=name_b,parameter=parameter,
                    quantile_probability=probability,units='prior width',
                    **paired_summary(q[a,:,j,k],q[b,:,j,k],ids,ids,alpha)))
    if len(pairs)!=config['families']['paired_central90']['hypotheses']:
        raise ValueError('The registered 15 paired hypotheses changed.')
    adjusted,rejected=holm([row['nominal']['mcnemar_exact_pvalue'] for row in pairs],alpha)
    bounds=holm_sensitivity([row['sensitivity']['pvalue_lower'] for row in pairs],
                           [row['sensitivity']['pvalue_upper'] for row in pairs],alpha=alpha)
    for i,row in enumerate(pairs):
        row.update(nominal_holm_pvalue=float(adjusted[i]),nominal_reject=bool(rejected[i]),
            sensitivity_holm_pvalue_bounds=[float(bounds['holm_lower'][i]),float(bounds['holm_upper'][i])],
            rejection_robust_to_sensitivity=bool(bounds['rejection_for_all_permitted_pvalues'][i]))
    summary=[]
    for m,name in enumerate(models):
        selected=[row for row in records if row['method']==name]
        summary.append(dict(model=name,simulations=n,
            functions_resolved_by_parameter=r[m].sum(axis=0).tolist(),
            simulations_with_all_six_resolved=int(r[m].all(axis=1).sum()),
            nominal_rejections=sum(row['nominal_reject'] for row in selected),
            robust_rejections=sum(row['rejection_robust_to_sensitivity'] for row in selected),
            quantile_distance_from_prior=prior_return_summary(q[m],np.tile(config['probabilities'],(5,1)),np.ones(5))))
    report=dict(scope='CONTINUOUS_PRIOR_PREDICTIVE_SBC_WITH_NUMERICAL_SENSITIVITY',
        all_simulations_retained=True,simulations_per_model=n,models=models,parameters=parameters,
        nominal_tests_are_conditional_on_computed_pits=True,
        numerical_resolution_is_not_inferred_from_uniformity=True,
        sensitivity_intervals=sensitivity,model_summary=summary,tests=records,paired_central90=pairs,
        descriptive_paired_quantiles=descriptive,
        quantile_horizontal_precision_not_certified_by_cdf_mcse=True,
        nonrejection_does_not_prove_correctness=True)
    return report,dict(pit_lower=lower,pit_upper=upper)
