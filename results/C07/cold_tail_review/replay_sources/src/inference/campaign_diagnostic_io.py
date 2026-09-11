"""Raw loader for a separate diagnostic process. Producer/trainer do not import truths."""
from pathlib import Path
import numpy as np
from .campaign_io import read_json,sha256

def load_target_levels(report_path,raw_root):
 report=read_json(report_path)
 if report.get('status')!='IID_COMPLETE_AWAITING_DIAGNOSTICS':raise ValueError('A complete IID target is required.')
 raw=Path(raw_root);result={}
 for level in report['levels']:
  rows=sorted([r for r in report['replicates'] if r['level']==level],key=lambda r:r['replicate'])
  if len(rows)!=4 or [r['replicate'] for r in rows]!=list(range(4)):raise ValueError('Four distinct replicas required at each level.')
  arrays={k:[] for k in ['x_unit','z','log_likelihood','log_weights','log_proposal','log_prior_logit']}
  for row in rows:
   if Path(row['raw_file']).name!=row['raw_file']:raise ValueError('Unsafe raw filename.')
   path=raw/row['raw_file']
   if sha256(path)!=row['raw_sha256']:raise RuntimeError('Raw digest mismatch.')
   with np.load(path,allow_pickle=False) as p:
    if int(p['target'])!=report['target'] or int(p['replicate'])!=row['replicate']:raise ValueError('Raw identity mismatch.')
    for key in arrays:
     value=p[key].copy();shape=(level,5) if key in ['x_unit','z'] else (level,)
     if value.shape!=shape or not np.isfinite(value).all():raise ValueError('Raw numeric shape/finitude mismatch.')
     arrays[key].append(value)
  arrays={k:np.asarray(v) for k,v in arrays.items()}
  if not np.array_equal(arrays['log_weights'],arrays['log_likelihood']+arrays['log_prior_logit']-arrays['log_proposal']):raise RuntimeError('Importance-weight formula differs from stored components.')
  result[level]=arrays
 return report,result

def load_truth_for_diagnostics(report_path,truth_data_path,bounds):
 """Only diagnostic callers explicitly request this separate truth-reading function."""
 report=read_json(report_path)
 if sha256(truth_data_path)!=report['input_sha256']['data']:raise RuntimeError('Truth source differs from the observation source bound into production.')
 with np.load(truth_data_path,allow_pickle=False) as p:truth=np.asarray(p['truth'][report['datum']],float)
 limits=np.asarray(bounds,float)
 if truth.shape!=(5,) or limits.shape!=(5,2) or not np.isfinite(truth).all():raise ValueError('Truth shape/finitude mismatch.')
 return truth,(truth-limits[:,0])/(limits[:,1]-limits[:,0])
