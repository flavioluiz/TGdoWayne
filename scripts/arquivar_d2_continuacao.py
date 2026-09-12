#!/usr/bin/env python3
"""Preserva resultados, fontes e falhas das continuações D2, sem física nova."""
import hashlib
import json
from pathlib import Path
import shutil
import zipfile
ROOT=Path(__file__).resolve().parents[1]
DEST=ROOT/'results/C09/D2_continuacao'


def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()


def main():
    audit=json.loads((ROOT/'tmp/c09_D2_continuation_v3/result_audit.json').read_text())
    assert audit['completed_analyses']==audit['primary_passed']==40
    assert audit['execution_status']=='COMPLETED' and not audit['missing_or_incomplete_curves']
    files=[]
    for version in (1,2,3):
        for stem in ('c09_D2_continuation_v','c09_D2_continuation_execution_v'):
            files.extend(p for p in (ROOT/'tmp'/f'{stem}{version}').rglob('*')
                         if p.is_file() and '__pycache__' not in p.parts and p.name!='.DS_Store')
    files.extend(ROOT/'tmp'/p for p in ['c09_D2_continuation_audit_v2.py',
        'c09_D2_continuation_audit_v3.py','c09_D2_paired_summary_v3.py',
        'c09_D2_test_all_recovered_v3.py','c09_D2_all_recovered_v3.json'])
    files=sorted(set(files));DEST.mkdir(parents=True,exist_ok=True)
    entries=[dict(path=str(p.relative_to(ROOT)),bytes=p.stat().st_size,sha256=sha(p)) for p in files]
    archive=DEST/'fontes_execucoes_e_referencias.zip'
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for p in files:z.write(p,p.relative_to(ROOT))
    with zipfile.ZipFile(archive) as z:
        for entry in entries:assert hashlib.sha256(z.read(entry['path'])).hexdigest()==entry['sha256']
    for source,target in [('result_audit.json','audit.json'),('paired_summary.json','contrastes_pareados.json')]:
        shutil.copyfile(ROOT/'tmp/c09_D2_continuation_v3'/source,DEST/target)
    ends=[]
    for version in (1,2,3):
        source=ROOT/f'tmp/c09_D2_continuation_execution_v{version}/execution_end.json'
        ends.append(json.loads(source.read_text()));shutil.copyfile(source,DEST/f'execution_end_v{version}.json')
    counts=sum(e['observed_value_counts']['additional_charged_values'] for e in ends)
    cpu=sum(e['measured_stage_CPU_seconds'] for e in ends)
    assert counts==40875 and abs(cpu-223.279596)<1e-8
    manifest=dict(archive=str(archive.relative_to(ROOT)),archive_sha256=sha(archive),
        archive_bytes=archive.stat().st_size,files=entries,members_verified=len(entries),
        additional_values_since_v086=counts,additional_CPU_since_v086=cpu,
        original_reservation_values=100000,original_reservation_CPU=480.,
        dependencies='Published v0.8.5 snapshot, v0.8.6 D2 archive and bound C06-C08 inputs; historical local paths retained.')
    (DEST/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps({k:v for k,v in manifest.items() if k!='files'},indent=2))


if __name__=='__main__':main()
