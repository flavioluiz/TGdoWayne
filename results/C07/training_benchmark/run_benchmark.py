"""Full batched warmup/EM engineering benchmark on frozen source snapshots."""
import os
os.environ['VECLIB_MAXIMUM_THREADS']='1'
from pathlib import Path
import gc,hashlib,json,resource,sys,time
import numpy as np
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE/'executed_sources/src'))
from inference.model import experiment
from inference.orf_interpolation import EvenThresholdCubicORF
from inference.pointwise_preallocated import PreallocatedCubicPointLikelihood
from inference.native_likelihood import NativeLikelihood
from inference.likelihood_threads import ThreadedLikelihood
from inference.pointwise import UnitPosterior
from inference.mh_training import TargetSeededMH
from inference.linalg_batch import forward_substitution
from inference.gmm_fit import fit_proposal
from inference.gmm_density import MultipleRHSGaussianDefensiveProposal


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


class TimedLikelihood:
    def __init__(self,likelihood,budget):
        self.likelihood=likelihood;self.budget=budget;self.points=0;self.calls=0;self.seconds=0.
    def __call__(self,theta,targets):
        if self.points+len(theta)>self.budget:raise RuntimeError('Frozen native evaluation budget exceeded.')
        start=time.perf_counter();result=self.likelihood(theta,targets)
        self.seconds+=time.perf_counter()-start;self.calls+=1;self.points+=len(theta)
        return result


def main():
    cfg=json.loads((HERE/'config.json').read_text());exp_cfg=json.loads((ROOT/cfg['experiment']).read_text())
    expected=3*sum(map(len,cfg['target_groups'].values()))*cfg['chains']*(cfg['steps']+1)
    if expected>cfg['maximum_likelihood_values']:raise RuntimeError('Preflight workload exceeds budget.')
    manifest=json.loads((HERE/'frozen_source_manifest.json').read_text())
    files=[HERE/'config.json',Path(__file__),ROOT/cfg['experiment'],ROOT/cfg['data'],ROOT/cfg['table'],ROOT/cfg['native_library']]
    inputs={str(p.relative_to(ROOT)):sha(p) for p in files}
    (HERE/'execution_manifest.json').write_text(json.dumps(dict(inputs=inputs,frozen_sources=manifest),indent=2)+'\n')
    e=experiment(exp_cfg);bounds=np.array(exp_cfg['prior']['bounds'])
    with np.load(ROOT/cfg['data'],allow_pickle=False) as datafile:
        data={k:datafile[k].copy() for k in ['q','x_physical','x_gaussian']}
    start=time.perf_counter()
    with np.load(ROOT/cfg['table'],allow_pickle=False) as f:
        table=EvenThresholdCubicORF(f['nodes'],f['matrices'],coordinate='beta')
    model=PreallocatedCubicPointLikelihood(e,data,table,maximum_estimated_numeric_bytes=cfg['maximum_estimated_numeric_bytes']);model.solve=forward_substitution
    native=NativeLikelihood(model,bounds,ROOT/cfg['native_library'])
    setup=time.perf_counter()-start
    rng=np.random.default_rng(907104002);theta=bounds[:,0]+rng.random((80,5))*np.diff(bounds,axis=1)[:,0]
    theta[:2,0]=[0,1];ids=np.arange(80);reference=model(theta,ids);baseline=native(theta,ids)
    maximum_difference=float(np.max(abs(reference-baseline)))
    if maximum_difference>1e-10:raise RuntimeError('Native/reference anchor mismatch.')
    del model,table;gc.collect()
    print(json.dumps(dict(setup_seconds=setup,native_reference_maximum_logl_difference=maximum_difference,darwin_maxrss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)),flush=True)
    reports=[];used=0;fits=0
    for group,targets in cfg['target_groups'].items():
        targets=np.asarray(targets,int);previous_points=None;previous_meta=None;previous_fit_digest=None
        for workers in cfg['threads']:
            wrapper=ThreadedLikelihood(native,workers=workers)
            if not np.array_equal(wrapper(theta,ids),baseline):raise RuntimeError('Deterministic threaded evaluation differs from serial.')
            timed=TimedLikelihood(wrapper,cfg['maximum_likelihood_values']-used)
            posterior=UnitPosterior(timed,bounds)
            start=time.perf_counter()
            sampler=TargetSeededMH(posterior,targets,seed=cfg['training_seed'],chains=cfg['chains'],mass_probability=.15,nuisance_probability=.20,independence_probability=.45,student_df=5.,student_scales=(1.,3.),student_weights=(.75,.25),adaptation_window=cfg['adaptation_window'])
            sampler.solve=forward_substitution
            selected=np.linspace(cfg['steps']//2,cfg['steps']-1,cfg['selection_points']//cfg['chains']).astype(int)
            states=[];next_index=0;steps_start=time.perf_counter();recent=steps_start
            for step in range(cfg['steps']):
                x,_=sampler.step(adapt=True)
                if next_index<len(selected) and step==selected[next_index]:states.append(x.copy());next_index+=1
                if (step+1)%1024==0:
                    now=time.perf_counter();print(json.dumps(dict(group=group,threads=workers,step=step+1,seconds_since_last=now-recent,seconds=now-steps_start)),flush=True);recent=now
            mh_seconds=time.perf_counter()-start
            points=np.asarray(states).transpose(1,0,2,3).reshape(len(targets),cfg['selection_points'],5)
            meta=sampler.metadata();meta_bytes=json.dumps(meta,sort_keys=True).encode()
            digest=hashlib.sha256(points.tobytes()).hexdigest()
            if previous_points is not None:
                if digest!=previous_points or meta_bytes!=previous_meta:raise RuntimeError('Thread count changed the adaptive trajectories or metadata.')
            previous_points=digest;previous_meta=meta_bytes
            em_start=time.perf_counter();em_times=[];fit_hash=hashlib.sha256()
            for j,target in enumerate(targets):
                if fits>=cfg['maximum_em_fits']:raise RuntimeError('Frozen EM budget exceeded.')
                begin=time.perf_counter();fit,diagnostics=fit_proposal(points[j],np.zeros(cfg['selection_points']),components=4,iterations=80,covariance_floor=.03,inflation=1.10)
                MultipleRHSGaussianDefensiveProposal(fit.component_weights[None],fit.means[None],fit.covariances[None],np.array(meta['mean'])[j:j+1],np.array(meta['cholesky'])[j:j+1],defensive_fraction=.15,student_df=5.,student_scale=3.)
                em_times.append(time.perf_counter()-begin)
                for array in [fit.component_weights,fit.means,fit.covariances]:fit_hash.update(array.tobytes())
                fits+=1
            em_seconds=time.perf_counter()-em_start;fit_digest=fit_hash.hexdigest()
            if previous_fit_digest is not None and fit_digest!=previous_fit_digest:raise RuntimeError('Thread count changed the EM fit.')
            previous_fit_digest=fit_digest
            path=HERE/'results'/f'engineering_T{group}_threads{workers}.npz'
            with path.open('xb') as f:np.savez(f,selected_points=points,targets=targets,selection_indices=selected,posterior_claimed=np.array(False))
            row=dict(targets=len(targets),threads=workers,steps=cfg['steps'],chains=cfg['chains'],mh_seconds=mh_seconds,em_seconds=em_seconds,mh_plus_em_seconds=mh_seconds+em_seconds,em_seconds_per_target=em_times,likelihood_calls=timed.calls,likelihood_points=timed.points,likelihood_seconds_including_thread_dispatch=timed.seconds,non_likelihood_mh_seconds=mh_seconds-timed.seconds,selected_points_sha256=digest,fit_parameters_sha256=fit_digest,thread_invariant_trajectories=True,thread_invariant_fits=True,source_file=str(path.relative_to(ROOT)),source_file_sha256=sha(path),metadata=meta,darwin_maxrss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
            out=HERE/'results'/f'engineering_T{group}_threads{workers}.json'
            with out.open('x') as f:json.dump(row,f,indent=2);f.write('\n')
            reports.append(row);used+=timed.points;wrapper.close();del sampler,states,points,posterior,timed,wrapper;gc.collect()
            print(json.dumps({k:v for k,v in row.items() if k not in ['metadata','em_seconds_per_target']}),flush=True)
    if any(sha(ROOT/p)!=h for p,h in manifest.items()):raise RuntimeError('Snapshot source changed.')
    if any(sha(ROOT/p)!=h for p,h in inputs.items()):raise RuntimeError('Executed input/source changed.')
    result=dict(status='ENGINEERING_BENCHMARK_COMPLETE_NOT_POSTERIOR_PRODUCTION',config=cfg,setup_seconds=setup,native_reference_maximum_logl_difference=maximum_difference,likelihood_points=used,em_fits=fits,reports=reports,source_unchanged=True,input_sha256=inputs,frozen_source_sha256=manifest)
    with (HERE/'results/benchmark_summary.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')


if __name__=='__main__':main()
