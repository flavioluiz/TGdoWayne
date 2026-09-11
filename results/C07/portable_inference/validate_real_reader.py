from pathlib import Path
import sys,json,time,hashlib
import numpy as np
sys.path.insert(0,str(Path('tmp/c07_inference_portable/src').resolve()))
from inference.campaign_diagnostics import numerical_statistics
b=Path('tmp/c07_iid_gmm_approved');index=5;target=14;levels=[];begin=time.perf_counter()
for n in [16384,65536]:
 with np.load(b/f'results/iid_N{n}.npz',allow_pickle=False) as a:
  levels.append({k:a[k][:,:,index].copy() for k in ['x_unit','log_weights','log_likelihood']})
  truth=a['truth_unit'][index].copy()
truth_ll=json.loads((b/'results/truth_likelihood.json').read_text())['truth_log_likelihood'][index]
bounds=np.array([[0,1],[-16,-14],[3,5.5],[-17,-14.5],[-.30103,.30103]])
arrays,summary=numerical_statistics(*levels,truth,truth_ll,bounds,population_targets=16)
reference=json.loads((b/'diagnostics_root.json').read_text())
errors=[];sameflags=True
for i,level in enumerate(reference['levels']):
 row=next(t for t in level['targets'] if t['target']==target)
 for j,cdf in enumerate(row['cdf_rows']):
  errors += [abs(cdf['estimate']-arrays['cdf_estimates_by_level'][i,j]),abs(cdf['mcse']-arrays['cdf_mcse_by_level'][i,j])]
  sameflags &= cdf['precision_pass']==bool(arrays['cdf_precision_by_level'][i,j])
 errors += [abs(row['weights']['log_evidence']-arrays['log_evidence_by_level'][i])]
assert max(errors)<1e-12 and sameflags
out=dict(test='A0d14 original 8336-node IID vs portable compact reader; not new SBC',target=target,maximum_absolute_error=max(errors),cdf_flags_identical=sameflags,high_precision=summary['high_cdf_precision_pass'],seconds=time.perf_counter()-begin,source_sha256={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in [Path(__file__),Path('tmp/c07_inference_portable/src/inference/campaign_diagnostics.py')]},note='Numerical families differ deliberately: old selected16 included extra40reference refinement endpoints; compact campaign reader has7per-target and reference is separate.')
path=Path('tmp/c07_inference_portable/results/real_reader_A0d14.json');path.write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
