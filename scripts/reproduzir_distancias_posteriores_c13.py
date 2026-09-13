"""Replay distance likelihoods, then the original bounded posterior recovery."""
from pathlib import Path
import argparse,json,subprocess,sys,hashlib,shutil
import numpy as np
R=Path(__file__).resolve().parents[1];p=argparse.ArgumentParser();p.add_argument('--clean-root',type=Path,required=True);a=p.parse_args();C=a.clean_root.resolve();base=C/'tmp/c09_distance_production_v1';saved=C/'tmp/c13_c09_distance_published';saved.mkdir(exist_ok=False)
for name in ('c09_nominal_production_v1','c09_self_production_v1','c09_nominal_refinement_v1'):
 inputs=json.loads((C/'tmp'/name/'plan.json').read_text())['input_sha256']
 assert not any(k.startswith('tmp/c09_distance_production_v1/'+s+'/') for k in inputs for s in ('execution','posterior_recovery'))
for name in ('execution','posterior_recovery'):(base/name).rename(saved/name)
out=R/'results/C13/distance_posterior_replay';out.mkdir(exist_ok=False)
def run(worker,label):
 command=[sys.executable,str(R/'scripts/executar_isolado_c13.py'),'--original-root',str(R),'--clean-root',str(C),'--receipt',str(C/'tmp'/('c13_distance_'+label+'_io.json')),worker]
 with (out/(label+'.log')).open('x') as f:code=subprocess.run(command,stdout=f,stderr=subprocess.STDOUT).returncode
 shutil.copy2(C/'tmp'/('c13_distance_'+label+'_io.json'),out/(label+'_io.json'))
 return code
code=run('scripts/executar_producao_distancias_c09.py','likelihood')
r=json.loads((base/'execution/receipt.json').read_text())
assert r['budget']['additional_charged_values']==12145500 and r['budget']['failed_reserved_values']==0
if code:assert r['status']=='FAILED' and 'MemoryError: Production RSS cap' in r['error'],r['error']
arrays=0
for i in range(3):
 with np.load(saved/f'execution/component_{i}.npz') as x,np.load(base/f'execution/component_{i}.npz') as y:
  assert x.files==y.files
  for k in x.files:assert np.array_equal(x[k],y[k]),(i,k);arrays+=1
assert json.loads((saved/'execution/scipy_checks.json').read_text())==json.loads((base/'execution/scipy_checks.json').read_text())
assert run('scripts/integrar_cache_distancias_c09.py','posterior')==0
before=json.loads((saved/'posterior_recovery/posteriors.json').read_text());after=json.loads((base/'posterior_recovery/posteriors.json').read_text());assert len(after)==3000 and before==after
report={'passed':True,'likelihood_values':12145500,'component_arrays_identical':arrays,'scipy_references_identical':13500,'posterior_records_identical':len(after),'original_producer_returncode':code,'original_producer_status':r['status'],'scope':'Distance likelihood components recomputed, then integrated by the original bounded recovery. Existing angular atlas reused; the monolithic producer may reproduce its historical memory-limit stop after saving all components.'}
(out/'comparison.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
