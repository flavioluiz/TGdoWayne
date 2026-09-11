"""Read-only identity/cache audit. No ORF integral or density evaluation."""
from pathlib import Path
import json,hashlib,sys,time,resource
import numpy as np
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];OLD=ROOT/'tmp/c08_beta_table';sys.path.insert(0,str(OLD));from beta_builder import sha_file,write_json
start=time.perf_counter();a=json.loads((HERE/'authorization.json').read_text());out=HERE/'results';g=json.loads((out/'gates_report.json').read_text());r=json.loads((out/'export_report.json').read_text())
for p,h in a['input_source_sha256'].items():
 if sha_file(ROOT/p)!=h:raise RuntimeError('Frozen source/input changed '+p)
rows=[json.loads(x) for x in (out/'resource_delta_ledger.jsonl').read_text().splitlines()];counts={k:sum(x['amount'] for x in rows if x['kind']==k) for k in ['real','angular','logL']};assert counts==g['resource_delta']==r['resource_delta']
errors=[]
for path in (out/'likelihood_cache').glob('*.npz'):
 with np.load(path,allow_pickle=False) as z:
  vals=[z['logL_'+k] for k in ['coarse','fine','oracle']];assert all(v.shape==(64,32) and np.isfinite(v).all() for v in vals);assert str(z['identity'])==g['identity'];errors.append([float(np.max(abs(vals[0]-vals[1]))),float(np.max(abs(vals[1]-vals[2])))])
assert len(errors)==287 and np.max(errors,axis=0).tolist()==[g['maximum_logL_coarse_fine'],g['maximum_logL_fine_oracle']]
refs=json.loads((out/'independent_references.json').read_text(),parse_constant=lambda v:(_ for _ in ()).throw(ValueError('Nonfinite JSON '+v)));assert len(refs)==54
for row in refs:assert np.isfinite([row[k] for k in ['mean_error','covariance_error','SciPy_logpdf_error','condition_number']]).all()
with np.load(out/'fine_first_curve.npz',allow_pickle=False) as z:n=z['nodes'];m=z['matrices'];c=z['coeff']
with np.load(OLD/'first_curve_root.npz',allow_pickle=False) as z:on=z['nodes'];om=z['matrices'];oc=z['coeff']
assert np.array_equal(m[np.searchsorted(n,on)],om);bound=np.sqrt((1-1/64)*(1+1/64));j=np.searchsorted(on,bound);assert np.array_equal(c[:j],oc[:j]);del on,om,oc
path=out/'C_full_table.npz';assert sha_file(path)==r['table_sha256']
with np.load(path,allow_pickle=False) as z:fn=z['nodes'];fm=z['matrices'];fc=z['coeff'];assert str(z['coordinate'])=='minus_beta' and str(z['construction_identity'])==r['identity']
assert np.array_equal(fn,n)
for k in range(4):assert np.array_equal(fm[:,k:k+1],m) and np.array_equal(fc[:,:,k:k+1],c)
metadata={name:dict(shape=list(v.shape),dtype=v.dtype.str,sha256=hashlib.sha256(memoryview(v).cast('B')).hexdigest()) for name,v in [('nodes',fn),('matrices',fm),('coeff',fc)]}
report=dict(status='READ_ONLY_C_FULL_V2_AUDIT_PASS',frozen_files=len(a['input_source_sha256']),checked_LL_caches=287,checked_independent_references=54,resource_delta=counts,resource_cumulative=r['resource_cumulative'],old_nodes_and_external_coefficients_bitexact=True,all_exported_channels_bitexact=True,all_reference_numeric_fields_finite=True,reference_finitude_guard_note='Executed source writes JSON with allow_nan=False before PASS/export; explicit np.isfinite at comparison point is recommended for clearer future errors, without changing this source.',array_metadata_sha256=metadata,table_sha256=sha_file(path),source_sha256=sha_file(__file__),seconds=time.perf_counter()-start,RSS_peak_bytes=int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss),no_ORF_or_logL_evaluations=True)
write_json(HERE/'audit_completed.json',report);print(json.dumps(report,indent=2))
