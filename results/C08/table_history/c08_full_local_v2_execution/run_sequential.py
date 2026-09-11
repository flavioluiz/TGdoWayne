from pathlib import Path
import subprocess,sys,os,time,json
HERE=Path(__file__).resolve().parent;out=HERE/'results';out.mkdir(exist_ok=False);env=os.environ.copy();env['VECLIB_MAXIMUM_THREADS']='1';rows=[];start=time.perf_counter()
for stage in ['local','oracle_coarse','oracle_fine','gates','export']:
 before=time.perf_counter()
 with (out/(stage+'.log')).open('x') as f:r=subprocess.run([sys.executable,str(HERE/'worker.py'),stage],stdout=f,stderr=subprocess.STDOUT,env=env)
 rows.append(dict(stage=stage,exit_code=r.returncode,seconds=time.perf_counter()-before));print(json.dumps(rows[-1]),flush=True)
 if r.returncode:
  with (out/'controller_failed.json').open('x') as f:json.dump(dict(status='STOPPED_NO_RETRY',rows=rows,seconds=time.perf_counter()-start),f,indent=2)
  raise SystemExit(r.returncode)
reports=[json.loads((out/(x['stage']+'_report.json')).read_text()) for x in rows]
with (out/'controller_report.json').open('x') as f:json.dump(dict(status='SEQUENTIAL_C_FULL_V2_COMPLETED',rows=rows,seconds=time.perf_counter()-start,maximum_worker_RSS_bytes=max(r['RSS_peak_bytes'] for r in reports),workers_simultaneous=1,BLAS_threads=1),f,indent=2)
