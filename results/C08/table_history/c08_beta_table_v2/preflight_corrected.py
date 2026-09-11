"""Prospective local refinement only: no harmonic basis, sky integral or logL."""
from pathlib import Path
import hashlib,json,datetime
import numpy as np
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];OLD=ROOT/'tmp/c08_beta_table'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def u_of(beta):
 b=np.asarray(beta,float);return np.sqrt((1-b)*(1+b))
def b_of(u):
 u=np.asarray(u,float);return np.sqrt((1-u)*(1+u))
old=json.loads((OLD/'preflight_v2.json').read_text());finish=json.loads((OLD/'results/original_diagnostic_continuation/report.json').read_text())
seed=808130101;rng=np.random.default_rng(seed);bjoin=1/64;delta=1/65536
random_u=np.r_[rng.uniform(size=24),u_of(rng.uniform(size=24)),u_of(10**rng.uniform(-6,np.log10(.05),size=16))]
anchor_beta=np.array([bjoin,bjoin-delta,bjoin+delta,bjoin/2,bjoin/4,bjoin/8,bjoin/16,bjoin/32]);control_u=np.unique(np.r_[random_u,u_of(anchor_beta)])
if len(control_u)!=72 or np.isin(control_u,np.array(old['validation_nodes_u'])).any():raise ValueError('New controls not72 distinct fresh points')
with np.load(OLD/'first_curve_root.npz',allow_pickle=False) as z:union=z['nodes'].copy()
# Phase values derive directly from the frozen source config/geometry, not data.
import sys
sys.path.insert(0,str(OLD/'executed_sources/src'))
from inference.model import experiment,YEAR
from inference.orf_blas import estimate
cfg=json.loads((OLD/'inputs/experiment.json').read_text());e=experiment(cfg);phase=2*np.pi*e['f'][:,None]*e['distance_ly'][None]*YEAR
rows=[];local_total=oracle_total=direct_total=0;input_sha={str(p.relative_to(ROOT)):sha(p) for p in [OLD/'execution_authorized.json',OLD/'preflight_v2.json',OLD/'results/gates/failure.json',OLD/'results/original_diagnostic_continuation/report.json',OLD/'inputs/experiment.json',OLD/'first_curve_root.npz']}
for k in range(1,5):
 path=OLD/f'results/gates/curve_channel{k:02d}.npz';input_sha[str(path.relative_to(ROOT))]=sha(path)
 with np.load(path,allow_pickle=False) as z:previous=z['nodes'].copy()
 row=old['rows'][k-1];full_work=72*row['real_multiplications_per_node'];oracle_total+=full_work
 entry=dict(channel=k,new_oracle_nodes=72,oracle_orders_coarse=row['coarse'],oracle_orders_fine=row['fine'],oracle_full_resolution_real_products=full_work,old_fine_becomes_new_coarse=True)
 if k>1:
  boundary=float(u_of([bjoin])[0]);old_inside=previous[previous>=boundary];local=np.union1d(old_inside,u_of(np.linspace(0,bjoin,1025)));global_new=np.union1d(previous,local);union=np.union1d(union,global_new)
  maximum_phase=float(b_of([boundary])[0]*phase[k-1].max());lc=int(np.ceil(maximum_phase)+100);nc=int(np.ceil(2*maximum_phase)+220);lf=lc+40;nf=nc+80
  charge=int(2*len(local)*12*((lc-1)*nc+(lf-1)*nf));local_total+=charge
  entry.update(local_candidate_nodes=len(local),old_nodes_in_patch=len(old_inside),new_interpolation_nodes=len(global_new),newly_inserted_nodes=len(global_new)-len(previous),patch_coarse_harmonic_orders=[lc,nc],patch_fine_harmonic_orders=[lf,nf],maximum_patch_phase=maximum_phase,local_real_products=charge,maximum_local_estimated_numeric_bytes=estimate(lf,nf,12,8)['estimated_memory_bytes'],boundary_u=boundary)
  if len(global_new)>10000:raise ValueError('Per-channel10000 node cap exceeded')
  # Two geometric anchors, both pulsar pairs; each full source curve is checked.
  checks=[]
  for beta in [bjoin/4,bjoin]:
   cm=max(64,int(np.ceil(2*beta*phase[k-1].max()+220)));fm=cm+80;cp=2*cm;fp=2*fm;work=2*(cm*cp+fm*fp);direct_total+=work;checks.append(dict(beta=beta,pairs=[[3,8],[0,11]],coarse_nmu_nphi=[cm,cp],fine_nmu_nphi=[fm,fp],work=work))
  entry['new_direct_checks']=checks
 rows.append(entry)
original_u=np.array(old['validation_nodes_u']);affected=int(np.sum(b_of(original_u)<=bjoin));new_historical_logL=affected*64*32;new_controls_logL=72*64*32*3;planned_logL=new_historical_logL+new_controls_logL
planned_real=local_total+oracle_total;previous=finish['resource_totals'];table_matrices=len(union)*4*12*12*16;coeff=(len(union)-1)*4*4*12*12*16
report=dict(schema='C08_BETA_LOCAL_REFINEMENT_PREFLIGHT_v2',status='PROSPECTIVE_ONLY_NOT_AUTHORIZED_OR_STARTED',created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),execution_enabled=False,refinement=dict(patch_beta_interval=[0,bjoin],join_on_existing_uniform_knot=True,uniform_subdivision_factor=8,base_uniform_spacing=1/8192,new_local_uniform_spacing=delta,retain_all_old_fine_nodes=True,new_coarse='entire original fine curve, unchanged',new_fine='replace only the geometric patch by a spline through old+new validated nodes, clamped to old boundary value/first derivative at beta_join and zero derivative at beta0; retain old polynomial coefficients outside patch exactly',do_not_refine_only_failure_point=True,old_coarse_is_not_modified=True),validation=dict(new_seed=seed,new_nuisance_seed=808130201,new_random_mass_points=64,new_anchor_mass_points=8,new_control_u=control_u.tolist(),anchor_beta=anchor_beta.tolist(),historical_masses=143,historical_affected_masses=affected,history_reuse='Existing original-fine and exact-oracle logL caches. Reuse new-fine logL outside patch only after bit-exact gamma/polynomial verification; no truth or data-based new point selection.',new_controls='64 new nuisances across72 new mass points, all32 engineering observations, old-fine/new-fine/exact-oracle. All original thresholds unchanged.',required_new_thresholds=dict(matrix_coarse_fine=1e-8,direct_coarse_fine=1e-7,direct_harmonic=1e-7,logL_coarse_fine=.001,logL_fine_oracle=.001),no_posterior_validation_claim=True),rows=rows,cost=dict(previous_real_products=previous['real'],new_patch_real_products=local_total,new_oracle_real_products=oracle_total,planned_new_real_products=planned_real,planned_cumulative_real_products=previous['real']+planned_real,maximum_cumulative_real_products=50_000_000_000_000,remaining_real_products_after_plan=50_000_000_000_000-previous['real']-planned_real,previous_logL=previous['logL'],new_historical_logL=new_historical_logL,new_control_logL=new_controls_logL,planned_new_logL=planned_logL,planned_cumulative_logL=previous['logL']+planned_logL,requested_new_logL_cap=600000,requested_cumulative_logL_cap=1600000,previous_direct_angular_work=previous['angular'],planned_new_direct_angular_work=direct_total,planned_cumulative_direct_angular_work=previous['angular']+direct_total,maximum_cumulative_direct_angular_work=8000000000),resources=dict(workers=1,VECLIB_MAXIMUM_THREADS=1,maximum_RSS_bytes=1610612736,maximum_estimated_numeric_bytes=1073741824,union_interpolation_nodes=len(union),common_matrix_bytes=table_matrices,common_coefficient_bytes=coeff,maximum_basis_buffers_bytes=max(r['maximum_basis_buffers_bytes'] for r in old['rows']),estimated_time='Expected a few minutes, dominated by eight full-resolution basis preparations and72 independent oracle points; measure, not promise. No native bank or posterior.',old_run_RSS_peak_bytes=1360314368),input_sha256=input_sha,source_sha256=sha(__file__),no_scientific_computations=True)
if report['cost']['planned_cumulative_real_products']>50_000_000_000_000 or planned_logL>600000 or report['cost']['planned_cumulative_logL']>1600000:raise ValueError('Prospective caps exceeded')
with (HERE/'preflight.json').open('x') as f:json.dump(report,f,indent=2);f.write('\n')
print(json.dumps({k:v for k,v in report.items() if k in ['status','cost','resources']},indent=2))
