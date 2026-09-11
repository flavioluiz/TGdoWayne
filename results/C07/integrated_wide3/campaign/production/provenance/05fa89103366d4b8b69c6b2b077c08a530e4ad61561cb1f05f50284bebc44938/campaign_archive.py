"""Reproducible target archives authorize raw retirement, not scientific approval."""
from pathlib import Path
from .campaign_io import read_json, sha256, write_json_new, verify_record, atomic_new, positive_int


def prepare_archive(runtime, target, proposal_root, output_root, diagnostic_path, *, resume=False):
    """Preserve complete numerical failures as well as passes before retiring raw."""
    target=positive_int(target,'target',True);output=Path(output_root)
    production=verify_record(output/f'target_{target:06d}.json',runtime.identity,status='IID_COMPLETE_AWAITING_DIAGNOSTICS')
    diagnostic=verify_record(diagnostic_path,runtime.identity,status='NUMERICAL_DIAGNOSTICS_COMPLETE')
    if diagnostic['target']!=target or diagnostic.get('raw_release_authorized') is not False:
        raise RuntimeError('A separate complete numerical diagnostic of this target is required.')
    raw_hashes={r['raw_file']:r['raw_sha256'] for r in production['replicates']}
    if diagnostic['raw_sha256']!=raw_hashes:raise RuntimeError('Diagnostic/raw identities differ.')
    numeric=Path(diagnostic_path).parent/diagnostic['numeric_file']
    if Path(diagnostic['numeric_file']).name!=diagnostic['numeric_file'] or sha256(numeric)!=diagnostic['numeric_sha256']:
        raise RuntimeError('Compact numeric diagnostic integrity failed.')
    proposal=Path(proposal_root)/f'target_{target:06d}.json'
    if sha256(proposal)!=production['proposal_sha256']:raise RuntimeError('Frozen proposal integrity failed.')
    sources=[('producer',output/f'target_{target:06d}.json'),('diagnostic',Path(diagnostic_path)),('numeric',numeric),('proposal',proposal)]
    for row in production['replicates']:
        checkpoint=output/f'target_{target:06d}_N{row["level"]}_rep_{row["replicate"]:02d}.json'
        check=verify_record(checkpoint,runtime.identity,status='IID_REPLICATE_COMPLETE')
        if check!=row or not all(k in check for k in ('rng_recipe','rng_state_before','rng_state_after','seed','proposal_sha256')):
            raise RuntimeError('Checkpoint/RNG recipe differs from the completed production record.')
        sources.append((f'checkpoint_N{row["level"]}_rep{row["replicate"]}',checkpoint))
    for name in ('experiment','settings','validation_config','table_manifest','native_build_manifest'):
        if name in runtime.paths:sources.append(('input_'+name,runtime.paths[name]))
    destination=output/f'archive_target_{target:06d}';artifacts=[]
    for role,source in sources:
        digest=sha256(source);saved=destination/(role+source.suffix)
        if saved.exists():
            if not resume or sha256(saved)!=digest:raise RuntimeError('Archive collision or changed artifact: '+role)
        else:atomic_new(saved,lambda path,source=source:path.write_bytes(source.read_bytes()))
        artifacts.append(dict(role=role,file=str(saved.relative_to(output)),sha256=digest,bytes=saved.stat().st_size))
    summary=diagnostic['summary'];numerical_flags={k:summary[k] for k in ('cdf_precision_pass','pooled_weight_guard_pass','saturation_guard_pass','replication_pass','refinement_pass')}
    precision_state='RECORDED_NUMERICAL_CHECKS_PASSED' if all(v is True for v in numerical_flags.values()) else 'NUMERICALLY_UNRESOLVED'
    receipt=dict(status='RAW_ARCHIVE_VERIFIED',archive_scope='reproducible_target_summary',identity=runtime.identity,target=target,datum=production['datum'],model=production['model'],raw_sha256=raw_hashes,artifacts=artifacts,numerical_status=precision_state,numerical_flags=numerical_flags,all_indicators_and_failures_retained=True,no_scientific_calibration_claim=True,reason='Retire reproducible temporary raw after complete diagnostics; retain this target even if numerical checks fail.',input_sha256=production['input_sha256'],source_provenance_identity=runtime.identity)
    path=output/f'archive_receipt_target_{target:06d}.json'
    if path.exists():
        if not resume or read_json(path)!=receipt:raise RuntimeError('Archive receipt changed.')
    else:write_json_new(path,receipt)
    return receipt


def verify_archive_receipt(path, output_root, identity, target, raw_hashes):
    receipt=verify_record(path,identity,status='RAW_ARCHIVE_VERIFIED')
    if receipt.get('archive_scope')!='reproducible_target_summary' or receipt.get('target')!=target or receipt.get('raw_sha256')!=raw_hashes or receipt.get('all_indicators_and_failures_retained') is not True or receipt.get('no_scientific_calibration_claim') is not True:
        raise RuntimeError('Complete target-preserving archive receipt required.')
    if receipt.get('numerical_status') not in ('RECORDED_NUMERICAL_CHECKS_PASSED','NUMERICALLY_UNRESOLVED'):
        raise RuntimeError('Numerical state must remain explicit.')
    roles=[];output=Path(output_root).resolve()
    for artifact in receipt.get('artifacts',[]):
        relative=Path(artifact['file']);path=(output/relative).resolve()
        if relative.is_absolute() or output not in path.parents or not path.is_file() or sha256(path)!=artifact['sha256']:
            raise RuntimeError('Preserved archive artifact missing or changed.')
        roles.append(artifact['role'])
    if len(roles)!=len(set(roles)) or not {'producer','diagnostic','numeric','proposal'}.issubset(roles) or sum(r.startswith('checkpoint_') for r in roles)!=8:
        raise RuntimeError('Archive does not preserve the diagnostic/proposal/eight RNG checkpoints.')
    return receipt
