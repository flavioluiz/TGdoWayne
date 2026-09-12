#!/usr/bin/env python3
"""Archive completed production generation and six nominal pilot posteriors."""
from pathlib import Path
import hashlib,json,zipfile
import numpy as np
R=Path(__file__).resolve().parents[1];P=R/'tmp/c09_production_v1';N=R/'tmp/c09_distance_nominal_posteriors_v1';DEST=R/'results/C09/production_generation'
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,x):p.write_text(json.dumps(x,indent=2,allow_nan=False)+'\n')
def main():
 DEST.mkdir(parents=True,exist_ok=True);responses=read(P/'response_audit/receipt.json');generation=read(P/'generation/receipt.json');audit=read(P/'generation/audit.json')
 assert responses['passed'] and responses['new_nodes']==1765 and responses['reused_nodes']==3
 assert sha(P/'response_audit/truth_responses.npz')==responses['truth_response_sha256']
 assert generation['status']=='COMPLETED_PRODUCTION_OBSERVATIONS' and audit['status']=='PASS'
 assert generation['datasets_generated']==audit['datasets_reconstructed']==5396
 assert sha(P/'generation/receipt.json')==audit['generator_receipt_sha256']
 for rel,h in read(P/'generation/activation.json')['source_sha256'].items():assert sha(R/rel)==h
 for f in generation['files']:
  path=P/'generation'/f['path'];assert sha(path)==f['sha256']
  with np.load(path,allow_pickle=False) as d:assert len(d['ids'])==f['datasets'] and all(np.isfinite(d[k]).all() for k in d.files if k!='ids')
 assert len({x['id'] for x in audit['checks']})==5396 and max(x['max_scaled_difference'] for x in audit['checks'])<=1e-10
 nr=read(N/'execution/receipt.json');assert nr['status']=='COMPLETED' and nr['primary_results']==nr['W1_passed']==6
 for rel,h in read(N/'execution/plan.json')['bindings'].items():assert sha(R/rel)==h
 count=0
 for p in (N/'execution/caches').glob('*.npz'):
  with np.load(p,allow_pickle=False) as d:assert np.all(np.diff(d['u'])>0) and np.isfinite(d['log_likelihood']).all();count+=len(d['u'])
 assert count+210==nr['budget']['additional_charged_values']==187197 and nr['budget']['failed_reserved_values']==0
 comparisons=read(N/'execution/comparisons.json');refs=[read(N/f'execution/W1_reference_{i}.json')['results'] for i in (1,2)]
 for j,c in enumerate(comparisons):
  r=read(N/'execution/results'/(c['curve']+'.json'))['results'][0]
  assert all(r['table_gates'][k] for k in ('normalization','CDF','quantiles','moments','KL'))
  assert r['delta_logZ']<=.001 and max(r['delta_CDF'])<=.002 and r['delta_KL']<=.001 and max(r['delta_moments'])<=.001
  assert all(q['upper']-q['lower']<=.001 for q in r['quantiles'])
  a,b=refs[0][j],refs[1][j];w=c['table_values'];delta=max(abs(w[0]-w[2]),abs(w[1]-w[2]),abs(a['W1']-b['W1']),abs(w[2]-b['W1']))+b['normalizer_uncertainty_sensitivity']
  assert abs(delta-c['W1_delta'])<1e-15 and c['W1_passed'] and delta<=.001
 summary=dict(response_generation=responses,observations={k:v for k,v in generation.items() if k!='files'},data_audit={k:v for k,v in audit.items() if k!='checks'},nominal_pilot_receipt=nr,nominal_pilot_comparisons=comparisons,cumulative_C09_likelihood_values=5999394,complete_primary_and_W1_D3_pilot_analyses=171,production_posteriors_evaluated=0,C09_complete=False)
 write(DEST/'audit.json',summary)
 groups=[('truth_backend.zip',[R/'tmp/c09_production_truth_backend_v1',R/'tmp/c09_production_truth_backend_v2']),('truths_data_audits.zip',[P]),('nominal_pilot_posteriors.zip',[N])];archives=[]
 for name,dirs in groups:
  files=sorted(p for d in dirs for p in d.rglob('*') if p.is_file() and '__pycache__' not in p.parts)
  entries=[dict(path=str(p.relative_to(R)),sha256=sha(p),bytes=p.stat().st_size) for p in files];archive=DEST/name
  with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
   for p in files:z.write(p,p.relative_to(R))
  assert archive.stat().st_size<=90*1024**2
  with zipfile.ZipFile(archive) as z:
   for e in entries:assert hashlib.sha256(z.read(e['path'])).hexdigest()==e['sha256']
  archives.append(dict(path=str(archive.relative_to(R)),sha256=sha(archive),bytes=archive.stat().st_size,files=entries))
 write(DEST/'manifest.json',dict(archives=archives,dependencies='Versioned C09 production configs and preparer; original C07 experiment/table and saved nominal harmonic controls; D2/D3 kernel/reference source archives. Production observations are not posterior calibration results.'))
 print(json.dumps(dict(datasets=5396,nominal_primary_W1=6,cumulative_likelihood_values=5999394,archives=[{k:v for k,v in a.items() if k!='files'} for a in archives]),indent=2))
if __name__=='__main__':main()
