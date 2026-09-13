"""Compare tensorial posterior products and their locally validated bindings.

The default requires a terminal, complete campaign. --prefix is explicitly
partial and cannot produce the final completion receipt.
"""
from pathlib import Path
import argparse
import hashlib
import json
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from inference.campaign_io import canonical_hash


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text())


def without(row, *fields):
    return {k: v for k, v in row.items() if k not in fields}


def compare(clean_root, prefix=None):
    roots = [clean_root / 'tmp/c13_c07_restored/campaign',
             clean_root / 'tmp/c13_c07_full_reproduction']
    count = 2500 if prefix is None else prefix
    assert 0 < count <= 2500
    if prefix is None:
        complete = [read(r / 'campaign_complete.json') for r in roots]
        assert without(complete[0], 'seconds') == without(complete[1], 'seconds')
        assert complete[1]['targets'] == list(range(2500))
        assert complete[1]['ledger']['total'] == 901130000
        assert complete[1]['ledger']['unclosed_reservations'] == 0
    arrays = 0
    for target in range(count):
        name = f'target_{target:06d}.json'
        proposal = [read(r / 'proposals' / name) for r in roots]
        for row in proposal:
            assert canonical_hash(without(row, 'proposal_content_hash')) == row['proposal_content_hash']
        assert without(proposal[0], 'em_seconds', 'training_block_seconds', 'proposal_content_hash') == without(proposal[1], 'em_seconds', 'training_block_seconds', 'proposal_content_hash'), name
        producers = []
        diagnostics = []
        states = []
        for root in roots:
            proposal_hash = sha(root / 'proposals' / name)
            producer = read(root / 'production' / name)
            assert producer['proposal_sha256'] == proposal_hash
            normalized_replicates = []
            assert len(producer['replicates']) == 8
            for row in producer['replicates']:
                repname = f"target_{target:06d}_N{row['level']}_rep_{row['replicate']:02d}"
                assert read(root / 'production' / (repname + '.json')) == row
                assert row['proposal_sha256'] == proposal_hash
                normalized_replicates.append(without(row, 'proposal_sha256', 'seconds'))
            producers.append({**without(producer, 'proposal_sha256', 'replicates'),
                              'replicates': normalized_replicates})
            diagnostic = read(root / 'diagnostics' / ('diagnostic_' + name))
            assert diagnostic['proposal_sha256'] == proposal_hash
            assert diagnostic['diagnostic_inputs']['producer_report_sha256'] == sha(root / 'production' / name)
            assert diagnostic['numeric_sha256'] == sha(root / 'diagnostics' / diagnostic['numeric_file'])
            diagnostics.append({**without(diagnostic, 'proposal_sha256', 'seconds', 'diagnostic_inputs'),
                                'diagnostic_inputs': without(diagnostic['diagnostic_inputs'], 'producer_report_sha256')})
            state = read(root / 'state' / name)
            for artifact in state['artifacts']:
                assert sha(root / artifact['file']) == artifact['sha256'], artifact
            states.append({**without(state, 'artifacts'),
                           'artifact_files': [a['file'] for a in state['artifacts']]})
        assert producers[0] == producers[1], ('producer', target)
        assert diagnostics[0] == diagnostics[1], ('diagnostic', target)
        assert states[0] == states[1], ('state', target)
        npzs = [Path('diagnostics') / f'diagnostic_target_{target:06d}.npz']
        npzs += [Path('production') / f'descriptive_target_{target:06d}_N{level}_rep_{rep:02d}.npz'
                 for level in (16384, 65536) for rep in range(4)]
        for rel in npzs:
            with np.load(roots[0] / rel) as x, np.load(roots[1] / rel) as y:
                assert x.files == y.files
                for key in x.files:
                    numeric = x[key].dtype.kind in 'fc'
                    assert x[key].dtype == y[key].dtype
                    assert np.array_equal(x[key], y[key], equal_nan=numeric), (rel, key)
                    arrays += 1
    return dict(passed=True, full_campaign=prefix is None, targets=count,
                replicate_summaries=8 * count, identical_arrays=arrays,
                scope='Scientific proposal, producer, diagnostics and state fields compared exactly. Execution times excluded; their derived proposal and producer bindings validated locally before comparison. State artifact links and numeric file hashes validated in both roots. Raw sample hashes agree; raw samples already retired by the original archival protocol.',
                terminal_campaign_compared=prefix is None)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--clean-root', type=Path, required=True)
    parser.add_argument('--prefix', type=int)
    args = parser.parse_args()
    result = compare(args.clean_root, args.prefix)
    suffix = 'full' if args.prefix is None else f'prefix_{args.prefix}'
    out = ROOT / f'results/C13/c07_inference_{suffix}_comparison.json'
    out.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result))
