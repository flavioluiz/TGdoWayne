"""Export a committed scientific baseline and restore C11 inputs in a fresh directory.

This prepares an isolated reproduction; successful restoration alone does not
validate the science. The dissertation edits are not exported from the worktree.
"""
from pathlib import Path
import argparse, hashlib, json, subprocess, sys, time

ROOT = Path(__file__).resolve().parents[1]

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--destination', type=Path, required=True)
    parser.add_argument('--revision', default='v0.12.0')
    args = parser.parse_args()
    dest = args.destination.resolve()
    if dest.exists():
        raise SystemExit('Destination must not exist; no automatic overwrite or continuation.')
    revision = subprocess.check_output(['git', 'rev-parse', args.revision+'^{commit}'], cwd=ROOT, text=True).strip()
    dest.mkdir(parents=True)
    start = time.monotonic()
    archive = subprocess.Popen(['git', 'archive', '--format=tar', revision], cwd=ROOT, stdout=subprocess.PIPE)
    with archive.stdout:
        extracted = subprocess.run(['tar', '-xf', '-', '-C', str(dest)], stdin=archive.stdout)
    if archive.wait() != 0 or extracted.returncode != 0:
        raise RuntimeError('Committed export failed; retain directory for diagnosis.')
    print(json.dumps({'exported_commit': revision, 'destination': str(dest)}), flush=True)
    with (dest/'c13_restore_c11.log').open('x') as log:
        restored = subprocess.run([sys.executable, str(dest/'scripts/restaurar_c11.py'), '--destination', str(dest)], cwd=dest, stdout=log, stderr=subprocess.STDOUT)
    if restored.returncode:
        raise RuntimeError('C11 restoration failed; inspect retained log.')
    # Completion commits can update prose that a prospective numerical manifest
    # bound before execution. Recover only a byte-identical committed ancestor.
    bindings = json.loads((dest/'tmp/c11_pilot16_candidate_v2/manifest.json').read_text())['bindings']
    historical = []
    for relative, expected in bindings.items():
        path = dest/relative
        if path.exists() and hashlib.sha256(path.read_bytes()).hexdigest() == expected['sha256']:
            continue
        found = False
        revisions = subprocess.check_output(['git','log','--format=%H',revision,'--',relative], cwd=ROOT, text=True).splitlines()
        for commit in revisions:
            value = subprocess.run(['git','show',commit+':'+relative], cwd=ROOT, capture_output=True)
            if value.returncode == 0 and hashlib.sha256(value.stdout).hexdigest() == expected['sha256']:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(value.stdout)
                historical.append(dict(path=relative, source_commit=commit, sha256=expected['sha256']))
                found = True
                break
        if not found:
            raise RuntimeError('No exact committed source for frozen binding: '+relative)
    record = dict(baseline_commit=revision, original_root=str(ROOT), clean_root=str(dest),
                  historical_bindings_restored=historical, restored=json.loads((dest/'c13_restore_c11.log').read_text()),
                  wall_seconds=time.monotonic()-start, python=sys.executable,
                  preparation_source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                  science_reproduced=False)
    (dest/'c13_preparation.json').write_text(json.dumps(record, indent=2)+'\n')
    (ROOT/'results/C13/clean_preparation.json').write_text(json.dumps(record, indent=2)+'\n')
    print(json.dumps(record), flush=True)

if __name__ == '__main__':
    main()
