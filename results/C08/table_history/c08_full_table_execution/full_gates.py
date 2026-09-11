"""C_full own moment/density gates. No harmonic/angular integrator or native bank."""
import os
os.environ['VECLIB_MAXIMUM_THREADS']='1'
from pathlib import Path
import sys,json,hashlib,time,resource,gc
import numpy as np
from scipy.interpolate import CubicSpline
from scipy.stats import multivariate_normal
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];OLD=ROOT/'tmp/c08_beta_table';sys.path.insert(0,str(OLD));sys.path.insert(0,str(OLD/'executed_sources/src'))
from beta_builder import sha_file,canonical,digest,write_json,write_npz,Ledger,matrices
from curve_algebra_v2 import evaluate,bernstein_eigenvalues
from gate_kernel import compressed_moments,compressed_logpdf
from inference.model import experiment
from independent_moments import moments

def run():
 a=json.loads((HERE/'execution_authorized.json').read_text());p=json.loads((ROOT/'tmp/c08_full_table_design/preflight.json').read_text());identity=hashlib.sha256(canonical(a).encode()).hexdigest();out=HERE/'results';out.mkdir(exist_ok=True)
 if (out/'gate_request.json').exists():raise FileExistsError('No overwrite/resume')
 def verify():
  for name,h in a['input_source_sha256'].items():
   if sha_file(ROOT/name)!=h:raise RuntimeError('Frozen source/input changed '+name)
 verify();write_json(out/'gate_request.json',dict(identity=identity,authorization_sha256=sha_file(HERE/'execution_authorized.json'),authorization=a));ledger=Ledger(out/'resource_ledger.jsonl',dict(real=0,angular=0,logL=1400000),identity);start=time.perf_counter();stages={}
 def rss(label):
  value=int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
  if value>a['maximum_RSS_bytes']:raise MemoryError('RSS ceiling exceeded '+label)
  return value
 try:
  cfg=json.loads((OLD/'inputs/experiment.json').read_text());e=experiment(cfg);old_u=np.array(p['controls']['historical_u']);new_u=np.array(p['controls']['new_u']);u=np.r_[old_u,new_u];values={};curve_reports=[]
  with np.load(ROOT/p['curves']['coarse']['source'],allow_pickle=False) as z:n=z['nodes'].copy();g=z['matrices'][:,0:1].copy()
  x=-np.sqrt((1-n)*(1+n));width=np.diff(x)[:,None,None,None];spline=CubicSpline(x,g,bc_type=('not-a-knot',(1,np.zeros(g.shape[1:]))));c=np.stack([spline.c[3-j]*width**j for j in range(4)],axis=1);checks=bernstein_eigenvalues(c);derivative=(c[-1,1]+2*c[-1,2]+3*c[-1,3])/(x[-1]-x[-2])
  if np.max(abs(derivative))>1e-7:raise RuntimeError('Coarse parity failed')
  values['coarse']=np.repeat(evaluate(n,c,u),4,axis=1);write_npz(out/'coarse_first_curve.npz',nodes=n,matrices=g,coeff=c,coordinate=np.array('minus_beta'));curve_reports.append(dict(representation='coarse',nodes=len(n),**checks));del n,g,c,spline;gc.collect();rss('coarse')
  with np.load(ROOT/p['curves']['fine']['source'],allow_pickle=False) as z:n=z['nodes'].copy();g=z['matrices'].copy();c=z['coeff'].copy()
  values['fine']=np.repeat(evaluate(n,c,u),4,axis=1);curve_reports.append(dict(representation='fine',nodes=len(n),**bernstein_eigenvalues(c)));del n,g,c;gc.collect();rss('fine')
  with np.load(ROOT/p['oracle']['historical_143_source'],allow_pickle=False) as z:
   if not np.array_equal(z['u'],old_u):raise RuntimeError('Historical oracle u mismatch')
   oracle=z['oracle'][:,0:1].copy()
  with np.load(ROOT/p['oracle']['new_72_source'],allow_pickle=False) as z:
   if not np.array_equal(z['u'],new_u):raise RuntimeError('New oracle u mismatch')
   oracle=np.concatenate([oracle,z['Gamma_fine'][:,None]])
  values['oracle']=np.repeat(oracle,4,axis=1)
  for label,v in values.items():
   for k in range(4):matrices(v[:,k],len(u),12)
   if not all(np.array_equal(v[:,k],v[:,0]) for k in range(4)):raise RuntimeError('C_full channel expansion differs')
  stages['curves']=curve_reports;write_json(out/'curve_checks.json',curve_reports);write_npz(out/'validation_matrices.npz',u=u,**values)
  with np.load(OLD/'inputs/pilot_data.npz',allow_pickle=False) as z:x=np.concatenate([z['x_physical'],z['x_gaussian']],axis=0)
  observed=np.einsum('rkd,k->rd',x,e['weights']);del x
  bounds=np.array(cfg['prior']['bounds'])[1:];eta=bounds[:,0]+np.random.default_rng(808140201).uniform(size=(64,4))*np.diff(bounds)[:,0];write_npz(out/'nuisances.npz',eta=eta);rows=[]
  for j,uu in enumerate(u):
   logs={}
   for label,v in values.items():
    ledger.charge('logL',2048,dict(stage='representation_gate',label=label,u=float(uu)));mu,cov=compressed_moments(eta,v[j],e);log=compressed_logpdf(mu,cov,observed)
    if not np.isfinite(log).all():raise RuntimeError('Nonfinite density')
    logs[label]=log
   cf=float(np.max(abs(logs['coarse']-logs['fine'])));fo=float(np.max(abs(logs['fine']-logs['oracle'])));row=dict(index=j,u=float(uu),coarse_fine=cf,fine_oracle=fo);rows.append(row)
   write_npz(out/'likelihood_cache'/f'node_{j:04d}.npz',u=np.array(uu),**{'logL_'+k:v for k,v in logs.items()},nuisances_sha256=np.array(digest(eta)),observations_sha256=np.array(digest(observed)),identity=np.array(identity))
   if max(cf,fo)>.001:
    write_json(out/'likelihood_failed.json',dict(rows=rows,failed=row));raise RuntimeError('C_full interpolation logL gate failed')
  stages['likelihood']=dict(rows=rows,maximum_coarse_fine=max(r['coarse_fine'] for r in rows),maximum_fine_oracle=max(r['fine_oracle'] for r in rows));write_json(out/'likelihood_checks.json',stages['likelihood'])
  references=[]
  for uu in [0.,.5,1.]:
   j=int(np.where(u==uu)[0][0])
   with np.load(out/'likelihood_cache'/f'node_{j:04d}.npz',allow_pickle=False) as z:cached={label:z['logL_'+label].copy() for label in values}
   for label,v in values.items():
    mu,cov=compressed_moments(eta[:6],v[j],e)
    for ii in range(6):
     mr,cr=moments(eta[ii],v[j],e);em=float(np.max(abs(mr-mu[ii]))/max(1.,np.max(abs(mr))));ec=float(np.max(abs(cr-cov[ii]))/max(1.,np.max(abs(cr))));ledger.charge('logL',32,dict(stage='independent_SciPy',label=label,u=uu,nuisance_index=ii));ref=multivariate_normal.logpdf(observed,mean=mr,cov=cr,allow_singular=False);el=float(np.max(abs(ref-cached[label][ii])));references.append(dict(u=uu,label=label,nuisance_index=ii,mean_error=em,covariance_error=ec,SciPy_logpdf_error=el,condition_number=float(np.linalg.cond(cr))))
     if max(em,ec)>1e-10 or el>1e-8:
      write_json(out/'independent_reference_failed.json',dict(rows=references,failed=references[-1],interpretation='Numerical reference discrepancy; inspect conditioning/roundoff before attributing physical-model error. No tolerance changed.'));raise RuntimeError('Independent moments/SciPy gate failed')
  stages['independent_moments_SciPy']=references;write_json(out/'independent_moments_SciPy.json',references)
  j0=int(np.where(u==0)[0][0]);j1=int(np.where(u==1)[0][0]);gfull=values['fine'][j0]
  with np.load(ROOT/'results/C07/orf_interpolation/orf_table_pilot12x4.npz',allow_pickle=False) as z:physical0=z['matrices'][0].copy()
  matrixdiff=np.max(abs(gfull-physical0),axis=(1,2));mu_full,cov_full=compressed_moments(eta[:6],gfull,e);mu_B,cov_B=compressed_moments(eta[:6],physical0,e)
  anchor=dict(u0_matrix_differences_by_channel=matrixdiff.tolist(),u0_compressed_mean_absolute_difference=float(np.max(abs(mu_full-mu_B))),u0_compressed_covariance_absolute_difference=float(np.max(abs(cov_full-cov_B))),u1_rank_by_channel=[int(np.sum(np.linalg.eigvalsh(g)>1e-10)) for g in values['fine'][j1]],C_full_is_not_assumed_equal_to_B_at_zero_mass=True,unchanged_spectrum_noise_and_observations=True)
  if matrixdiff[0]>1e-11 or max(anchor['u1_rank_by_channel'])>5:raise RuntimeError('First channel or threshold rank anchor failed')
  for uu in [0.,.2,.5,.8,1.]:
   j=int(np.where(u==uu)[0][0]);assert all(np.array_equal(values['fine'][j,k],values['fine'][j,0]) for k in range(4))
  stages['anchors']=anchor;write_json(out/'anchor_checks.json',anchor)
  if ledger.totals!={'real':0,'angular':0,'logL':1322688}:raise RuntimeError('Exact prospective work changed')
  verify();report=dict(status='C_FULL_GATES_PASS_PENDING_EXPORT',identity=identity,scientific_variant='C_full',stages=stages,resource_totals=ledger.totals,RSS_peak_bytes=rss('finished'),seconds=time.perf_counter()-start,authorization_sha256=sha_file(HERE/'execution_authorized.json'),no_truth_deserialized=True,no_new_quadratures=True,no_posterior_or_native_bank=True,finite_validation_only=True);write_json(out/'gate_report.json',report);print(json.dumps({k:v for k,v in report.items() if k!='stages'}),flush=True)
 except Exception as exc:
  write_json(out/'failure_gates.json',dict(status='FAILED_NO_AUTOMATIC_REFINEMENT',identity=identity,type=type(exc).__name__,message=str(exc),stages_completed=list(stages),resource_totals=ledger.totals,RSS_peak_bytes=int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss),seconds=time.perf_counter()-start));raise
if __name__=='__main__':run()
