from pathlib import Path
import subprocess,sys,json,time,os
HERE=Path(__file__).resolve().parent
start=time.perf_counter();out=HERE/'results';out.mkdir(exist_ok=False);env=os.environ.copy();env['VECLIB_MAXIMUM_THREADS']='1';rows=[]
for name in ['full_gates','full_export']:
 before=time.perf_counter()
 with (out/(name+'.log')).open('x') as f:run=subprocess.run([sys.executable,str(HERE/(name+'.py'))],stdout=f,stderr=subprocess.STDOUT,env=env)
 rows.append(dict(stage=name,exit_code=run.returncode,seconds=time.perf_counter()-before));print(json.dumps(rows[-1]),flush=True)
 if run.returncode:
  with (out/'controller_failure.json').open('x') as f:json.dump(dict(status='STOPPED_NO_RETRY',rows=rows,seconds=time.perf_counter()-start),f,indent=2)
  raise SystemExit(run.returncode)
with (out/'controller_report.json').open('x') as f:json.dump(dict(status='SEQUENTIAL_GATES_EXPORT_COMPLETED',rows=rows,seconds=time.perf_counter()-start),f,indent=2)
