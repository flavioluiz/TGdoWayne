#!/usr/bin/env python3
"""Independent small-NPZ/JSON audit of all2500 conditional numerical masks."""
import time
START_CPU=time.process_time()
import argparse,hashlib,io,itertools,json,os,resource
from pathlib import Path
for key in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','VECLIB_MAXIMUM_THREADS'):
    if key in os.environ and os.environ[key]!='1':raise RuntimeError('One numerical thread required.')
    os.environ[key]='1'
import numpy as np
from scipy.stats import norm

MODELS=['A0_CN','A_CN','B_CN','A_G','B_G']
FLAGS=('cdf_precision_pass','pooled_weight_guard_pass','saturation_guard_pass','replication_pass','refinement_pass')
PIT_INDICES=[0,5,10,15,20,25]
SPECS=np.array([[level,index,a,b] for level,indices in ((0,PIT_INDICES+[26]),(1,list(range(27)))) for index in indices for a,b in itertools.combinations(range(4),2)])


def digest_bytes(value):return hashlib.sha256(value).hexdigest()

def load_json(path):return json.loads(Path(path).read_bytes())


def audit(args):
    root=Path(args.diagnostics).resolve();summary_bytes=Path(args.summary).read_bytes();summary=json.loads(summary_bytes)
    complete_bytes=Path(args.complete).read_bytes();complete=json.loads(complete_bytes)
    if digest_bytes(summary_bytes)!=args.expected_summary_sha or digest_bytes(complete_bytes)!=args.expected_complete_sha:raise RuntimeError('Closed source hashes differ.')
    if complete['status']!='ALL_TARGET_PRODUCTS_ARCHIVED' or complete['targets']!=list(range(2500)):raise RuntimeError('Closed2500 required.')
    protocol_bytes=Path(args.protocol).read_bytes();protocol=json.loads(protocol_bytes)
    if (protocol['population_targets']!=2500 or protocol['levels']!=[16384,65536] or protocol['cdf_mcse_target']!=.00335
            or protocol['alpha_replicate_family']!=.05 or protocol['alpha_refinement_family']!=.05
            or protocol['maximum_saturated_target_weight']!=1e-12):raise RuntimeError('Numerical protocol changed.')
    npz_bytes=Path(args.arrays).read_bytes()
    if digest_bytes(npz_bytes)!=summary['arrays_sha256']:raise RuntimeError('Aggregate array hash differs.')
    with np.load(io.BytesIO(npz_bytes),allow_pickle=False) as source:
        aggregate={k:source[k] for k in ('resolved','pit','mcse','cut_precision_pass')}
    inventory=summary['provenance']['inventory']
    if len(inventory)!=2500 or sorted(x['target'] for x in inventory)!=list(range(2500)):raise RuntimeError('Every logical target required.')
    by_id={v['target']:v for v in inventory};expected_paths=[f'diagnostic_target_{i:06d}' for i in range(2500)]
    for extension in ('.json','.npz'):
        if sorted(p.name for p in root.glob('diagnostic_target_*'+extension))!=[name+extension for name in expected_paths]:raise RuntimeError('Missing, additional or misnamed compact products.')
    z_rep=float(-norm.ppf(.05/(2*204*2500)));z_ref=float(-norm.ppf(.05/(2*7*2500)))
    result_mask=np.zeros((5,500,6),bool);failure_rows=[];false_targets=[];bytes_read=0;processed=0
    failures_by_flag={name:[] for name in FLAGS};not_resolved_causes={name:0 for name in ('high_CDF_precision','weight_guard','saturation_guard','logZ_replicates','logZ_refinement','own_replicates','own_refinement')}
    max_deletion_error=0.;hash_records=[]
    for target in range(2500):
        if time.process_time()-START_CPU>25:
            break  # Preserve partial scope; never enlarge the authorized30s budget.
        p=root/f'diagnostic_target_{target:06d}.json';jsonbytes=p.read_bytes();meta=json.loads(jsonbytes);item=by_id[target];m,d=divmod(target,500)
        if digest_bytes(jsonbytes)!=item['diagnostic_sha256'] or meta['numeric_sha256']!=item['numeric_sha256'] or meta['diagnostic_inputs']['producer_report_sha256']!=item['producer_sha256']:raise RuntimeError('Frozen JSON/inventory binding differs.')
        if meta['identity']!=summary['provenance']['runtime_identity'] or meta['schema']!='C07_TARGET_IID_DIAGNOSTICS_v1' or meta['status']!='NUMERICAL_DIAGNOSTICS_COMPLETE' or meta['target']!=target or meta['datum']!=d or meta['model']!=MODELS[m] or meta['numeric_file']!=p.with_suffix('.npz').name:raise RuntimeError('Compact identity/schema differs.')
        if meta['diagnostic_inputs']['protocol_sha256']!=digest_bytes(protocol_bytes):raise RuntimeError('Executed compact diagnostic protocol differs.')
        binary=p.with_suffix('.npz').read_bytes();bytes_read+=len(jsonbytes)+len(binary)
        if digest_bytes(binary)!=item['numeric_sha256']:raise RuntimeError('Compact NPZ hash differs from closed synthesis.')
        with np.load(io.BytesIO(binary),allow_pickle=False) as archive:
            a={key:archive[key] for key in ('target','datum','model_index','pit','pit_mcse','pit_precision_pass','pit_resolved','cdf_mcse_by_level','cdf_precision_by_level','cdf_resolved_by_level','cut_precision_pass','replication_specification','replication_difference','replication_mcse','replication_resolved','replication_pass','refinement_difference','refinement_mcse','refinement_resolved','refinement_pass','weight_deletion_guard_by_level','saturated_weight')}
        if [int(a[k]) for k in ('target','datum','model_index')]!=[target,d,m] or not np.array_equal(a['replication_specification'],SPECS):raise RuntimeError('Numeric indices or204 contrast specifications differ.')
        errors=a['cdf_mcse_by_level'];resolved=np.isfinite(errors);precision=resolved&(errors>0)&(errors<=.00335)
        if errors.shape!=(2,26) or np.isnan(errors).any() or (errors<=0).any() or not np.array_equal(a['cdf_resolved_by_level'],resolved) or not np.array_equal(a['cdf_precision_by_level'],precision):raise RuntimeError('CDF flags disagree with error values.')
        if not np.array_equal(a['pit_mcse'],errors[1,PIT_INDICES]) or not np.array_equal(a['pit_resolved'],resolved[1,PIT_INDICES]) or not np.array_equal(a['pit_precision_pass'],precision[1,PIT_INDICES]):raise RuntimeError('PIT extraction differs.')
        cut_indices=np.array([[j*5+k for k in range(1,5)] for j in range(5)])
        if not np.array_equal(a['cut_precision_pass'],precision[1,cut_indices]) or not np.array_equal(a['cut_precision_pass'],aggregate['cut_precision_pass'][m,d]):raise RuntimeError('Twenty cut precision flags differ.')
        computed={}
        for name,n,z in (('replication',204,z_rep),('refinement',7,z_ref)):
            difference=a[name+'_difference'];se=a[name+'_mcse']
            if se.shape!=(n,) or difference.shape!=(n,) or not np.isfinite(difference).all() or np.isnan(se).any() or (se<0).any():raise RuntimeError('Invalid finite contrast data.')
            resolved_c=np.isfinite(se)&(se>0);passed=resolved_c&(np.abs(difference)<=z*se)
            if not np.array_equal(a[name+'_resolved'],resolved_c) or not np.array_equal(a[name+'_pass'],passed):raise RuntimeError('Stored contrast flags differ from independent Bonferroni reconstruction.')
            computed[name]=passed
        weights=[]
        for row in meta['summary']['weights_by_level']:
            w=row['maximum_normalized_weight']
            if not 0<=w<1:raise RuntimeError('Observed maximum weight outside the usable finite domain.')
            deletion=w/(1-w);max_deletion_error=max(max_deletion_error,abs(deletion-row['single_deletion_cdf_bound']))
            if abs(deletion-row['single_deletion_cdf_bound'])>2e-15:raise RuntimeError('Single-deletion algebra differs.')
            passed=deletion<=.00335
            if row['single_deletion_guard_pass'] is not bool(passed):raise RuntimeError('JSON deletion flag differs from observed maximum weight.')
            weights.append(passed)
        if len(weights)!=2 or not np.array_equal(a['weight_deletion_guard_by_level'],weights):raise RuntimeError('Both weight guards differ.')
        saturation=a['saturated_weight']
        if saturation.shape!=(2,4) or not np.isfinite(saturation).all() or (saturation<0).any() or (saturation>1).any():raise RuntimeError('Invalid saturated weight mass.')
        sat_pass=bool((saturation<=1e-12).all());weight_pass=all(weights)
        flags=dict(cdf_precision_pass=bool(precision[1].all()),pooled_weight_guard_pass=weight_pass,saturation_guard_pass=sat_pass,replication_pass=bool(computed['replication'].all()),refinement_pass=bool(computed['refinement'].all()))
        if any(type(meta['summary'][k]) is not bool or meta['summary'][k]!=v for k,v in flags.items()):raise RuntimeError('JSON five numerical flags differ from compact numerics.')
        if not all(flags.values()):
            false_targets.append(target);failure_rows.append(dict(target=target,model=MODELS[m],datum=d,false_flags=[k for k,v in flags.items() if not v]))
        for k,v in flags.items():
            if not v:failures_by_flag[k].append(target)
        zrep=bool(computed['replication'][SPECS[:,1]==26].all());zref=bool(computed['refinement'][6])
        for j,index in enumerate(PIT_INDICES):
            ownrep=bool(computed['replication'][SPECS[:,1]==index].all());ownref=bool(computed['refinement'][j]);prec=bool(precision[1,index])
            causes=dict(high_CDF_precision=prec,weight_guard=weight_pass,saturation_guard=sat_pass,logZ_replicates=zrep,logZ_refinement=zref,own_replicates=ownrep,own_refinement=ownref)
            result_mask[m,d,j]=all(causes.values())
            for name,ok in causes.items():
                if not ok:not_resolved_causes[name]+=1
        if not np.array_equal(a['pit'],aggregate['pit'][m,d]) or not np.array_equal(a['pit_mcse'],aggregate['mcse'][m,d]):raise RuntimeError('Aggregated PIT/MCSE differs from individual compact data.')
        hash_records.append(dict(target=target,json_sha256=digest_bytes(jsonbytes),npz_sha256=digest_bytes(binary)))
        processed+=1
    complete_scope=processed==2500
    mismatch=[]
    if complete_scope:
        mismatch=np.argwhere(result_mask!=aggregate['resolved']).tolist()
        if false_targets!=complete['numerically_unresolved_targets']:raise RuntimeError('The81 target flags disagree with campaign closure.')
    counts_by_model=[dict(model=MODELS[m],failed_targets=sum(t//500==m for t in false_targets),unresolved_by_function=(~result_mask[m]).sum(axis=0).tolist(),all_six_resolved=int(result_mask[m].all(axis=1).sum())) for m in range(5)] if complete_scope else None
    result=dict(status=('PASS' if not mismatch else 'FAIL_MASK') if complete_scope else 'PARTIAL_RESOURCE_LIMIT_PRESERVED',scope='COMPACT_JSON_NPZ_DIAGNOSTIC_MASK_RECONSTRUCTION_NOT_INFERENCE',processed_targets=processed,all_2500_hashes_verified=complete_scope,summary_mask_mismatches=mismatch,targets_with_any_of_five_numerical_flags_false=len(false_targets),unresolved_PIT_functions=int((~result_mask).sum()) if complete_scope else None,failed_target_inventory=failure_rows,targets_by_failed_flag=failures_by_flag,unresolved_cause_occurrences=not_resolved_causes,causes_may_overlap=True,per_model=counts_by_model,maximum_single_deletion_formula_difference=max_deletion_error,compact_bytes_read=bytes_read,source_sha256=digest_bytes(Path(__file__).read_bytes()),input_sha256={str(Path(args.summary).resolve()):digest_bytes(summary_bytes),str(Path(args.complete).resolve()):digest_bytes(complete_bytes),str(Path(args.arrays).resolve()):digest_bytes(npz_bytes),str(Path(args.protocol).resolve()):digest_bytes(protocol_bytes)},process_cpu_seconds=time.process_time()-START_CPU,maximum_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,raw_reads=0,ORF_evaluations=0,likelihood_evaluations=0,root_helpers_imported=False,maximum_cpu_seconds=30,maximum_rss_bytes_allowed=256*1024**2)
    if result['process_cpu_seconds']>30 or result['maximum_rss_bytes']>256*1024**2:result['status']='FAIL_RESOURCE'
    out=Path(args.output)
    if out.exists():raise FileExistsError('Preserve previous independent mask audit.')
    out.mkdir(parents=True);(out/'review.json').write_text(json.dumps(result,indent=2)+'\n');(out/'hash_inventory.json').write_text(json.dumps(hash_records,indent=2)+'\n')
    if complete_scope:np.save(out/'independent_resolved.npy',result_mask,allow_pickle=False)
    print(json.dumps({k:result[k] for k in ('status','processed_targets','targets_with_any_of_five_numerical_flags_false','unresolved_PIT_functions','process_cpu_seconds','maximum_rss_bytes')}))
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('diagnostics','summary','complete','arrays','protocol','output'):p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--expected-summary-sha',required=True);p.add_argument('--expected-complete-sha',required=True)
    args=p.parse_args();result=audit(args);raise SystemExit(result['status']!='PASS')
