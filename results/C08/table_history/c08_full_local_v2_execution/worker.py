"""Own C_full v2 stages; each runs in a fresh single-BLAS process."""
import os
os.environ['VECLIB_MAXIMUM_THREADS']='1'
from pathlib import Path
import sys,json,hashlib,time,resource,gc
import numpy as np
from scipy.stats import multivariate_normal
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];OLD=ROOT/'tmp/c08_beta_table';HIST=ROOT/'tmp/c08_full_table_execution';CONT=ROOT/'tmp/c08_full_original_diagnostics/execution/results'
sys.path.insert(0,str(OLD));sys.path.insert(0,str(ROOT/'tmp/c08_beta_table_v2'));sys.path.insert(0,str(HIST));sys.path.insert(0,str(OLD/'executed_sources/src'))
from beta_builder import sha_file,canonical,digest,write_json,write_npz,Ledger,matrices,beta_from_u,u_from_beta
from inference.model import experiment,YEAR
from inference.orf_blas import RealHarmonicBasis,TableBudget,estimate
from pta.orf import raw_direct_orf
from curve_algebra_v2 import evaluate,bernstein_eigenvalues
from patch_curve import stitch
from gate_kernel import compressed_moments,compressed_logpdf
from independent_moments import moments

def curve(path):
 with np.load(path,allow_pickle=False) as z:return z['nodes'].copy(),z['matrices'].copy(),z['coeff'].copy()

def run(stage):
 if stage not in ['local','oracle_coarse','oracle_fine','gates','export']:raise ValueError('Invalid fixed stage')
 a=json.loads((HERE/'authorization.json').read_text());p=json.loads((ROOT/'tmp/c08_full_local_v2_design/preflight.json').read_text());identity=hashlib.sha256(canonical(a).encode()).hexdigest();out=HERE/'results';out.mkdir(exist_ok=True);start=time.perf_counter();marker=out/(stage+'_report.json')
 if marker.exists():raise FileExistsError('No overwrite or retry')
 def verify():
  for name,h in a['input_source_sha256'].items():
   if sha_file(ROOT/name)!=h:raise RuntimeError('Frozen source/input changed '+name)
 verify();ledger=Ledger(out/'resource_delta_ledger.jsonl',dict(real=20000000000,angular=2000000,logL=600000),identity)
 def rss(label):
  value=int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
  if value>a['maximum_RSS_bytes']:raise MemoryError('RSS ceiling exceeded '+label)
  return value
 def save_report(payload):
  verify();report=dict(identity=identity,stage=stage,seconds=time.perf_counter()-start,RSS_peak_bytes=rss('finished'),resource_delta=ledger.totals,**payload);write_json(marker,report);print(json.dumps(report),flush=True)
 try:
  cfg=json.loads((OLD/'inputs/experiment.json').read_text());e=experiment(cfg);phase=2*np.pi*e['f'][0]*e['distance_ly']*YEAR
  def harmonic(nodes,orders,label):
   l,nm=orders;est=estimate(l,nm,12,8)
   if est['estimated_memory_bytes']+64*1024**2>a['maximum_numeric_bytes']:raise MemoryError('Numeric basis budget exceeded')
   basis=RealHarmonicBasis(e['points'],lmax=l,nmu=nm,budget=TableBudget(a['maximum_numeric_bytes']-64*1024**2,20000000000,8),planned_batch=8);rss('basis');bb=beta_from_u(nodes);g=np.empty((len(nodes),12,12),complex)
   for begin in range(0,len(nodes),8):
    end=min(begin+8,len(nodes));ledger.charge('real',2*(end-begin)*12*nm*(l-1),dict(stage=stage,resolution=label,first=begin,last=end));g[begin:end]=basis.evaluate(bb[begin:end],phase);rss('harmonic')
   matrices(g,len(g),12);del basis;gc.collect();return g
  if stage=='local':
   n,g,c=curve(OLD/'first_curve_root.npz');bound=float(u_from_beta(np.array([1/64]))[0]);patch=np.union1d(n[n>=bound],u_from_beta(np.linspace(0,1/64,257)))
   if len(patch)!=353:raise RuntimeError('Local prospective count changed')
   co=harmonic(patch,p['local_harmonic']['coarse_orders'],'coarse');fi=harmonic(patch,p['local_harmonic']['fine_orders'],'fine');old_ix=np.where(n>=bound)[0];ix=np.searchsorted(patch,n[old_ix]);ec=float(np.max(abs(co-fi)));eo=float(np.max(abs(fi[ix]-g[old_ix,0])))
   if max(ec,eo)>1e-8:raise RuntimeError('Local harmonic gate failed')
   write_npz(out/'local_quadrature.npz',u=patch,Gamma_coarse=co,Gamma_fine=fi);fi[ix]=g[old_ix,0];nn,gg,cc,checks=stitch(n,g,c,patch,fi[:,None]);checks.update(bernstein_eigenvalues(cc))
   if len(nn)!=8448:raise RuntimeError('Fine count changed')
   write_npz(out/'fine_first_curve.npz',nodes=nn,matrices=gg,coeff=cc,coordinate=np.array('minus_beta'));save_report(dict(status='LOCAL_CURVE_PASS',coarse_fine_error=ec,old_node_reproduction_error=eo,checks=checks,curve_sha256=sha_file(out/'fine_first_curve.npz')));return
  if stage.startswith('oracle_'):
   label=stage.split('_')[1];nodes=np.array(p['new_oracles']['u']);g=harmonic(nodes,p['new_oracles'][label+'_orders'],label);write_npz(out/(stage+'.npz'),u=nodes,Gamma=g,identity=np.array(identity));save_report(dict(status='ORACLE_RESOLUTION_COMPLETE',file_sha256=sha_file(out/(stage+'.npz'))));return
  if stage=='gates':
   for name in ['local','oracle_coarse','oracle_fine']:
    r=json.loads((out/(name+'_report.json')).read_text())
    if r['identity']!=identity:raise RuntimeError('Stage identity mismatch')
    file=out/('fine_first_curve.npz' if name=='local' else name+'.npz');expected=r['curve_sha256'] if name=='local' else r['file_sha256']
    if sha_file(file)!=expected:raise RuntimeError('Stage artifact changed')
   newu=np.array(p['new_oracles']['u']);gg=[]
   for name in ['oracle_coarse','oracle_fine']:
    with np.load(out/(name+'.npz'),allow_pickle=False) as z:
     if str(z['identity'])!=identity or not np.array_equal(z['u'],newu):raise RuntimeError('Oracle cache changed')
     gg.append(z['Gamma'].copy())
   err=float(np.max(abs(gg[0]-gg[1])))
   if err>1e-8:raise RuntimeError('Full oracle convergence failed')
   neworacle=np.repeat(gg[1][:,None],4,axis=1)
   with np.load(HIST/'results/validation_matrices.npz',allow_pickle=False) as z:hu=z['u'].copy();hc=z['fine'].copy();ho=z['oracle'].copy()
   with np.load(HIST/'results/nuisances.npz',allow_pickle=False) as z:oldeta=z['eta'].copy()
   n,g,c=curve(out/'fine_first_curve.npz');hf=np.repeat(evaluate(n,c,hu),4,axis=1);nf=np.repeat(evaluate(n,c,newu),4,axis=1);del n,g,c;gc.collect()
   n,g,c=curve(OLD/'first_curve_root.npz');nc=np.repeat(evaluate(n,c,newu),4,axis=1);del n,g,c;gc.collect();bound=float(u_from_beta(np.array([1/64]))[0]);outside=hu<bound
   if not np.array_equal(hf[outside],hc[outside]):raise RuntimeError('Outside Gamma not bit exact; no cache reuse')
   cos=np.clip(e['points']@e['points'].T,-1,1);direct=[]
   for check in p['direct_checks']:
    uu=float(u_from_beta(np.array([check['beta']]))[0]);j=np.where(hu==uu)[0]
    if len(j)!=1:raise RuntimeError('Historical harmonic anchor missing')
    beta=float(beta_from_u(np.array([uu]))[0])
    for ia,ib in check['pairs']:
     vals=[]
     for label in ['coarse','fine']:
      nm,nphi=check[label+'_nmu_nphi'];ledger.charge('angular',nm*nphi,dict(beta=beta,pair=[ia,ib],resolution=label));vals.append(raw_direct_orf(beta,float(cos[ia,ib]),float(phase[ia]),float(phase[ib]),nmu=nm,nphi=nphi))
     dc=float(abs(vals[0]-vals[1]));dh=float(abs(vals[1]-ho[j[0],0,ia,ib]));direct.append(dict(beta=beta,pair=[ia,ib],coarse_fine=dc,direct_harmonic=dh))
     if max(dc,dh)>1e-7:raise RuntimeError('Direct gate failed')
   write_json(out/'direct_checks.json',direct);write_npz(out/'validation_matrices.npz',historical_u=hu,historical_coarse=hc,historical_fine=hf,historical_oracle=ho,new_u=newu,new_coarse=nc,new_fine=nf,new_oracle=neworacle)
   bounds=np.array(cfg['prior']['bounds'])[1:];neweta=bounds[:,0]+np.random.default_rng(808150201).uniform(size=(64,4))*np.diff(bounds)[:,0]
   with np.load(OLD/'inputs/pilot_data.npz',allow_pickle=False) as z:x=np.concatenate([z['x_physical'],z['x_gaussian']],axis=0)
   obs=np.einsum('rkd,k->rd',x,e['weights']);rows=[]
   def ll(eta,g,kind,j,label):
    ledger.charge('logL',2048,dict(kind=kind,index=j,label=label));mu,cov=compressed_moments(eta,g,e);v=compressed_logpdf(mu,cov,obs)
    if not np.isfinite(v).all():raise RuntimeError('Nonfinite logL')
    return v
   def compare(kind,j,u,eta,logs):
    row=dict(kind=kind,index=j,u=float(u),coarse_fine=float(np.max(abs(logs['coarse']-logs['fine']))),fine_oracle=float(np.max(abs(logs['fine']-logs['oracle']))));rows.append(row);write_npz(out/'likelihood_cache'/f'{kind}_{j:04d}.npz',u=np.array(u),**{'logL_'+k:v for k,v in logs.items()},nuisances_sha256=np.array(digest(eta)),observations_sha256=np.array(digest(obs)),identity=np.array(identity))
    if max(row['coarse_fine'],row['fine_oracle'])>.001:
     write_json(out/'likelihood_failed.json',dict(rows=rows,failed=row));raise RuntimeError('C_full v2 interpolation logL gate failed')
   for j,uu in enumerate(hu):
    path=(HIST/'results' if j<118 else CONT)/'likelihood_cache'/f'node_{j:04d}.npz'
    with np.load(path,allow_pickle=False) as z:
     if float(z['u'])!=uu or str(z['nuisances_sha256'])!=digest(oldeta) or str(z['observations_sha256'])!=digest(obs) or str(z['identity'])!=a['historical_cache_identities'][0 if j<118 else 1]:raise RuntimeError('Historical LL cache identity mismatch')
     vc=z['logL_fine'].copy();vo=z['logL_oracle'].copy()
    vf=vc.copy() if outside[j] else ll(oldeta,hf[j],'historical',j,'fine');compare('historical',j,uu,oldeta,dict(coarse=vc,fine=vf,oracle=vo))
   for j,uu in enumerate(newu):compare('new',j,uu,neweta,{label:ll(neweta,g[j],'new',j,label) for label,g in [('coarse',nc),('fine',nf),('oracle',neworacle)]})
   references=[]
   for uu in p['likelihood']['independent_reference_u']:
    if uu in hu:kind='historical';j=int(np.where(hu==uu)[0][0]);eta=oldeta;gammas=dict(coarse=hc[j],fine=hf[j],oracle=ho[j])
    else:kind='new';j=int(np.where(newu==uu)[0][0]);eta=neweta;gammas=dict(coarse=nc[j],fine=nf[j],oracle=neworacle[j])
    with np.load(out/'likelihood_cache'/f'{kind}_{j:04d}.npz',allow_pickle=False) as z:cached={label:z['logL_'+label].copy() for label in gammas}
    for label,gamma in gammas.items():
     mu,cov=compressed_moments(eta[:6],gamma,e)
     for ii in range(6):
      mr,cr=moments(eta[ii],gamma,e);em=float(np.max(abs(mu[ii]-mr))/max(1.,np.max(abs(mr))));ec=float(np.max(abs(cov[ii]-cr))/max(1.,np.max(abs(cr))));ledger.charge('logL',32,dict(stage='SciPy_reference',kind=kind,index=j,label=label,nuisance=ii));v=multivariate_normal.logpdf(obs,mean=mr,cov=cr,allow_singular=False);el=float(np.max(abs(v-cached[label][ii])));references.append(dict(kind=kind,u=uu,label=label,nuisance=ii,mean_error=em,covariance_error=ec,SciPy_logpdf_error=el,condition_number=float(np.linalg.cond(cr))))
      if max(em,ec)>1e-10 or el>1e-8:
       write_json(out/'reference_failed.json',dict(rows=references,failed=references[-1]));raise RuntimeError('Independent reference gate failed; inspect roundoff without changing thresholds')
   write_json(out/'likelihood_checks.json',dict(rows=rows,maximum_coarse_fine=max(r['coarse_fine'] for r in rows),maximum_fine_oracle=max(r['fine_oracle'] for r in rows)));write_json(out/'independent_references.json',references);write_npz(out/'nuisances.npz',historical=oldeta,new=neweta)
   expected=dict(real=p['budget']['planned_new_real_products'],angular=p['budget']['planned_new_angular_work'],logL=p['budget']['planned_new_logL'])
   if ledger.totals!=expected:raise RuntimeError('Exact work plan changed')
   save_report(dict(status='C_FULL_V2_GATES_PASS_PENDING_EXPORT',harmonic_coarse_fine=err,direct_maximum=max(max(q['coarse_fine'],q['direct_harmonic']) for q in direct),maximum_logL_coarse_fine=max(r['coarse_fine'] for r in rows),maximum_logL_fine_oracle=max(r['fine_oracle'] for r in rows),maximum_SciPy_logpdf_error=max(r['SciPy_logpdf_error'] for r in references),maximum_mean_error=max(r['mean_error'] for r in references),maximum_covariance_error=max(r['covariance_error'] for r in references),historical_controls=215,new_controls=72,historical_outside_Gamma_bitexact=True));return
  gate=json.loads((out/'gates_report.json').read_text());local=json.loads((out/'local_report.json').read_text())
  if gate['status']!='C_FULL_V2_GATES_PASS_PENDING_EXPORT' or gate['identity']!=identity or sha_file(out/'fine_first_curve.npz')!=local['curve_sha256']:raise RuntimeError('Own C_full gates required')
  n,g,c=curve(out/'fine_first_curve.npz');estimated=n.nbytes+5*(g.nbytes+c.nbytes)+64*1024**2
  if estimated>a['maximum_numeric_bytes']:raise MemoryError('Export numeric budget exceeded')
  gg=np.repeat(g,4,axis=1);cc=np.repeat(c,4,axis=2)
  if not all(np.array_equal(gg[:,k:k+1],g) and np.array_equal(cc[:,:,k:k+1],c) for k in range(4)):raise RuntimeError('Expansion changed coefficients')
  checks=bernstein_eigenvalues(cc);j1=np.where(n==1)[0][0];rank=int(np.sum(np.linalg.eigvalsh(g[j1,0])>1e-10))
  if rank>5:raise RuntimeError('Threshold rank exceeded')
  with np.load(ROOT/'results/C07/orf_interpolation/orf_table_pilot12x4.npz',allow_pickle=False) as z:physical0=z['matrices'][0].copy()
  diff=np.max(abs(gg[0]-physical0),axis=(1,2))
  if diff[0]>1e-11:raise RuntimeError('First physical massless channel changed')
  write_npz(out/'C_full_table.npz',nodes=n,matrices=gg,coeff=cc,coordinate=np.array('minus_beta'),response=np.array('C_full: own refined first-frequency physical ORF repeated; spectra/noise unchanged'),construction_identity=np.array(identity));save_report(dict(status='C_FULL_V2_PASS_STATED_FINITE_TABLE_GATES_ONLY',table_sha256=sha_file(out/'C_full_table.npz'),gate_report_sha256=sha_file(out/'gates_report.json'),nodes=len(n),channels=4,expanded_channels_bitexact=True,checks=checks,u1_rank=rank,u0_C_full_minus_B_matrix_max_by_channel=diff.tolist(),resource_cumulative=dict(real=ledger.totals['real'],angular=ledger.totals['angular'],logL=1322688+ledger.totals['logL']),no_C07_or_C_beta_modifications=True,no_posterior_or_native_bank=True,finite_checks_not_uniform_proof=True))
 except Exception as exc:
  write_json(out/('failure_'+stage+'.json'),dict(status='FAILED_NO_AUTOMATIC_RETRY',identity=identity,stage=stage,type=type(exc).__name__,message=str(exc),resource_delta=ledger.totals,RSS_peak_bytes=int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss),seconds=time.perf_counter()-start));raise
if __name__=='__main__':run(sys.argv[1])
