#!/usr/bin/env python3
"""Archive self controls, paired omissions, W1 runs and preserved failures."""
from pathlib import Path
import hashlib,json,zipfile
import numpy as np
R=Path(__file__).resolve().parents[1];S=R/'tmp/c09_D3_self_controls_v1';W=R/'tmp/c09_D3_w1_v1';D=R/'tmp/c09_D3_components_v1';DEST=R/'results/C09/D3_complementos'
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,x):p.write_text(json.dumps(x,indent=2,allow_nan=False)+'\n')
def main():
 DEST.mkdir(parents=True,exist_ok=True)
 controls=read(S/'audit.json');assert controls['analyses']==controls['primary_passed']==21
 assert read(S/'generation_audit.json')['passed']
 rows=[];total=0;measured_CPU=0.;sources=[]
 jobs=read(W/'execution/plan.json')['jobs']
 for kind,i,n in jobs:
  directory=W/'execution'/f'{kind}_{i}';old=D/'posterior_execution'/f'd{i}' if kind=='nominal' else S/'execution'/f'{kind}_{i}'
  special=kind=='nominal' and i==0
  comparisons=read((W/'recovered_nominal_0' if special else directory)/'comparisons.json')
  assert len(comparisons)==n
  refs=[read(directory/f'reference_{j}.json')['results'] for j in (1,2)]
  plan=read(directory/'plan.json');charged=0
  for rel,h in plan['bindings'].items():
   path=W/'worker_attempt1.py' if special and rel==str((W/'worker.py').relative_to(R)) else R/rel
   assert sha(path)==h,rel
  for j,(c,x) in enumerate(zip(plan['curves'],comparisons)):
   assert c['curve_id']==x['curve'];name=x['curve']
   with np.load(old/'caches'/(name+'.npz'),allow_pickle=False) as oldcache,np.load(directory/'caches'/(name+'.npz'),allow_pickle=False) as newcache:
    u=newcache['u'];idx=np.searchsorted(u,oldcache['u'])
    assert np.array_equal(u[idx].view(np.uint64),oldcache['u'].view(np.uint64))
    assert np.array_equal(newcache['log_likelihood'][idx].view(np.uint64),oldcache['log_likelihood'].view(np.uint64))
    charged+=len(u)-len(oldcache['u'])+3
   a,b=refs[0][j],refs[1][j];ws=x['table_values']
   delta=max(abs(ws[0]-ws[2]),abs(ws[1]-ws[2]),abs(a['W1']-b['W1']),abs(ws[2]-b['W1']))+b['normalizer_uncertainty_sensitivity']
   previous=read(old/'results'/(name+'.json'))['results'][0]['reference']
   cdf=max(float(np.max(abs(np.array(v['cdf'])-previous['cdf']))) for v in (a,b));zd=max(v['normalization_relative_discrepancy'] for v in (a,b))
   assert abs(delta-x['operational_delta'])<1e-15 and abs(cdf-x['CDF_delta'])<1e-15 and abs(zd-x['Z_relative_delta'])<1e-15
   assert x['passed']==(delta<=.001 and cdf<=.002 and zd<=.001)
   rows.append(dict(kind=kind,data_id=i,**x))
  if special:
   receipt=read(W/'recovered_nominal_0/receipt.json');assert charged==receipt['additional_charged_values'] and receipt['CPU_measured'] is None
  else:
   receipt=read(directory/'receipt.json');assert receipt['status']=='COMPLETED'
   assert charged==receipt['budget']['additional_charged_values'] and receipt['budget']['failed_reserved_values']==0
   measured_CPU+=receipt['CPU']
  total+=charged
 assert len(rows)==161
 summary=dict(controls=controls,W1_analyses=161,W1_passed=sum(x['passed'] for x in rows),W1_rows=rows,
  W1_charged_values=total,W1_measured_worker_CPU=measured_CPU,W1_failed_worker_CPU_charged_reservation=60,
  W1_failed_worker_CPU_measured=None,W1_recovery_CPU_measured=None,
  W1_max_delta=max(x['operational_delta'] for x in rows),W1_max_CDF_delta=max(x['CDF_delta'] for x in rows),
  cumulative_C09_likelihood_values=controls['cumulative_C09_values']+total,C09_complete=False,
  limitations='W1 finite-response operational checks only; no logL event completion, distance posteriors, production D3 or SBC.')
 write(DEST/'audit.json',summary)
 for source,name in [(S,'controles_e_omissoes.zip'),(W,'W1_fontes_execucoes.zip')]:
  files=sorted(p for p in source.rglob('*') if p.is_file() and '__pycache__' not in p.parts)
  entries=[dict(path=str(p.relative_to(R)),sha256=sha(p),bytes=p.stat().st_size) for p in files]
  path=DEST/name
  with zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
   for p in files:z.write(p,p.relative_to(R))
  with zipfile.ZipFile(path) as z:
   for entry in entries:assert hashlib.sha256(z.read(entry['path'])).hexdigest()==entry['sha256']
  sources.append(dict(path=str(path.relative_to(R)),sha256=sha(path),bytes=path.stat().st_size,members=len(entries),files=entries))
 write(DEST/'manifest.json',dict(archives=sources,dependencies='v0.8.9 D3 pilot archive, D2 archives and bound C06-C08 inputs. Original failed W1 source and log retained; first references recovered without physical reevaluation.'))
 print(json.dumps({k:v for k,v in summary.items() if k not in ('controls','W1_rows')},indent=2))
if __name__=='__main__':main()
