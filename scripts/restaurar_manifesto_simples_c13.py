"""Restore a manifest of non-multipart ZIP members, verifying all stored hashes."""
from pathlib import Path
import argparse,hashlib,json,zipfile
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,required=True);p.add_argument('--manifest',required=True);p.add_argument('--receipt',type=Path,required=True);a=p.parse_args();root=a.root.resolve();manifest=root/a.manifest
if a.receipt.exists():raise ValueError('Fresh receipt required')
d=json.loads(manifest.read_text());count=0;new=0
for archive in d['archives']:
 path=root/archive['path'];assert hashlib.sha256(path.read_bytes()).hexdigest()==archive['sha256']
 with zipfile.ZipFile(path) as z:
  for f in archive['files']:
   dest=root/f['path'];assert dest.resolve().is_relative_to(root)
   data=z.read(f['path']);assert len(data)==f['bytes'] and hashlib.sha256(data).hexdigest()==f['sha256']
   if dest.exists():assert dest.read_bytes()==data,str(dest)
   else:
    dest.parent.mkdir(parents=True,exist_ok=True)
    with dest.open('xb') as out:out.write(data)
    new+=1
   count+=1
result=dict(manifest=a.manifest,manifest_sha256=hashlib.sha256(manifest.read_bytes()).hexdigest(),verified_files=count,new_files_restored=new,archives=len(d['archives']))
a.receipt.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
