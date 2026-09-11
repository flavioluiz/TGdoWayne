from pathlib import Path
import sys,json,time,hashlib,resource
ROOT=Path.cwd();sys.path.insert(0,str(ROOT/'src'))
from inference.campaign_runtime import CampaignRuntime
from inference.campaign_training import train_block
from inference.campaign_iid import produce_target
from inference.campaign_io import write_json_new
out=ROOT/'tmp/c07_integrated_engineering';out.mkdir(exist_ok=True)
configpath=out/'execution.json'
if configpath.exists():raise FileExistsError('Preserve complete or interrupted engineering execution; inspect before replay.')
cfg=json.loads((ROOT/'configs/calibration/campaign_500_prospective.json').read_text())
cfg.update(status='ENGINEERING_WHOLE_FLOW_NOT_SBC500',execution_enabled=True,targets=[0,3,8,9,11,14,20,25,28,35,46,51,52,62,67,78])
cfg['training']['seed']=907130101;cfg['production']['seed']=907130102
cfg['budget'].update(maximum_training_likelihood_values=600000,maximum_production_likelihood_values=6000000,maximum_total_likelihood_values=7000000)
write_json_new(configpath,cfg)
runtime=CampaignRuntime(ROOT/'configs/calibration/pilot_initial.json',ROOT/'results/C07/fixtures/pilot_data.npz',ROOT/'results/C07/orf_interpolation/orf_table_pilot12x4.npz',ROOT/'results/C07/orf_interpolation/orf_table_manifest.json',ROOT/'configs/calibration/pilot_initial.json',configpath,threads=6,training_threads=1,native_library_path=ROOT/'tmp/native/c586a0637ce30e440b8a5235/libpta_likelihood.dylib',native_build_manifest_path=ROOT/'tmp/native/c586a0637ce30e440b8a5235/build_manifest.json')
plan=runtime.preflight();write_json_new(out/'preflight.json',plan);assert plan['execution_ready']
print('READY',plan['targets'],plan['planned_training_plus_production_likelihood_values'],plan['estimated_numeric_bytes'],flush=True)
start=time.perf_counter();runtime.build();buildtime=time.perf_counter()-start
print('BUILT',buildtime,flush=True)
trainstart=time.perf_counter();train_block(runtime,runtime.targets,out/'proposals');traintime=time.perf_counter()-trainstart
print('TRAINED',traintime,flush=True)
rows=[];prodstart=time.perf_counter()
for target in runtime.targets:
 t=time.perf_counter();row=produce_target(runtime,int(target),out/'proposals',out/'production',out/'raw');rows.append(dict(target=int(target),seconds=time.perf_counter()-t))
 print('PRODUCED',rows[-1],flush=True)
productiontime=time.perf_counter()-prodstart
runtime.verify_unchanged();runtime.close()
report=dict(status='PRODUCER_FLOW_EXECUTED_DIAGNOSTICS_PENDING',scope='16 pre-existing engineering targets only; no posterior SBC500',driver_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),identity=runtime.identity,build_seconds=buildtime,training_seconds=traintime,production_seconds=productiontime,total_seconds=time.perf_counter()-start,likelihood_values=runtime.likelihood_evaluations,target_times=rows,raw_bytes=sum(p.stat().st_size for p in (out/'raw').glob('*.npz')),maximum_process_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,truth_deserialized=False)
write_json_new(out/'execution_summary.json',report);print(json.dumps(report),flush=True)
