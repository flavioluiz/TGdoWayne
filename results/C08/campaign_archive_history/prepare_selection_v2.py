"""Explicit metadata-only selection of completed engineering/main C08 products."""
from pathlib import Path
import hashlib
import json

ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text())


def main():
    campaigns=[]
    for p in sorted((ROOT/'tmp/c08_posterior_campaign').glob('*/C08/*/*/campaign_complete.json')):
        c=read(p);phase=c['phase'];variant=c['response_variant']
        review=ROOT/('tmp/c08_engineering_ROOT/result_review.json' if phase=='engineering' else f'tmp/c08_main_ROOT/{variant}_result_review.json')
        campaigns.append(dict(path=p.parent.relative_to(ROOT).as_posix(),completion_sha256=sha(p),root_review=dict(path=review.relative_to(ROOT).as_posix(),sha256=sha(review))))
    assert len(campaigns)==4
    roots=['tmp/c08_engineering_ROOT','tmp/c08_main_ROOT','tmp/c08_runtime_design','tmp/c08_runtime_bindings_v2',
        'tmp/c08_driver_design','tmp/c08_driver_independent_review','tmp/c08_truth_diagnostic_runner',
        'tmp/c08_truth_diagnostic_execution_v1','tmp/c08_truth_ROOT_review','tmp/c08_G0',
        'tmp/c08_main_quantile_driver_v1','tmp/c08_main_quantile_review_v1','tmp/c08_quantile_replay_design',
        'src/inference','src/pta','configs/calibration','scripts/run_calibration_campaign.py',
        'tmp/native/c586a0637ce30e440b8a5235/build_manifest.json',
        'results/C08/table_publication_copy.json','tmp/c08_domain_review',
        'tmp/c08_runtime_inputs/finite_evidence_aggregate.json',
        'results/C07/data500_independent_review/review.json']
    tablecopy=read(ROOT/'results/C08/table_publication_copy.json')
    deps=[]
    for r in tablecopy['files']:
        if '/payload.gz.part' in r['source']:
            deps.append(dict(path=r['destination'],sha256=r['sha256'],bytes=r['bytes'],role='C08_existing_compressed_table_part'))
        else:
            roots.append(r['source'])
    reconstructed=[]
    for variant in ['C_beta','C_full']:
        p=ROOT/f'results/C08/orf_tables/{variant}_parts/manifest.json'
        deps.append(dict(path=p.relative_to(ROOT).as_posix(),sha256=sha(p),role='C08_existing_table_transport_manifest'))
        transport=read(p)
        reconstructed.append(dict(path=('tmp/c08_beta_table_v2_continuation/results/C_beta_common_table.npz' if variant=='C_beta' else 'tmp/c08_full_local_v2_execution/results/C_full_table.npz'),
            sha256=transport['original_sha256'],bytes=transport['original_bytes'],transport_manifest=p.relative_to(ROOT).as_posix(),
            transport_manifest_sha256=sha(p),decompressed_bytes_included=False))
    for name in ['results/C07/prior_predictive/data.npz','results/C07/prior_predictive/generation.json',
        'results/C07/fixtures/pilot_data.npz','tmp/native/c586a0637ce30e440b8a5235/libpta_likelihood.dylib']:
        p=ROOT/name;deps.append(dict(path=name,sha256=sha(p),bytes=p.stat().st_size,role='Existing_C07_runtime_dependency'))
    # Include each selected root only once; a subtree already included elsewhere
    # is represented by its parent. This is path coverage, not SHA deduplication.
    roots=sorted(set(roots));roots=[n for n in roots if not any(n.startswith(p+'/') for p in roots if p!=n)]
    spec=dict(schema='C08_ARCHIVE_SELECTION_v1',original_repository_prefix=str(ROOT),campaigns=campaigns,include=roots,
        external_dependencies=deps,reconstructed_dependencies=reconstructed,
        selection_scope='Four completed engineering/main variant campaigns and exact historical source/evidence packages',
        exclusion_policy='No raw arrays, decompressed response tables, active replay or active finite-domain execution.',
        deferred=[dict(path='tmp/c08_required_high_replay_with_kl_v1',reason='Separate completion plus ROOT result review required before new selection.'),
            dict(path='tmp/c08_finite_ROOT',reason='Finite-response stage active; not selected.')],
        table_restoration='Use existing results/C08/orf_tables/{C_beta,C_full}_parts and their compactar_arquivo.py. No respline, conversion or float rewrite.',
        does_not_claim_full_historical_quadrature_reexecution=True,new_physics_calls=0)
    with (HERE/'selection_engineering_main_v2.json').open('x') as f:json.dump(spec,f,indent=2);f.write('\n')
    print(json.dumps(dict(campaigns=len(campaigns),source_roots=len(roots),external_dependencies=len(deps),selection_sha256=sha(HERE/'selection_engineering_main_v2.json'))))


if __name__=='__main__':main()
