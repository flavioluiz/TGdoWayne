"""Final owned wrapper on the same frozen physical points, no new sampling."""
from pathlib import Path
import importlib.util,json,sys,time
import numpy as np
HERE=Path(__file__).resolve().parent;ROOT=Path.cwd();sys.path[:0]=[str(ROOT/'src'),str(ROOT/'tmp/c07_sampler')]
from inference.model import experiment
from cubic_even import EvenThresholdCubicORF
from cubic import CubicPointLikelihood
from linalg_batch import forward_substitution
import hashlib
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def main():
    frozen=json.loads((HERE/'results/physical_review.json').read_text())
    for path,h in frozen['source_hashes'].items():
        if sha(path)!=h:raise RuntimeError('Reference source/input changed: '+path)
    start=time.perf_counter();config_path=ROOT/'configs/calibration/pilot_initial.json';cfg=json.loads(config_path.read_text())
    table_path=ROOT/'tmp/c07_sampler/results/table_beta8193_local.npz';tab=np.load(table_path,allow_pickle=False)
    data_path=ROOT/'results/C07/fixtures/pilot_data.npz';data=dict(np.load(data_path,allow_pickle=False))
    model=CubicPointLikelihood(experiment(cfg),data,EvenThresholdCubicORF(tab['nodes'],tab['matrices']));model.solve=forward_substitution
    source=HERE/'sources/native_owned.py';library=HERE/'sources/full_guarded.dylib'
    spec=importlib.util.spec_from_file_location('final_owned',source);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    native=module.NativeLikelihood(model,cfg['prior']['bounds'],library);arrays_path=HERE/'results/physical_arrays.npz';arrays=np.load(arrays_path,allow_pickle=False);rows=[]
    for name in ['posterior_selected_from_historical553_recomputed8336','mass_endpoints_and_midpoint_all80targets']:
        theta=arrays[name+'_theta'];targets=arrays[name+'_targets'];current=native(theta,targets)
        old=arrays[name+'_native'];reference=arrays[name+'_direct_numpy'];python_now=model(theta,targets)
        rows.append({'name':name,'N':len(theta),'maximum_abs_owned_minus_direct_numpy':float(np.max(abs(current-reference))),
            'maximum_abs_owned_minus_current_python':float(np.max(abs(current-python_now))),
            'bit_identical_to_original_native':bool(np.array_equal(current,old)),
            'all_within_frozen_tolerance':bool(np.all(abs(current-reference)<=1e-7+1e-11*abs(reference)))})
    result={'label':'FINAL_OWNED_WRAPPER_PHYSICAL_CROSSCHECK','rows':rows,'all_pass':all(r['all_within_frozen_tolerance']for r in rows),
        'seconds':time.perf_counter()-start,'new_posterior_samples':False,
        'source_hashes':{str(p):sha(p)for p in [Path(__file__),source,library,HERE/'sources/full_guarded.cpp',arrays_path,config_path,table_path,data_path]}}
    (HERE/'results/owned_physical_review.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n');print(json.dumps(result,indent=2))

if __name__=='__main__':main()
