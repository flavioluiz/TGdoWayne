import json
from pathlib import Path
import numpy as np
import unittest,tempfile
from unittest.mock import patch
from scipy.special import expit,beta as beta_function
from scipy.stats import beta,norm,t
from inference.mh_training import TargetSeededMH
from inference.linalg_batch import forward_substitution
from inference.gmm_proposal import GaussianDefensiveProposal
from inference.likelihood_threads import ThreadedLikelihood
from inference.campaign_iid import sample_single_target,produce_target,release_raw
from inference.campaign_diagnostic_io import load_target_levels
from inference.campaign_io import canonical_hash,write_json_new,read_json,load_observations

def expect_raises(exc,match=''):
 return unittest.TestCase().assertRaisesRegex(exc,match)

A=np.array([1.3,2.1,3.2,.7,1.2]);B=np.array([1.7,4.,2.,1.4,.9])
def target(z,ids):
 x=expit(z);ll=np.sum(beta.logpdf(x,A,B),axis=1);jac=(-np.logaddexp(0,-z)-np.logaddexp(0,z)).sum(axis=1);return ll+jac,ll

def mh(ids):
 s=TargetSeededMH(target,ids,seed=987123,chains=4,mass_probability=.15,nuisance_probability=.20,independence_probability=.45,student_scales=[1.,3.],student_weights=[.75,.25]);s.solve=forward_substitution;return s

def test_rng_target_batch_permutation_and_subset():
 full=mh([1,7]);reverse=mh([7,1]);single=mh([7])
 for i in range(1300):
  a,_=full.step(adapt=True);b,_=reverse.step(adapt=True);c,_=single.step(adapt=True)
  np.testing.assert_allclose(a,b[::-1],atol=2e-14,rtol=0);np.testing.assert_allclose(a[1],c[0],atol=2e-14,rtol=0)
 assert np.array_equal(full.accept,reverse.accept[:,::-1])
 full.freeze()
 with expect_raises(RuntimeError):full.step(adapt=True)
 with expect_raises(RuntimeError):mh([1]).freeze()

def mixture():
 return GaussianDefensiveProposal(np.array([[.6,.4]]),np.array([[[-.5,.3,0.,.2,-.4],[.7,-.2,.3,-.4,.1]]]),np.broadcast_to(np.eye(5),(1,2,5,5)).copy(),np.zeros((1,5)),np.eye(5)[None],defensive_fraction=.15,student_df=5,student_scale=3)

def test_vectorized_sampler_projection_cdf():
 q=mixture();z,_=sample_single_target(q,np.random.default_rng(91231),131072)
 for coordinate in [0,3]:
  for cut in [-2.,-.3,1.1,3.]:
   expected=.85*sum(w*norm.cdf(cut,mu[coordinate],1) for w,mu in zip(q.weights[0],q.means[0]))+.15*t.cdf(cut/(3*np.sqrt(3/5)),df=5)
   actual=np.mean(z[:,coordinate]<=cut);se=np.sqrt(expected*(1-expected)/len(z));assert abs(actual-expected)<4.5*se

class ToyRuntime:
 def __init__(self):
  self.identity='toy_execution';self.target_identity='toy_data';self.targets=np.array([0,1]);self.n=2;self.bounds=np.tile([0.,1.],(5,1));self.input_hashes={};self.settings={'production':{'levels':[64,256],'replicates':4,'seed':91232,'likelihood_batch':64,'descriptive_points_per_replicate':16},'budget':{'maximum_active_raw_bytes':2000000}}
 def require_execution(self):return self
 def set_phase(self,phase):self.phase=phase
 def snapshot(self,path):return None
 def verify_unchanged(self):return None
 def likelihood(self,theta,ids):return np.sum(beta.logpdf(theta,A,B),axis=1)

def put_proposal(path):
 q=mixture();r=dict(status='FROZEN_PROPOSAL',identity='toy_data',target=0,uses_truth=False,weights=q.weights[0].tolist(),means=q.means[0].tolist(),covariances=q.cov[0].tolist(),global_mean=q.global_mean[0].tolist(),global_cholesky=q.global_chol[0].tolist(),defensive_fraction=q.alpha,student_df=q.nu,student_scale=q.scale)
 r['proposal_content_hash']=canonical_hash(r);write_json_new(path/'target_000000.json',r)

def test_checkpoint_resume_and_explicit_release(tmp_path):
 rt=ToyRuntime();proposals=tmp_path/'proposals';out=tmp_path/'summary';raw=tmp_path/'raw';put_proposal(proposals)
 result=produce_target(rt,0,proposals,out,raw);assert len(result['replicates'])==8
 loaded,levels=load_target_levels(out/'target_000000.json',raw);assert sorted(levels)==[64,256] and levels[256]['x_unit'].shape==(4,256,5)
 with expect_raises(FileExistsError):produce_target(rt,0,proposals,out,raw)
 assert produce_target(rt,0,proposals,out,raw,resume=True)==result
 states=[json.dumps(r['rng_state_before'],sort_keys=True) for r in result['replicates']];assert len(set(states))==8
 # No truth member is present; every output carries raw proposal/likelihood terms.
 for p in raw.glob('*.npz'):
  with np.load(p) as saved:assert 'truth' not in saved and 'log_prior_logit' in saved
 bad=tmp_path/'bad_diagnostic.json';write_json_new(bad,dict(status='NUMERICALLY_APPROVED',identity=rt.identity,target=0,raw_sha256={}))
 with expect_raises(RuntimeError):release_raw(rt,0,out,raw,bad)
 good=tmp_path/'good_diagnostic.json';write_json_new(good,dict(status='NUMERICALLY_APPROVED',identity=rt.identity,target=0,approval_scope='posterior_numerical_validation',checks={k:True for k in ['orf_and_kernel_validation','weight_and_saturation_guards','cdf_precision','replication','refinement','reference_controls']},validation_references={'toy':'analytic beta only; not PTA approval'},raw_sha256={r['raw_file']:r['raw_sha256'] for r in result['replicates']}))
 release_raw(rt,0,out,raw,good);assert not list(raw.glob('*.npz'));assert len(list(out.glob('descriptive_*.npz')))==8
 assert produce_target(rt,0,proposals,out,raw,resume=True)==result
 assert release_raw(rt,0,out,raw,good,resume=True)['status']=='RAW_RELEASED'

def test_raw_quota_blocks_before_generation(tmp_path):
 rt=ToyRuntime();rt.settings['budget']['maximum_active_raw_bytes']=1;put_proposal(tmp_path/'p')
 with expect_raises(RuntimeError,match='quota'):produce_target(rt,0,tmp_path/'p',tmp_path/'o',tmp_path/'r')
 assert not list((tmp_path/'r').glob('*.npz'))

def test_observation_loader_never_reads_truth(monkeypatch):
 exp=dict(points=np.eye(2),distance_ly=np.ones(2),sigma=np.ones(2),red=np.ones(2),f=np.ones(1),scale=np.ones(1),H=np.ones((1,2,2)))
 values=dict(q=np.ones((2,1,2),complex),x_physical=np.ones((2,1,1)),x_gaussian=np.ones((2,1,1)),directions=exp['points'],distances_ly=exp['distance_ly'],sigma=exp['sigma'],red_pattern=exp['red'],frequency_hz=exp['f'],scale=exp['scale']);read=[]
 class Guard:
  def __enter__(self):return self
  def __exit__(self,*args):return None
  def __contains__(self,key):return key in values or key=='truth'
  def __getitem__(self,key):
   read.append(key)
   if key=='truth':raise AssertionError('Injected truth was read.')
   return values[key]
 monkeypatch.setattr(np,'load',lambda *a,**k:Guard());loaded=load_observations('ignored',exp);assert set(loaded)=={'q','x_physical','x_gaussian'} and 'truth' not in read

class PortableContracts(unittest.TestCase):
 def test_target_rng(self):test_rng_target_batch_permutation_and_subset()
 def test_iid_sampler(self):test_vectorized_sampler_projection_cdf()
 def test_thread_order(self):
  def function(theta,ids):return np.sum(theta*theta,axis=1)+ids
  x=np.arange(1025*5,dtype=float).reshape(1025,5)/100.;ids=np.arange(1025)
  parallel=ThreadedLikelihood(function,6)
  try:
   for workers in [1,4,6,1]:
    parallel.set_workers(workers);np.testing.assert_array_equal(parallel(x,ids),function(x,ids))
   with self.assertRaises(ValueError):parallel.set_workers(7)
  finally:parallel.close()
 def test_checkpoints(self):
  with tempfile.TemporaryDirectory() as path:test_checkpoint_resume_and_explicit_release(Path(path))
 def test_orphan_recovery(self):
  with tempfile.TemporaryDirectory() as directory:
   root=Path(directory);rt=ToyRuntime();put_proposal(root/'p')
   import inference.campaign_iid as module
   original=module.write_json_new
   def interrupt_checkpoint(path,record):
    if record.get('status')=='IID_REPLICATE_COMPLETE':raise RuntimeError('simulated interruption')
    return original(path,record)
   with patch.object(module,'write_json_new',interrupt_checkpoint):
    with self.assertRaisesRegex(RuntimeError,'simulated'):produce_target(rt,0,root/'p',root/'o',root/'r')
   result=produce_target(rt,0,root/'p',root/'o',root/'r',resume=True)
   self.assertTrue(result['replicates'][0]['orphan_recovered_by_deterministic_replay'])
   self.assertFalse(result['replicates'][1]['orphan_recovered_by_deterministic_replay'])
 def test_budget(self):
  with tempfile.TemporaryDirectory() as path:test_raw_quota_blocks_before_generation(Path(path))
 def test_truth_separation(self):
  class Patcher:
   def setattr(self,obj,key,value):self.p=patch.object(obj,key,value);self.p.start()
  helper=Patcher()
  try:test_observation_loader_never_reads_truth(helper)
  finally:helper.p.stop()
if __name__=='__main__':unittest.main()
