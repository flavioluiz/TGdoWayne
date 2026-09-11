"""Authorized C08 v2 table-only execution. Immutable v1 history and explicit delta ledger."""
import os
os.environ['VECLIB_MAXIMUM_THREADS']='1'
from pathlib import Path
import sys,json,hashlib,gc,time,resource
import numpy as np
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];OLD=ROOT/'tmp/c08_beta_table'
sys.path.insert(0,str(OLD));sys.path.insert(0,str(OLD/'executed_sources/src'))
from beta_builder import sha_file,canonical,digest,write_json,write_npz,matrices,Ledger,beta_from_u,u_from_beta
from inference.model import experiment,YEAR
from inference.orf_blas import RealHarmonicBasis,TableBudget,estimate
from pta.orf import raw_direct_orf
from curve_algebra_v2 import evaluate,subdivide,bernstein_eigenvalues
from gate_kernel import compressed_moments,compressed_logpdf


def load_curve(path):
 with np.load(path,allow_pickle=False) as z:return z['nodes'].copy(),z['matrices'].copy(),z['coeff'].copy()

def run():
 auth=json.loads((HERE/'execution_authorized.json').read_text());V2=ROOT/'tmp/c08_beta_table_v2';CURVES=V2/'results';plan=json.loads((V2/'preflight.json').read_text());identity=hashlib.sha256(canonical(auth).encode()).hexdigest();out=HERE/'results'
 if (out/'gate_request.json').exists():raise FileExistsError('No implicit resume/overwrite of gates')
 def verify():
  for p,h in auth['input_source_sha256'].items():
   if sha_file(ROOT/p)!=h:raise RuntimeError('Frozen input/source changed: '+p)
 verify();write_json(out/'gate_request.json',dict(identity=identity,authorization_sha256=sha_file(HERE/'execution_authorized.json'),authorization=auth,worker_files={str(p.relative_to(ROOT)):sha_file(p) for p in out.glob('oracle_k4_*.npz')}))
 baseline=auth['baseline'];caps=auth['cumulative_limits'];delta_limits={k:caps[k]-baseline[k] for k in caps};delta_limits['logL']=min(delta_limits['logL'],auth['maximum_additional_logL']);ledger=Ledger(out/'resource_delta_ledger.jsonl',delta_limits,identity)
 def totals():return {k:baseline[k]+ledger.totals[k] for k in baseline}
 def rss(phase):
  peak=int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
  if peak>auth['maximum_RSS_bytes']:raise MemoryError('Observed Darwin RSS ceiling exceeded at '+phase)
  return peak
 cfg=json.loads((OLD/'inputs/experiment.json').read_text());e=experiment(cfg);P=len(e['points']);phase=2*np.pi*e['f'][:,None]*e['distance_ly'][None]*YEAR;cos=np.clip(e['points']@e['points'].T,-1,1);start=time.perf_counter();stages={}
 try:
  stages['local_curves']=json.loads((CURVES/'local_curves.json').read_text());newu=np.array(plan['validation']['new_control_u']);neworacle=np.empty((72,4,P,P),complex);oraclereports=[]
  for k in range(1,5):
   if k<4:
    with np.load(CURVES/f'oracle_channel{k:02d}.npz',allow_pickle=False) as z:
     if not np.array_equal(z['u'],newu):raise RuntimeError('Reused oracle coordinates changed')
     co=z['Gamma_coarse'].copy();fi=z['Gamma_fine'].copy();r=json.loads(str(z['record']))
     if r['channel']!=k or r['identity']!=auth['previous_execution_identity']:raise RuntimeError('Reused oracle identity changed')
   else:
    arrays=[]
    for label in ['coarse','fine']:
     with np.load(out/f'oracle_k4_{label}.npz',allow_pickle=False) as z:
      r=json.loads(str(z['record']))
      if not np.array_equal(z['u'],newu) or r['identity']!=identity or r['channel']!=4 or r['resolution']!=label or r['orders']!=plan['rows'][3]['oracle_orders_'+label]:raise RuntimeError('Fresh worker identity mismatch')
      arrays.append(z['Gamma'].copy())
    co,fi=arrays
   matrices(co,72,P);matrices(fi,72,P);error=float(np.max(abs(co-fi)))
   if error>1e-8:raise RuntimeError('Oracle harmonic convergence gate failed')
   neworacle[:,k-1]=fi;oraclereports.append(dict(channel=k,error=error,reused_v2=(k<4)));del co,fi
  stages['new_oracles']=oraclereports;write_json(out/'new_oracles.json',oraclereports)
  direct=[]
  for row in plan['rows'][1:]:
   k=row['channel']
   for check in row['new_direct_checks']:
    uu=float(u_from_beta(np.array([check['beta']]))[0]);bb=float(beta_from_u(np.array([uu]))[0]);j=int(np.searchsorted(newu,uu))
    if j==len(newu) or newu[j]!=uu:raise RuntimeError('Frozen direct anchor absent from oracle controls')
    for ia,ib in check['pairs']:
     vals=[]
     for label,orders in [('coarse',check['coarse_nmu_nphi']),('fine',check['fine_nmu_nphi'])]:
      nm,np_=orders;ledger.charge('angular',nm*np_,dict(channel=k,beta=bb,pair=[ia,ib],resolution=label));vals.append(raw_direct_orf(bb,float(cos[ia,ib]),float(phase[k-1,ia]),float(phase[k-1,ib]),nmu=nm,nphi=np_));rss('direct')
     dc=float(abs(vals[0]-vals[1]));dh=float(abs(vals[1]-neworacle[j,k-1,ia,ib]));direct.append(dict(channel=k,u=uu,beta=bb,pair=[ia,ib],coarse_fine=dc,direct_harmonic=dh))
     if max(dc,dh)>1e-7:raise RuntimeError('Independent direct gate failed')
  stages['direct']=direct;write_json(out/'direct_checks.json',direct)
  with np.load(OLD/'results/gates/validation_matrices.npz',allow_pickle=False) as z:histu=z['u'].copy();histold=z['fine'].copy();historacle=z['oracle'].copy()
  histfine=np.empty_like(histold);newcoarse=np.empty_like(neworacle);newfine=np.empty_like(neworacle);outside=histu<plan['rows'][1]['boundary_u'];union=None
  for k in range(1,5):
   n,g,c=load_curve(CURVES/f'curve_channel{k:02d}.npz');histfine[:,k-1:k]=evaluate(n,c,histu);newfine[:,k-1:k]=evaluate(n,c,newu);union=n.copy() if union is None else np.union1d(union,n);del n,g,c
   n,g,c=load_curve(OLD/f'results/gates/curve_channel{k:02d}.npz');newcoarse[:,k-1:k]=evaluate(n,c,newu);del n,g,c;gc.collect()
  if not np.array_equal(histfine[outside],histold[outside]):raise RuntimeError('Outside patch Gamma not bit exact; historical LL reuse prohibited')
  if not np.array_equal(histfine[:,0],histold[:,0]):raise RuntimeError('First channel inheritance not bit exact')
  write_npz(out/'validation_matrices.npz',historical_u=histu,historical_old_fine=histold,historical_new_fine=histfine,historical_oracle=historacle,new_u=newu,new_coarse=newcoarse,new_fine=newfine,new_oracle=neworacle)
  bounds=np.array(cfg['prior']['bounds'])[1:]
  def nuisances(seed):return bounds[:,0]+np.random.default_rng(seed).uniform(size=(64,4))*np.diff(bounds)[:,0]
  oldeta=nuisances(808120201);neweta=nuisances(plan['validation']['new_nuisance_seed'])
  with np.load(OLD/'inputs/pilot_data.npz',allow_pickle=False) as z:x=np.concatenate([z['x_physical'],z['x_gaussian']],axis=0)
  observed=np.einsum('rkd,k->rd',x,e['weights']);del x
  def ll(eta,g,label,u):
   ledger.charge('logL',64*32,dict(stage=label,u=float(u)));mu,cov=compressed_moments(eta,g,e);v=compressed_logpdf(mu,cov,observed)
   if v.shape!=(64,32) or not np.isfinite(v).all():raise RuntimeError('Nonfinite/wrong LL shape')
   return v
  checks=[]
  def compare(kind,j,u,vc,vf,vo):
   dcf=abs(vc-vf);dfo=abs(vf-vo);r=dict(kind=kind,index=j,u=float(u),coarse_fine=float(dcf.max()),fine_oracle=float(dfo.max()),worst_coarse_fine=list(map(int,np.unravel_index(np.argmax(dcf),dcf.shape))),worst_fine_oracle=list(map(int,np.unravel_index(np.argmax(dfo),dfo.shape))));checks.append(r)
   write_npz(out/'likelihood_cache'/f'{kind}_{j:04d}.npz',u=np.array(u),logL_coarse=vc,logL_fine=vf,logL_oracle=vo,nuisances_sha256=np.array(digest(oldeta if kind=='historical' else neweta)),observations_sha256=np.array(digest(observed)),identity=np.array(identity))
   if max(r['coarse_fine'],r['fine_oracle'])>.001:
    write_json(out/'likelihood_failed.json',dict(rows=checks,failed=r));raise RuntimeError('Likelihood interpolation .001 gate failed; no automatic refinement')
  oldidentity=json.loads((OLD/'results/matrix_manifest.json').read_text())['identity']
  for j,u in enumerate(histu):
   path=OLD/('results/gates/likelihood_cache' if j<121 else 'results/original_diagnostic_continuation/likelihood_cache')/f'node_{j:04d}.npz'
   with np.load(path,allow_pickle=False) as z:
    if float(z['u'])!=u or str(z['nuisances_sha256'])!=digest(oldeta) or str(z['observations_sha256'])!=digest(observed) or str(z['construction_identity'])!=oldidentity:raise RuntimeError('Historical cache identity mismatch')
    vc=z['logL_fine'].copy();vo=z['logL_oracle'].copy()
   if not np.isfinite(vc).all() or not np.isfinite(vo).all():raise ValueError('Nonfinite historical cache')
   vf=vc.copy() if outside[j] else ll(oldeta,histfine[j],'historical_new_fine',u);compare('historical',j,u,vc,vf,vo)
  stages['historical_likelihood_completed']=len(histu);print(json.dumps(dict(stage='historical_ll',logL_delta=ledger.totals['logL'],maximum_coarse_fine=max(r['coarse_fine'] for r in checks),maximum_fine_oracle=max(r['fine_oracle'] for r in checks))),flush=True)
  for j,u in enumerate(newu):compare('new',j,u,ll(neweta,newcoarse[j],'new_coarse',u),ll(neweta,newfine[j],'new_fine',u),ll(neweta,neworacle[j],'new_oracle',u))
  stages['likelihood']=dict(rows=checks,maximum_coarse_fine=max(r['coarse_fine'] for r in checks),maximum_fine_oracle=max(r['fine_oracle'] for r in checks),new_logL_values=ledger.totals['logL'],historical_outside_reuse_bitexact=True,old_nuisance_seed=808120201,new_nuisance_seed=plan['validation']['new_nuisance_seed'],no_truth_deserialized=True)
  write_json(out/'likelihood_checks.json',stages['likelihood']);write_npz(out/'likelihood_nuisances.npz',historical_eta=oldeta,new_eta=neweta)
  if len(union)!=plan['resources']['union_interpolation_nodes']:raise RuntimeError('Common union count differs')
  # Export only exact polynomial subdivision, never a new common spline fit.
  coeff=np.empty((len(union)-1,4,4,P,P),complex);gamma=np.empty((len(union),4,P,P),complex);subchecks=[];allu=np.r_[histu,newu]
  for k in range(1,5):
   n,g,c=load_curve(CURVES/f'curve_channel{k:02d}.npz');sub=subdivide(n,c,union);coeff[:,:,k-1:k]=sub;gamma[:,k-1:k]=evaluate(n,c,union);d=float(np.max(abs(evaluate(union,sub,allu)-evaluate(n,c,allu))))
   if d>1e-11:raise RuntimeError('Subdivision curve identity gate failed')
   subchecks.append(dict(channel=k,maximum_subdivision_error=d,**bernstein_eigenvalues(sub)));del n,g,c,sub;gc.collect();rss('common export')
  write_npz(out/'C_beta_common_table.npz',nodes=union,matrices=gamma,coeff=coeff,coordinate=np.array('minus_beta'),response=np.array('C_beta: common beta_ref, actual channel phases'),construction_identity=np.array(identity));del coeff,gamma;gc.collect();stages['subdivision']=subchecks
  expected=json.loads((HERE/'preflight.json').read_text())['remaining_work']
  if ledger.totals!=expected:raise RuntimeError('Executed work differs from frozen exact plan')
  verify();report=dict(status='C_BETA_V2_PASS_STATED_FINITE_TABLE_GATES_ONLY',technical_continuation_preserves_failed_attempt=True,previous_failed_execution_sha256=sha_file(V2/'results/failure.json'),identity=identity,stages=stages,resource_delta=ledger.totals,resource_cumulative=totals(),seconds=time.perf_counter()-start,RSS_peak_bytes=rss('finished'),workers=1,VECLIB_MAXIMUM_THREADS=1,RSS_units='Darwin bytes; observed, not guaranteed by numeric estimate',no_posterior_inference=True,no_C07_modifications=True,no_T_window_execution=True,finite_checks_not_uniform_error_proof=True,table_sha256=sha_file(out/'C_beta_common_table.npz'),authorization_sha256=sha_file(HERE/'execution_authorized.json'));write_json(out/'final_report.json',report);print(json.dumps({k:v for k,v in report.items() if k!='stages'}),flush=True)
 except Exception as exc:
  write_json(out/'failure.json',dict(status='FAILED_NO_AUTOMATIC_REFINEMENT',identity=identity,type=type(exc).__name__,message=str(exc),stages_completed=list(stages),resource_delta=ledger.totals,resource_cumulative=totals(),seconds=time.perf_counter()-start,RSS_peak_bytes=int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)));raise
if __name__=='__main__':run()
