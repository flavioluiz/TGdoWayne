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
    out = R/'results/C09/production_reproducibility'
    out.mkdir(parents=True, exist_ok=False)
    sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
    roots = ['c09_nominal_production_v1', 'c09_self_production_v1', 'c09_nominal_refinement_v1',
             'c09_distance_production_v1', 'c09_distance_truth_thresholds_v1', 'c09_sbc_synthesis_v1']
    files = {p for root in roots for p in (R/'tmp'/root).rglob('*') if p.is_file() and '__pycache__' not in p.parts}
    # Follow explicit SHA bindings in current results and the selected campaigns.
    queue = list((R/'results/C09').rglob('*.json'))+[p for p in files if p.suffix == '.json']; seen = set()
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
    pending = [e for name,e in wanted.items() if name not in reused]
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
            for e in entries: z.write(R/e['path'], e['path'])
        assert archive.stat().st_size < 90*1024**2
        with zipfile.ZipFile(archive) as z:
            assert z.testzip() is None
            for e in entries: assert hashlib.sha256(z.read(e['path'])).hexdigest() == e['sha256']
        archives.append(dict(path=str(archive.relative_to(R)), sha256=sha(archive), bytes=archive.stat().st_size, files=entries))
        print(archive.name, len(entries), archive.stat().st_size, flush=True)
    manifest = dict(schema='C09_PRODUCTION_REPRODUCIBILITY_v1', source_sha256=sha(Path(__file__)),
        requested_files=len(wanted), reused_files=[dict(**wanted[n], archive=a) for n,a in sorted(reused.items())],
        reused_archive_sha256=old_archives, archives=archives,
        scope='Selected complete production campaigns and currently matching explicit SHA dependencies; old mismatching snapshots retain their prior archives. No scientific gate is inferred from archival integrity.')
    assert len(reused)+sum(len(a['files']) for a in archives) == len(wanted)
    (out/'manifest.json').write_text(json.dumps(manifest, indent=2)+'\n')
    print(json.dumps(dict(files=len(wanted), reused=len(reused), new_archives=len(archives), new_bytes=sum(a['bytes'] for a in archives))))


if __name__ == '__main__': main()
