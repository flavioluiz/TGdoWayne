"""One fresh OS worker, one remaining harmonic resolution; no curve bank loaded."""
import os
os.environ['VECLIB_MAXIMUM_THREADS']='1'
from pathlib import Path
import sys,json,hashlib,time,resource
import numpy as np
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];OLD=ROOT/'tmp/c08_beta_table';sys.path.insert(0,str(OLD));sys.path.insert(0,str(OLD/'executed_sources/src'))
from beta_builder import sha_file,canonical,write_json,write_npz,matrices,Ledger,beta_from_u
from inference.model import experiment,YEAR
from inference.orf_blas import RealHarmonicBasis,TableBudget,estimate

def run(label):
 if label not in ['coarse','fine']:raise ValueError('Only remaining k4 resolution accepted')
 auth=json.loads((HERE/'execution_authorized.json').read_text());identity=hashlib.sha256(canonical(auth).encode()).hexdigest();plan=json.loads((ROOT/'tmp/c08_beta_table_v2/preflight.json').read_text());out=HERE/'results';out.mkdir(exist_ok=True);dest=out/f'oracle_k4_{label}.npz'
 if dest.exists():raise FileExistsError('No overwrite or implicit resume')
 for p,h in auth['input_source_sha256'].items():
  if sha_file(ROOT/p)!=h:raise RuntimeError('Frozen input/source changed: '+p)
 caps={k:auth['cumulative_limits'][k]-auth['baseline'][k] for k in auth['baseline']};caps['logL']=min(caps['logL'],auth['maximum_additional_logL']);ledger=Ledger(out/'resource_delta_ledger.jsonl',caps,identity);start=time.perf_counter()
 def rss(stage):
  v=int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
  if v>auth['maximum_RSS_bytes']:raise MemoryError('RSS ceiling exceeded at '+stage)
  return v
 try:
  e=experiment(json.loads((OLD/'inputs/experiment.json').read_text()));nodes=np.array(plan['validation']['new_control_u']);beta=beta_from_u(nodes);phase=2*np.pi*e['f'][3]*e['distance_ly']*YEAR;l,n=plan['rows'][3]['oracle_orders_'+label];est=estimate(l,n,12,8)
  if est['estimated_memory_bytes']+64*1024**2>auth['maximum_numeric_bytes']:raise MemoryError('Numeric budget exceeded')
  basis=RealHarmonicBasis(e['points'],lmax=l,nmu=n,budget=TableBudget(auth['maximum_numeric_bytes']-64*1024**2,2_000_000_000_000,8),planned_batch=8);rss('basis');g=np.empty((72,12,12),complex)
  for first in range(0,72,8):ledger.charge('real',2*8*12*n*(l-1),dict(channel=4,resolution=label,first=first,last=first+8));g[first:first+8]=basis.evaluate(beta[first:first+8],phase);rss('evaluate')
  checks=matrices(g,72,12);record=dict(identity=identity,channel=4,resolution=label,orders=[l,n],checks=checks,seconds=time.perf_counter()-start,RSS_peak_bytes=rss('end'),real_products=2*72*12*n*(l-1),numeric_estimate=est,workers=1,VECLIB_MAXIMUM_THREADS=1)
  write_npz(dest,u=nodes,Gamma=g,record=np.array(canonical(record)));write_json(out/f'worker_{label}_report.json',record);print(json.dumps(record),flush=True)
 except Exception as exc:
  write_json(out/f'failure_worker_{label}.json',dict(type=type(exc).__name__,message=str(exc),identity=identity,resource_delta=ledger.totals,RSS_peak_bytes=int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss),seconds=time.perf_counter()-start));raise
if __name__=='__main__':run(sys.argv[1])
