"""Restore archived C09 production paths into an explicit directory.

Run after cloning; defaults to verification without writing. Existing differing
files are never overwritten. Multipart payloads are rejoined before SHA checks.
"""
from pathlib import Path
import argparse
import hashlib
import json
import zipfile
from contextlib import ExitStack
R = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--destination', type=Path, help='Restore under this directory; omission verifies only')
    args = parser.parse_args()
    manifest = json.loads((R/'results/C09/production_reproducibility/manifest.json').read_text())
    sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
    locations = {}; entries = {}; archive_hashes = dict(manifest['reused_archive_sha256'])
    for archive in manifest['archives']:
        archive_hashes[archive['path']] = archive['sha256']
        for e in archive['files']: locations[e['path']] = archive['path']; entries[e['path']] = e
    for e in manifest['reused_files']: locations[e['path']] = e['archive']; entries[e['path']] = e
    for path, digest in archive_hashes.items():
        assert sha(R/path) == digest, path
    parts = {p for e in manifest['large_files'] for p in e['ordered_parts']}
    logical = [e for name,e in entries.items() if name not in parts]+manifest['large_files']
    assert len(logical) == manifest['requested_files']
    count = 0
    with ExitStack() as stack:
      opened = {p:stack.enter_context(zipfile.ZipFile(R/p)) for p in archive_hashes}
      for e in logical:
        name = e['path']; relative = Path(name)
        assert not relative.is_absolute() and '..' not in relative.parts
        payload = bytearray()
        for part in e.get('ordered_parts', [name]):
            value = opened[locations[part]].read(part)
            assert hashlib.sha256(value).hexdigest() == entries[part]['sha256']
            payload.extend(value)
        assert len(payload) == e['bytes'] and hashlib.sha256(payload).hexdigest() == e['sha256'], name
        if args.destination:
            dest = args.destination.resolve()/relative
            assert dest.resolve().is_relative_to(args.destination.resolve())
            if dest.exists(): assert sha(dest) == e['sha256'], 'Refusing to overwrite differing file: '+str(dest)
            else:
                dest.parent.mkdir(parents=True, exist_ok=True)
                with dest.open('xb') as f: f.write(payload)
        count += 1
    print(json.dumps(dict(verified_logical_files=count, verified_archives=len(archive_hashes),
                         restored_to=str(args.destination.resolve()) if args.destination else None)))


if __name__ == '__main__': main()
