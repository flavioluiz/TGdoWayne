"""Bind the reviewed C10 engineering pilot to the verified C09 prerequisite."""
from pathlib import Path
import hashlib
import json
import subprocess
R = Path(__file__).resolve().parents[1]


def main():
    sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
    specfile = R/'tmp/c10_exact_lifecycle_v1/execution_spec.json'
    spec = json.loads(specfile.read_text())
    for p,h in spec['source_sha256'].items(): assert sha(R/p) == h, p
    release = R/'tmp/publication_v0.9.0/receipt.json'; receipt = json.loads(release.read_text())
    manifest = R/'releases/v0.9.0/manifest.json'; m = json.loads(manifest.read_text())
    commit = subprocess.check_output(['git','rev-parse','v0.9.0^{}'],cwd=R,text=True).strip()
    assert receipt['commit'] == commit and receipt['remote_bytes_equal_local'] and receipt['workflow_success']
    assert sha(R/m['pdf']) == m['pdf_sha256']
    nodal = R/'tmp/c10_ROOT_component/nodal_reuse_review_v1.json'; n = json.loads(nodal.read_text())
    assert n['approved'] and n['nodal_gates_pass'] and not n['interpolation_approved']
    assert sha(R/spec['nodal_table']['path']) == n['table_sha256']
    tests = R/'tmp/c10_lifecycle_review_tests.txt'; log = tests.read_text(); assert 'Ran 11 tests' in log and '\nOK\n' in log
    out = R/'results/C10/pilot_activation'; out.mkdir(parents=True, exist_ok=False)
    prerequisite = dict(approved=True, scope='C09_PREREQUISITE_FOR_C10', commit=commit,
        release_receipt_sha256=sha(release), manifest_sha256=sha(manifest),
        interpretation='C09 delivery published and verified. Its unresolved numerical cases are not approved; C10 has independent response and likelihood controls.')
    preq = out/'C09_prerequisite.json'; preq.write_text(json.dumps(prerequisite, indent=2)+'\n')
    approval = dict(approved=True, stages=['pilot'], spec_sha256=sha(specfile), source_sha256=spec['source_sha256'],
        pilot_CPU_seconds=spec['pilot_CPU_seconds'], maximum_output_bytes=spec['maximum_output_bytes'],
        nodal_receipt_sha256=sha(nodal), prerequisite_receipt_sha256=sha(preq),
        reviewer='ROOT implementation review under user authorization to implement C01-C13',
        checks=['Exact-node lookup rejects absent float.hex coordinates; failed linear interpolation excluded',
            'C=C0+epsilon*C1; one linked scalar mode; proper-CN moments and normalized Gaussian logdet',
            'Truth values, three H levels, SciPy and epsilon0 densities are charged explicitly',
            'Fine, nested and independent product grids retain their data and response identities',
            'Event threshold and measure both widen under response differences; unavailable margins remain unresolved',
            'Shared ledger reserves before work; CPU includes children; outputs and failures are preserved'],
        limits=dict(datasets=16, analyses_per_datum=9, maximum_logL_values=15000000,
            allocated_logL_values=sum(spec['allocations'].values()), maximum_parent_RSS_bytes=spec['maximum_RSS_bytes'],
            maximum_child_RSS_bytes=512*1024**2, historical_ORF_CPU_seconds=spec['historical_ORF_CPU_seconds'],
            inherited_ORF_CPU_cap=600, no_production500_approval=True, no_uniform_physical_certificate=True),
        test_log_sha256=sha(tests), preparer_sha256=sha(Path(__file__)))
    (out/'pilot_review.json').write_text(json.dumps(approval, indent=2)+'\n')
    (out/'test_output.txt').write_bytes(tests.read_bytes())
    print(json.dumps(dict(status='REVIEWED_ENGINEERING_PILOT', allocated_logL_values=sum(spec['allocations'].values()), CPU=spec['pilot_CPU_seconds'])))


if __name__ == '__main__': main()
