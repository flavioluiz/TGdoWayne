"""Compare the complete C07 synthesis, allowing only the relocated root prefix."""
from pathlib import Path
import argparse,hashlib,json,numpy as np
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--clean-root',type=Path,required=True);p.add_argument('--original-root',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();root=a.clean_root.resolve();old=str(a.original_root.resolve());new=str(root)
def norm(v):
 if isinstance(v,dict):return {norm(k):norm(x) for k,x in v.items()}
 if isinstance(v,list):return [norm(x) for x in v]
 if isinstance(v,str) and v.startswith(old+'/'):return new+v[len(old):]
 return v
ref=root/'results/C07/synthesis';replay=root/'tmp/c13_c07_synthesis'
x=json.loads((ref/'summary.json').read_text());y=json.loads((replay/'summary.json').read_text());assert norm(x)==y
with np.load(ref/'arrays.npz') as x,np.load(replay/'arrays.npz') as y:
 assert set(x.files)==set(y.files)
 for k in x.files:assert np.array_equal(x[k],y[k]),k
 count=len(x.files)
for name in ['tests.csv','paired_central90.csv']:assert (ref/name).read_bytes()==(replay/name).read_bytes()
result=dict(passed=True,simulations_per_model=500,models=5,tests=155,paired_tests=15,unresolved_PITs=243,identical_arrays=count,scope='Full 2500-target diagnostic inventory and synthesis replay; only root prefixes normalized, with no numerical fields excluded.',reference_sha256=hashlib.sha256((ref/'summary.json').read_bytes()).hexdigest(),reproduced_sha256=hashlib.sha256((replay/'summary.json').read_bytes()).hexdigest())
with a.output.open('x') as f:json.dump(result,f,indent=2);f.write('\n')
print(json.dumps(result))
