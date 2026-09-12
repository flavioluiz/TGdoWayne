"""Archive current production caches and bound local dependencies, in small ZIPs.

Existing archives are reused only after content-hash comparison. No tmp files
are removed. Each new archive is reopened and every member checked.
"""
from pathlib import Path
import hashlib
import json
import zipfile
R = Path(__file__).resolve().parents[1]


def main():
    out = R/'results/C10/production_reproducibility'
    terminal = json.loads((R/'tmp/c10_production_v1/complete.json').read_text())['payload']
    assert terminal['targets'] == 6344 and terminal['charged'] == terminal['completed']
    assert (R/'results/C10/production_audit/audit.json').is_file()
    assert (R/'results/C10/population_synthesis/results.json').is_file()
    out.mkdir(parents=True, exist_ok=True)
    assert not (out/'manifest.json').exists() and not list(out.glob('production_*.zip'))
    sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
    roots = ['c10_production_v1']
    files = {p for root in roots for p in (R/'tmp'/root).rglob('*') if p.is_file() and '__pycache__' not in p.parts}
    # Follow explicit SHA bindings in current results and the selected campaigns.
    queue = list((R/'results/C10').rglob('*.json'))+[p for p in files if p.suffix == '.json']; seen = set()
    def walk(value):
        if isinstance(value, dict):
            for k,v in value.items():
                if isinstance(k,str) and k.startswith('tmp/') and isinstance(v,str) and len(v) == 64 and all(c in '0123456789abcdef' for c in v):
                    p = R/k
                    if p.is_file() and sha(p) == v:
                        if p not in files and p.suffix == '.json': queue.append(p)
                        files.add(p)
                walk(v)
        elif isinstance(value,list):
            for v in value: walk(v)
    while queue:
        p = queue.pop()
        if p in seen: continue
        seen.add(p); walk(json.loads(p.read_text()))
    wanted = {str(p.relative_to(R)):dict(path=str(p.relative_to(R)), sha256=sha(p), bytes=p.stat().st_size) for p in sorted(files)}
    reused = {}; old_archives = {}
    for archive in sorted((R/'results').rglob('*.zip')):
        if out in archive.parents: continue
        with zipfile.ZipFile(archive) as z:
            candidates = set(z.namelist()) & (set(wanted)-set(reused))
            if not candidates: continue
            for name in sorted(candidates):
                if hashlib.sha256(z.read(name)).hexdigest() == wanted[name]['sha256']:
                    rel = str(archive.relative_to(R)); reused[name] = rel
                    if rel not in old_archives: old_archives[rel] = sha(archive)
    pending = []; chunk_sources = {}; large_files = []
    for name,e in wanted.items():
        if name in reused: continue
        if e['bytes'] <= 75*1024**2: pending.append(e); continue
        chunks = []
        with (R/name).open('rb') as f:
            index = 0
            while payload := f.read(70*1024**2):
                part = name+f'.archivepart{index:03d}'
                entry = dict(path=part, sha256=hashlib.sha256(payload).hexdigest(), bytes=len(payload))
                chunk_sources[part] = (name, index*70*1024**2, len(payload)); chunks.append(part); pending.append(entry); index+=1
        large_files.append(dict(**e, ordered_parts=chunks))
    batches = []; batch = []; size = 0
    for e in pending:
        if e['bytes'] > 75*1024**2: raise ValueError('Individual source exceeds75MiB: '+e['path'])
        if size+e['bytes'] > 75*1024**2 and batch: batches.append(batch); batch=[]; size=0
        batch.append(e); size+=e['bytes']
    if batch: batches.append(batch)
    archives = []
    for i, entries in enumerate(batches):
        archive = out/f'production_{i:02d}.zip'
        with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as z:
            for e in entries:
                if e['path'] in chunk_sources:
                    name, offset, size = chunk_sources[e['path']]
                    with (R/name).open('rb') as f: f.seek(offset); z.writestr(e['path'], f.read(size))
                else: z.write(R/e['path'], e['path'])
        assert archive.stat().st_size < 90*1024**2
        with zipfile.ZipFile(archive) as z:
            assert z.testzip() is None
            for e in entries: assert hashlib.sha256(z.read(e['path'])).hexdigest() == e['sha256']
        archives.append(dict(path=str(archive.relative_to(R)), sha256=sha(archive), bytes=archive.stat().st_size, files=entries))
        print(archive.name, len(entries), archive.stat().st_size, flush=True)
    locations = {e['path']:a['path'] for a in archives for e in a['files']}
    for large in large_files:
        digest = hashlib.sha256()
        for part in large['ordered_parts']:
            with zipfile.ZipFile(R/locations[part]) as z: digest.update(z.read(part))
        assert digest.hexdigest() == large['sha256']
    manifest = dict(schema='C10_PRODUCTION_REPRODUCIBILITY_v1', source_sha256=sha(Path(__file__)), large_files=large_files,
        requested_files=len(wanted), reused_files=[dict(**wanted[n], archive=a) for n,a in sorted(reused.items())],
        reused_archive_sha256=old_archives, archives=archives,
        scope='Selected complete production campaigns and currently matching explicit SHA dependencies; old mismatching snapshots retain their prior archives. No scientific gate is inferred from archival integrity.')
    assert len(reused)+sum(len(a['files']) for a in archives)-sum(len(f['ordered_parts'])-1 for f in large_files) == len(wanted)
    (out/'manifest.json').write_text(json.dumps(manifest, indent=2)+'\n')
    print(json.dumps(dict(files=len(wanted), reused=len(reused), new_archives=len(archives), new_bytes=sum(a['bytes'] for a in archives))))


if __name__ == '__main__': main()
