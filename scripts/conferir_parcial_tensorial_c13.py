"""Check an explicit completed prefix while the tensorial replay continues."""
from pathlib import Path
import argparse,hashlib,json,sys
import numpy as np
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'src'))
from inference.campaign_io import canonical_hash
p=argparse.ArgumentParser();p.add_argument('--clean-root',type=Path,required=True);p.add_argument('--targets',type=int,required=True);a=p.parse_args()
old=a.clean_root/'tmp/c13_c07_restored/campaign';new=a.clean_root/'tmp/c13_c07_full_reproduction';checks=0;arrays=0
for target in range(a.targets):
 name=f'target_{target:06d}.json'
 rows=[json.loads((r/'proposals'/name).read_text()) for r in (old,new)]
 for row in rows:assert canonical_hash({k:v for k,v in row.items() if k!='proposal_content_hash'})==row['proposal_content_hash']
 assert {k:v for k,v in rows[0].items() if k not in ('em_seconds','training_block_seconds','proposal_content_hash')}=={k:v for k,v in rows[1].items() if k not in ('em_seconds','training_block_seconds','proposal_content_hash')}
 for level in (16384,65536):
  for rep in range(4):
   name=f'target_{target:06d}_N{level}_rep_{rep:02d}.json'
   records=[json.loads((r/'production'/name).read_text()) for r in (old,new)]
   for r,row in zip((old,new),records):assert row['proposal_sha256']==hashlib.sha256((r/'proposals'/f'target_{target:06d}.json').read_bytes()).hexdigest()
   assert {k:v for k,v in records[0].items() if k not in ('proposal_sha256','seconds')}=={k:v for k,v in records[1].items() if k not in ('proposal_sha256','seconds')},name
   name='descriptive_'+name.replace('.json','.npz')
   with np.load(old/'production'/name) as x,np.load(new/'production'/name) as y:
    assert x.files==y.files
    for k in x.files:assert np.array_equal(x[k],y[k]),(name,k);arrays+=1
   checks+=1
result={'passed':True,'completed_prefix_targets':a.targets,'replicate_summaries':checks,'descriptive_arrays_equal':arrays,'scope':'Explicit initial targets only. Proposal content hashes and producer proposal bindings independently verified; excluded fields only execution times and their validated derived proposal hashes. Full campaign and synthesis still require completion.'}
(R/f'results/C13/c07_partial_{a.targets}.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
