#!/usr/bin/env python3
"""Audit and preserve D3 pilot data and completed/partial posterior runs."""
from pathlib import Path
import hashlib,json,zipfile
import numpy as np
ROOT=Path(__file__).resolve().parents[1];SOURCE=ROOT/'tmp/c09_D3_components_v1';DEST=ROOT/'results/C09/D3_piloto'
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,x):p.write_text(json.dumps(x,indent=2,allow_nan=False)+'\n')
def main():
 DEST.mkdir(parents=True,exist_ok=True)
 original=read(SOURCE/'backend_execution/receipt.json');continuation=read(SOURCE/'backend_continuation/receipt.json')
 assert original['status']=='FAILED' and continuation['status']=='TRUTH_RESPONSES_AND_PAIRED_DATA_COMPLETE'
 for rel,h in original['files'].items():assert sha(SOURCE/'backend_execution'/rel)==h
 for rel,h in continuation['files'].items():assert sha(SOURCE/'backend_continuation'/rel)==h
 worker_receipts=[read(p) for p in (SOURCE/'backend_continuation').glob('channel_*/receipt.json')]
 assert len(worker_receipts)==6 and all(r['status']=='COMPLETED' for r in worker_receipts)
 assert sum(r['products'] for r in worker_receipts)+original['real_products']==continuation['cumulative_products']
 with np.load(SOURCE/'backend_continuation/truth_responses.npz',allow_pickle=False) as f:
  assert f['Gamma'].shape==(10,4,12,12) and np.isfinite(f['Gamma']).all()
  assert max(f['nodes_error'].max(),f['ell_error'].max())<=1e-8
  assert np.linalg.eigvalsh(f['Gamma']).min()>=-1e-12
 with np.load(SOURCE/'backend_continuation/data.npz',allow_pickle=False) as f:
  assert f['q'].shape==(16,4,12) and f['x_physical'].shape==f['x_gaussian'].shape==(16,4,10)
  assert all(np.isfinite(f[k]).all() for k in f.files)
 finite=[read(SOURCE/p/'receipt.json') for p in ('finite_checks_execution','finite_domain_execution')]
 assert all(r['status']=='COMPLETED' and r['passed']==140 for r in finite)
 rows=[];total=0;cpu=0.;cache_values=0;failed_reserved=0;workers=[]
 for i in list(range(13))+[15]:
  directory=SOURCE/'posterior_execution'/f'd{i}';receipt=read(directory/'receipt.json')
  plan=read(directory/'plan.json')
  for rel,h in plan['bindings'].items():assert sha(ROOT/rel)==h
  total+=receipt['budget']['additional_charged_values'];cpu+=receipt['CPU'];failed_reserved+=receipt['budget']['failed_reserved_values']
  workers.append(dict(row=i,status=receipt['status']))
  stored=0
  for p in (directory/'caches').glob('*.npz'):
   with np.load(p,allow_pickle=False) as f:
    assert len(f['u'])==len(f['log_likelihood']) and np.isfinite(f['log_likelihood']).all()
    assert np.all(np.diff(f['u'])>0) and np.all((f['u']>=0)&(f['u']<=1))
    stored+=len(f['u'])
  cache_values+=stored
  assert stored+receipt['budget']['failed_reserved_values']==receipt['budget']['additional_charged_values']
  for curve in plan['curves']:
   path=directory/'results'/(curve['curve_id']+'.json')
   result=read(path) if path.exists() else {}
   if 'results' not in result:
    rows.append(dict(row=i,curve=curve['curve_id'],status='UNRESOLVED',reason=result.get('reason',receipt['error'])));continue
   r=result['results'][0];passed=all(r['table_gates'][k] for k in ('normalization','CDF','quantiles','moments','KL'))
   assert result['finite_backend_evidence']['accepted_finite_domain'] is True
   q=next(q for q in r['quantiles'] if q['probability']==.95)
   rows.append(dict(row=i,curve=curve['curve_id'],prior=r['prior_id'],truth_u=curve['fixed_truth_u'],
    status='PASS_PRIMARY_FINITE_DOMAIN_OPERATIONAL' if passed else 'UNRESOLVED',
    q95=[q['lower'],q['upper']],KL=r['summary']['kl_to_prior'],mean=r['summary']['mean'],
    delta_logZ=r['delta_logZ'],max_delta_CDF=max(r['delta_CDF']),delta_KL=r['delta_KL'],
    W1_status='PENDING',logL_event_status='PENDING'))
 assert len(rows)==140
 summary=dict(generated_engineering_data=16,nominal_distance_posterior_analyses=140,
   primary_passed=sum(r['status']=='PASS_PRIMARY_FINITE_DOMAIN_OPERATIONAL' for r in rows),workers=workers,
   posterior_values=total,posterior_CPU=cpu,cache_values=cache_values,failed_reserved=failed_reserved,
   finite_checks_values=sum(r['budget']['additional_charged_values'] for r in finite),
   finite_checks_CPU=sum(r['CPU'] for r in finite),response_products=continuation['cumulative_products'],
   response_worker_CPU=continuation['cumulative_worker_CPU'],response_controller_CPU=continuation['controller_CPU'],
   cumulative_C09_likelihood_values=848956+total+sum(r['budget']['additional_charged_values'] for r in finite),
   response_audit=read(SOURCE/'backend_continuation/response_audit.json'),rows=rows,
   pending=['distance posterior mixture and response interpolation','matched self-control pilot data and posteriors','W1 and logL events for new data','production D3 and SBC'],
   engineering_excluded_from_SBC=True,C09_complete=False)
 write(DEST/'audit.json',summary)
 files=sorted(p for p in SOURCE.rglob('*') if p.is_file() and '__pycache__' not in p.parts)
 entries=[dict(path=str(p.relative_to(ROOT)),sha256=sha(p),bytes=p.stat().st_size) for p in files]
 archive=DEST/'fontes_dados_execucoes.zip'
 with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
  for p in files:z.write(p,p.relative_to(ROOT))
 with zipfile.ZipFile(archive) as z:
  for x in entries:assert hashlib.sha256(z.read(x['path'])).hexdigest()==x['sha256']
 write(DEST/'manifest.json',dict(archive=str(archive.relative_to(ROOT)),archive_sha256=sha(archive),members=len(entries),files=entries,
  dependencies='D2 continuation archive and components, nominal14 snapshots and bound C06-C08 inputs; restore these before rerunning the driver.'))
 print(json.dumps({k:v for k,v in summary.items() if k not in ('rows','workers')},indent=2))
if __name__=='__main__':main()
