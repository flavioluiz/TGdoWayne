"""Finish the ORIGINAL finite gate cases after an explicitly authorized stop.

No meshes, quadratures, criteria or old outputs are changed. This continuation
cannot classify the candidate PASS: it only completes the failure diagnosis.
"""
import os
os.environ['VECLIB_MAXIMUM_THREADS']='1'
from pathlib import Path
import datetime,json,time,resource
import numpy as np
from beta_builder import HERE,ROOT,sha_file,canonical,digest,write_json,write_npz,Ledger
from inference.model import experiment
from gate_kernel import compressed_moments,compressed_logpdf

def run():
 cfg=json.loads((HERE/'execution_authorized.json').read_text());old=HERE/'results/gates';out=HERE/'results/original_diagnostic_continuation';out.mkdir(exist_ok=False)
 failure=json.loads((old/'failure.json').read_text());previous=json.loads((old/'likelihood_failed.json').read_text());record=json.loads((HERE/'results/execution_request.json').read_text());identity=record['identity'];ecfg=json.loads((HERE/'inputs/experiment.json').read_text());e=experiment(ecfg)
 bounds=np.array(ecfg['prior']['bounds'])[1:];eta=bounds[:,0]+np.random.default_rng(cfg['likelihood_nuisance_seed']).uniform(size=(64,4))*np.diff(bounds)[:,0]
 with np.load(HERE/'inputs/pilot_data.npz',allow_pickle=False) as d:x=np.concatenate([d['x_physical'],d['x_gaussian']],axis=0)
 observed=np.einsum('rkd,k->rd',x,e['weights']);del x
 with np.load(old/'validation_matrices.npz',allow_pickle=False) as z:data={k:z[k].copy() for k in ['u','coarse','fine','oracle']}
 u=data['u'];start_index=len(previous['rows']);assert start_index==121 and len(u)==143 and len(u)-start_index==22
 paths=[Path(__file__),HERE/'gate_kernel.py',old/'failure.json',old/'likelihood_failed.json',old/'validation_matrices.npz',HERE/'inputs/experiment.json',HERE/'inputs/pilot_data.npz',HERE/'execution_authorized.json']+sorted((old/'likelihood_cache').glob('node_*.npz'))
 hashes={str(p.relative_to(ROOT)):sha_file(p) for p in paths}
 for path,h in cfg['source_sha256'].items():
  if sha_file(ROOT/path)!=h:raise ValueError('Frozen construction input changed')
 auth=dict(schema='C08_ORIGINAL_DIAGNOSTIC_CONTINUATION_v1',authorized_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),authorization='Parent /root: evaluate only the remaining22 original masses,135168 logL, original cumulative cap1M, separate diagnostic continuation, no PASS status.',old_failure_sha256=sha_file(old/'failure.json'),old_execution_identity=identity,new_logL_values=22*3*64*32,old_logL_values=failure['resource_totals']['logL'],cumulative_expected_logL=878592,source_input_sha256=hashes)
 write_json(out/'authorization_and_inputs.json',auth)
 ledger=Ledger(HERE/'results/resource_ledger.jsonl',dict(real=cfg['maximum_real_multiplications'],angular=cfg['maximum_direct_angular_work'],logL=cfg['maximum_logL_values']),identity)
 if ledger.totals!=failure['resource_totals']:raise ValueError('Unexpected intervening resource ledger entries')
 start=time.perf_counter();rows=[];maxcf=maxfo=0.;worstcf=worstfo=None
 for j,uu in enumerate(u):
  if j<start_index:
   with np.load(old/'likelihood_cache'/f'node_{j:04d}.npz',allow_pickle=False) as z:
    if float(z['u'])!=uu or str(z['construction_identity'])!=identity or str(z['nuisances_sha256'])!=digest(eta) or str(z['observations_sha256'])!=digest(observed):raise ValueError('Old cached likelihood identity mismatch')
    vals=[z['logL_'+key].copy() for key in ['coarse','fine','oracle']]
  else:
   vals=[]
   for key in ['coarse','fine','oracle']:
    ledger.charge('logL',64*32,dict(scope='original_diagnostic_continuation',u=float(uu),representation=key));mu,cov=compressed_moments(eta,data[key][j],e);vals.append(compressed_logpdf(mu,cov,observed))
   write_npz(out/'likelihood_cache'/f'node_{j:04d}.npz',u=np.array(uu),logL_coarse=vals[0],logL_fine=vals[1],logL_oracle=vals[2],nuisances_sha256=np.array(digest(eta)),observations_sha256=np.array(digest(observed)),construction_identity=np.array(identity))
  if any(v.shape!=(64,32) or not np.isfinite(v).all() for v in vals):raise ValueError('Invalid likelihood payload')
  dcf=abs(vals[0]-vals[1]);dfo=abs(vals[1]-vals[2]);ec=float(dcf.max());eo=float(dfo.max())
  if ec>maxcf:maxcf=ec;worstcf=dict(u=float(uu),beta=float(np.sqrt((1-uu)*(1+uu))),index=list(map(int,np.unravel_index(np.argmax(dcf),dcf.shape))))
  if eo>maxfo:maxfo=eo;worstfo=dict(u=float(uu),beta=float(np.sqrt((1-uu)*(1+uu))),index=list(map(int,np.unravel_index(np.argmax(dfo),dfo.shape))))
  rows.append(dict(u=float(uu),beta=float(np.sqrt((1-uu)*(1+uu))),coarse_fine=ec,fine_oracle=eo,coarse_fine_within_registered_threshold=ec<=.001,fine_oracle_within_registered_threshold=eo<=.001))
 for path,h in hashes.items():
  if sha_file(ROOT/path)!=h:raise ValueError('Frozen original evidence or source changed')
 rss=int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
 if rss>cfg['maximum_RSS_bytes']:raise MemoryError('RSS operational ceiling exceeded')
 report=dict(status='ORIGINAL_DIAGNOSTICS_COMPLETE_CANDIDATE_REMAINS_FAILED',old_failure_preserved=True,rows=rows,maximum_coarse_fine=maxcf,maximum_fine_oracle=maxfo,worst_coarse_fine=worstcf,worst_fine_oracle=worstfo,coarse_fine_failures=sum(r['coarse_fine']>.001 for r in rows),fine_oracle_failures=sum(r['fine_oracle']>.001 for r in rows),resource_totals=ledger.totals,new_logL_values=22*3*64*32,seconds=time.perf_counter()-start,RSS_peak_bytes=rss,no_new_ORF_nodes=True,no_automatic_refinement=True,inputs_manifest_sha256=sha_file(out/'authorization_and_inputs.json'))
 write_json(out/'report.json',report);print(json.dumps({k:v for k,v in report.items() if k!='rows'}),flush=True)
if __name__=='__main__':run()
