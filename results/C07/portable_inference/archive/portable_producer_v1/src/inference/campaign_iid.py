"""Four independent IID replicates; no truth access, clipping, smoothing or resampling for inference."""
from pathlib import Path
from time import perf_counter
import numpy as np
from scipy.special import expit,logsumexp
from .campaign_io import *
from .campaign_training import validate_proposal
from .iid_diagnostics import weight_summary,json_safe

def sample_single_target(proposal,rng,count):
 """Vectorized form of the audited Gaussian/Student mixture, one target only."""
 if proposal.n!=1:raise ValueError('One explicitly identified target per IID stream required.')
 count=positive_int(count,'IID count');u=rng.random(count);which=np.sum(u[:,None]>proposal.cumulative[0],axis=1);noise=rng.normal(size=(count,proposal.d));chi=rng.chisquare(proposal.nu,size=count)
 if np.any(chi<=0):raise ArithmeticError('Unrepresentable Student scale; no replacement draw.')
 component=np.minimum(which,proposal.k-1);z=proposal.means[0,component]+np.einsum('nij,nj->ni',proposal.chol[0,component],noise)
 student=proposal.global_mean[0]+(noise@proposal.global_chol[0].T)*np.sqrt((proposal.nu-2)/chi)[:,None]*proposal.scale
 mask=which==proposal.k;z[mask]=student[mask]
 return z,which

def produce_target(runtime,target,proposal_root,output_root,raw_root,*,resume=False):
 runtime.require_execution();runtime.set_phase('production');target=positive_int(target,'target',True)
 if target not in runtime.targets:raise ValueError('Target outside frozen campaign.')
 settings=runtime.settings['production'];levels=[positive_int(n,'IID level') for n in settings['levels']];replicates=settings['replicates'];
 if len(levels)!=2 or levels!=sorted(set(levels)):raise ValueError('Two ordered independent levels required.')
 batch=positive_int(settings.get('likelihood_batch',512),'likelihood batch')
 if replicates!=4:raise ValueError('Four independent replicates required.')
 if settings.get('raw_compression','stored') not in ['stored','deflate']:raise ValueError('Choose explicit ZIP_STORED or deflate raw format.')
 ppath=Path(proposal_root)/f'target_{target:06d}.json';row=verify_record(ppath,runtime.target_identity,status='FROZEN_PROPOSAL')
 if row['target']!=target or row.get('uses_truth') is not False:raise ValueError('Proposal target/training contract mismatch.')
 digest=row.get('proposal_content_hash');unhashed={k:v for k,v in row.items() if k!='proposal_content_hash'}
 if canonical_hash(unhashed)!=digest:raise RuntimeError('Frozen proposal contents changed.')
 proposal=validate_proposal(row);psha=sha256(ppath);out=Path(output_root);runtime.snapshot(out);raw=Path(raw_root);raw.mkdir(parents=True,exist_ok=True);summaries=[]
 complete=out/f'target_{target:06d}.json'
 if complete.exists():
  if not resume:raise FileExistsError('Completed target exists.')
  record=verify_record(complete,runtime.identity,status='IID_COMPLETE_AWAITING_DIAGNOSTICS')
  if record['proposal_sha256']!=psha:raise RuntimeError('Completed target uses a different proposal.')
  released=out/f'released_target_{target:06d}.json'
  if released.exists():
   release=verify_record(released,runtime.identity,status='RAW_RELEASED')
   archived=out/f'approved_diagnostic_target_{target:06d}.json'
   expected={r['raw_file']:r['raw_sha256'] for r in record['replicates']}
   if release['raw_sha256']!=expected or not archived.exists() or sha256(archived)!=release['diagnostic_sha256']:raise RuntimeError('Released target lacks its preserved approved diagnostic.')
   return record
  for rep in record['replicates']:
   path=raw/rep['raw_file']
   if not path.exists() or sha256(path)!=rep['raw_sha256']:raise RuntimeError('Completed raw was removed or changed; use its approved diagnostic/release record, not silent recomputation.')
  return record
 for level_index,count in enumerate(levels):
  for replicate in range(replicates):
   name=f'target_{target:06d}_N{count}_rep_{replicate:02d}.npz';rawpath=raw/name;checkpoint=out/f'target_{target:06d}_N{count}_rep_{replicate:02d}.json'
   if checkpoint.exists():
    if not resume:raise FileExistsError('IID checkpoint exists.')
    rep=verify_record(checkpoint,runtime.identity,status='IID_REPLICATE_COMPLETE')
    if rep['proposal_sha256']!=psha or rep['samples']!=count or rep['replicate']!=replicate or not rawpath.exists() or sha256(rawpath)!=rep['raw_sha256']:raise RuntimeError('IID checkpoint/raw mismatch.')
    summaries.append(rep);continue
   orphan=rawpath.exists()
   if orphan and not resume:raise RuntimeError('Uncommitted raw output exists; explicit --resume performs deterministic replay and comparison.')
   actual_bytes=sum(p.stat().st_size for p in raw.glob('target_*.npz'))
   predicted=count*(14*8+1)+65536
   if actual_bytes+(0 if orphan else predicted)>runtime.settings['budget']['maximum_active_raw_bytes']:raise RuntimeError('Raw quota reached. Diagnose and explicitly release completed targets before continuing.')
   rng=rng_for(settings['seed'],320+100*level_index,target,replicate);state_before=rng.bit_generator.state;start=perf_counter();z,component=sample_single_target(proposal,rng,count);x=expit(z);logq=proposal.logpdf(z);logprior=(-np.logaddexp(0,-z)-np.logaddexp(0,z)).sum(axis=1);theta=runtime.bounds[:,0]+x*np.diff(runtime.bounds,axis=1)[:,0];ll=np.empty(count)
   for begin in range(0,count,batch):
    stop=min(count,begin+batch);ll[begin:stop]=runtime.likelihood(theta[begin:stop],np.full(stop-begin,target,int))
   logw=ll+logprior-logq
   if not all(np.isfinite(a).all() for a in [z,x,ll,logq,logprior,logw]):raise ArithmeticError('Nonfinite likelihood/weight; no silent clipping or dropped points.')
   saturated=np.any((x==0)|(x==1),axis=1);satmass=float(np.exp(logsumexp(logw[saturated])-logsumexp(logw))) if saturated.any() else 0.
   raw_arrays=dict(z=z,x_unit=x,log_likelihood=ll,log_weights=logw,log_proposal=logq,log_prior_logit=logprior,proposal_component=component.astype(np.uint8),target=np.asarray(target),replicate=np.asarray(replicate))
   if orphan:verify_arrays(rawpath,raw_arrays)
   else:write_npz_new(rawpath,compressed=settings.get('raw_compression','stored')=='deflate',**raw_arrays)
   rep=dict(status='IID_REPLICATE_COMPLETE',identity=runtime.identity,target=target,replicate=replicate,level=count,level_index=level_index,samples=count,likelihood_evaluations=count,orphan_recovered_by_deterministic_replay=orphan,raw_compression=settings.get('raw_compression','stored'),raw_file=name,raw_sha256=sha256(rawpath),raw_bytes=rawpath.stat().st_size,proposal_sha256=psha,seed=settings['seed'],rng_recipe='PCG64 SeedSequence([master,320+100*level_index,global_target,replicate]); uniforms, normals and chisquares outside likelihood workers',rng_state_before=state_before,rng_state_after=rng.bit_generator.state,weight_summary=json_safe(weight_summary(logw)),saturated_rows=int(saturated.sum()),saturated_normalized_target_weight=satmass,seconds=perf_counter()-start,uses_truth=False,precision_claimed=False)
   # A separate seed produces a SMALL descriptive weighted resample. It is never
   # supplied to MCSE/SBC diagnostics and is not labelled IID posterior sampling.
   viscount=positive_int(settings.get('descriptive_points_per_replicate',128),'descriptive count');visrng=rng_for(settings['seed'],330+100*level_index,target,replicate);selected=visrng.choice(count,size=viscount,replace=True,p=np.exp(logw-logsumexp(logw)))
   description_path=out/f'descriptive_target_{target:06d}_N{count}_rep_{replicate:02d}.npz';description_arrays=dict(x_unit=x[selected],source_indices=selected,label=np.asarray('Descriptive weighted resample of finite importance cloud; not IID posterior draws; excluded from precision/SBC.'))
   if description_path.exists():
    if not resume:raise FileExistsError('Existing descriptive sample requires explicit resume.')
    verify_arrays(description_path,description_arrays)
   else:write_npz_new(description_path,**description_arrays)
   write_json_new(checkpoint,rep);summaries.append(rep)
 record=dict(status='IID_COMPLETE_AWAITING_DIAGNOSTICS',identity=runtime.identity,target=target,model=MODELS[target//runtime.n],datum=target%runtime.n,proposal_sha256=psha,levels=levels,replicates=summaries,uses_truth=False,posterior_precision_claimed=False,input_sha256=runtime.input_hashes)
 runtime.verify_unchanged();write_json_new(complete,record);return record

def verify_arrays(path,expected):
 """Resume only an exact deterministic replay; never replace an orphan file."""
 with np.load(path,allow_pickle=False) as saved:
  if set(saved.files)!=set(expected):raise RuntimeError('Orphan array names differ from deterministic replay.')
  for name,array in expected.items():
   old=saved[name]
   if old.dtype!=array.dtype or old.shape!=array.shape or not np.array_equal(old,array):raise RuntimeError('Orphan array differs from deterministic replay: '+name)


def release_raw(runtime,target,output_root,raw_root,diagnostic_path,*,resume=False):
 """Explicit post-diagnostic release. No automatic raw removal by the producer."""
 target=positive_int(target,'target',True);out=Path(output_root);raw=Path(raw_root);diagnostic=verify_record(diagnostic_path,runtime.identity,status='NUMERICALLY_APPROVED');record=verify_record(out/f'target_{target:06d}.json',runtime.identity,status='IID_COMPLETE_AWAITING_DIAGNOSTICS')
 if diagnostic.get('target')!=target:raise RuntimeError('Diagnostic target mismatch.')
 required_checks={'orf_and_kernel_validation','weight_and_saturation_guards','cdf_precision','replication','refinement','reference_controls'}
 checks=diagnostic.get('checks',{})
 if diagnostic.get('approval_scope')!='posterior_numerical_validation' or set(checks)!=required_checks or any(checks[k] is not True for k in required_checks) or not diagnostic.get('validation_references'):raise RuntimeError('Complete external numerical approval is required; MCSE/ESS alone do not authorize raw release.')
 required={rep['raw_file']:rep['raw_sha256'] for rep in record['replicates']}
 if diagnostic.get('raw_sha256')!=required:raise RuntimeError('Diagnostic is not linked to exactly these raw samples.')
 intent=out/f'release_intent_target_{target:06d}.json';done=out/f'released_target_{target:06d}.json';dsha=sha256(diagnostic_path)
 if done.exists():
  if not resume:raise FileExistsError('Raw release already completed.')
  old=verify_record(done,runtime.identity,status='RAW_RELEASED')
  if old['diagnostic_sha256']!=dsha:raise RuntimeError('Release diagnostic changed.')
  return old
 if intent.exists():
  if not resume:raise FileExistsError('Raw release intent exists; explicit resume required.')
  old=verify_record(intent,runtime.identity,status='RAW_RELEASE_AUTHORIZED')
  if old['diagnostic_sha256']!=dsha or old['raw_sha256']!=required:raise RuntimeError('Release intent changed.')
 else:
  for name,digest in required.items():
   if Path(name).name!=name or not (raw/name).is_file() or sha256(raw/name)!=digest:raise RuntimeError('Raw integrity failed before release.')
  archived=out/f'approved_diagnostic_target_{target:06d}.json'
  if archived.exists():
   if sha256(archived)!=dsha:raise RuntimeError('Preserved diagnostic differs.')
  else:atomic_new(archived,lambda p:p.write_bytes(Path(diagnostic_path).read_bytes()))
  write_json_new(intent,dict(status='RAW_RELEASE_AUTHORIZED',identity=runtime.identity,target=target,diagnostic_sha256=dsha,raw_sha256=required))
 for name,digest in required.items():
  path=raw/name
  if path.exists():
   if path.is_symlink() or sha256(path)!=digest:raise RuntimeError('Raw changed during release.')
   path.unlink()
 result=dict(status='RAW_RELEASED',identity=runtime.identity,target=target,diagnostic_sha256=dsha,raw_sha256=required,proposals_checkpoints_and_descriptive_samples_retained=True)
 write_json_new(done,result);return result
