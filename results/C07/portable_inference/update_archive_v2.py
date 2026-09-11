from pathlib import Path
p=Path('tmp/c07_inference_portable/src/inference/campaign_iid.py');s=p.read_text();s=s[:s.index('\ndef release_raw(')]+'''
def release_raw(runtime,target,output_root,raw_root,diagnostic_path,*,resume=False):
 """Retire hashed raw only after an integrity receipt; keep failed targets intact."""
 from .campaign_archive import verify_archive_receipt
 target=positive_int(target,'target',True);out=Path(output_root);raw=Path(raw_root)
 record=verify_record(out/f'target_{target:06d}.json',runtime.identity,status='IID_COMPLETE_AWAITING_DIAGNOSTICS')
 required={rep['raw_file']:rep['raw_sha256'] for rep in record['replicates']}
 receipt=verify_archive_receipt(diagnostic_path,out,runtime.identity,target,required)
 intent=out/f'release_intent_target_{target:06d}.json';done=out/f'released_target_{target:06d}.json';digest=sha256(diagnostic_path)
 if done.exists():
  if not resume:raise FileExistsError('Raw release already completed.')
  old=verify_record(done,runtime.identity,status='RAW_RELEASED')
  if old['archive_receipt_sha256']!=digest:raise RuntimeError('Release archive receipt changed.')
  return old
 if intent.exists():
  if not resume:raise FileExistsError('Raw release intent exists; explicit resume required.')
  old=verify_record(intent,runtime.identity,status='RAW_RELEASE_AUTHORIZED')
  if old['archive_receipt_sha256']!=digest or old['raw_sha256']!=required:raise RuntimeError('Release intent changed.')
 else:
  for name,sha in required.items():
   if Path(name).name!=name or not (raw/name).is_file() or sha256(raw/name)!=sha:raise RuntimeError('Raw integrity failed before release.')
  archived=out/f'preserved_archive_receipt_target_{target:06d}.json'
  if archived.exists():
   if sha256(archived)!=digest:raise RuntimeError('Preserved archive receipt differs.')
  else:atomic_new(archived,lambda p:p.write_bytes(Path(diagnostic_path).read_bytes()))
  write_json_new(intent,dict(status='RAW_RELEASE_AUTHORIZED',identity=runtime.identity,target=target,archive_receipt_sha256=digest,raw_sha256=required,numerical_status=receipt['numerical_status']))
 for name,sha in required.items():
  path=raw/name
  if path.exists():
   if path.is_symlink() or sha256(path)!=sha:raise RuntimeError('Raw changed during release.')
   path.unlink()
 result=dict(status='RAW_RELEASED',identity=runtime.identity,target=target,archive_receipt_sha256=digest,raw_sha256=required,numerical_status=receipt['numerical_status'],all_diagnostic_flags_preserved=True,no_scientific_calibration_claim=True,reason=receipt['reason'],proposals_checkpoints_and_descriptive_samples_retained=True)
 write_json_new(done,result);return result
'''
s=s.replace("archived=out/f'approved_diagnostic_target_{target:06d}.json'", "archived=out/f'preserved_archive_receipt_target_{target:06d}.json'")
s=s.replace("sha256(archived)!=release['diagnostic_sha256']", "sha256(archived)!=release['archive_receipt_sha256']")
s=s.replace("raise RuntimeError('Released target lacks its preserved approved diagnostic.')", "raise RuntimeError('Released target lacks its preserved archive receipt.')\n   from .campaign_archive import verify_archive_receipt\n   verify_archive_receipt(archived,out,runtime.identity,target,expected)")
p.write_text(s)
p=Path('tmp/c07_inference_portable/src/inference/campaign_runtime.py');s=p.read_text().replace("'campaign_runtime','campaign_io'", "'campaign_runtime','campaign_archive','campaign_io'");p.write_text(s)
p=Path('tmp/c07_inference_portable/scripts/infer_calibration.py');s=p.read_text().replace('from inference.campaign_iid import', 'from inference.campaign_archive import prepare_archive\nfrom inference.campaign_iid import');s=s.replace("['preflight','train','produce','release']", "['preflight','train','produce','archive','release']")
s=s.replace(" if len(targets)!=1 or a.raw is None or a.diagnostic is None:raise ValueError('Release one target with explicit --raw and --diagnostic.')", " if a.stage=='archive':\n  if len(targets)!=1 or a.proposals is None or a.diagnostic is None:raise ValueError('Archive one target with explicit --proposals and --diagnostic.')\n  row=prepare_archive(runtime,targets[0],a.proposals,a.output,a.diagnostic,resume=a.resume);print(json.dumps(row,indent=2));return\n if len(targets)!=1 or a.raw is None or a.diagnostic is None:raise ValueError('Release one target with explicit --raw and --diagnostic archive receipt.')")
p.write_text(s)
p=Path('tmp/c07_inference_portable/tests/test_portable_contract.py');s=p.read_text().replace('from inference.campaign_io import canonical_hash,write_json_new,read_json,load_observations', 'from inference.campaign_io import canonical_hash,write_json_new,read_json,load_observations,write_npz_new,sha256\nfrom inference.campaign_archive import prepare_archive')
s=s.replace("self.input_hashes={};self.settings=", "self.input_hashes={};self.paths={};self.settings=")
start=s.index(" good=tmp_path/'good_diagnostic.json'");end=s.index(" release_raw(rt,0,out,raw,good);",start)
s=s[:start]+''' numeric=tmp_path/'numeric.npz';write_npz_new(numeric,pit=np.zeros(6),pit_resolved=np.zeros(6,bool))
 diagnostic=tmp_path/'complete_diagnostic.json';write_json_new(diagnostic,dict(status='NUMERICAL_DIAGNOSTICS_COMPLETE',identity=rt.identity,target=0,raw_release_authorized=False,numeric_file=numeric.name,numeric_sha256=sha256(numeric),summary=dict(cdf_precision_pass=False,pooled_weight_guard_pass=True,saturation_guard_pass=True,replication_pass=False,refinement_pass=False),raw_sha256={r['raw_file']:r['raw_sha256'] for r in result['replicates']}))
 receipt=prepare_archive(rt,0,proposals,out,diagnostic);assert receipt['numerical_status']=='NUMERICALLY_UNRESOLVED'
 good=out/'archive_receipt_target_000000.json'
'''+s[end:]
p.write_text(s)
