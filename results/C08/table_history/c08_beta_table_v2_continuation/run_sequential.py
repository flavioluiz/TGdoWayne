"""Small controller; worker processes never overlap and no numeric bank lives here."""
from pathlib import Path
import subprocess,sys,json,time,hashlib,os
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
def sha(p):
 h=hashlib.sha256()
 with open(p,'rb') as f:
  for b in iter(lambda:f.read(1024**2),b''):h.update(b)
 return h.hexdigest()
def write(path,value):
 with path.open('x') as f:json.dump(value,f,indent=2);f.write('\n')
def main():
 auth=json.loads((HERE/'execution_authorized.json').read_text());out=HERE/'results';out.mkdir(exist_ok=False)
 for p,h in auth['input_source_sha256'].items():
  if sha(ROOT/p)!=h:raise RuntimeError('Frozen source/input mismatch: '+p)
 write(out/'execution_request.json',dict(authorization_sha256=sha(HERE/'execution_authorized.json'),authorization=auth));start=time.perf_counter();env=os.environ.copy();env['VECLIB_MAXIMUM_THREADS']='1';stages=[]
 for name,args in [('k4_coarse',['harmonic_worker.py','coarse']),('k4_fine',['harmonic_worker.py','fine']),('gates_export',['continuation_gates.py'])]:
  before=time.perf_counter()
  with (out/(name+'.log')).open('x') as log:r=subprocess.run([sys.executable,str(HERE/args[0]),*args[1:]],stdout=log,stderr=subprocess.STDOUT,env=env)
  stages.append(dict(stage=name,exit_code=r.returncode,seconds=time.perf_counter()-before));print(json.dumps(stages[-1]),flush=True)
  if r.returncode:
   write(out/'controller_failed.json',dict(status='STOPPED_NO_AUTOMATIC_RETRY',stages=stages,seconds=time.perf_counter()-start));raise SystemExit(r.returncode)
 report=json.loads((out/'final_report.json').read_text());workers=[json.loads((out/f'worker_{label}_report.json').read_text()) for label in ['coarse','fine']]
 write(out/'controller_report.json',dict(status='SEQUENTIAL_CONTINUATION_COMPLETED',stages=stages,seconds=time.perf_counter()-start,maximum_worker_RSS_bytes=max([w['RSS_peak_bytes'] for w in workers]+[report['RSS_peak_bytes']]),worker_RSS_is_Darwin_bytes=True,prior_failed_attempt_seconds=auth['prior_failed_attempt_seconds'],prior_failed_peak_RSS_bytes=auth['prior_failed_peak_RSS_bytes'],original_failure_preserved=True,resource_cumulative=report['resource_cumulative']))
if __name__=='__main__':main()
