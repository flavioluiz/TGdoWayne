"""Prospective proposal-training workload; never loads the injected truths."""
from pathlib import Path
import hashlib,json,resource,sys,time
import numpy as np
ROOT=Path.cwd();HERE=Path(__file__).resolve().parent;S=ROOT/'tmp/c07_sampler';M=ROOT/'tmp/c07_memory_kernel'
sys.path[:0]=[str(ROOT/'src'),str(S),str(M),str(ROOT/'tmp/c07_efficiency')]
from inference.model import experiment
from cubic_even import EvenThresholdCubicORF
from preallocated_cubic import PreallocatedCubicPointLikelihood
from pointwise import UnitPosterior
from mh import BatchedMH
from linalg_batch import forward_substitution
from proposal import fit_proposal
TABLE=S/'results/table_beta8193_local.npz';CONFIG=ROOT/'configs/calibration/pilot_initial.json';DATA=ROOT/'results/C07/fixtures/pilot_data.npz'
TABLE_SHA='75632dfbdd9cce8b60b9f760a3177a76798a4adb7ac9ccc724092aeaf53ad70d'
RESULTS=HERE/'results';RESULTS.mkdir(exist_ok=True)

def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda:f.read(1024**2),b''):h.update(b)
    return h.hexdigest()

def main():
    if (RESULTS/'summary.json').exists():raise FileExistsError('Preserve previous training.')
    cfg=json.loads(CONFIG.read_text());e=experiment(cfg)
    with np.load(DATA,allow_pickle=False) as p:data={k:p[k].copy() for k in ['q','x_physical','x_gaussian']}
    assert 'truth' not in data and sha(TABLE)==TABLE_SHA
    settings=dict(targets=[62],training_steps=[4096,8192],chains=4,seeds=[907103101,907103102],
                  points_for_EM=2048,selection='512 fixed evenly spaced time indices in the second half, all four chains.',
                  adaptation_window=4000,mass_probability=.15,nuisance_probability=.20,independence_probability=.45,
                  student_df=5.,student_scales=[1.,3.],student_weights=[.75,.25],em_components=4,em_iterations=80,covariance_floor=.03,inflation=1.10,
                  maximum_estimated_numeric_bytes=2*1024**3,table_sha256=TABLE_SHA,
                  scope='One selected pilot target A_Gd14. Adaptive trajectories train proposals only; no posterior or coverage claim. Truth arrays are not loaded.')
    (HERE/'config.json').write_text(json.dumps(settings,indent=2)+'\n')
    paths=[Path(__file__),M/'preallocated_cubic.py',S/'cubic_even.py',S/'cubic.py',S/'pointwise.py',S/'mh.py',S/'linalg_batch.py',ROOT/'tmp/c07_efficiency/proposal.py',CONFIG,DATA,TABLE]
    sources={str(p.relative_to(ROOT)):sha(p) for p in paths}
    for p in paths:
        if p.suffix in ['.py','.json']:
            out=HERE/'executed_sources'/p.relative_to(ROOT);out.parent.mkdir(parents=True,exist_ok=True);out.write_bytes(p.read_bytes())
    (HERE/'source_manifest.json').write_text(json.dumps(sources,indent=2)+'\n')
    with np.load(TABLE,allow_pickle=False) as p:nodes=p['nodes'];matrices=p['matrices']
    coefficient_bytes=int(4*(len(nodes)-1)*np.prod(matrices.shape[1:])*16)
    spline_estimate=4*coefficient_bytes+matrices.nbytes+128*1024**2
    if spline_estimate>settings['maximum_estimated_numeric_bytes']:raise RuntimeError('Independent spline-construction numeric preflight exceeded.')
    start=time.perf_counter();table=EvenThresholdCubicORF(nodes,matrices,coordinate='beta');table_seconds=time.perf_counter()-start
    start=time.perf_counter();lk=PreallocatedCubicPointLikelihood(e,data,table,maximum_estimated_numeric_bytes=settings['maximum_estimated_numeric_bytes']);lk.solve=forward_substitution;kernel_seconds=time.perf_counter()-start
    posterior=UnitPosterior(lk,cfg['prior']['bounds']);records=[]
    print(json.dumps(dict(setup_complete=True,table_seconds=table_seconds,kernel_seconds=kernel_seconds,spline_estimated_numeric_bytes=spline_estimate,kernel_budget=lk.construction_budget,maxrss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)),flush=True)
    for count,seed in zip(settings['training_steps'],settings['seeds']):
        output=RESULTS/f'warmup{count}_proposal.json'
        if output.exists():raise FileExistsError('Do not overwrite a frozen trained proposal.')
        sampler=BatchedMH(posterior,[62],seed=seed,chains=4,mass_probability=.15,nuisance_probability=.20,independence_probability=.45,student_df=5.,student_scales=(1.,3.),student_weights=(.75,.25),adaptation_window=min(4000,count));sampler.solve=forward_substitution
        selection=np.linspace(count//2,count-1,512).astype(int);states=[];j=0;start=time.perf_counter()
        for i in range(count):
            x,_=sampler.step(adapt=True)
            if j<len(selection) and i==selection[j]:states.append(x[0].copy());j+=1
            if (i+1)%2048==0:print(json.dumps(dict(training_steps=count,completed=i+1,seconds=time.perf_counter()-start)),flush=True)
        warm_seconds=time.perf_counter()-start;samples=np.asarray(states).reshape(2048,5)
        start=time.perf_counter();fit,diagnostics=fit_proposal(samples,np.zeros(len(samples)),components=4,iterations=80,covariance_floor=.03,inflation=1.10);fit_seconds=time.perf_counter()-start
        meta=sampler.metadata();row=dict(target=62,weights=fit.component_weights.tolist(),means=fit.means.tolist(),covariances=fit.covariances.tolist(),global_mean=meta['mean'][0],global_cholesky=meta['cholesky'][0],random_walk_logscale=meta['logscale'][0],fit_diagnostics=diagnostics)
        proposal=dict(status='FROZEN_COLD_TRAINING_ONLY_NOT_POSTERIOR',targets=[62],records=[row],defensive_student_fraction=.15,student_df=5.,student_scale=3.,uses_truth=False,
                      training_steps=count,training_seed=seed,chains=4,selection_indices=selection.tolist(),selected_points_sha256=hashlib.sha256(samples.tobytes()).hexdigest(),
                      training_seconds=warm_seconds,fit_seconds=fit_seconds,adaptation=meta,table_sha256=TABLE_SHA,source_sha256=sources,
                      note='Selected trajectories were adaptive and are excluded from future IID estimates.')
        np.savez_compressed(RESULTS/f'warmup{count}_selected_points.npz',x_unit=samples,selection=selection)
        output.write_text(json.dumps(proposal,indent=2)+'\n');records.append(dict(steps=count,seed=seed,training_seconds=warm_seconds,fit_seconds=fit_seconds,proposal=str(output.relative_to(ROOT))))
    assert all(sha(ROOT/p)==h for p,h in sources.items())
    summary=dict(status='TWO_FROZEN_TRAINING_LEVELS_AWAITING_INDEPENDENT_IID',settings=settings,levels=records,table_seconds=table_seconds,kernel_seconds=kernel_seconds,
                 spline_estimated_numeric_bytes=spline_estimate,kernel_budget=lk.construction_budget,darwin_maxrss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,source_unchanged=True,
                 data_fields_loaded=list(data),source_sha256=sources)
    (RESULTS/'summary.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary['levels'],indent=2),flush=True)
if __name__=='__main__':main()
