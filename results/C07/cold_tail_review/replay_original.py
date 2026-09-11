"""Original failed target25: exact raw replay with archived modules and seeds."""
import os
os.environ['VECLIB_MAXIMUM_THREADS']='1'
from pathlib import Path
import gc,hashlib,json,resource,sys,time
import numpy as np
from scipy.special import expit
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE/'replay_sources/src'))
from inference.model import experiment
from inference.orf_interpolation import EvenThresholdCubicORF
from inference.pointwise_preallocated import PreallocatedCubicPointLikelihood
from inference.native_likelihood import NativeLikelihood
from inference.likelihood_threads import ThreadedLikelihood
from inference.linalg_batch import forward_substitution
from inference.campaign_training import validate_proposal
from inference.campaign_iid import sample_single_target
from inference.campaign_io import rng_for,write_npz_new,sha256

def main():
 c=json.loads((HERE/'replay_config.json').read_text());old=ROOT/'tmp/c07_integrated_engineering/production/archive_target_000025';cfg=json.loads((old/'input_experiment.json').read_text());e=experiment(cfg);bounds=np.array(cfg['prior']['bounds']);q=validate_proposal(json.loads((ROOT/c['proposal']).read_text()))
 inputs={str(p.relative_to(ROOT)):sha256(p) for p in [Path(__file__),HERE/'replay_config.json',ROOT/c['proposal'],HERE/'replay_source_manifest.json']}
 (HERE/'replay_execution_manifest.json').write_text(json.dumps(inputs,indent=2)+'\n')
 with np.load(ROOT/'results/C07/fixtures/pilot_data.npz',allow_pickle=False) as f:data={k:f[k].copy() for k in ['q','x_physical','x_gaussian']}
 with np.load(ROOT/'tmp/c07_sampler/results/table_beta8193_local.npz',allow_pickle=False) as f:table=EvenThresholdCubicORF(f['nodes'],f['matrices'],coordinate='beta')
 t=time.perf_counter();ref=PreallocatedCubicPointLikelihood(e,data,table,maximum_estimated_numeric_bytes=c['maximum_estimated_numeric_bytes']);ref.solve=forward_substitution;native=NativeLikelihood(ref,bounds,ROOT/'tmp/native/c586a0637ce30e440b8a5235/libpta_likelihood.dylib');del ref,table;gc.collect();lk=ThreadedLikelihood(native,workers=6);results=[];total=0
 print(json.dumps(dict(setup_seconds=time.perf_counter()-t)),flush=True)
 for level,N in enumerate(c['levels']):
  for rep in range(4):
   checkpoint=json.loads((old/f'checkpoint_N{N}_rep{rep}.json').read_text());rng=rng_for(c['seed'],320+100*level,25,rep);assert rng.bit_generator.state==checkpoint['rng_state_before'];z,component=sample_single_target(q,rng,N);assert rng.bit_generator.state==checkpoint['rng_state_after'];x=expit(z);logq=q.logpdf(z);logprior=(-np.logaddexp(0,-z)-np.logaddexp(0,z)).sum(axis=1);theta=bounds[:,0]+x*np.diff(bounds,axis=1)[:,0];ll=np.empty(N)
   for start in range(0,N,2048):
    stop=min(N,start+2048);ll[start:stop]=lk(theta[start:stop],np.full(stop-start,25,int));total+=stop-start
    if total>c['maximum_likelihood_values']:raise RuntimeError('Replay budget exceeded')
   logw=ll+logprior-logq;dest=HERE/'replay_raw'/checkpoint['raw_file'];write_npz_new(dest,compressed=False,z=z,x_unit=x,log_likelihood=ll,log_weights=logw,log_proposal=logq,log_prior_logit=logprior,proposal_component=component.astype(np.uint8),target=np.asarray(25),replicate=np.asarray(rep));actual=sha256(dest);row=dict(N=N,replicate=rep,file=str(dest.relative_to(ROOT)),expected_sha256=checkpoint['raw_sha256'],actual_sha256=actual,identical=actual==checkpoint['raw_sha256']);results.append(row);print(json.dumps(row),flush=True)
   if not row['identical']:raise RuntimeError('Replay bytes do not equal archived raw SHA')
 lk.close();sources=json.loads((HERE/'replay_source_manifest.json').read_text());assert all(sha256(ROOT/p)==v for p,v in sources.items());assert all(sha256(ROOT/p)==v for p,v in inputs.items())
 with (HERE/'results/replay_summary.json').open('x') as f:json.dump(dict(status='EXACT_ORIGINAL_REPLAY_PASS',records=results,likelihood_values=total,peak_RSS_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,uses_truth=False,input_sha256=inputs,source_hashes_unchanged=True),f,indent=2);f.write('\n')
if __name__=='__main__':main()
