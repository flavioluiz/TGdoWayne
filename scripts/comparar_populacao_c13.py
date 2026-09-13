"""Compare every regenerated C11 NPZ array and RNG state against the archived run."""
from pathlib import Path
import argparse,hashlib,json
import numpy as np
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--reference',type=Path,required=True);p.add_argument('--reproduced',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
a=p.parse_args();reference=a.reference.resolve();reproduced=a.reproduced.resolve()
end=json.loads((reproduced/'execution_end.json').read_text());old=json.loads((reference/'execution_end.json').read_text())
assert end['execution_passed'] is True and end['counts']==old['counts']
refpaths={p.relative_to(reference) for p in reference.rglob('*.npz')}
newpaths={p.relative_to(reproduced) for p in reproduced.rglob('*.npz')}
assert refpaths==newpaths, (len(refpaths),len(newpaths),sorted(refpaths^newpaths)[:10])
records=[];arrays=0;maximum=0.;not_identical=0
for relative in sorted(refpaths):
 with np.load(reference/relative,allow_pickle=False) as ref,np.load(reproduced/relative,allow_pickle=False) as new:
  assert set(ref.files)==set(new.files)
  for key in ref.files:
   x=ref[key];y=new[key];assert x.shape==y.shape and x.dtype==y.dtype
   if np.issubdtype(x.dtype,np.number):
    assert np.isfinite(x).all() and np.isfinite(y).all()
    delta=float(np.max(np.abs(x-y))) if x.size else 0.
    scale=max(1.,float(np.max(np.abs(x)))) if x.size else 1.
    scaled=delta/scale;maximum=max(maximum,scaled)
    assert scaled<=1e-12,(str(relative),key,scaled)
   else:assert np.array_equal(x,y)
   not_identical+=not np.array_equal(x,y);arrays+=1
 records.append({'path':str(relative),'reference_sha256':hashlib.sha256((reference/relative).read_bytes()).hexdigest(),'reproduced_sha256':hashlib.sha256((reproduced/relative).read_bytes()).hexdigest()})
rng=[]
for original in sorted(reference.rglob('*rng*.json')):
 relative=original.relative_to(reference);assert json.loads(original.read_text())==json.loads((reproduced/relative).read_text());rng.append(str(relative))
report=dict(passed=True,reference=str(reference),reproduced=str(reproduced),counts=end['counts'],npz_files=len(records),arrays=arrays,arrays_not_bitwise_identical=not_identical,maximum_scaled_absolute_error=maximum,tolerance=1e-12,random_state_files=rng,files=records,scope='Complete regenerated NPZ population products and recorded RNG states; posterior synthesis checked separately.')
a.output.parent.mkdir(parents=True,exist_ok=True)
with a.output.open('x') as f:json.dump(report,f,indent=2);f.write('\n')
print(json.dumps({k:v for k,v in report.items() if k not in ('files','random_state_files')}))
