"""Independent table gates. Run only after harmonic construction has completed."""
import os
os.environ['VECLIB_MAXIMUM_THREADS']='1'
import gc,json,resource,time
from pathlib import Path
import numpy as np
from beta_builder import HERE,ROOT,Ledger,sha_file,canonical,digest,write_json,write_npz,matrices,beta_from_u,u_from_beta,planned_nodes
from inference.model import experiment,YEAR
from inference.orf_interpolation import EvenThresholdCubicORF
from pta.orf import raw_direct_orf,threshold_full
from curve_algebra_v2 import evaluate,subdivide,bernstein_eigenvalues
from gate_kernel import compressed_moments,compressed_logpdf


def run():
 cfg=json.loads((HERE/'execution_authorized.json').read_text());gcfg=json.loads((HERE/'gates_frozen.json').read_text());pre=json.loads((HERE/'preflight_v2.json').read_text());out=HERE/'results';manifest=json.loads((out/'matrix_manifest.json').read_text())
 if manifest['status']!='HARMONIC_MATRICES_COMPLETE_PENDING_INDEPENDENT_GATES':raise ValueError('Construction must finish before gates')
 if manifest['execution_config_sha256']!=sha_file(HERE/'execution_authorized.json'):raise ValueError('Wrong construction identity')
 if gcfg['construction_configuration_sha256']!=sha_file(HERE/'execution_authorized.json'):raise ValueError('Gate configuration identity changed')
 allhash=cfg['source_sha256']|gcfg['source_sha256']
 for path,h in allhash.items():
  if sha_file(ROOT/path)!=h:raise ValueError('Frozen source/input changed: '+path)
 dest=out/'gates';dest.mkdir(exist_ok=False);write_json(dest/'gate_request.json',gcfg)
 ledger=Ledger(out/'resource_ledger.jsonl',dict(real=cfg['maximum_real_multiplications'],angular=cfg['maximum_direct_angular_work'],logL=cfg['maximum_logL_values']),manifest['identity'])
 def rss(label):
  peak=int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
  if peak>cfg['maximum_RSS_bytes']:raise MemoryError('Darwin observed peak RSS exceeded authorized ceiling')
  return peak
 start=time.perf_counter();stages={};ecfg=json.loads((HERE/'inputs/experiment.json').read_text());e=experiment(ecfg);P=len(e['points']);phase=2*np.pi*e['f'][:,None]*e['distance_ly'][None]*YEAR;cos=np.clip(e['points']@e['points'].T,-1,1);u=np.array(pre['validation_nodes_u']);oracle=np.empty((len(u),4,P,P),complex);fine_values=np.empty_like(oracle);coarse_values=np.empty_like(oracle)
 def channel(k):
  row=manifest['rows'][k-1];path=ROOT/row['file']
  if sha_file(path)!=row['sha256']:raise ValueError('Completed channel file altered')
  with np.load(path,allow_pickle=False) as z:a={key:z[key].copy() for key in z.files}
  r=json.loads(str(a['record']))
  if r['identity']!=manifest['identity'] or r['channel']!=k:raise ValueError('Channel signature mismatch')
  request,fine,coarse=planned_nodes(k,u)
  for key,want in [('u',request),('beta',beta_from_u(request)),('fine_grid_u',fine),('coarse_grid_u',coarse)]:
   if not np.array_equal(a[key],want):raise ValueError('Channel coordinate/grid changed')
  for key in ['u','beta','Gamma_coarse','Gamma_fine','errors']:
   if digest(a[key])!=r[key+'_sha256']:raise ValueError('Channel array hash altered: '+key)
  matrices(a['Gamma_coarse'],len(request),P);matrices(a['Gamma_fine'],len(request),P)
  err=np.max(abs(a['Gamma_fine']-a['Gamma_coarse']),axis=(1,2))
  if not np.array_equal(err,a['errors']) or not np.isfinite(err).all() or err.max()>1e-8:raise ValueError('Harmonic gate not reproduced')
  return a
 try:
  # Read the ROOT first curve only. The other three columns are massless anchors.
  with np.load(ROOT/cfg['inherited_first_curve']['root_source'],allow_pickle=False) as root:
   root_massless=root['matrices'][0].copy()
  with np.load(HERE/'first_curve_root.npz',allow_pickle=False) as z:
   first_nodes=z['nodes'].copy();first_coeff=z['coeff'].copy();first_matrices=z['matrices'].copy()
  fine_values[:,0:1]=evaluate(first_nodes,first_coeff,u);coarse_values[:,0:1]=fine_values[:,0:1]
  write_npz(dest/'curve_channel01.npz',nodes=first_nodes,matrices=first_matrices,coeff=first_coeff,coordinate=np.array('minus_beta'))
  curves=[dict(channel=1,node_count=len(first_nodes),inherited_ROOT_first_curve=True,coarse_policy='same inherited curve; separate harmonic oracle validation',**bernstein_eigenvalues(first_coeff))];union=first_nodes.copy();del first_coeff,first_matrices
  anchors=[]
  for k in range(1,5):
   a=channel(k);ix=np.searchsorted(a['u'],u)
   if not np.array_equal(a['u'][ix],u):raise ValueError('Oracle coordinates absent')
   oracle[:,k-1]=a['Gamma_fine'][ix]
   g0=a['Gamma_fine'][np.searchsorted(a['u'],1.)];g1=a['Gamma_fine'][np.searchsorted(a['u'],0.)]
   exact=np.array([[threshold_full(float(cos[i,j]),float(phase[k-1,i]),float(phase[k-1,j])) for j in range(P)] for i in range(P)])
   threshold_error=float(np.max(abs(g0-exact)));massless_error=float(np.max(abs(g1-root_massless[k-1])))
   if threshold_error>1e-8 or massless_error>1e-8:raise ValueError('Analytic threshold or ROOT massless anchor failed')
   anchors.append(dict(channel=k,threshold_matrix_error=threshold_error,massless_ROOT_matrix_error=massless_error,threshold_rank_numerical=int(np.sum(np.linalg.eigvalsh(g0)>1e-10))))
   if anchors[-1]['threshold_rank_numerical']>5:raise ValueError('Threshold tensor rank exceeded five')
   if k>1:
    for label,nodes in [('coarse',a['coarse_grid_u']),('fine',a['fine_grid_u'])]:
     indices=np.searchsorted(a['u'],nodes);gg=a['Gamma_fine'][indices,None];curve=EvenThresholdCubicORF(nodes,gg,coordinate='beta');value=curve(u);checks=bernstein_eigenvalues(curve.coeff)
     derivative=-(curve.coeff[-1,1]+2*curve.coeff[-1,2]+3*curve.coeff[-1,3])/(curve.alpha[-1]-curve.alpha[-2]);derivative_error=float(np.max(abs(derivative)))
     if derivative_error>1e-7:raise ValueError('Threshold parity derivative gate failed')
     if label=='fine':
      fine_values[:,k-1:k]=value;union=np.union1d(union,nodes);write_npz(dest/f'curve_channel{k:02d}.npz',nodes=nodes,matrices=gg,coeff=curve.coeff,coordinate=np.array('minus_beta'))
     else:coarse_values[:,k-1:k]=value
     curves.append(dict(channel=k,resolution=label,node_count=len(nodes),fallback_intervals=curve.fallback.tolist(),threshold_derivative_error=derivative_error,**checks));del curve,gg,value;gc.collect();rss('curve')
   del a;gc.collect();print(json.dumps(dict(stage='interpolation_curves',completed_channel=k,RSS_peak_bytes=rss('channel'))),flush=True)
  stages['anchors']=anchors;stages['curves']=curves
  interp=dict(maximum_coarse_fine_matrix=float(np.max(abs(coarse_values-fine_values))),maximum_fine_oracle_matrix=float(np.max(abs(fine_values-oracle))),by_channel_fine_oracle=np.max(abs(fine_values-oracle),axis=(0,2,3)).tolist(),validation_nodes=len(u),first_curve_coarse_fine_is_identical=True)
  write_npz(dest/'validation_matrices.npz',u=u,oracle=oracle,fine=fine_values,coarse=coarse_values)
  stages['interpolation']=interp;write_json(dest/'curves_and_anchors.json',dict(anchors=anchors,curves=curves,interpolation=interp))
  # Full direct angular rules use effective represented beta, not ideal beta.
  direct=[]
  for row in pre['direct_checks']:
   k=row['channel'];desired=row['beta'];uu=u_from_beta(np.array([desired]));bb=float(beta_from_u(uu)[0]);a=channel(k);j=np.searchsorted(a['u'],uu[0])
   if a['u'][j]!=uu[0]:raise ValueError('Direct anchor missing')
   for ia,ib in row['pairs']:
    values=[]
    for label,orders in [('coarse',row['coarse_nmu_nphi']),('fine',row['fine_nmu_nphi'])]:
     nmu,nphi=orders
     if not(1<=nmu<=20000 and 1<=nphi<=20000):raise ValueError('Direct order outside C05 public domain')
     ledger.charge('angular',nmu*nphi,dict(channel=k,beta=bb,pair=[ia,ib],resolution=label));values.append(raw_direct_orf(bb,float(cos[ia,ib]),float(phase[k-1,ia]),float(phase[k-1,ib]),nmu=nmu,nphi=nphi));rss('direct')
    dc=abs(values[0]-values[1]);dh=abs(values[1]-a['Gamma_fine'][j,ia,ib]);r=dict(channel=k,beta_desired=desired,beta_effective=bb,u=float(uu[0]),pair=[ia,ib],coarse_fine_error=float(dc),direct_harmonic_error=float(dh))
    direct.append(r)
    if max(dc,dh)>1e-7:raise ValueError('Independent sky gate failed; no automatic refinement')
   print(json.dumps(dict(stage='direct',completed=len(direct),angular_work=ledger.totals['angular'],RSS_peak_bytes=rss('direct_done'))),flush=True);del a;gc.collect()
  stages['direct']=direct;write_json(dest/'direct_checks.json',dict(rows=direct,angular_work=ledger.totals['angular']))
  # Exactly 143*64*32*3 model densities; no hidden A0/A models are evaluated.
  bounds=np.array(ecfg['prior']['bounds'])[1:];rng=np.random.default_rng(cfg['likelihood_nuisance_seed']);eta=bounds[:,0]+rng.uniform(size=(64,4))*np.diff(bounds)[:,0]
  with np.load(HERE/'inputs/pilot_data.npz',allow_pickle=False) as data:x=np.concatenate([data['x_physical'],data['x_gaussian']],axis=0)
  if x.shape!=(32,4,10):raise ValueError('Frozen engineering observations shape mismatch')
  observed=np.einsum('rkd,k->rd',x,e['weights']);del x;details=[];maxcf=maxfo=0.;worstcf=worstfo=None
  for j,uu in enumerate(u):
   vals=[]
   for label,gamma in [('coarse',coarse_values[j]),('fine',fine_values[j]),('oracle',oracle[j])]:
    ledger.charge('logL',64*32,dict(u=float(uu),representation=label));mu,cov=compressed_moments(eta,gamma,e);val=compressed_logpdf(mu,cov,observed)
    if not np.isfinite(val).all():raise ValueError('Nonfinite likelihood')
    vals.append(val)
   dcf=abs(vals[0]-vals[1]);dfo=abs(vals[1]-vals[2]);ec=float(dcf.max());eo=float(dfo.max())
   if ec>maxcf:maxcf=ec;worstcf=dict(u=float(uu),index=list(map(int,np.unravel_index(np.argmax(dcf),dcf.shape))))
   if eo>maxfo:maxfo=eo;worstfo=dict(u=float(uu),index=list(map(int,np.unravel_index(np.argmax(dfo),dfo.shape))))
   details.append(dict(u=float(uu),coarse_fine=ec,fine_oracle=eo))
   write_npz(dest/'likelihood_cache'/f'node_{j:04d}.npz',u=np.array(uu),logL_coarse=vals[0],logL_fine=vals[1],logL_oracle=vals[2],nuisances_sha256=np.array(digest(eta)),observations_sha256=np.array(digest(observed)),construction_identity=np.array(manifest['identity']))
   if max(ec,eo)>.001:
    write_json(dest/'likelihood_failed.json',dict(rows=details,maximum_coarse_fine=maxcf,maximum_fine_oracle=maxfo,worst_coarse_fine=worstcf,worst_fine_oracle=worstfo));raise ValueError('Likelihood interpolation gate failed; no automatic refinement')
  stages['likelihood']=dict(rows=details,maximum_coarse_fine=maxcf,maximum_fine_oracle=maxfo,worst_coarse_fine=worstcf,worst_fine_oracle=worstfo,values=ledger.totals['logL'],nuisance_seed=cfg['likelihood_nuisance_seed'],prior_or_engineering_validation_only=True,no_truth_deserialized=True)
  write_json(dest/'likelihood_checks.json',stages['likelihood']);write_npz(dest/'likelihood_nuisances.npz',eta=eta)
  # A common knot set is obtained by exact polynomial subdivision, not refitting.
  coeff=np.empty((len(union)-1,4,4,P,P),complex);gamma=np.empty((len(union),4,P,P),complex);subchecks=[]
  for k in range(1,5):
   with np.load(dest/f'curve_channel{k:02d}.npz',allow_pickle=False) as z:old=z['nodes'];c=z['coeff'];sub=subdivide(old,c,union);coeff[:,:,k-1:k]=sub;gamma[:,k-1:k]=evaluate(old,c,union)
   discrepancy=float(np.max(abs(evaluate(union,sub,u)-fine_values[:,k-1:k])))
   if discrepancy>1e-11:raise ValueError('Algebraic subdivision changed curve')
   subchecks.append(dict(channel=k,maximum_subdivision_error=discrepancy,**bernstein_eigenvalues(sub)));del sub,c;gc.collect();rss('common_export')
  write_npz(dest/'C_beta_common_table.npz',nodes=union,matrices=gamma,coeff=coeff,coordinate=np.array('minus_beta'),response=np.array('C_beta: common beta_ref, actual channel phases'),construction_identity=np.array(manifest['identity']))
  stages['subdivision']=subchecks;del coeff,gamma;gc.collect()
  for path,h in allhash.items():
   if sha_file(ROOT/path)!=h:raise ValueError('Frozen source/input changed during gates')
  report=dict(status='C_BETA_CANDIDATE_TABLE_PASS_STATED_GATES_ONLY',construction_identity=manifest['identity'],stages=stages,resource_totals=ledger.totals,seconds=time.perf_counter()-start,RSS_peak_bytes=rss('finished'),no_posterior_inference=True,no_T_Hann_map=True,interpolation_not_automatically_approved_on_future_C_posteriors=True,source_sha256=gcfg['source_sha256'],output_sha256={str(p.relative_to(ROOT)):sha_file(p) for p in sorted(dest.iterdir()) if p.is_file()})
  write_json(dest/'final_report.json',report);print(json.dumps({k:v for k,v in report.items() if k not in ['stages','source_sha256','output_sha256']}),flush=True)
 except Exception as exc:
  write_json(dest/'failure.json',dict(status='GATE_FAILED_NO_AUTOMATIC_REFINEMENT',error_type=type(exc).__name__,message=str(exc),stages_completed=list(stages),resource_totals=ledger.totals,seconds=time.perf_counter()-start,RSS_peak_bytes=int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)));raise
if __name__=='__main__':run()
