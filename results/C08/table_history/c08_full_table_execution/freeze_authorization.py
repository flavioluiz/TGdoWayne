from pathlib import Path
import sys,json,datetime
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];OLD=ROOT/'tmp/c08_beta_table';sys.path.insert(0,str(OLD));from beta_builder import sha_file,write_json
pre=ROOT/'tmp/c08_full_table_design/preflight.json';p=json.loads(pre.read_text());files=set((OLD/'executed_sources').rglob('*.py'))|set(HERE.glob('*.py'))|{OLD/'beta_builder.py',pre,ROOT/'tmp/c08_full_table_design/PREFLIGHT.md'}
hashes=p['input_sha256']|{str(f.relative_to(ROOT)):sha_file(f) for f in files}
for f,h in hashes.items():
 if sha_file(ROOT/f)!=h:raise ValueError('Frozen input mismatch '+f)
a=dict(schema='C08_C_FULL_TABLE_AUTHORIZED_v1',recorded_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),authorization=dict(allowed=True,source='Parent read prospective C_full PREFLIGHT.md and JSON and authorized only gates/export',exact_work_logL=1322688,own_ledger_starts_zero=True,processes='two fresh sequential processes: gates then export',failure_stops=True,no_C07_mutation=True,no_native_bank_or_posterior=True),maximum_logL=1400000,maximum_harmonic_real_products=0,maximum_direct_angular_work=0,maximum_numeric_bytes=1073741824,maximum_RSS_bytes=1610612736,workers=1,blas_threads=1,input_source_sha256=hashes)
write_json(HERE/'execution_authorized.json',a);print(json.dumps(dict(files=len(hashes),authorization_sha256=sha_file(HERE/'execution_authorized.json'))))
