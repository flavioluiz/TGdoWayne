"""Replay every frozen C09 truth-response job through the audited I/O adapter."""
from pathlib import Path
import argparse,hashlib,json,subprocess,sys,time
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--clean-root',type=Path,required=True);a=p.parse_args();root=a.clean_root.resolve();original=Path(__file__).resolve().parents[1]
base=root/'tmp/c09_production_truth_backend_v2';out=base/'backend_execution';saved=base/'c13_backend_execution_published'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
plan=read(base/'prepared/plan.json');assert plan['CPU_preflight_accepted']
if saved.exists():raise ValueError('Fresh replay required; inspect any previous run before continuing')
out.rename(saved);out.mkdir()
activation=dict(plan_sha256=sha(base/'prepared/plan.json'),worker_sha256=sha(base/'worker.py'),driver_sha256=sha(base/'run_backend.py'),execution_scope='Production continuous truth nodes; three refinements; no likelihood or observation generation',original_plan_execution_flag_unchanged=True)
(out/'activation.json').write_text(json.dumps(activation,indent=2)+'\n')
started=time.monotonic();cpu=0.;products=0;runs=[]
for index,job in enumerate(plan['jobs']):
 assert cpu+120<=plan['combined_worker_CPU_cap'] and products+job['products']<=plan['real_products']
 request=out/(job['name']+'.json');request.write_text(json.dumps(dict(job_index=index,**activation),indent=2)+'\n')
 log=out/(job['name']+'_replay.log');io=out/(job['name']+'_io.json')
 command=[sys.executable,str(original/'scripts/executar_isolado_c13.py'),'--original-root',str(original),'--clean-root',str(root),'--receipt',str(io),'tmp/c09_production_truth_backend_v2/worker.py',str(request),sha(request)]
 with log.open('x') as stream:code=subprocess.run(command,cwd=root,stdout=stream,stderr=subprocess.STDOUT,timeout=190).returncode
 receipt=read(out/job['name']/'receipt.json') if (out/job['name']/'receipt.json').exists() else {}
 cpu+=receipt.get('CPU',0);products+=receipt.get('products',0)
 run=dict(job=job['name'],status=receipt.get('status','NO_RECEIPT'),returncode=code)
 if code==0 and run['status']=='COMPLETED':
  now=out/job['name']/'matrices.npz';old=saved/job['name']/'matrices.npz'
  run.update(reference_sha256=sha(old),reproduced_sha256=sha(now),byte_identical=sha(old)==sha(now))
 runs.append(run)
 result=dict(runs=runs,CPU=cpu,products=products,all_jobs_completed=len(runs)==len(plan['jobs']) and all(r['status']=='COMPLETED' and r.get('byte_identical') for r in runs),C09_complete=False,wall_seconds=time.monotonic()-started,replay_driver_sha256=sha(Path(__file__)))
 (out/'summary.json').write_text(json.dumps(result,indent=2)+'\n')
 print(json.dumps(dict(jobs_completed=len(runs),jobs_total=len(plan['jobs']),CPU=cpu,last=run)),flush=True)
 if code or run['status']!='COMPLETED' or not run.get('byte_identical'):raise RuntimeError('Retained replay failure; no automatic retry')
assert products==plan['real_products']
(original/'results/C13/c09_truth_responses_reproduced.json').write_text(json.dumps(result,indent=2)+'\n')
