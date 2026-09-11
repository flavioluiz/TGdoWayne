"""Two cold-training lengths, frozen before independent IID tail assessment."""
import os
os.environ['VECLIB_MAXIMUM_THREADS']='1'
from pathlib import Path
import gc,hashlib,json,resource,sys,time
import numpy as np
from scipy.special import expit
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
from inference.campaign_iid import sample_single_target

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()

class Budgeted:
    def __init__(self,fn,limit):self.fn=fn;self.limit=limit;self.count=0
    def __call__(self,theta,targets):
        if self.count+len(theta)>self.limit:raise RuntimeError('Frozen likelihood budget exceeded.')
        out=self.fn(theta,targets);self.count+=len(theta);return out

def proposal(row):
    return MultipleRHSGaussianDefensiveProposal(*[np.asarray(row[k])[None] for k in ['weights','means','covariances','global_mean','global_cholesky']],defensive_fraction=.15,student_df=5.,student_scale=3.)

def main():
    cfg=json.loads((HERE/'config.json').read_text());targets=np.array(cfg['targets']);n=len(targets)
    planned=sum((s+1)*4*n for s in cfg['training_lengths'])+len(cfg['training_lengths'])*sum(cfg['levels'])*4*n
    assert planned<cfg['maximum_likelihood_values']
    inputs={str(p.relative_to(ROOT)):sha(p) for p in [Path(__file__),HERE/'config.json',ROOT/cfg['data'],ROOT/cfg['experiment'],ROOT/cfg['table'],ROOT/cfg['native_library'],ROOT/cfg['frozen_cdf_grid']]}
    (HERE/'execution_manifest.json').write_text(json.dumps(inputs,indent=2)+'\n')
    expcfg=json.loads((ROOT/cfg['experiment']).read_text());e=experiment(expcfg);bounds=np.array(expcfg['prior']['bounds']);width=np.diff(bounds,axis=1)[:,0]
    with np.load(ROOT/cfg['data'],allow_pickle=False) as f:data={k:f[k].copy() for k in ['q','x_physical','x_gaussian']}
    start=time.perf_counter()
    with np.load(ROOT/cfg['table'],allow_pickle=False) as f:table=EvenThresholdCubicORF(f['nodes'],f['matrices'],coordinate='beta')
    reference=PreallocatedCubicPointLikelihood(e,data,table,maximum_estimated_numeric_bytes=cfg['maximum_estimated_numeric_bytes']);reference.solve=forward_substitution
    native=NativeLikelihood(reference,bounds,ROOT/cfg['native_library']);del reference,table;gc.collect()
    counted=Budgeted(native,cfg['maximum_likelihood_values']);posterior=UnitPosterior(counted,bounds)
    print(json.dumps(dict(setup_seconds=time.perf_counter()-start,RSS=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)),flush=True)
    trained=[];all_rows=[]
    for steps,seed in zip(cfg['training_lengths'],cfg['training_seeds']):
        start=time.perf_counter();sampler=TargetSeededMH(posterior,targets,seed=seed,chains=4,mass_probability=.15,nuisance_probability=.20,independence_probability=.45,student_df=5.,student_scales=(1.,3.),student_weights=(.75,.25),adaptation_window=4000);sampler.solve=forward_substitution
        selection=np.linspace(steps//2,steps-1,512).astype(int);states=[];next_index=0
        for i in range(steps):
            x,_=sampler.step(adapt=True)
            if next_index<len(selection) and i==selection[next_index]:states.append(x.copy());next_index+=1
            if (i+1)%4096==0:print(json.dumps(dict(training_steps=steps,completed=i+1,seconds=time.perf_counter()-start)),flush=True)
        elapsed=time.perf_counter()-start;points=np.asarray(states).transpose(1,0,2,3).reshape(n,2048,5);meta=sampler.metadata();rows=[]
        for j,target in enumerate(targets):
            fit,diagnostics=fit_proposal(points[j],np.zeros(2048),components=4,iterations=80,covariance_floor=.03,inflation=1.10)
            row=dict(target=int(target),training_steps=steps,training_seed=seed,weights=fit.component_weights.tolist(),means=fit.means.tolist(),covariances=fit.covariances.tolist(),global_mean=meta['mean'][j],global_cholesky=meta['cholesky'][j],em_diagnostics=diagnostics,uses_truth=False)
            proposal(row);rows.append(row)
        output=HERE/'results'/f'train{steps}_proposals.json'
        with output.open('x') as f:json.dump(dict(status='FROZEN_BEFORE_ALL_NEW_IID_PRODUCTION',records=rows,training_seconds=elapsed,metadata=meta,uses_truth=False,selected_indices=selection.tolist()),f,indent=2);f.write('\n')
        with (HERE/'results'/f'train{steps}_states.npz').open('xb') as f:np.savez(f,x_unit=points,last_adaptive_window_z=np.asarray(sampler.history),targets=targets,selection=selection)
        trained.append(dict(steps=steps,file=str(output.relative_to(ROOT)),sha256=sha(output),training_seconds=elapsed));all_rows.extend(rows)
        del sampler,points,states;gc.collect()
    # Every density is fixed before the first evaluation sample is generated.
    wrapper=ThreadedLikelihood(native,workers=cfg['production_workers']);counted.fn=wrapper
    production=[]
    for steps in cfg['training_lengths']:
        densities=[proposal(next(r for r in all_rows if r['training_steps']==steps and r['target']==t)) for t in targets]
        for N in cfg['levels']:
            dest=HERE/'results'/f'train{steps}_iid_N{N}.npz'
            if dest.exists():raise FileExistsError(dest)
            shape=(cfg['replicates'],N,n);xs=np.empty(shape+(5,));zs=np.empty_like(xs);lls=np.empty(shape);lqs=np.empty(shape);lps=np.empty(shape);components=np.empty(shape,np.uint8)
            start=time.perf_counter()
            for rep in range(cfg['replicates']):
                for j,(target,q) in enumerate(zip(targets,densities)):
                    rng=np.random.default_rng(np.random.SeedSequence([cfg['production_seed'],320,int(target),steps,N,rep]));z,component=sample_single_target(q,rng,N)
                    x=expit(z);logq=q.logpdf(z);logp=(-np.logaddexp(0,-z)-np.logaddexp(0,z)).sum(axis=1)
                    theta=bounds[:,0]+width*x;ll=np.empty(N)
                    for begin in range(0,N,cfg['likelihood_batch']):
                        stop=min(N,begin+cfg['likelihood_batch']);ll[begin:stop]=counted(theta[begin:stop],np.full(stop-begin,int(target)))
                    xs[rep,:,j]=x;zs[rep,:,j]=z;lls[rep,:,j]=ll;lqs[rep,:,j]=logq;lps[rep,:,j]=logp;components[rep,:,j]=component
                print(json.dumps(dict(training_steps=steps,N=N,replicate=rep,seconds=time.perf_counter()-start)),flush=True)
            lw=lls+lps-lqs
            assert all(np.isfinite(a).all() for a in [xs,zs,lls,lqs,lps,lw])
            active=sum(p.stat().st_size for p in (HERE/'results').glob('*.npz'))
            if active+sum(a.nbytes for a in [xs,zs,lls,lqs,lps,lw,components])+65536>cfg['maximum_raw_bytes']:raise RuntimeError('Frozen raw budget exceeded.')
            with dest.open('xb') as f:np.savez(f,x_unit=xs,z=zs,log_likelihood=lls,log_proposal=lqs,log_prior_logit=lps,log_weights=lw,proposal_component=components,targets=targets,prior_bounds=bounds,uses_truth=np.array(False))
            production.append(dict(training_steps=steps,N=N,R=4,seconds=time.perf_counter()-start,file=str(dest.relative_to(ROOT)),sha256=sha(dest)))
            del xs,zs,lls,lqs,lps,lw,components;gc.collect()
    wrapper.close()
    assert counted.count==planned
    source=json.loads((HERE/'source_manifest.json').read_text())
    assert all(sha(ROOT/p)==v for p,v in source.items()) and all(sha(ROOT/p)==v for p,v in inputs.items())
    result=dict(status='FROZEN_TRAINING_AND_INDEPENDENT_IID_COMPLETE_AWAITING_DIAGNOSTICS',config=cfg,training=trained,production=production,likelihood_evaluations=counted.count,source_unchanged=True,uses_truth=False,RSS_max_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,input_sha256=inputs)
    with (HERE/'results/execution_summary.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')

if __name__=='__main__':main()
