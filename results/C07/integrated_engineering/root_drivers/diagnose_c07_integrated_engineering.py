from pathlib import Path
import sys,json,time,hashlib
import numpy as np
ROOT=Path.cwd();sys.path.insert(0,str(ROOT/'src'))
from inference.campaign_runtime import CampaignRuntime
from inference.campaign_diagnostics import diagnose_target
from inference.campaign_diagnostic_io import load_target_levels
from inference.iid_optimized import compare_brackets
from inference.campaign_archive import prepare_archive
from inference.campaign_iid import release_raw
from inference.campaign_io import write_json_new
out=ROOT/'tmp/c07_integrated_engineering';proto=out/'diagnostic_protocol.json'
cfg=json.loads((ROOT/'configs/calibration/campaign_diagnostics_v1.json').read_text());cfg.update(scope='16 engineering targets only',population_targets=16,global_replicate_contrasts=3264,global_refinement_contrasts=112)
write_json_new(proto,cfg)
runtime=CampaignRuntime(ROOT/'configs/calibration/pilot_initial.json',ROOT/'results/C07/fixtures/pilot_data.npz',ROOT/'results/C07/orf_interpolation/orf_table_pilot12x4.npz',ROOT/'results/C07/orf_interpolation/orf_table_manifest.json',ROOT/'configs/calibration/pilot_initial.json',out/'execution.json',threads=6,training_threads=1,native_library_path=ROOT/'tmp/native/c586a0637ce30e440b8a5235/libpta_likelihood.dylib',native_build_manifest_path=ROOT/'tmp/native/c586a0637ce30e440b8a5235/build_manifest.json')
start=time.perf_counter();rows=[]
for target in runtime.targets:
 r=diagnose_target(runtime,out/f'production/target_{target:06d}.json',out/'raw',ROOT/'results/C07/fixtures/pilot_data.npz',proto,out/'diagnostics',truth_loglikelihood_path=out/'truth_log_likelihood.json');rows.append(r)
 print('DIAGNOSTIC',target,r['summary']['high_cdf_precision_pass'],r['summary']['maximum_finite_high_mcse'],r['summary']['replication_pass'],r['summary']['refinement_pass'],flush=True)
ref=json.loads((ROOT/'results/C07/reference/quantiles/posterior_reference.json').read_text());bounds=np.asarray(ref['prior_bounds_original']);width=np.diff(bounds,axis=1)[:,0];br=(np.asarray(ref['brackets_original'])-bounds[:,0,None,None])/width[:,None,None]
record,levels=load_target_levels(out/'production/target_000014.json',out/'raw');a=levels[65536]
reference=compare_brackets(a['x_unit'],a['log_weights'],br,ref['probabilities'],ref['endpoint_CDF_fine139'],ref['endpoint_CDF_resolution_spread'],ref['endpoint_CDF_omission_bound'])
write_json_new(out/'A0d14_reference.json',reference)
print('REFERENCE',reference['consistent_brackets'],reference['brackets_passing_mc_precision'],flush=True)
for target in runtime.targets:
 prepare_archive(runtime,int(target),out/'proposals',out/'production',out/f'diagnostics/diagnostic_target_{target:06d}.json')
 release_raw(runtime,int(target),out/'production',out/'raw',out/f'production/archive_receipt_target_{target:06d}.json')
report=dict(status='WHOLE_FLOW_EXECUTED_WITH_EXPLICIT_NUMERICAL_FLAGS',identity=runtime.identity,seconds=time.perf_counter()-start,cdf_precise=sum(r['summary']['high_cdf_precision_pass'] for r in rows),cdf_total=416,all_cdf_precise_targets=sum(r['summary']['cdf_precision_pass'] for r in rows),replication_pass=all(r['summary']['replication_pass'] for r in rows),refinement_pass=all(r['summary']['refinement_pass'] for r in rows),all_pooled_weight_guards=all(r['summary']['pooled_weight_guard_pass'] for r in rows),all_saturation_guards=all(r['summary']['saturation_guard_pass'] for r in rows),reference_consistent=reference['consistent_brackets'],reference_precise=reference['brackets_passing_mc_precision'],raw_count_after_release=len(list((out/'raw').glob('*.npz'))),driver_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),kernel_built_in_diagnostic=False,PTA_SBC500_executed=False)
write_json_new(out/'diagnostic_summary.json',report);print(json.dumps(report),flush=True)
