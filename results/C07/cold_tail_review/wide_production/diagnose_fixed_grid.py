"""Prospective54 truth-blind cuts per target; no truth member is deserialized."""
import os
os.environ['VECLIB_MAXIMUM_THREADS']='1'
from pathlib import Path
import hashlib,json,sys
import numpy as np
ROOT=Path(__file__).resolve().parents[3];HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'replay_sources/src'))
from inference.iid_diagnostics import replicated_cdf,replicated_weights,simultaneous_differences,json_safe

def main():
 execution=json.loads((HERE/'execution_summary.json').read_text());gridpath=ROOT/'tmp/c07_iid_portable/results/gmm_truth_blind_planning.json';grid=json.loads(gridpath.read_text());rows=[]
 for target in execution['targets']:
  cuts=next(t for t in grid['targets'] if t['target']==target)['functions']
  for N in execution['levels']:
   records=sorted((r for r in execution['records'] if r['target']==target and r['N']==N),key=lambda r:r['replicate']);pieces=[]
   for r in records:
    p=ROOT/r['file'];assert hashlib.sha256(p.read_bytes()).hexdigest()==r['sha256']
    with np.load(p,allow_pickle=False) as f:pieces.append({k:f[k] for k in ['x_unit','log_likelihood','log_weights']})
   x=np.stack([p['x_unit'] for p in pieces]);ll=np.stack([p['log_likelihood'] for p in pieces]);lw=np.stack([p['log_weights'] for p in pieces]);functions=[]
   for name in dict.fromkeys(c['function'] for c in cuts):
    group=[c for c in cuts if c['function']==name];values=ll if name=='log_likelihood' else x[:,:,int(name[-1])];diags=replicated_cdf(values,lw,[c['cdf']['threshold'] for c in group]);functions.extend(dict(function=name,probability=c['pilot_quantile_probability'],cdf=d) for c,d in zip(group,diags))
   w=replicated_weights(lw);worst=max(functions,key=lambda f:f['cdf']['mcse']);rows.append(dict(target=target,N=N,precise_cuts=sum(f['cdf']['precision_pass'] for f in functions),total_cuts=54,maximum_mcse=worst['cdf']['mcse'],worst_function=worst['function'],worst_probability=worst['probability'],functions=functions,weights=w));print(json.dumps(dict(target=target,N=N,precise=rows[-1]['precise_cuts'],maximum_mcse=rows[-1]['maximum_mcse'])),flush=True)
 a=[r for r in rows if r['N']==execution['levels'][0]];b=[r for r in rows if r['N']==execution['levels'][1]];vals=lambda rr,key:[f['cdf'][key] for r in rr for f in r['functions']];contrast=simultaneous_differences(vals(a,'estimate'),vals(a,'mcse'),vals(b,'estimate'),vals(b,'mcse'));summary=dict(status='FIXED54_GRID_TRUTH_BLIND_DIAGNOSTICS',rows=[{k:r[k] for k in ['target','N','precise_cuts','total_cuts','maximum_mcse','worst_function','worst_probability']}|{k:r['weights'][k] for k in ['log_evidence','log_evidence_delta_mcse','maximum_normalized_weight','single_deletion_guard_pass','weight_ess_concentration_only']} for r in rows],high_level_precise=sum(r['precise_cuts'] for r in b),total_high_level_cuts=16*54,all_high_level_guards=all(r['weights']['single_deletion_guard_pass'] for r in b),refinement_family_size=16*54,refinement_all_consistent=contrast['all_consistent'],refinement_failures=int(np.count_nonzero(~contrast['consistent'])),refinement_max_standardized_difference=float(np.max(abs(contrast['difference'])/contrast['difference_mcse'])),uses_truth=False)
 with (HERE/'fixed_grid_diagnostics.json').open('x') as f:json.dump(json_safe(dict(summary=summary,rows=rows,refinement=contrast,source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),frozen_grid_sha256=hashlib.sha256(gridpath.read_bytes()).hexdigest(),execution_summary_sha256=hashlib.sha256((HERE/'execution_summary.json').read_bytes()).hexdigest())),f,indent=2);f.write('\n')
 with (HERE/'fixed_grid_summary.json').open('x') as f:json.dump(json_safe(summary),f,indent=2);f.write('\n')
if __name__=='__main__':main()
