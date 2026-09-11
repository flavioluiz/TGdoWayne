from pathlib import Path
import json,hashlib,importlib.util
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent
P=ROOT/'tmp/c08_campaign_archive_v3/scripts/campanha_compressao.py'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text())
def write(p,v):
 with Path(p).open('x') as f:json.dump(v,f,indent=2);f.write('\n')
assert sha(P)=='27e03ac594e9d5db3136e9723d6b9857ed690f8341386d0cbd32a57031b443b8'
sp=importlib.util.spec_from_file_location('archive',P);m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m)
base=ROOT/'tmp/c08_offline_selection_v1';listed=base/'selected_artifacts.json';s=read(base/'selection_candidate.json');a=read(listed)
assert sha(listed)=='1e75f3f5ca9a6150dff6bc7307cf953c8e0f814d035451024b740d54f4f11b7a'
assert len(a['artifacts'])==2131 and a['selected_bytes']==449606358
for r in a['artifacts']:assert sha(ROOT/r['path'])==r['sha256'] and (ROOT/r['path']).stat().st_size==r['bytes']
reviews={k:dict(path='tmp/'+p,sha256=sha(ROOT/'tmp'/p)) for k,p in [('finite','c08_finite_ROOT/result_review.json'),('paired','c08_supplemental_ROOT/synthesis_result_review.json'),('supplemental','c08_supplemental_ROOT/supplemental_index.json')]}
assert read(ROOT/reviews['finite']['path'])['status']=='ALL_FINITE_OUTPUTS_REVIEWED'
assert read(ROOT/reviews['paired']['path'])['status']=='ALL_PAIRED_PRODUCTS_REVIEWED'
identity=hashlib.sha256(json.dumps(reviews,sort_keys=True).encode()).hexdigest()
wrapper=ROOT/'tmp/c08_offline_transport_ROOT';wrapper.mkdir()
completion=dict(schema='C08_OFFLINE_ROOT_COMPLETE_v1',status='ALL_SELECTED_ANALYSIS_BYTES_PRESERVED',scope='C08_FINITE_OFFLINE_SUPPLEMENTAL_PAIRED_LOSSLESS_TRANSPORT_ONLY',
 identity=identity,workers_exited=True,all_failures_preserved=True,no_uniform_proof=True,artifact_namespace='repository',artifacts=a['artifacts'],reviews=reviews,
 original_finite_status='FAILED_PRESERVED_NO_RETRY',original_failed_run_unchanged=True,no_new_physics=True)
write(wrapper/'complete.json',completion)
review=dict(schema='ROOT_C08_OFFLINE_ROOT_REVIEW_v1',status='OFFLINE_ROOT_COMPLETE_REVIEWED',root_path=str(wrapper.relative_to(ROOT)),lock_path=s['campaigns'][0]['lock_path'],
 completion_sha256=sha(wrapper/'complete.json'),identity=identity,artifact_namespace='repository',artifact_count=2131,
 reviewer='ROOT',source_read=['v1 full transport','v2 full patch and selection','v3 full patch','select_payload.py'],
 closed_physical_and_statistical_products_reviewed=True,all_failures_preserved=True,no_new_physics=True,no_historical_reexecution_claim=True)
write(wrapper/'ROOT_review.json',review)
s['campaigns'][0]['completion_sha256']=sha(wrapper/'complete.json');s['campaigns'][0]['root_review']['sha256']=sha(wrapper/'ROOT_review.json')
s['ROOT_wrapper_receipts_pending']=False;s['no_plan_or_pack_authorized_by_this_file']=False
s['include']+=['tmp/c08_offline_selection_v1/selected_artifacts.json','tmp/c08_offline_selection_v1/external_dependencies.json','tmp/c08_offline_selection_v1/selection_candidate.json','tmp/c08_offline_selection_v1/result.json','tmp/c08_offline_transport_io/prepare_ROOT.py']
write(HERE/'selection.json',s)
r=m.plan(HERE/'selection.json',ROOT,HERE/'inventory.json');write(HERE/'preflight.json',r);print(json.dumps(r))
