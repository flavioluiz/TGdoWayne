"""Complete only the original C_full diagnostic grid; preserve FAILED candidate."""
import os
os.environ['VECLIB_MAXIMUM_THREADS']='1'
from pathlib import Path
import sys,json,hashlib,time,resource
import numpy as np
from scipy.stats import multivariate_normal
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2];OLD=ROOT/'tmp/c08_beta_table';PRIOR=ROOT/'tmp/c08_full_table_execution';sys.path.insert(0,str(OLD));sys.path.insert(0,str(PRIOR));sys.path.insert(0,str(OLD/'executed_sources/src'))
from beta_builder import sha_file,canonical,digest,write_json,write_npz,Ledger
from gate_kernel import compressed_moments,compressed_logpdf
from independent_moments import moments
from inference.model import experiment

def run():
 a=json.loads((HERE/'authorization.json').read_text());identity=hashlib.sha256(canonical(a).encode()).hexdigest();out=HERE/'results';out.mkdir(exist_ok=False);start=time.perf_counter()
 def verify():
  for p,h in a['input_source_sha256'].items():
   if sha_file(ROOT/p)!=h:raise RuntimeError('Frozen source/input changed '+p)
 verify();write_json(out/'request.json',a);ledger=Ledger(out/'resource_delta_ledger.jsonl',dict(real=0,angular=0,logL=1400000-724992),identity)
 def rss():
  v=int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
  if v>1610612736:raise MemoryError('RSS ceiling exceeded')
  return v
 try:
  e=experiment(json.loads((OLD/'inputs/experiment.json').read_text()))
  with np.load(PRIOR/'results/nuisances.npz',allow_pickle=False) as z:eta=z['eta'].copy()
  with np.load(PRIOR/'results/validation_matrices.npz',allow_pickle=False) as z:u=z['u'].copy();values={k:z[k].copy() for k in ['coarse','fine','oracle']}
  with np.load(OLD/'inputs/pilot_data.npz',allow_pickle=False) as z:x=np.concatenate([z['x_physical'],z['x_gaussian']],axis=0)
  observed=np.einsum('rkd,k->rd',x,e['weights']);rows=json.loads((PRIOR/'results/likelihood_failed.json').read_text())['rows'];assert len(rows)==118
  for j in range(118,215):
   logs={}
   for label,v in values.items():
    ledger.charge('logL',2048,dict(stage='remaining_original',index=j,label=label));mu,cov=compressed_moments(eta,v[j],e);log=compressed_logpdf(mu,cov,observed)
    if not np.isfinite(log).all():raise RuntimeError('Nonfinite likelihood')
    logs[label]=log
   row=dict(index=j,u=float(u[j]),coarse_fine=float(np.max(abs(logs['coarse']-logs['fine']))),fine_oracle=float(np.max(abs(logs['fine']-logs['oracle']))));rows.append(row)
   write_npz(out/'likelihood_cache'/f'node_{j:04d}.npz',u=np.array(u[j]),**{'logL_'+k:v for k,v in logs.items()},nuisances_sha256=np.array(digest(eta)),observations_sha256=np.array(digest(observed)),identity=np.array(identity));rss()
  references=[]
  for uu in [0.,.5,1.]:
   j=int(np.where(u==uu)[0][0]);path=(PRIOR/'results' if j<118 else out)/'likelihood_cache'/f'node_{j:04d}.npz'
   with np.load(path,allow_pickle=False) as z:
    if float(z['u'])!=uu or str(z['nuisances_sha256'])!=digest(eta) or str(z['observations_sha256'])!=digest(observed):raise RuntimeError('Reference cache identity mismatch')
    cached={label:z['logL_'+label].copy() for label in values}
   for label,v in values.items():
    mu,cov=compressed_moments(eta[:6],v[j],e)
    for ii in range(6):
     mr,cr=moments(eta[ii],v[j],e);em=float(np.max(abs(mr-mu[ii]))/max(1.,np.max(abs(mr))));ec=float(np.max(abs(cr-cov[ii]))/max(1.,np.max(abs(cr))));ledger.charge('logL',32,dict(stage='independent_SciPy',label=label,u=uu,nuisance_index=ii));ref=multivariate_normal.logpdf(observed,mean=mr,cov=cr,allow_singular=False);el=float(np.max(abs(ref-cached[label][ii])))
     if not np.isfinite([em,ec,el]).all():raise RuntimeError('Nonfinite independent reference')
     references.append(dict(u=uu,label=label,nuisance_index=ii,mean_error=em,covariance_error=ec,SciPy_logpdf_error=el,condition_number=float(np.linalg.cond(cr)),passed=(max(em,ec)<=1e-10 and el<=1e-8)));rss()
  if ledger.totals!={'real':0,'angular':0,'logL':597696}:raise RuntimeError('Work differs from prospectively fixed continuation')
  verify();report=dict(status='ORIGINAL_C_FULL_DIAGNOSTICS_COMPLETE_CANDIDATE_REMAINS_FAILED',identity=identity,original_failure_sha256=sha_file(PRIOR/'results/failure_gates.json'),original_control_count=215,original_plus_continued_rows=rows,maximum_coarse_fine=max(r['coarse_fine'] for r in rows),maximum_fine_oracle=max(r['fine_oracle'] for r in rows),coarse_fine_failed_controls=sum(r['coarse_fine']>.001 for r in rows),fine_oracle_failed_controls=sum(r['fine_oracle']>.001 for r in rows),independent_reference_cases=references,independent_reference_failed_cases=sum(not r['passed'] for r in references),resource_delta=ledger.totals,resource_cumulative=dict(real=0,angular=0,logL=1322688),seconds=time.perf_counter()-start,RSS_peak_bytes=rss(),no_refinement=True,no_export=True,no_posterior=True,no_new_quadrature=True);write_json(out/'report.json',report);print(json.dumps({k:v for k,v in report.items() if k not in ['original_plus_continued_rows','independent_reference_cases']}),flush=True)
 except Exception as exc:
  write_json(out/'failure.json',dict(status='DIAGNOSTIC_CONTINUATION_INTERRUPTED',identity=identity,type=type(exc).__name__,message=str(exc),resource_delta=ledger.totals,RSS_peak_bytes=int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss),seconds=time.perf_counter()-start));raise
if __name__=='__main__':run()
