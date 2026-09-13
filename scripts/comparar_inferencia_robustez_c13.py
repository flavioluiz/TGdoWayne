"""Compare every nominal/self-control/refined C09 posterior and saved likelihood array."""
from pathlib import Path
import argparse,json,hashlib
import numpy as np
R=Path(__file__).resolve().parents[1];p=argparse.ArgumentParser();p.add_argument('--clean-root',type=Path,required=True);a=p.parse_args();C=a.clean_root
base=C/'tmp/c13_c09_nominal_reproduction';run=json.loads((base/'reproduction.json').read_text());assert run['status']=='complete' and len(run['completed'])==24
rows=0;arrays=0;files=0;entries=[]
for job in run['jobs']:
 old=C/'tmp'/job['campaign']/'execution'/job['job'];new=base/job['job']
 x=json.loads((old/'posteriors.json').read_text());y=json.loads((new/'posteriors.json').read_text());assert x==y,job['job'];assert len(x)==job['curves'];rows+=len(x)
 oldfiles={p.relative_to(old) for p in old.rglob('*.npz')};newfiles={p.relative_to(new) for p in new.rglob('*.npz')};assert oldfiles==newfiles,(job['job'],oldfiles^newfiles)
 for rel in oldfiles:
  with np.load(old/rel) as x,np.load(new/rel) as y:
   assert set(x.files)==set(y.files)
   for k in x.files:assert np.array_equal(x[k],y[k]),(job['job'],str(rel),k);arrays+=1
  files+=1
 entries.append({'job':job['job'],'posteriors':job['curves'],'posterior_sha256':hashlib.sha256((new/'posteriors.json').read_bytes()).hexdigest()})
assert rows==22957
report={'passed':True,'jobs':24,'posterior_records_identical_including_replacement':rows,'unique_posteriors':22956,'npz_files':files,'arrays_identical':arrays,'entries':entries,'scope':'All nominal and self-control likelihood products and posterior records, including one refined replacement. Distance mixture is separate.'}
(R/'results/C13/c09_nominal_inference_comparison.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k!='entries'}))
