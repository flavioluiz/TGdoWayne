"""Node/cost plan only: no basis, quadrature, table or likelihood evaluation."""
from pathlib import Path
import hashlib,json,sys
import numpy as np
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'src'))
from inference.orf_blas import estimate
cfg=json.loads((ROOT/'tmp/c08_response_approximation/preflight.json').read_text())
rng=np.random.default_rng(808120101)
def ub(beta):
 beta=np.asarray(beta,float);u=np.sqrt((1-beta)*(1+beta));return u,np.sqrt((1-u)*(1+u))
validation_u=np.r_[rng.uniform(0,1,48),ub(rng.uniform(0,1,48))[0],ub(np.exp(rng.uniform(np.log(1e-6),np.log(.05),32)))[0],[0,.2,.5,.8,.995],ub([0,.0001,.0005,.001,.005,.01,.1,.5,.9,.99,1])[0]]
validation_u=np.unique(validation_u);validation_beta=np.sqrt((1-validation_u)*(1+validation_u));budget=50_000_000_000_000;rows=[];total=0;all_u=[]
for item in cfg['domains']:
 k=item['channel'];den=131072 if k==2 else 262144
 u,b=ub(np.r_[np.linspace(0,1,8193),np.arange(129)/den]);fine_u=np.unique(u);coarse_u=np.unique(ub(np.r_[np.linspace(0,1,4097),np.arange(0,129,2)/den])[0]);request=np.union1d(fine_u,validation_u) if k>1 else validation_u
 per=2*12*((item['coarse_lmax']-1)*item['coarse_nmu']+(item['fine_lmax']-1)*item['fine_nmu']);work=int(len(request)*per);total+=work
 est=max(estimate(item[f'{s}_lmax'],item[f'{s}_nmu'],12,8)['estimated_memory_bytes'] for s in ['coarse','fine']);reserve=3*len(request)*12*12*16+len(request)*16 # node arrays/current coarse+fine+checkpoint buffers
 rows.append(dict(channel=k,table_nodes_evaluated=0 if k==1 else len(fine_u),coarse_interpolation_nodes=None if k==1 else len(coarse_u),validation_and_table_unique_evaluations=len(request),validation_nodes=len(validation_u),real_multiplications=work,real_multiplications_per_node=int(per),maximum_basis_buffers_bytes=est,reserve_bytes=reserve,estimated_numeric_bytes=est+reserve,coarse=[item['coarse_lmax'],item['coarse_nmu']],fine=[item['fine_lmax'],item['fine_nmu']],table_reuses_C07_first_curve=k==1))
 if k>1:all_u.extend(fine_u)
with np.load(ROOT/'tmp/c07_sampler/results/table_beta8193_local.npz') as f:old_u=f['nodes']
union=np.unique(np.r_[all_u,old_u]);N=len(union)
plan=dict(status='TABLE_ONLY_PREFLIGHT_NO_EXECUTION',workers=1,blas_threads=1,rss_operational_stop_bytes=1610612736,maximum_estimated_numeric_bytes=1073741824,maximum_real_multiplications=budget,planned_real_multiplications=total,remaining_real_multiplications=budget-total,maximum_requested_table_nodes_per_frequency=10000,validation_seed=808120101,validation_nodes=len(validation_u),validation_nodes_u=validation_u.tolist(),rows=rows,union_interpolation_nodes=N,common_complex_matrix_bytes=int(N*4*12*12*16),common_cubic_coefficient_bytes=int((N-1)*4*4*12*12*16),direct_angular_work_separate_budget=8_000_000_000,likelihood_validation_budget=1_000_000,maximum_phase=5585.0536063818545,execution_authorized=False,first_curve_source='tmp/c07_sampler/results/table_beta8193_local.npz',source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
assert total<budget and max(r['estimated_numeric_bytes'] for r in rows)<plan['maximum_estimated_numeric_bytes'] and N<10000
with (HERE/'preflight.json').open('x') as f:json.dump(plan,f,indent=2);f.write('\n')
with (HERE/'nodes_plan.npz').open('xb') as f:np.savez(f,validation_u=validation_u,validation_beta=validation_beta,union_u=union)
print(json.dumps({k:v for k,v in plan.items() if k not in ['validation_nodes_u']},indent=2))
