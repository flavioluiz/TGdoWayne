from pathlib import Path
import json,sys,datetime
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2];OLD=ROOT/'tmp/c08_beta_table';P=ROOT/'tmp/c08_full_table_execution';sys.path.insert(0,str(OLD));from beta_builder import sha_file,write_json
old=json.loads((P/'execution_authorized.json').read_text());pre=json.loads((HERE.parent/'preflight.json').read_text());h=old['input_source_sha256']|pre['input_sha256']
for p in set(HERE.glob('*.py'))|{HERE.parent/'preflight.json',HERE.parent/'preflight.py'}:h[str(p.relative_to(ROOT))]=sha_file(p)
for p,s in h.items():
 if sha_file(ROOT/p)!=s:raise ValueError('Historical source changed')
a=dict(schema='C08_C_FULL_ORIGINAL_DIAGNOSTICS_AUTHORIZED_v1',recorded_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),authorization=dict(allowed=True,source='Parent read preflight.json and original failure report; explicitly authorized remaining97 controls plus54 reference cases',keep_candidate_FAILED=True,no_export_or_refinement=True),baseline_logL=724992,additional_logL=597696,final_cumulative_logL=1322688,maximum_cumulative_logL=1400000,maximum_new_real_products=0,maximum_new_direct_angular=0,maximum_RSS_bytes=1610612736,maximum_numeric_bytes=1073741824,workers=1,blas_threads=1,input_source_sha256=h)
write_json(HERE/'authorization.json',a);print(json.dumps(dict(files=len(h),sha256=sha_file(HERE/'authorization.json'))))
