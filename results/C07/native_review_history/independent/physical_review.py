"""Selected posterior/corner points under the validated beta8336 table."""
from pathlib import Path
import hashlib,json,sys,time
import numpy as np
HERE=Path(__file__).resolve().parent;ROOT=Path.cwd();sys.path.insert(0,str(HERE))
from independent_review import Native,direct_numpy,sha
from inference.model import experiment
from cubic_even import EvenThresholdCubicORF
from cubic import CubicPointLikelihood
from linalg_batch import forward_substitution

def main():
    review=json.loads((HERE/'review_config.json').read_text());cfgpath=ROOT/'configs/calibration/pilot_initial.json';cfg=json.loads(cfgpath.read_text())
    data_path=ROOT/'results/C07/fixtures/pilot_data.npz';data=dict(np.load(data_path,allow_pickle=False))
    table_path=ROOT/'tmp/c07_sampler/results/table_beta8193_local.npz'
    assert sha(table_path)=='75632dfbdd9cce8b60b9f760a3177a76798a4adb7ac9ccc724092aeaf53ad70d'
    start=time.perf_counter();tab=np.load(table_path,allow_pickle=False);table=EvenThresholdCubicORF(tab['nodes'],tab['matrices'])
    model=CubicPointLikelihood(experiment(cfg),data,table);model.solve=forward_substitution;native=Native(model)
    print('physical setup seconds',time.perf_counter()-start,flush=True)
    bounds=np.array(cfg['prior']['bounds']);width=np.diff(bounds,axis=1)[:,0];rng=np.random.default_rng(review['seed']+1)
    metadata_path=ROOT/'tmp/c07_sampler/results/pilot553_mixture.json';meta=json.loads(metadata_path.read_text())
    draws_path=ROOT/'tmp/c07_sampler/results/pilot553_mixture_draws.npy';draws=np.load(draws_path,mmap_mode='r')
    # Sample indices selected by a new seed without inspecting likelihood values.
    selected=[];ids=[];indices=[]
    for j,target in enumerate(meta['targets']):
        draw_index=rng.integers(0,len(draws),size=review['physical_posterior_points_per_target']);chain_index=rng.integers(0,4,size=len(draw_index))
        selected.extend(draws[draw_index,j,chain_index]);ids.extend([target]*len(draw_index));indices.append({'target':target,'draw_indices':draw_index.tolist(),'chain_indices':chain_index.tolist()})
    selected=np.asarray(selected);ids=np.array(ids);rows=[];arrays={}
    corners=np.tile(np.mean(bounds,axis=1),(5*80,1));corners[:,0]=np.repeat([0.,np.nextafter(0.,1.),.5,np.nextafter(1.,0.),1.],80)
    for name,theta,targets in [('posterior_selected_from_historical553_recomputed8336',bounds[:,0]+selected*width,ids),('mass_endpoints_and_midpoint_all80targets',corners,np.tile(np.arange(80),5))]:
        v=native(theta,targets);baseline=model(theta,targets);independent=direct_numpy(model,theta,targets)
        delta=abs(v-independent);rows.append({'name':name,'N':len(theta),'maximum_abs_native_minus_direct_matrix':float(delta.max()),
            'maximum_scaled_difference':float(np.max(delta/(1+abs(independent)))),
            'maximum_abs_native_minus_python_bank':float(np.max(abs(v-baseline))),
            'all_within_frozen_tolerance':bool(np.all(delta<=review['physical_absolute_tolerance']+review['relative_tolerance']*abs(independent))),
            'targets':np.unique(targets).tolist()})
        arrays[name+'_theta']=theta;arrays[name+'_targets']=targets;arrays[name+'_native']=v;arrays[name+'_direct_numpy']=independent;arrays[name+'_bank_numpy']=baseline
    paths=[Path(__file__),HERE/'independent_review.py',HERE/'review_config.json',cfgpath,data_path,table_path,metadata_path,draws_path]
    paths.extend([ROOT/'tmp/c07_sampler'/name for name in ['cubic.py','cubic_even.py','pointwise.py','linalg_batch.py']])
    result={'label':'CPP_SELECTED_PARAMETER_VERIFICATION_NOT_NEW_POSTERIOR_SAMPLES','rows':rows,
        'all_pass':all(a['all_within_frozen_tolerance']for a in rows),'posterior_selection':indices,
        'table_coordinate':'beta with even threshold boundary condition','new_posterior_production':False,
        'seconds':time.perf_counter()-start,'source_hashes':{str(p):sha(p)for p in paths}}
    np.savez_compressed(HERE/'results/physical_arrays.npz',**arrays)
    (HERE/'results/physical_review.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    print(json.dumps({k:result[k]for k in ['rows','all_pass','seconds']},indent=2))

if __name__=='__main__':main()
