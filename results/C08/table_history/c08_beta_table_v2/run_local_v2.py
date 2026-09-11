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
from patch_curve import stitch

def load_curve(path):
 with np.load(path,allow_pickle=False) as z:return z['nodes'].copy(),z['matrices'].copy(),z['coeff'].copy()

def run():
 auth=json.loads((HERE/'execution_authorized.json').read_text());plan=json.loads((HERE/'preflight.json').read_text());identity=hashlib.sha256(canonical(auth).encode()).hexdigest();out=HERE/'results';out.mkdir(exist_ok=False)
 def verify():
  for p,h in auth['input_source_sha256'].items():
   if sha_file(ROOT/p)!=h:raise RuntimeError('Frozen input/source changed: '+p)
 verify();write_json(out/'execution_request.json',dict(identity=identity,authorization_sha256=sha_file(HERE/'execution_authorized.json'),authorization=auth))
 baseline=auth['baseline'];caps=auth['cumulative_limits'];delta_limits={k:caps[k]-baseline[k] for k in caps};delta_limits['logL']=min(delta_limits['logL'],auth['maximum_additional_logL']);ledger=Ledger(out/'resource_delta_ledger.jsonl',delta_limits,identity)
 def totals():return {k:baseline[k]+ledger.totals[k] for k in baseline}
 def rss(phase):
  peak=int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
  if peak>auth['maximum_RSS_bytes']:raise MemoryError('Observed Darwin RSS ceiling exceeded at '+phase)
  return peak
 cfg=json.loads((OLD/'inputs/experiment.json').read_text());e=experiment(cfg);P=len(e['points']);phase=2*np.pi*e['f'][:,None]*e['distance_ly'][None]*YEAR;cos=np.clip(e['points']@e['points'].T,-1,1);start=time.perf_counter();stages={}
 def harmonic(k,nodes,orders,label):
  lmax,nmu=orders;N=len(nodes);reserve=64*1024**2;est=estimate(lmax,nmu,P,8)
  if est['estimated_memory_bytes']+reserve>auth['maximum_numeric_bytes']:raise MemoryError('Explicit numeric estimate exceeded')
  basis=RealHarmonicBasis(e['points'],lmax=lmax,nmu=nmu,budget=TableBudget(auth['maximum_numeric_bytes']-reserve,2_000_000_000_000,8),planned_batch=8);rss('basis '+label);values=np.empty((N,P,P),complex);beta=beta_from_u(nodes)
  for first in range(0,N,8):
   last=min(first+8,N);ledger.charge('real',int(2*(last-first)*P*nmu*(lmax-1)),dict(channel=k,stage=label,first=first,last=last));values[first:last]=basis.evaluate(beta[first:last],phase[k-1]);rss('harmonic '+label)
  del basis;gc.collect();checks=matrices(values,N,P)
  print(json.dumps(dict(stage=label,channel=k,nodes=N,real_delta=ledger.totals['real'],seconds=time.perf_counter()-start,RSS_peak_bytes=rss(label))),flush=True)
  return values,checks
 try:
  # Local construction uses physical y, reducing l/n only through beta*y at the patch.
  reports=[]
  for row in plan['rows']:
   k=row['channel'];path=OLD/f'results/gates/curve_channel{k:02d}.npz';nodes,gamma,coeff=load_curve(path)
   if k==1:
    write_npz(out/'curve_channel01.npz',nodes=nodes,matrices=gamma,coeff=coeff,coordinate=np.array('minus_beta'));reports.append(dict(channel=1,inherited_ROOT_and_v1_bitexact=True,**bernstein_eigenvalues(coeff)))
   else:
    bound=row['boundary_u'];patch=np.union1d(nodes[nodes>=bound],u_from_beta(np.linspace(0,1/64,1025)))
    if len(patch)!=row['local_candidate_nodes']:raise RuntimeError('Prospective local node count changed')
    old_ix=np.where(nodes>=bound)[0];old_vals=gamma[old_ix,0].copy();del gamma,coeff;gc.collect()
    coarse,cs=harmonic(k,patch,row['patch_coarse_harmonic_orders'],'local_coarse');fine,fs=harmonic(k,patch,row['patch_fine_harmonic_orders'],'local_fine');err=float(np.max(abs(coarse-fine)));ix=np.searchsorted(patch,nodes[old_ix]);inheriterr=float(np.max(abs(fine[ix]-old_vals)))
    if max(err,inheriterr)>1e-8:raise RuntimeError('Local harmonic or old-node reproduction gate failed')
    write_npz(out/f'local_quadrature_channel{k:02d}.npz',u=patch,Gamma_coarse=coarse,Gamma_fine=fine,record=np.array(canonical(dict(channel=k,identity=identity,coarse_fine=err,old_node_error=inheriterr))))
    fine[ix]=old_vals;nodes,gamma,coeff=load_curve(path);nn,gg,cc,checks=stitch(nodes,gamma,coeff,patch,fine[:,None]);checks.update(bernstein_eigenvalues(cc))
    if len(nn)!=row['new_interpolation_nodes']:raise RuntimeError('Global refined count changed')
    write_npz(out/f'curve_channel{k:02d}.npz',nodes=nn,matrices=gg,coeff=cc,coordinate=np.array('minus_beta'));reports.append(dict(channel=k,harmonic_coarse_fine=err,old_node_reproduction_error=inheriterr,**checks));del nn,gg,cc,coarse,fine,old_vals
   del nodes,gamma,coeff;gc.collect();rss('local curve completed')
  stages['local_curves']=reports;write_json(out/'local_curves.json',reports)
  # All 72 new controls receive original full harmonic orders, including channel1.
  newu=np.array(plan['validation']['new_control_u']);neworacle=np.empty((len(newu),4,P,P),complex);oraclereports=[]
  for row in plan['rows']:
   k=row['channel'];co,cs=harmonic(k,newu,row['oracle_orders_coarse'],'new_oracle_coarse');fi,fs=harmonic(k,newu,row['oracle_orders_fine'],'new_oracle_fine');error=float(np.max(abs(co-fi)))
   if error>1e-8:raise RuntimeError('New full-order oracle convergence failed')
   neworacle[:,k-1]=fi;write_npz(out/f'oracle_channel{k:02d}.npz',u=newu,Gamma_coarse=co,Gamma_fine=fi,record=np.array(canonical(dict(identity=identity,channel=k,error=error,coarse=row['oracle_orders_coarse'],fine=row['oracle_orders_fine']))));oraclereports.append(dict(channel=k,error=error,coarse_checks=cs,fine_checks=fs));del co,fi;gc.collect()
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
   n,g,c=load_curve(out/f'curve_channel{k:02d}.npz');histfine[:,k-1:k]=evaluate(n,c,histu);newfine[:,k-1:k]=evaluate(n,c,newu);union=n.copy() if union is None else np.union1d(union,n);del n,g,c
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
   n,g,c=load_curve(out/f'curve_channel{k:02d}.npz');sub=subdivide(n,c,union);coeff[:,:,k-1:k]=sub;gamma[:,k-1:k]=evaluate(n,c,union);d=float(np.max(abs(evaluate(union,sub,allu)-evaluate(n,c,allu))))
   if d>1e-11:raise RuntimeError('Subdivision curve identity gate failed')
   subchecks.append(dict(channel=k,maximum_subdivision_error=d,**bernstein_eigenvalues(sub)));del n,g,c,sub;gc.collect();rss('common export')
  write_npz(out/'C_beta_common_table.npz',nodes=union,matrices=gamma,coeff=coeff,coordinate=np.array('minus_beta'),response=np.array('C_beta: common beta_ref, actual channel phases'),construction_identity=np.array(identity));del coeff,gamma;gc.collect();stages['subdivision']=subchecks
  expected=dict(real=plan['cost']['planned_new_real_products'],angular=plan['cost']['planned_new_direct_angular_work'],logL=plan['cost']['planned_new_logL'])
  if ledger.totals!=expected:raise RuntimeError('Executed work differs from frozen exact plan')
  verify();report=dict(status='C_BETA_V2_PASS_STATED_FINITE_TABLE_GATES_ONLY',identity=identity,stages=stages,resource_delta=ledger.totals,resource_cumulative=totals(),seconds=time.perf_counter()-start,RSS_peak_bytes=rss('finished'),workers=1,VECLIB_MAXIMUM_THREADS=1,RSS_units='Darwin bytes; observed, not guaranteed by numeric estimate',no_posterior_inference=True,no_C07_modifications=True,no_T_window_execution=True,finite_checks_not_uniform_error_proof=True,table_sha256=sha_file(out/'C_beta_common_table.npz'),authorization_sha256=sha_file(HERE/'execution_authorized.json'));write_json(out/'final_report.json',report);print(json.dumps({k:v for k,v in report.items() if k!='stages'}),flush=True)
 except Exception as exc:
  write_json(out/'failure.json',dict(status='FAILED_NO_AUTOMATIC_REFINEMENT',identity=identity,type=type(exc).__name__,message=str(exc),stages_completed=list(stages),resource_delta=ledger.totals,resource_cumulative=totals(),seconds=time.perf_counter()-start,RSS_peak_bytes=int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)));raise
if __name__=='__main__':run()
