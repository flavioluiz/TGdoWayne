#!/usr/bin/env python3
"""Independent audit of CLOSED fixed96 products. No ROOT scientific helpers."""
import time
START_CPU=time.process_time()
from pathlib import Path
import argparse,hashlib,io,itertools,json,os,resource
for key in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','VECLIB_MAXIMUM_THREADS'):
    if key in os.environ and os.environ[key]!='1':raise RuntimeError('One numerical thread required.')
    os.environ[key]='1'
import numpy as np
from scipy.stats import beta,norm

FUNCTIONS=['u','log10_Agw','gamma_gw','log10_Ar','log10_EFAC','logL_at_truth']
SCENARIOS=['mass_zero_signal_present','near_kinematic_edge','no_gravitational_signal']
PIT=[0,5,10,15,20,25];PROBS=[.05,.5,.9,.95]
FLAGS=['cdf_precision_pass','pooled_weight_guard_pass','saturation_guard_pass','replication_pass','refinement_pass']


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def read(path):return json.loads(Path(path).read_bytes())

def assert_(condition,detail):
    if not condition:raise RuntimeError(detail)


class Checks:
    def __init__(self):self.n=0;self.max_difference=0.;self.differences=[]
    def same(self,name,a,b,*,exact=False):
        self.n+=1;a=np.asarray(a);b=np.asarray(b)
        numeric=a.dtype.kind in 'fiub' and b.dtype.kind in 'fiub'
        if exact or not numeric:
            ok=a.shape==b.shape and (np.array_equal(a,b,equal_nan=True) if numeric else np.array_equal(a,b))
        else:
            ok=a.shape==b.shape and np.allclose(a,b,atol=5e-12,rtol=2e-11,equal_nan=True)
            if a.shape==b.shape and a.size:
                good=np.isfinite(a)&np.isfinite(b)
                if good.any():
                    error=float(np.max(np.abs(a[good].astype(float)-b[good].astype(float))))
                    self.max_difference=max(self.max_difference,error)
                    if error:self.differences.append(dict(field=name,maximum_absolute_difference=error))
        assert_(ok,'Independent mismatch: '+name)


def expected_masks(target):
    applicable=np.ones(6,bool);structural=np.zeros(6,bool)
    if target<32:structural[0]=True
    if target>=64:applicable[[0,1,2,5]]=False
    cdf_app=np.ones(26,bool);cdf_app[PIT]=applicable
    exact=np.zeros(26,bool);exact[PIT]=structural
    return applicable,structural,cdf_app,exact


def expected_contrasts(target):
    app,struct,capp,exact=expected_masks(target);indices=[j for j in PIT if capp[j] and not exact[j]]
    low=[j for j in PIT if capp[j] and not exact[j]]+[26]
    high=[j for j in range(26) if capp[j] and not exact[j]]+[26]
    return np.array([[level,j,a,b] for level,values in enumerate((low,high)) for j in values for a,b in itertools.combinations(range(4),2)]),np.array(indices+[26])


def cp(k,n=32):
    return [0. if k==0 else float(beta.ppf(.025,k,n-k+1)),1. if k==n else float(beta.isf(.025,k+1,n-k))]


def coverage(p,a,b,central=False,structural=False):
    p,a,b=map(np.asarray,(p,a,b))
    assert_(p.shape==a.shape==b.shape==(32,) and np.isfinite([p,a,b]).all() and np.all((0<=a)&(a<=p)&(p<=b)&(b<=1)),'32 valid containing PIT intervals required.')
    if structural:assert_(np.all(p==0)&np.all(a==0)&np.all(b==0),'Structural u0 must be exactly zero.')
    hit=((p>=.05)&(p<=.95)) if central else p<=.9
    certain=((a>=.05)&(b<=.95)) if central else b<=.9
    possible=((b>=.05)&(a<=.95)) if central else a<=.9
    n=int(hit.sum());nmin=int(certain.sum());nmax=int(possible.sum())
    return dict(n=32,calculated_count=n,calculated_fraction=n/32,pointwise_cp95=cp(n),certainly_covered=nmin,possibly_covered=nmax,coverage_fraction_sensitivity=[nmin/32,nmax/32],pointwise_cp95_union_over_count_range=[cp(nmin)[0],cp(nmax)[1]],approximate_numerical_sensitivity_not_exact_confidence=True,interval='central_equal_tail_90' if central else 'prior_lower_bound_to_upper90',structural_population_coverage=(0. if central else 1.) if structural else None,structural_exception=bool(structural),no_test_of_universal_nominal_coverage=True)


def numerical_target(check,target,a,meta,truth,logl,bounds):
    applicable,structural,capp,exact=expected_masks(target)
    for key,value in dict(target=target,datum=target,model_index=0,scenario_index=target//32,replicate_within_scenario=target%32).items():check.same(str(target)+'.'+key,a[key],value,exact=True)
    for key,value in dict(pit_applicable=applicable,pit_structural_exact=structural,cdf_applicable=capp,cdf_structural_exact=exact,cdf_numerically_evaluated=capp&~exact,truth_defined=applicable[:5]).items():check.same(str(target)+'.'+key,a[key],value,exact=True)
    check.same('truth',a['truth_physical'],truth,exact=True);check.same('unit_truth',a['truth_unit'],(truth-bounds[:,0])/(bounds[:,1]-bounds[:,0]),exact=True)
    check.same('truth_logL',a['truth_log_likelihood'],logl,exact=True);check.same('truth_logL_defined',a['truth_log_likelihood_defined'],target<64,exact=True)
    check.same('probs',a['probabilities'],PROBS,exact=True)
    q=a['quantiles_unit'];assert_(q.shape==(5,4) and np.isfinite(q).all() and np.all((q>=0)&(q<=1)) and np.all(np.diff(q,axis=1)>=0),'All20 finite monotone quantiles required.')
    check.same('physical_quantiles',a['quantiles_physical'],bounds[:,0,None]+(bounds[:,1]-bounds[:,0])[:,None]*q,exact=True)
    p=a['cdf_estimates_by_level'];se=a['cdf_mcse_by_level'];numeric=capp&~exact
    assert_(p.shape==se.shape==(2,26),'Two full26-CDF levels required.')
    assert_(np.isnan(p[:,~capp]).all() and np.isnan(se[:,~capp]).all(),'Undefined CDF slots must remain NaN.')
    assert_(np.isfinite(p[:,capp]).all() and np.all((p[:,capp]>=0)&(p[:,capp]<=1)),'Applicable CDFs must be probabilities.')
    assert_(np.all(p[:,exact]==0) and np.all(se[:,exact]==0),'Structural F_u(0)=0,MCSE0 required.')
    assert_(not np.isnan(se[:,numeric]).any() and np.all(se[:,numeric]>0),'Only structural constants may have MCSE0.')
    resolved=np.isfinite(se)&capp[None,:];precision=resolved&(se<=.00335)
    for key,value in dict(cdf_resolved_by_level=resolved,cdf_precision_by_level=precision,pit=p[1,PIT],pit_mcse=se[1,PIT],pit_resolved=resolved[1,PIT],pit_precision_pass=precision[1,PIT]).items():check.same(key,a[key],value,exact=True)
    cut=np.array([[j*5+k for k in range(1,5)] for j in range(5)])
    for key,value in dict(cut_cdf=p[1,cut],cut_mcse=se[1,cut],cut_resolved=resolved[1,cut],cut_precision_pass=precision[1,cut]).items():check.same(key,a[key],value,exact=True)
    reps,refs=expected_contrasts(target);check.same('rep_specs',a['replication_specification'],reps,exact=True);check.same('ref_specs',a['refinement_specification'],refs,exact=True)
    passes={}
    for prefix,family,size in [('replication',19584,len(reps)),('refinement',672,len(refs))]:
        diff=a[prefix+'_difference'];err=a[prefix+'_mcse'];assert_(diff.shape==err.shape==(size,) and np.isfinite(diff).all() and not np.isnan(err).any() and np.all(err>=0),'Valid finite contrasts required.')
        valid=np.isfinite(err)&(err>0);passed=valid&(np.abs(diff)<=float(-norm.ppf(.05/(2*family)))*err)
        check.same(prefix+'_resolved',a[prefix+'_resolved'],valid,exact=True);check.same(prefix+'_pass',a[prefix+'_pass'],passed,exact=True);passes[prefix]=passed
    weight=a['weight_deletion_guard_by_level'];sat=a['saturated_weight']
    assert_(weight.dtype.kind=='b' and weight.shape==(2,) and sat.shape==(2,4) and np.isfinite(sat).all() and np.all((sat>=0)&(sat<=1)),'Finite both-level weight/saturation records required.')
    common=bool(weight.all() and (sat<=1e-12).all() and passes['replication'][reps[:,1]==26].all() and passes['refinement'][refs==26].all())
    output=structural.copy()
    for j,index in enumerate(PIT):
        if applicable[j] and not structural[j]:
            output[j]=common and precision[1,index] and bool(passes['replication'][reps[:,1]==index].all()) and bool(passes['refinement'][refs==index].all())
    flags=dict(cdf_precision_pass=bool(precision[1,capp].all()),pooled_weight_guard_pass=bool(weight.all()),saturation_guard_pass=bool((sat<=1e-12).all()),replication_pass=bool(passes['replication'].all()),refinement_pass=bool(passes['refinement'].all()))
    for key,value in flags.items():
        assert_(type(meta['summary'][key]) is bool,'Strict numerical bool required.');check.same('summary.'+key,meta['summary'][key],value,exact=True)
    return output,flags,len(reps),len(refs)


def audit(args):
    check=Checks();paths={k:Path(getattr(args,k)).resolve() for k in ('summary','arrays','campaign','synthesis_config','numerical_protocol','scientific_protocol','experiment','data','generation')}
    complete_path=paths['campaign']/'campaign_complete.json';plan_path=paths['campaign']/'campaign_plan.json'
    assert_(sha(paths['summary'])==args.expected_summary_sha and sha(complete_path)==args.expected_complete_sha,'Exact closed summary and complete hashes required.')
    report=read(paths['summary']);complete=read(complete_path);plan=read(plan_path);cfg=read(paths['synthesis_config']);num=read(paths['numerical_protocol']);sci=read(paths['scientific_protocol']);exp=read(paths['experiment']);gen=read(paths['generation'])
    assert_(complete['status']=='ALL_TARGET_PRODUCTS_ARCHIVED' and complete['scope']=='FIXED_TRUTH96_NOT_SBC' and complete['targets']==list(range(96)) and complete['driver_identity']==plan['driver_identity'],'Full closed96 A0 campaign required.')
    check.same('config',json.dumps(report['config'],sort_keys=True),json.dumps(cfg,sort_keys=True),exact=True)
    assert_(cfg['population_targets']==96 and cfg['models']==['A0_CN'] and cfg['discard_realizations'] is False and cfg['pointwise_cp_alpha']==.05 and cfg['uniformity_tests'] is False and cfg['coverage_null_hypothesis'] is None,'Fixed conditional scope required.')
    assert_(cfg['numerical_sensitivity']==dict(family_size=576,alpha_mc=.01,deterministic_component=.002,cdf_mcse_target=.00335),'Family576 may not shrink for omissions.')
    assert_(num['global_replicate_contrasts']==19584 and num['global_refinement_contrasts']==672 and num['population_targets']==96 and num['cdf_mcse_target']==.00335 and num['levels']==[16384,65536],'Frozen numerical denominators required.')
    assert_(sci['repetitions_per_scenario']==32 and sci['parameter_order']==FUNCTIONS[:5] and [v['id'] for v in sci['scenarios']]==SCENARIOS,'Exactly32 per fixed scenario required.')
    for key,argkey in [('data','data'),('experiment','experiment'),('generation','generation'),('scientific_protocol','scientific_protocol'),('numerical_protocol','numerical_protocol')]:check.same('bound.'+key,cfg['sources'][key]['sha256'],sha(paths[argkey]),exact=True)
    assert_(gen['status']=='FIXED_DATA_GENERATED_NOT_POSTERIOR_INFERENCE' and gen['data_sha256']==sha(paths['data']) and gen['absent_signal_covariance_exactly_zero'] is True,'Exact absent GW generation provenance required.')
    for path,value in report['executed_source_sha256'].items():check.same('executed_source',sha(path),value,exact=True)
    check.same('arrays_hash',sha(paths['arrays']),report['arrays_sha256'],exact=True)
    with np.load(paths['arrays'],allow_pickle=False) as archive:arrays={k:archive[k] for k in archive.files}
    assert_(sum(v.nbytes for v in arrays.values())<64*1024**2,'Small compact-array bound exceeded.')
    with np.load(paths['data'],allow_pickle=False) as source:
        original={key:source[key] for key in ('truth','truth_defined','log_likelihood_at_truth','log_likelihood_at_truth_defined','structural_lower_boundary_pit','target','scenario_index','replicate_within_scenario')}
    truth=np.repeat(np.array([[np.nan if v is None else v for v in row['truth']] for row in sci['scenarios']]),32,axis=0);bounds=np.asarray(exp['prior']['bounds'])
    check.same('truth_prior',arrays['truth'],truth,exact=True);check.same('truth_generation',original['truth'],truth,exact=True);check.same('targets',arrays['targets'],np.arange(96),exact=True)
    masks=[expected_masks(i) for i in range(96)];app=np.array([x[0] for x in masks]);struct=np.array([x[1] for x in masks]);check.same('applicable',arrays['pit_applicable'],app,exact=True);check.same('structural',arrays['pit_structural_exact'],struct,exact=True)
    check.same('generation.truth_defined',original['truth_defined'],app[:,:5],exact=True);check.same('generation.logL_defined',original['log_likelihood_at_truth_defined'],np.arange(96)<64,exact=True);check.same('generation.structural',original['structural_lower_boundary_pit'],struct[:,:5],exact=True)
    assert_(np.isfinite(original['log_likelihood_at_truth'][:64]).all() and np.isnan(original['log_likelihood_at_truth'][64:]).all(),'noGW logL truth must stay undefined.')
    inventory=report['provenance']['inventory'];assert_(len(inventory)==96 and [x['target'] for x in inventory]==list(range(96)),'All96 ordered compact inventory required.')
    mask=np.zeros((96,6),bool);failed=[];total_rep=total_ref=0;individual=[]
    diagnostic_root=paths['campaign']/'diagnostics'
    for suffix in ('.json','.npz'):assert_(sorted(p.name for p in diagnostic_root.glob('diagnostic_target_*'+suffix))==[f'diagnostic_target_{i:06d}'+suffix for i in range(96)],'No missing/extra compact products.')
    for t,item in enumerate(inventory):
        if time.process_time()-START_CPU>25:raise RuntimeError('Stop before30s total CPU; no expansion.')
        jsonpath=diagnostic_root/f'diagnostic_target_{t:06d}.json';npzpath=jsonpath.with_suffix('.npz');meta=read(jsonpath)
        check.same('compact_json_sha',sha(jsonpath),item['diagnostic_sha256'],exact=True);check.same('compact_npz_sha',sha(npzpath),item['numeric_sha256'],exact=True)
        assert_(meta['schema']=='C07_FIXED_MASKED_IID_DIAGNOSTICS_v2_OPERATIONAL' and meta['scope']=='FIXED_TRUTH96_NOT_SBC' and meta['status']=='NUMERICAL_DIAGNOSTICS_COMPLETE' and meta['identity']==plan['identity'] and meta['target']==t and meta['datum']==t and meta['model']=='A0_CN' and meta['raw_release_authorized'] is False,'Fixed diagnostic identity/scope differs.')
        with np.load(npzpath,allow_pickle=False) as archive:a={k:archive[k] for k in archive.files}
        own,flags,nrep,nref=numerical_target(check,t,a,meta,truth[t],original['log_likelihood_at_truth'][t],bounds);mask[t]=own;total_rep+=nrep;total_ref+=nref
        for key in ('pit','pit_mcse','pit_applicable','pit_structural_exact','quantiles_unit','quantiles_physical','cut_precision_pass'):check.same('aggregate.'+key,arrays[key][t],a[key],exact=True)
        if not all(flags.values()):failed.append(t)
        producer_path=paths['campaign']/'production'/f'target_{t:06d}.json';producer=read(producer_path);receipt_path=producer_path.parent/f'archive_receipt_target_{t:06d}.json';receipt=read(receipt_path)
        check.same('producer_sha',sha(producer_path),item['producer_sha256'],exact=True);check.same('receipt_sha',sha(receipt_path),item['archive_sha256'],exact=True)
        assert_(producer['uses_truth'] is False and producer['identity']==plan['identity'] and producer['target']==t and producer['model']=='A0_CN','Frozen producer identity/observation-only contract differs.')
        check.same('diagnostic_protocol',meta['diagnostic_inputs']['protocol_sha256'],sha(paths['numerical_protocol']),exact=True);check.same('diagnostic_generation',meta['diagnostic_inputs']['generation_sha256'],sha(paths['generation']),exact=True)
        roles={x['role']:x['sha256'] for x in receipt['artifacts']}
        for role,expected in dict(producer=item['producer_sha256'],diagnostic=item['diagnostic_sha256'],numeric=item['numeric_sha256'],proposal=meta['proposal_sha256']).items():check.same('archive.'+role,roles[role],expected,exact=True)
        status='RECORDED_NUMERICAL_CHECKS_PASSED' if all(flags.values()) else 'NUMERICALLY_UNRESOLVED'
        for key in FLAGS:check.same('archive_flag.'+key,receipt['numerical_flags'][key],flags[key],exact=True)
        check.same('archive_status',receipt['numerical_status'],status,exact=True)
        individual.append(dict(target=t,json_sha256=sha(jsonpath),npz_sha256=sha(npzpath),producer_sha256=sha(producer_path),archive_sha256=sha(receipt_path)))
    check.same('mask',arrays['resolved_for_function'],mask,exact=True);check.same('failed_targets',complete['numerically_unresolved_targets'],failed,exact=True)
    check.same('replicate_count',total_rep,17664,exact=True);check.same('refinement_count',total_ref,512,exact=True)
    p=arrays['pit'];se=arrays['pit_mcse'];numeric=app&~struct;lo=np.full((96,6),np.nan);hi=np.full((96,6),np.nan);lo[struct]=hi[struct]=0
    finite_mask=mask&numeric;unresolved=~mask&numeric;z=float(-norm.ppf(.01/(2*576)))
    lo[finite_mask]=np.maximum(0,p[finite_mask]-.002-z*se[finite_mask]);hi[finite_mask]=np.minimum(1,p[finite_mask]+.002+z*se[finite_mask]);lo[unresolved]=0;hi[unresolved]=1
    check.same('envelope.lo',arrays['pit_lower'],lo);check.same('envelope.hi',arrays['pit_upper'],hi);check.same('envelope.z',report['numerical_sensitivity']['z'],z)
    assert_(np.isnan(p[~app]).all() and np.isnan(se[~app]).all() and np.isnan(lo[~app]).all() and np.isnan(hi[~app]).all(),'Undefined slots were replaced instead of masked.')
    assert_(np.all(p[struct]==0) and np.all(se[struct]==0) and np.all(mask[struct]),'Structural support proof must remain exact and resolved.')
    check.same('report.scope',report['scope'],'FIXED96_CONDITIONAL_STRESS_SUMMARY_NOT_SBC',exact=True)
    for key in ('all_ids_retained','no_KS_or_uniformity_test','pointwise_CP_only_no_familywise_claim','no_Bayes_factors','numerical_failures_do_not_trigger_target_selection'):check.same('scope.'+key,report[key],True,exact=True)
    assert_(len(report['scenarios'])==3 and len(report['functions'])==18 and len(report['quantiles'])==15,'Complete scenario/function/quantile inventory required.')
    grid=np.linspace(0,1,101);check.same('ecdf_grid',arrays['ecdf_grid'],grid,exact=True);coverage_rows=[]
    for scenario,name in enumerate(SCENARIOS):
        sl=slice(scenario*32,(scenario+1)*32);row=report['scenarios'][scenario]
        for key,value in dict(id=name,targets=list(range(scenario*32,(scenario+1)*32)),n=32,applicable_pits=int(app[sl].sum()),structural_pits=int(struct[sl].sum()),numerically_resolved_nonstructural_pits=int((mask[sl]&~struct[sl]).sum()),unresolved_nonstructural_pits=int((app[sl]&~mask[sl]).sum())).items():check.same('scenario.'+key,row[key],value,exact=True)
        for j,parameter in enumerate(FUNCTIONS):
            row=report['functions'][scenario*6+j];check.same('function.name',row['parameter'],parameter,exact=True);check.same('function.scenario',row['scenario'],name,exact=True);check.same('function.applicable',row['applicable'],bool(app[sl,j].all()),exact=True)
            if not app[sl,j].all():
                assert_(not any(key in row for key in ('upper90','central90','calculated_pit_quantiles','ecdf_lower','ecdf_upper')),'Undefined truth cannot receive coverage/PIT summaries.');continue
            for key,value in dict(n=32,target_ids=list(range(scenario*32,(scenario+1)*32)),resolved_count=int(mask[sl,j].sum()),structural_count=int(struct[sl,j].sum()),calculated_pit_quantiles=np.quantile(p[sl,j],[.05,.5,.95]),ecdf_lower=np.mean(hi[sl,j,None]<=grid[None,:],axis=0),ecdf_upper=np.mean(lo[sl,j,None]<=grid[None,:],axis=0),conditional_distribution_not_expected_to_be_uniform=True).items():check.same('function.'+key,row[key],value)
            if j<5:
                for key,central in [('upper90',False),('central90',True)]:
                    own=coverage(p[sl,j],lo[sl,j],hi[sl,j],central,bool(struct[sl,j].all()))
                    for field,value in own.items():check.same('coverage.'+field,row[key][field],value)
                    assert_(not any('pvalue' in key.lower() for key in row[key]),'No universal nominal-coverage null test permitted.')
                    coverage_rows.append(dict(scenario=name,parameter=parameter,interval=key,count=own['calculated_count'],possible_count_range=[own['certainly_covered'],own['possibly_covered']],cp95=own['pointwise_cp95']))
            else:assert_('upper90' not in row and 'central90' not in row,'No logL quantile-coverage claim.')
        for j,parameter in enumerate(FUNCTIONS[:5]):
            row=report['quantiles'][scenario*5+j];q=arrays['quantiles_physical'][sl,j]
            for key,value in dict(scenario=name,parameter=parameter,probabilities=PROBS,across32_quantiles_min_median_max=np.array([q.min(axis=0),np.median(q,axis=0),q.max(axis=0)]),precise_independent_cut_counts=arrays['cut_precision_pass'][sl,j].sum(axis=0),descriptive_only=True,no_recovery_bias_if_truth_undefined=not bool(app[sl,j].all()),CDF_precision_does_not_certify_horizontal_quantile_error=True).items():check.same('quantile.'+key,row[key],value)
    result=dict(status='PASS',scope='CLOSED_FIXED96_INDEPENDENT_ARITHMETIC_MASK_AND_INVENTORY_AUDIT',checks=check.n,maximum_absolute_difference=check.max_difference,largest_differences=sorted(check.differences,key=lambda x:x['maximum_absolute_difference'],reverse=True)[:15],targets=96,scenarios=report['scenarios'],applicable_PITs=int(app.sum()),structural_PITs=int(struct.sum()),undefined_PIT_slots=int((~app).sum()),unresolved_applicable_PITs=int(unresolved.sum()),targets_any_global_flag_false=failed,quantiles_retained=96*20,executed_replicate_contrasts=total_rep,executed_refinement_contrasts=total_ref,coverage=coverage_rows,source_sha256=sha(__file__),input_sha256={str(path):sha(path) for key,path in paths.items() if key!='campaign'}|{str(complete_path):sha(complete_path),str(plan_path):sha(plan_path)},process_cpu_seconds=time.process_time()-START_CPU,maximum_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,raw_reads=0,ORF_evaluations=0,likelihood_evaluations=0,ROOT_helpers_imported=False,limits=dict(CPU_seconds=30,RSS_bytes=256*1024**2),limitations=['Fixed truth is not prior-predictive SBC; no uniformity test or universal nominal Bayesian coverage is imposed.','CP intervals are pointwise for32 conditional realizations; numerical envelopes remain approximate sensitivity.','All20 quantiles remain descriptive including parameters without a generating truth.','Full raw/RNG replay and physical generation are not repeated; linked generation/configuration and compact artifacts are verified.'])
    assert_(result['process_cpu_seconds']<=30 and result['maximum_rss_bytes']<=256*1024**2,'Resource cap exceeded.')
    out=Path(args.output);assert_(not out.exists(),'Preserve prior audit outputs.');out.mkdir(parents=True);(out/'review.json').write_text(json.dumps(result,indent=2)+'\n');(out/'hash_inventory.json').write_text(json.dumps(individual,indent=2)+'\n');np.save(out/'independent_resolved.npy',mask,allow_pickle=False)
    print(json.dumps({k:result[k] for k in ('status','checks','maximum_absolute_difference','targets','applicable_PITs','structural_PITs','undefined_PIT_slots','unresolved_applicable_PITs','process_cpu_seconds','maximum_rss_bytes')}));return result


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('summary','arrays','campaign','synthesis_config','numerical_protocol','scientific_protocol','experiment','data','generation','output'):parser.add_argument('--'+name.replace('_','-'),type=Path,required=True)
    parser.add_argument('--expected-summary-sha',required=True);parser.add_argument('--expected-complete-sha',required=True)
    audit(parser.parse_args())
