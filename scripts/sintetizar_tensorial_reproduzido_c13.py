"""Repeat the original synthesis after verified completion of tensorial replay."""
from pathlib import Path
import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import numpy as np

ROOT = Path(__file__).resolve().parents[1]

def read(p):
    return json.loads(p.read_text())

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def main(clean):
    proof = read(ROOT / 'results/C13/c07_inference_full_comparison.json')
    assert proof['passed'] and proof['full_campaign'] and proof['targets'] == 2500
    campaign = clean / 'tmp/c13_c07_full_reproduction'
    terminal = read(campaign / 'campaign_complete.json')
    assert terminal['targets'] == list(range(2500))
    assert terminal['ledger']['total'] == 901130000
    replay = clean / 'tmp/c13_c07_fresh_synthesis'
    assert not replay.exists(), 'Existing synthesis must be inspected, never silently replaced.'
    previous_io = read(ROOT / 'results/C13/c07_synthesis_io.json')
    args = [v.replace('tmp/c13_c07_restored/campaign', 'tmp/c13_c07_full_reproduction')
            .replace('tmp/c13_c07_synthesis', 'tmp/c13_c07_fresh_synthesis')
            for v in previous_io['arguments']]
    receipt = clean / 'tmp/c13_c07_fresh_synthesis_io.json'
    command = [sys.executable, str(ROOT / 'scripts/executar_isolado_c13.py'),
               '--original-root', str(ROOT), '--clean-root', str(clean),
               '--receipt', str(receipt), previous_io['worker'], *args]
    with (ROOT / 'tmp/c13_c07_fresh_synthesis.log').open('x') as log:
        subprocess.run(command, check=True, stdout=log, stderr=subprocess.STDOUT)
    shutil.copy2(receipt, ROOT / 'results/C13/c07_fresh_synthesis_io.json')
    reference = clean / 'results/C07/synthesis'
    old_campaign = clean / 'tmp/c13_c07_restored/campaign'
    old = read(reference / 'summary.json')
    new = read(replay / 'summary.json')
    for report, folder in [(old, old_campaign), (new, campaign)]:
        inventory = report['provenance']['inventory']
        assert [row['target'] for row in inventory] == list(range(2500))
        for row in inventory:
            stem = f"target_{row['target']:06d}"
            for field, rel in [
                ('diagnostic_sha256', f'diagnostics/diagnostic_{stem}.json'),
                ('numeric_sha256', f'diagnostics/diagnostic_{stem}.npz'),
                ('producer_sha256', f'production/{stem}.json')]:
                assert row[field] == sha(folder / rel), (field, stem)
            # These two files contain timing-derived bindings. Their full
            # scientific contents were compared by the required full proof.
            del row['diagnostic_sha256']
            del row['producer_sha256']
    def norm(value):
        if isinstance(value, dict):
            return {norm(k): norm(v) for k, v in value.items()}
        if isinstance(value, list):
            return [norm(v) for v in value]
        if isinstance(value, str) and value.startswith(str(ROOT) + '/'):
            return str(clean) + value[len(str(ROOT)):]
        return value
    assert norm(old) == new, 'Scientific synthesis differs.'
    count = 0
    for folder in (reference, replay):
        assert read(folder / 'summary.json')['arrays_sha256'] == sha(folder / 'arrays.npz')
    with np.load(reference / 'arrays.npz') as x, np.load(replay / 'arrays.npz') as y:
        assert x.files == y.files
        for key in x.files:
            assert np.array_equal(x[key], y[key], equal_nan=x[key].dtype.kind in 'fc'), key
            count += 1
    for name in ('tests.csv', 'paired_central90.csv'):
        assert (reference / name).read_bytes() == (replay / name).read_bytes()
    result = dict(passed=True, targets=2500, tests=len(new['tests']),
                  paired_tests=len(new['paired_central90']), identical_arrays=count,
                  reference_sha256=sha(reference / 'summary.json'),
                  reproduced_sha256=sha(replay / 'summary.json'),
                  full_inference_proof_sha256=sha(ROOT / 'results/C13/c07_inference_full_comparison.json'),
                  scope='Fresh original synthesis from all regenerated posterior diagnostics. Scientific JSON, numeric arrays and CSVs agree; local provenance bindings independently verified before normalizing timing-derived producer/diagnostic hashes and relocated source paths.')
    (ROOT / 'results/C13/c07_fresh_synthesis_comparison.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result))

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--clean-root', type=Path, required=True)
    main(parser.parse_args().clean_root.resolve())
