#!/usr/bin/env python3
"""Preserve the completed six-wave continuation for the C09 milestone."""
from pathlib import Path
import json,hashlib,zipfile
R=Path(__file__).resolve().parents[1];H=R/'tmp/c09_D3_reference_continuation';D=R/'results/C09/D3_distancias_continuacao'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 audit=json.loads((H/'execution/audit.json').read_text());assert audit['status']=='COMPLETED_BUDGET_REFERENCE_PARTIAL' and audit['new_nodes']==2016
 activation=json.loads((H/'execution/activation.json').read_text())
 for rel,h in activation['source_sha256'].items():assert sha(R/rel)==h
 dirs=[H]+[R/f'tmp/c09_D3_distance_reference_v{n}' for n in range(4,10)]
 files=sorted(p for d in dirs for p in d.rglob('*') if p.is_file() and '__pycache__' not in p.parts)
 D.mkdir(parents=True,exist_ok=True);archive=D/'fontes_execucoes.zip';entries=[dict(path=str(p.relative_to(R)),sha256=sha(p),bytes=p.stat().st_size) for p in files]
 with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
  for p in files:z.write(p,p.relative_to(R))
 assert archive.stat().st_size<=90*1024**2
 with zipfile.ZipFile(archive) as z:
  for e in entries:assert hashlib.sha256(z.read(e['path'])).hexdigest()==e['sha256']
 (D/'audit.json').write_text(json.dumps(audit,indent=2)+'\n')
 result=dict(archive=str(archive.relative_to(R)),sha256=sha(archive),bytes=archive.stat().st_size,files=entries,dependencies=['results/C09/D3_distancias_referencia/','results/C09/D3_distancias_iniciais/','results/C09/D3_piloto/'],C09_complete=False)
 (D/'manifest.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k!='files'}))
if __name__=='__main__':main()
