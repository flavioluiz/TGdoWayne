"""Compare all C11 posterior records and statistical conclusions after full replay."""
from pathlib import Path
import argparse,hashlib,json
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--reference',type=Path,required=True);p.add_argument('--reproduced',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
def read(path):return json.loads(path.read_text())
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
r=a.reference.resolve();n=a.reproduced.resolve();old=read(r/'synthesis.json');new=read(n/'synthesis.json')
assert new['posterior_targets']==old['posterior_targets']==10728
refnames={q.name for q in r.glob('*.json')};newnames={q.name for q in n.glob('*.json')};assert refnames==newnames
files=[];targets=0
for name in sorted(refnames-{'synthesis.json'}):
 x=read(r/name);y=read(n/name)
 # Input files themselves must have the same hash, not only similar arrays.
 assert x==y,name
 assert [v['id'] for v in y['rows']]==list(range(596))
 targets+=len(y['rows']);files.append(dict(path=name,reference_sha256=sha(r/name),reproduced_sha256=sha(n/name)))
assert targets==10728 and len(files)==18
excluded={'products','production_end_sha256','wall_seconds','source_sha256'}
assert old.keys()==new.keys()
assert len(old['source_sha256'])==len(new['source_sha256'])==2
def sources(v):return {str(Path(k).relative_to(Path(k).parents[2])):h for k,h in v.items()}
assert sources(old['source_sha256'])==sources(new['source_sha256'])
for key in old.keys()-excluded:assert old[key]==new[key],key
assert len(old['products'])==len(new['products'])==18
for x,y in zip(old['products'],new['products']):
 assert x.keys()==y.keys()
 for key in x.keys()-{'path'}:assert x[key]==y[key],(x['model'],key)
 assert Path(x['path']).name==Path(y['path']).name
result=dict(passed=True,posterior_targets=targets,model_products=18,comparison='Exact equality of all posterior JSON values, input hashes, SBC families and recovery statistics',provenance_differences_allowed=['output directory in product paths','root directory in source paths (source hashes must match)','production receipt hash (resource cap and output paths)','elapsed wall time'],files=files,reference_summary_sha256=sha(r/'synthesis.json'),reproduced_summary_sha256=sha(n/'synthesis.json'))
a.output.parent.mkdir(parents=True,exist_ok=True)
with a.output.open('x') as f:json.dump(result,f,indent=2);f.write('\n')
print(json.dumps({k:v for k,v in result.items() if k!='files'}))
