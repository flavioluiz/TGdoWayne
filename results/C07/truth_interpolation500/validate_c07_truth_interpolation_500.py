from pathlib import Path
import sys,json,time,hashlib
import numpy as np
ROOT=Path.cwd();sys.path.insert(0,str(ROOT/'src'))
from inference.campaign_runtime import CampaignRuntime
from inference.campaign_io import write_json_new
out=ROOT/'tmp/c07_truth_interpolation500';out.mkdir(exist_ok=True)
if (out/'validation.json').exists():raise FileExistsError('Preserve previous independent validation.')
runtime=CampaignRuntime(ROOT/'configs/calibration/prior_predictive_500_v1.json',ROOT/'results/C07/prior_predictive/data.npz',ROOT/'results/C07/orf_interpolation/orf_table_pilot12x4.npz',ROOT/'results/C07/orf_interpolation/orf_table_manifest.json',ROOT/'configs/calibration/pilot_initial.json',ROOT/'configs/calibration/campaign_500_prospective.json',threads=6,training_threads=1,native_library_path=ROOT/'tmp/native/c586a0637ce30e440b8a5235/libpta_likelihood.dylib',native_build_manifest_path=ROOT/'tmp/native/c586a0637ce30e440b8a5235/build_manifest.json')
protocol=dict(scope='Finite ORF interpolation check at all 500 generating parameters and corresponding five models; separate truth-reading validation, not fitting or SBC.',maximum_absolute_loglikelihood_difference=.001,targets=2500,table_sha256=runtime.input_hashes['table'],data_sha256=runtime.input_hashes['data'],truth_logl_sha256=hashlib.sha256((ROOT/'results/C07/prior_predictive/truth_log_likelihood.json').read_bytes()).hexdigest(),driver_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
write_json_new(out/'protocol.json',protocol)
start=time.perf_counter();runtime.build();runtime.set_phase('production')
with np.load(ROOT/'results/C07/prior_predictive/data.npz',allow_pickle=False) as f:truth=f['truth']
expected=np.asarray(json.loads((ROOT/'results/C07/prior_predictive/truth_log_likelihood.json').read_text())['log_likelihood'])
actual=runtime.likelihood(np.tile(truth,(5,1)),np.arange(2500)).reshape(5,500)
difference=actual-expected
np.savez_compressed(out/'arrays.npz',direct=expected,interpolated=actual,difference=difference)
report=dict(status='PASS_FINITE_500_TRUTH_INTERPOLATION' if np.max(abs(difference))<=protocol['maximum_absolute_loglikelihood_difference'] else 'FAIL_FINITE_500_TRUTH_INTERPOLATION',protocol=protocol,maximum_absolute_difference=float(np.max(abs(difference))),maximum_by_model=np.max(abs(difference),axis=1).tolist(),mean_absolute_by_model=np.mean(abs(difference),axis=1).tolist(),maximum_location=np.unravel_index(np.argmax(abs(difference)),difference.shape),seconds=time.perf_counter()-start,arrays_sha256=hashlib.sha256((out/'arrays.npz').read_bytes()).hexdigest(),runtime_identity=runtime.identity,source_sha256=runtime.source_hashes,posterior_computed=False,global_analytic_error_bound=False)
report['maximum_location']=list(map(int,report['maximum_location']))
runtime.verify_unchanged();runtime.close();write_json_new(out/'validation.json',report)
print(json.dumps(report),flush=True)
if not report['status'].startswith('PASS'):raise RuntimeError('Interpolation exceeds the predeclared finite-case criterion.')
