"""Compare every C08 window worker product after the unchanged physical replay."""
import argparse,hashlib,json
from pathlib import Path
import numpy as np
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--clean-root',type=Path,required=True);a=p.parse_args();r=a.clean_root.resolve();root=Path(__file__).resolve().parents[1]
old=r/'tmp/c08_window_map_v1';new=r/'tmp/c13_window_physical';original=json.loads((old/'complete.json').read_text());replay=json.loads((new/'complete.json').read_text());assert replay['status']==original['status']=='FINITE_DISTRIBUTIONAL_MAP_GATES_PASS_NOT_POSTERIORS'
assert len(original['workers'])==len(replay['workers'])==43
runtime={'CPU_seconds','wall_seconds','RSS_peak_bytes','child_CPU_seconds_including_startup'}
rows=[];array_count=0
for record in original['workers']:
 name=record['name'];x=json.loads((old/name/'report.json').read_text());y=json.loads((new/name/'report.json').read_text())
 assert {k:v for k,v in x.items() if k not in runtime}=={k:v for k,v in y.items() if k not in runtime},name
 row=dict(worker=name,scientific_report_exact=True)
 if 'arrays_sha256' in record:
  aa=old/name/'arrays.npz';bb=new/name/'arrays.npz'
  with np.load(aa,allow_pickle=False) as u,np.load(bb,allow_pickle=False) as v:
   assert u.files==v.files
   for key in u.files:assert np.array_equal(u[key],v[key],equal_nan=True),(name,key);array_count+=1
  row.update(original_sha256=hashlib.sha256(aa.read_bytes()).hexdigest(),reproduced_sha256=hashlib.sha256(bb.read_bytes()).hexdigest(),arrays_exact=True)
 rows.append(row)
for file in old.glob('harmonic_gate_*.json'):assert json.loads(file.read_text())==json.loads((new/file.name).read_text())
result=dict(passed=True,workers=43,arrays=array_count,comparison=rows,ignored_operational_fields=sorted(runtime),original_resources=original['resources'],reproduced_resources=replay['resources'],scope='Unchanged C08 physical controller and all workers executed in clean root with original resource limits. Scientific JSON values and arrays exactly compared. No posterior inference in this map.')
(root/'results/C13/window_physical_comparison.json').write_text(json.dumps(result,indent=2)+'\n')
# Restore later modules only after the physical campaign has terminated and compared.
p=root/'results/C13/window_namespace_adjustment.json';d=json.loads(p.read_text())
for row in d['files']:
 source=r/row['temporary_destination'];target=r/row['path'];assert hashlib.sha256(source.read_bytes()).hexdigest()==row['sha256'];assert not target.exists();source.rename(target)
d['restored_after_successful_replay']=True;p.write_text(json.dumps(d,indent=2)+'\n')
print(json.dumps(dict(passed=True,workers=43,arrays=array_count)))
