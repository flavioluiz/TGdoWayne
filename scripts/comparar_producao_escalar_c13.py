"""Compare the complete frozen C10 posterior production, never a prefix."""
from pathlib import Path
import argparse,hashlib,json
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--clean-root',type=Path,required=True);a=p.parse_args();root=Path(__file__).resolve().parents[1];r=a.clean_root.resolve();old=r/'tmp/c13_c10_production_published';new=r/'tmp/c10_production_v1'
def read(p):
 d=json.loads(p.read_text());return d.get('payload',d)
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
x=read(old/'complete.json');y=read(new/'complete.json');assert x['targets']==y['targets']==6344
assert x['status']==y['status']=='PRODUCTION_POSTERIORS_COMPLETE_NOT_SCIENTIFIC_SYNTHESIS'
assert x['charged']==x['completed']==y['charged']==y['completed']
operational={'CPU','wall'};assert {k:v for k,v in x.items() if k not in operational}=={k:v for k,v in y.items() if k not in operational}
paths=lambda base:{str(p.relative_to(base)) for folder in ('targets','events','grids') for p in (base/folder).rglob('*') if p.is_file()}|{'plan.json','truth_logL.npy'}
expected=paths(old);assert expected==paths(new)
records=[]
for name in sorted(expected):
 aa=sha(old/name);bb=sha(new/name);assert aa==bb,name
 records.append(dict(path=name,sha256=aa,bytes=(new/name).stat().st_size))
result=dict(passed=True,scope='All C10 production grids, targets, direct-event products and truth densities regenerated and compared byte for byte; complete scientific receipt exact except CPU and wall time.',files=len(records),targets=6344,charged=y['charged'],original_CPU=x['CPU'],reproduced_CPU=y['CPU'],files_verified=records)
(root/'results/C13/scalar_full_production_comparison.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k!='files_verified'}))
