"""Fixed broadening of all16 original cold proposals; independent IID production."""
import os
os.environ['VECLIB_MAXIMUM_THREADS']='1'
from pathlib import Path
import gc,hashlib,json,resource,sys,time
import numpy as np
from scipy.special import expit
ROOT=Path(__file__).resolve().parents[3];HERE=Path(__file__).resolve().parent;BASE=HERE.parent
sys.path.insert(0,str(BASE/'replay_sources/src'))
from inference.model import experiment
from inference.orf_interpolation import EvenThresholdCubicORF
from inference.pointwise_preallocated import PreallocatedCubicPointLikelihood
from inference.native_likelihood import NativeLikelihood
from inference.likelihood_threads import ThreadedLikelihood
from inference.linalg_batch import forward_substitution
from inference.gmm_density import MultipleRHSGaussianDefensiveProposal
from inference.campaign_iid import sample_single_target
from inference.campaign_io import rng_for,write_npz_new,sha256

def main():
 c=json.loads((HERE/'config.json').read_text());planned=sum(c['levels'])*4*len(c['targets']);assert planned<c['maximum_new_likelihood_values'] and planned+c['previous_values_including_replay_and20reference']<c['maximum_total_with_previous_values']
 sources=json.loads((BASE/'replay_source_manifest.json').read_text());inputs={str(p.relative_to(ROOT)):sha256(p) for p in [Path(__file__),HERE/'config.json',*[ROOT/c[k] for k in ['data','experiment','table','native_library']]]};inputs.update({r['file']:r['sha256'] for r in c['proposal_records']});assert all(sha256(ROOT/p)==v for p,v in inputs.items())
 with (HERE/'execution_manifest.json').open('x') as f:json.dump(dict(inputs=inputs,sources=sources),f,indent=2);f.write('\n')
 cfg=json.loads((ROOT/c['experiment']).read_text());e=experiment(cfg);bounds=np.array(cfg['prior']['bounds'])
 with np.load(ROOT/c['data']) as f:data={k:f[k].copy() for k in ['q','x_physical','x_gaussian']}
 with np.load(ROOT/c['table']) as f:table=EvenThresholdCubicORF(f['nodes'],f['matrices'],coordinate='beta')
 start=time.perf_counter();ref=PreallocatedCubicPointLikelihood(e,data,table,maximum_estimated_numeric_bytes=c['maximum_estimated_numeric_bytes']);ref.solve=forward_substitution;native=NativeLikelihood(ref,bounds,ROOT/c['native_library']);del ref,table;gc.collect();lk=ThreadedLikelihood(native,workers=c['workers']);setup=time.perf_counter()-start;records=[];total=0;activebytes=0
 print(json.dumps(dict(setup_seconds=setup,peak_RSS_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)),flush=True)
 start=time.perf_counter()
 for item in c['proposal_records']:
  target=item['target'];row=json.loads((ROOT/item['file']).read_text());q=MultipleRHSGaussianDefensiveProposal(*[np.asarray(row[k])[None] for k in ['weights','means','covariances','global_mean','global_cholesky']],defensive_fraction=.15,student_df=5,student_scale=3);assert q.k==8
  for level,N in enumerate(c['levels']):
   for rep in range(4):
    rng=rng_for(c['seed'],320+100*level,target,rep);state_before=rng.bit_generator.state;z,component=sample_single_target(q,rng,N);x=expit(z);logq=q.logpdf(z);logprior=(-np.logaddexp(0,-z)-np.logaddexp(0,z)).sum(axis=1);theta=bounds[:,0]+x*np.diff(bounds,axis=1)[:,0];ll=np.empty(N)
    for begin in range(0,N,c['likelihood_batch']):
     stop=min(N,begin+c['likelihood_batch']);ll[begin:stop]=lk(theta[begin:stop],np.full(stop-begin,target,int));total+=stop-begin
    logw=ll+logprior-logq;assert all(np.isfinite(a).all() for a in [z,x,ll,logq,logprior,logw]);dest=HERE/'raw'/f'target_{target:06d}_N{N}_rep_{rep:02d}.npz';anticipated=N*(14*8+1)+65536
    if activebytes+anticipated>c['maximum_active_raw_bytes']:raise RuntimeError('Frozen raw quota exceeded')
    write_npz_new(dest,compressed=False,z=z,x_unit=x,log_likelihood=ll,log_weights=logw,log_proposal=logq,log_prior_logit=logprior,proposal_component=component.astype(np.uint8),target=np.asarray(target),replicate=np.asarray(rep));activebytes+=dest.stat().st_size
    rec=dict(target=target,N=N,replicate=rep,file=str(dest.relative_to(ROOT)),sha256=sha256(dest),proposal_sha256=item['sha256'],rng_state_before=state_before,rng_state_after=rng.bit_generator.state);records.append(rec)
  print(json.dumps(dict(target=target,completed=len(records),likelihood_values=total,production_seconds=time.perf_counter()-start)),flush=True)
 lk.close();assert total==planned;assert all(sha256(ROOT/p)==v for p,v in inputs.items());assert all(sha256(ROOT/p)==v for p,v in sources.items())
 result=dict(status='WIDE16_IID_COMPLETE_AWAITING_INDEPENDENT_DIAGNOSTICS',targets=c['targets'],levels=c['levels'],replicates=4,seed=c['seed'],likelihood_evaluations=total,previous_likelihood_values=c['previous_values_including_replay_and20reference'],combined_values=total+c['previous_values_including_replay_and20reference'],setup_seconds=setup,production_and_io_seconds=time.perf_counter()-start,RSS_max_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,raw_bytes=activebytes,records=records,input_hashes_unchanged=True,source_hashes_unchanged=True,uses_truth=False)
 with (HERE/'execution_summary.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
if __name__=='__main__':main()
