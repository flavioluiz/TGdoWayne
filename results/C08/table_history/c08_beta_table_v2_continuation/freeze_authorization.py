from pathlib import Path
import sys,json,datetime
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];OLD=ROOT/'tmp/c08_beta_table';V2=ROOT/'tmp/c08_beta_table_v2';sys.path.insert(0,str(OLD))
from beta_builder import sha_file,write_json
pre=json.loads((HERE/'preflight.json').read_text());oldauth=json.loads((V2/'execution_authorized.json').read_text());failure=json.loads((V2/'results/failure.json').read_text());hashes=oldauth['input_source_sha256']|pre['input_sha256']
for p in set(HERE.glob('*.py'))|{HERE/'preflight.json',HERE/'PREFLIGHT.md'}:hashes[str(p.relative_to(ROOT))]=sha_file(p)
auth=dict(schema='C08_V2_TECHNICAL_CONTINUATION_AUTHORIZED_v1',recorded_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),authorization=dict(allowed=True,source='Parent explicitly read PREFLIGHT.md and JSON and authorized sequential k4 coarse/fine plus third gates/export process',scope='EXACT_REMAINING_TABLE_GATES_NO_POSTERIOR',no_automatic_retry=True),baseline=pre['continuation_baseline'],previous_execution_identity=failure['identity'],previous_failed_execution_sha256=sha_file(V2/'results/failure.json'),previous_ledger_sha256=sha_file(V2/'results/resource_delta_ledger.jsonl'),prior_failed_attempt_seconds=pre['failed_attempt_seconds'],prior_failed_peak_RSS_bytes=pre['failed_attempt_peak_RSS_bytes'],failed_basis_preparation_cost_preserved=True,cumulative_limits=pre['unchanged_cumulative_caps'],maximum_additional_logL=600000,maximum_RSS_bytes=1610612736,maximum_numeric_bytes=1073741824,workers=1,blas_threads=1,input_source_sha256=hashes,expected_remaining_work=pre['remaining_work'])
for p,h in hashes.items():
 if sha_file(ROOT/p)!=h:raise ValueError('Frozen source changed: '+p)
write_json(HERE/'execution_authorized.json',auth);print(json.dumps(dict(files=len(hashes),authorization_sha256=sha_file(HERE/'execution_authorized.json'),baseline=auth['baseline'])))
