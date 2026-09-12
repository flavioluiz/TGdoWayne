#!/usr/bin/env python3
"""Preserve B_G omission and initial direct-distance rules with independent audit."""
from pathlib import Path
import hashlib,json,zipfile
import numpy as np
R=Path(__file__).resolve().parents[1];B=R/'tmp/c09_D3_BG_omission_v1';D=R/'tmp/c09_D3_distances_v1';DEST=R/'results/C09/D3_distancias_iniciais'
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,x):p.write_text(json.dumps(x,indent=2,allow_nan=False)+'\n')
def main():
 DEST.mkdir(parents=True,exist_ok=True);bg=read(B/'execution/receipt.json');assert bg['status']=='COMPLETED' and bg['primary_results']==bg['W1_passed']==4
 for rel,h in read(B/'execution/plan.json')['bindings'].items():assert sha(R/rel)==h
 stored=0
 for p in (B/'execution/caches').glob('*.npz'):
  with np.load(p,allow_pickle=False) as f:assert np.all(np.diff(f['u'])>0) and np.isfinite(f['log_likelihood']).all();stored+=len(f['u'])
 assert stored+140==bg['budget']['additional_charged_values'] and bg['budget']['failed_reserved_values']==0
 comparisons=read(B/'execution/comparisons.json');wrefs=[read(B/f'execution/W1_reference_{j}.json')['results'] for j in (1,2)]
 for j,c in enumerate(comparisons):
  p=R/f'tmp/c09_D3_components_v1/posterior_execution/d{c["data_id"]}/results/d{c["data_id"]}_B_G_full_variable.json'
  assert sha(p)==c['included_result_sha256']
  inc=read(p)['results'][0];om=read(B/'execution/results'/(c['curve']+'.json'))['results'][0]
  assert all(inc['table_gates'][k] and om['table_gates'][k] for k in ('normalization','CDF','quantiles','moments','KL'))
  qi=next(q for q in inc['quantiles'] if q['probability']==.95);qo=next(q for q in om['quantiles'] if q['probability']==.95)
  assert np.allclose(c['q95_difference'],[qo['lower']-qi['upper'],qo['upper']-qi['lower']],rtol=0,atol=1e-15)
  a,b=wrefs[0][j],wrefs[1][j];ws=c['table_values']
  delta=max(abs(ws[0]-ws[2]),abs(ws[1]-ws[2]),abs(a['W1']-b['W1']),abs(ws[2]-b['W1']))+b['normalizer_uncertainty_sensitivity']
  assert abs(delta-c['W1_delta'])<1e-15 and c['W1_passed'] and delta<=.001
 plan=read(D/'prepared/plan.json');backend=read(D/'backend_execution/summary.json');initial=read(D/'initial_execution/receipt.json')
 assert backend['all_jobs_completed'] and initial['status']=='COMPLETED_INITIAL_RULES_REFERENCE_PENDING'
 stages=np.empty((3,2,960,4,12,12),complex);products=0
 for job in plan['jobs']:
  p=D/'backend_execution'/job['name'];receipt=read(p/'receipt.json');assert receipt['status']=='COMPLETED'
  assert sha(p/'matrices.npz')==receipt['matrix_sha256'];products+=receipt['products']
  with np.load(p/'matrices.npz',allow_pickle=False) as f:stages[job['level_index'],:,:,job['channel']]=f['Gamma']
 assert products==plan['real_products']==20759249462592
 ref=read(D/'initial_execution/response_audit.json')
 assert abs(np.max(abs(stages[1]-stages[0]))-ref['max_nodes_delta'])<1e-18
 assert abs(np.max(abs(stages[2]-stages[1]))-ref['max_ell_delta'])<1e-18
 assert np.linalg.eigvalsh(stages).min()>=-1e-12
 with np.load(D/'initial_execution/responses.npz',allow_pickle=False) as f:assert np.array_equal(f['Gamma'].view(np.float64),stages[2].view(np.float64))
 with np.load(D/'initial_execution/likelihoods.npz',allow_pickle=False) as f:
  ell=f['component_logL'];mixture=f['mixture_logL'];shift=ell.max(axis=0)
  independent=shift+np.log(np.sum(np.array([.25,.5,.25])[:,None,None]*np.exp(ell-shift),axis=0))
  assert np.max(abs(independent-mixture))<1e-12
 assert initial['budget']['additional_charged_values']==17334 and initial['budget']['failed_reserved_values']==0
 results=read(D/'initial_execution/results.json');assert len(results)==12 and all(r['initial_rules_agree'] for r in results)
 maximum={k:max(r['deltas'][k] for r in results) for k in ('logZ','mean','second','KL','CDF')}
 summary=dict(BG_omission_comparisons=comparisons,BG_charged_values=bg['budget']['additional_charged_values'],BG_CPU=bg['CPU'],
   distance_response_audit=ref,distance_initial_results=results,distance_initial_max_deltas=maximum,
   distance_initial_charged_values=17334,distance_initial_CPU=initial['CPU'],
   cumulative_C09_likelihood_values=5655578+bg['budget']['additional_charged_values']+17334,
   complete_primary_and_W1_D3_analyses=165,distance_posterior_quantiles_validated=False,
   distance_independent_reference_complete=False,C09_complete=False,engineering_not_SBC=True)
 write(DEST/'audit.json',summary)
 groups=[('BG_fontes_execucoes.zip',[p for p in B.rglob('*') if p.is_file() and '__pycache__' not in p.parts]),
         ('distancias_fontes_execucoes.zip',[p for p in D.rglob('*') if p.is_file() and '__pycache__' not in p.parts])]
 archives=[]
 for name,files in groups:
  entries=[dict(path=str(p.relative_to(R)),sha256=sha(p),bytes=p.stat().st_size) for p in sorted(files)];archive=DEST/name
  with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
   for p in sorted(files):z.write(p,p.relative_to(R))
  with zipfile.ZipFile(archive) as z:
   for x in entries:assert hashlib.sha256(z.read(x['path'])).hexdigest()==x['sha256']
  archives.append(dict(path=str(archive.relative_to(R)),sha256=sha(archive),bytes=archive.stat().st_size,files=entries))
 write(DEST/'manifest.json',dict(archives=archives,dependencies='D3 pilot and complement archives, original C09 design, D2 components and C06-C08 inputs. Initial distance rules do not certify posterior quantiles or an ORF interpolant.'))
 print(json.dumps({k:v for k,v in summary.items() if k not in ('BG_omission_comparisons','distance_initial_results')},indent=2))
if __name__=='__main__':main()
