"""Recover missing exact SHA-bound inputs from committed ZIP archives."""
from pathlib import Path
import argparse,hashlib,json,zipfile
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,required=True);p.add_argument('--manifest',required=True);p.add_argument('--field',default='bindings');p.add_argument('--receipt',type=Path,required=True);a=p.parse_args();r=a.root.resolve();d=json.loads((r/a.manifest).read_text());need={};recovered=[]
for name,value in d[a.field].items():
 h=value['sha256'] if isinstance(value,dict) else value;p=r/name;assert p.resolve().is_relative_to(r)
 if p.exists():assert hashlib.sha256(p.read_bytes()).hexdigest()==h,name
 else:need[name]=h
for archive in sorted((r/'results').rglob('*.zip')):
 if not need:break
 with zipfile.ZipFile(archive) as z:
  for name in set(z.namelist())&need.keys():
   value=z.read(name)
   if hashlib.sha256(value).hexdigest()!=need[name]:continue
   p=r/name;p.parent.mkdir(parents=True,exist_ok=True)
   with p.open('xb') as f:f.write(value)
   recovered.append(dict(path=name,sha256=need[name],archive=str(archive.relative_to(r)),archive_sha256=hashlib.sha256(archive.read_bytes()).hexdigest()));del need[name]
assert not need,need
with a.receipt.open('x') as f:json.dump(dict(manifest=a.manifest,recovered=recovered),f,indent=2);f.write('\n')
print(json.dumps(dict(recovered=len(recovered))))
