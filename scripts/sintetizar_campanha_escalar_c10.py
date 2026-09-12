"""Frozen 39/26/6 SBC families, detection and fixed-cell recovery summaries."""
from pathlib import Path
import argparse,json,math,sys
import numpy as np
from scipy import stats
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'src'),str(R/'tmp/c10_exact_lifecycle_v1')]
from physical import sha
from pta.scalar_campaign import hypotheses,inventory,PAIRS
from inference.diagnostics import holm,clopper_pearson
from inference.sbc_sensitivity import ks_bounds,coverage_bounds,holm_sensitivity,paired_binary_bounds
P=R/'tmp/c10_production_v1';O=R/'results/C10/population_synthesis';C=R/'configs/scalar/c10_production_v1.json'

def read(path):
    d=json.loads(path.read_text());return d.get('payload',d)

def plain(x):
    if isinstance(x,dict):return {k:plain(v) for k,v in x.items()}
    if isinstance(x,(list,tuple)):return [plain(v) for v in x]
    if isinstance(x,np.ndarray):return plain(x.tolist())
    if isinstance(x,np.generic):return x.item()
    return x

def freeze():
    protocol=read(C);families=hypotheses(protocol)
    files=[Path(__file__),C,R/'src/pta/scalar_campaign.py',R/'src/inference/diagnostics.py',R/'src/inference/sbc_sensitivity.py',P/'plan.json']
    plan=dict(schema='C10_SCIENTIFIC_SYNTHESIS_v1',sources={str(p.relative_to(R)):sha(p) for p in files},hypotheses=families,
              population_counts={'null':500,'prior2D':500,'recovery':192},expected_targets=6344,
              alpha=.05,multiplicity='Holm separately within 39/26/6; no across-family FWER claim',
              numerical_intervals='Deterministic operational sensitivity, not MCSE or rigorous physical confidence bounds',
              unresolved='Every unresolved PIT [0,1] retained; uncertain BF gives certain/possible counts',
              C_scope='Descriptive only; N32 null/prior and N5/N6 per recovery cell',
              no_rejection_is_not_validation=True)
    O.mkdir(exist_ok=False);(O/'plan.json').write_text(json.dumps(plan,indent=2)+'\n')
    print(json.dumps(dict(status='SYNTHESIS_PLAN_FROZEN',families={k:len(v) for k,v in families.items()})))

def execute():
    plan=read(O/'plan.json')
    for n,h in plan['sources'].items():assert sha(R/n)==h,n
    done=read(P/'complete.json');assert done['targets']==6344 and done['charged']==done['completed']
    protocol=read(C);records=inventory(protocol);rows={};bindings={}
    for record in records:
        for label in record['analyses']:
            name=f'{label}_d{record["global_id"]}';path=P/'targets'/f'{name}.json';row=read(path)
            assert row['global_id']==record['global_id'] and row['label']==label and row['ensemble']==record['ensemble']
            rows[name]=row;bindings[str(path.relative_to(R))]=sha(path)
    assert len(rows)==6344
    models=protocol['models'];pit={};intervals={};central={};tests=[]
    for model in models:
        selected=[rows[f'{model}_d{i}'] for i in range(500,1000)]
        values=np.array([r['fine']['parameter_CDF']+[r['fine']['logL_CDF']] for r in selected])
        bounds=np.array([r['parameter_PIT_intervals']+[r['logL_event']['interval']] for r in selected])
        assert values.shape==(500,3) and bounds.shape==(500,3,2)
        assert np.isfinite(values).all() and np.all((values>=0)&(values<=1)) and np.all(bounds[:,:,0]<=bounds[:,:,1])
        pit[model]=values;intervals[model]=bounds
        for j,parameter in enumerate(('u','epsilon')):
            _,certain,possible=coverage_bounds(bounds[:,j,0],bounds[:,j,1],upper_probability=.95,lower_probability=.05)
            central[model,parameter]=(certain,possible)
    for family,specifications in plan['hypotheses'].items():
        group=[]
        for spec in specifications:
            if family=='paired_central90':
                a,b=spec['models'];j=('u','epsilon').index(spec['statistic']);cx,px=central[a,spec['statistic']];cy,py=central[b,spec['statistic']]
                bounds=paired_binary_bounds(cx,px,cy,py);x=(pit[a][:,j]>=.05)&(pit[a][:,j]<=.95);y=(pit[b][:,j]>=.05)&(pit[b][:,j]<=.95)
                n10=int(np.sum(x&~y));n01=int(np.sum(y&~x));nominal=1. if n10+n01==0 else float(stats.binomtest(n10,n10+n01,.5).pvalue)
            else:
                model=spec['model'];j=('u','epsilon','logL_same_data').index(spec['statistic']);v=pit[model][:,j];lo=intervals[model][:,j,0];hi=intervals[model][:,j,1]
                if spec['kind']=='KS_uniform':bounds=ks_bounds(lo,hi);nominal=float(stats.kstest(v,'uniform').pvalue)
                elif spec['event']=='central90':
                    bounds,_,_=coverage_bounds(lo,hi,upper_probability=.95,lower_probability=.05);nominal=float(stats.binomtest(int(np.sum((v>=.05)&(v<=.95))),500,.9).pvalue)
                else:
                    p=spec['probability'];bounds,_,_=coverage_bounds(lo,hi,upper_probability=p);nominal=float(stats.binomtest(int(np.sum(v<=p)),500,p).pvalue)
            group.append(dict(family=family,hypothesis=spec,nominal_pvalue=nominal,sensitivity=bounds))
        adjusted,reject=holm([x['nominal_pvalue'] for x in group],.05)
        sensitive=holm_sensitivity([x['sensitivity']['pvalue_lower'] for x in group],[x['sensitivity']['pvalue_upper'] for x in group])
        for j,row in enumerate(group):
            row.update(nominal_Holm_pvalue=float(adjusted[j]),nominal_reject=bool(reject[j]),
                       sensitivity_Holm_lower=float(sensitive['holm_lower'][j]),sensitivity_Holm_upper=float(sensitive['holm_upper'][j]),
                       decision='REJECT_FOR_ALL_INTERVAL_VALUES' if sensitive['rejection_for_all_permitted_pvalues'][j] else ('INDETERMINATE' if sensitive['rejection_not_excluded_by_rectangular_bounds'][j] else 'NO_REJECTION_CONDITIONAL_ON_INTERVALS'))
        tests.extend(group)
    summaries=[]
    for label in protocol['models']+protocol['C_models']:
        for ensemble in ('null','prior2D','recovery'):
            cells=range(6) if ensemble=='recovery' else [None]
            for cell in cells:
                selected=[r for r in rows.values() if r['label']==label and r['ensemble']==ensemble and (cell is None or r['local_id']//32==cell)]
                n=len(selected);assert n>0
                logbf=np.array([r['fine']['logBF'] for r in selected]);certain=possible=0
                for row in selected:
                    lo,hi=row['logBF_interval'];lo=-math.inf if lo is None else lo;hi=math.inf if hi is None else hi
                    certain+=int(lo>math.log(10));possible+=int(hi>math.log(10))
                nominal=int(np.sum(logbf>math.log(10)))
                coverage=[]
                for j,parameter in enumerate(('u','epsilon')):
                    bounds=np.array([r['parameter_PIT_intervals'][j] for r in selected]);values=np.array([r['fine']['parameter_CDF'][j] for r in selected])
                    cov,_,_=coverage_bounds(bounds[:,0],bounds[:,1],upper_probability=.95,lower_probability=.05)
                    coverage.append(dict(parameter=parameter,nominal_hits=int(np.sum((values>=.05)&(values<=.95))),**cov,
                                         nominal_coverage_test_applicable=ensemble=='prior2D'))
                summaries.append(dict(label=label,ensemble=ensemble,cell=cell,n=n,
                    detection=dict(threshold_BF10=10,nominal_count=nominal,certain_count=certain,possible_count=possible,
                                   nominal_fraction=nominal/n,nominal_CP95=clopper_pearson(nominal,n),
                                   CP95_union=[clopper_pearson(certain,n)[0],clopper_pearson(possible,n)[1]]),
                    central90_coverage=coverage,median_posterior_medians=np.median([r['fine']['quantiles'] for r in selected],axis=0)[:,1].tolist(),
                    scope='Fixed cell conditional recovery' if ensemble=='recovery' else ('False-positive rate marginalized over declared mass prior' if ensemble=='null' else 'Prior predictive ensemble')))
    contrasts=[]
    pairs=list(PAIRS)+[('B_CN','C_beta_CN'),('B_CN','C_full_CN'),('B_G','C_beta_G'),('B_G','C_full_G')]
    for a,b in pairs:
        for ensemble in ('null','prior2D','recovery'):
            for cell in (range(6) if ensemble=='recovery' else [None]):
                ids=[r['global_id'] for r in rows.values() if r['label']==b and r['ensemble']==ensemble and (cell is None or r['local_id']//32==cell)]
                for j,param in enumerate(('u','epsilon')):
                    for k,p in enumerate((.05,.5,.9,.95)):
                        delta=[];bounds=[]
                        for i in ids:
                            x=rows[f'{a}_d{i}'];y=rows[f'{b}_d{i}'];delta.append(y['fine']['quantiles'][j][k]-x['fine']['quantiles'][j][k])
                            xl,xh=x['quantile_intervals'][j][k];yl,yh=y['quantile_intervals'][j][k];bounds.append([yl-xh,yh-xl])
                        contrasts.append(dict(methods=[a,b],ensemble=ensemble,cell=cell,parameter=param,probability=p,n=len(ids),
                                              mean_paired_difference=float(np.mean(delta)),mean_numerical_interval=np.mean(bounds,axis=0).tolist(),
                                              descriptive_standard_error=float(np.std(delta,ddof=1)/np.sqrt(len(ids))),formal_hypothesis_test=False))
    resolved={m:np.sum(np.any(intervals[m]!=np.array([0.,1.]),axis=2),axis=0).tolist() for m in models}
    result=dict(status='C10_POPULATION_SYNTHESIS_COMPLETE_CONDITIONAL_OPERATIONAL',targets=6344,tests=tests,ensemble_summaries=summaries,contrasts=contrasts,
                resolved_PIT_counts=resolved,PIT_order=['u','epsilon','logL_same_data'],
                source_sha256=sha(Path(__file__)),production_complete_sha256=sha(P/'complete.json'),target_sha256=bindings,
                assumptions=['Continuous PIT statistics; numerical intervals are operational, not rigorous physical bounds',
                             'No rejection does not establish calibration or learning','Gaussian controls are distinct experiments; approximate normals on physical statistics are analyzed separately',
                             'Null detection rates average over the declared mass prior; fixed recovery cells are not pooled for binomial inference'],
                no_targets_discarded=True,new_likelihood_values=0,new_ORFs=0)
    with (O/'results.json').open('x') as f:json.dump(plain(result),f,indent=2,allow_nan=False);f.write('\n')
    np.savez_compressed(O/'PITs.npz',**{f'{m}_point':v for m,v in pit.items()},**{f'{m}_interval':v for m,v in intervals.items()})
    print(json.dumps(dict(targets=6344,tests=len(tests),resolved=resolved)))
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--execute',action='store_true');execute() if p.parse_args().execute else freeze()
