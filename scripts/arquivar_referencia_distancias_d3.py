#!/usr/bin/env python3
"""Audit three independent/adaptive distance waves without new likelihoods."""
from pathlib import Path
import hashlib,json,zipfile
import numpy as np
R=Path(__file__).resolve().parents[1];DEST=R/'results/C09/D3_distancias_referencia'
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,x):p.write_text(json.dumps(x,indent=2,allow_nan=False)+'\n')
def main():
 DEST.mkdir(parents=True,exist_ok=True);waves=[];previous=None;archives=[];LL=0;products=0;cpu=0.;response_cpu=0.;nodes=0
 for number in (1,2,3):
  H=R/f'tmp/c09_D3_distance_reference_v{number}';plan=read(H/'prepared/plan.json');receipt=read(H/'initial_execution/receipt.json');backend=read(H/'backend_execution/summary.json')
  assert receipt['status']=='COMPLETED_REFERENCE_DENSITIES' and backend['all_jobs_completed']
  for rel,h in plan['bindings'].items():assert sha(R/rel)==h
  assert sha(R/plan['rules_file'])==plan['rules_sha256']
  N=plan['u_nodes_per_scale'];stages=np.empty((3,2,N,4,12,12),complex);cost=0
  for job in plan['jobs']:
   p=H/'backend_execution'/job['name'];rr=read(p/'receipt.json');assert rr['status']=='COMPLETED' and sha(p/'matrices.npz')==rr['matrix_sha256'];cost+=rr['products']
   with np.load(p/'matrices.npz',allow_pickle=False) as f:stages[job['level_index'],:,:,job['channel']]=f['Gamma']
  assert cost==plan['real_products']==backend['products']
  audit=read(H/'initial_execution/response_audit.json')
  assert float(np.max(abs(stages[1]-stages[0])))==audit['max_nodes_delta']<=1e-8
  assert float(np.max(abs(stages[2]-stages[1])))==audit['max_ell_delta']<=1e-8
  assert np.linalg.eigvalsh(stages).min()>=-1e-12
  with np.load(H/'initial_execution/responses.npz',allow_pickle=False) as f:assert np.array_equal(stages[2],f['Gamma'])
  with np.load(H/'initial_execution/likelihoods.npz',allow_pickle=False) as f:
   ell=f['component_logL'];mix=f['mixture_logL'];shift=ell.max(axis=0)
   assert ell.shape==(3,N,6) and np.max(abs(shift+np.log(np.sum(np.array([.25,.5,.25])[:,None,None]*np.exp(ell-shift),axis=0))-mix))<1e-12
  count=18*N+54;assert count==receipt['budget']['additional_charged_values'] and receipt['budget']['failed_reserved_values']==0
  recovery=read(H/'scipy_recovery/receipt.json')
  assert recovery['status']=='COMPLETED' and len(recovery['checks'])==54
  assert max(c['delta'] for c in recovery['checks'])<=1e-8
  assert recovery['budget']['additional_charged_values']==54 and recovery['budget']['failed_reserved_values']==0
  result=read(H/'initial_execution/integrals.json');assert len(result['results'])==12
  rows=[]
  for j,row in enumerate(result['results']):
   delta={}
   if previous:
    old=previous['results'][j];assert (old['curve'],old['mode'])==(row['curve'],row['mode'])
    a,b=old['reference'],row['reference'];delta={k:abs(a[k]-b[k]) for k in ('logZ','mean','second','KL')};delta['CDF']=max(abs(x-y) for x,y in zip(a['CDF_at_panel_edges'],b['CDF_at_panel_edges']))
   refinement=bool(delta) and all(delta[k]<=.001 for k in ('logZ','mean','second','KL')) and delta['CDF']<=.002
   gate=refinement and row['functional_agreement'] and row['embedded_error_scaled']<=.001
   rows.append(dict(**row,previous_wave_deltas=delta,refinement_agreement=refinement,reference_gate=bool(gate)))
  waves.append(dict(number=number,rows=rows,reference_passed=sum(r['reference_gate'] for r in rows),maximum_embedded_error=result['max_embedded_error'],response_audit=audit,LL=count,CPU=receipt['CPU']))
  previous=result;LL+=count+54;products+=cost;nodes+=2*N;cpu+=receipt['CPU']+recovery['CPU'];response_cpu+=backend['CPU']
  files=[p for p in H.rglob('*') if p.is_file() and '__pycache__' not in p.parts];entries=[dict(path=str(p.relative_to(R)),sha256=sha(p),bytes=p.stat().st_size) for p in sorted(files)];archive=DEST/f'onda_{number-1}.zip'
  with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
   for p in sorted(files):z.write(p,p.relative_to(R))
  with zipfile.ZipFile(archive) as z:
   for e in entries:assert hashlib.sha256(z.read(e['path'])).hexdigest()==e['sha256']
  archives.append(dict(path=str(archive.relative_to(R)),sha256=sha(archive),bytes=archive.stat().st_size,files=entries))
 assert nodes==1092 and nodes<=1152
 summary=dict(waves=waves,new_nodes=nodes,remaining_reference_nodes=1152-nodes,new_likelihood_values=LL,cumulative_C09_likelihood_values=5783577+LL,real_products=products,response_CPU=response_cpu,density_CPU=cpu,reference_passed=waves[-1]['reference_passed'],reference_total=12,all_references_complete=waves[-1]['reference_passed']==12,quantiles_W1_events_complete=False,C09_complete=False,engineering_not_SBC=True)
 write(DEST/'audit.json',summary);write(DEST/'manifest.json',dict(archives=archives,dependencies='D3 initial distance archive, D3 pilot data, C07 table and C09 conditional kernels; no new SBC data.'))
 print(json.dumps({k:v for k,v in summary.items() if k!='waves'},indent=2))
if __name__=='__main__':main()
