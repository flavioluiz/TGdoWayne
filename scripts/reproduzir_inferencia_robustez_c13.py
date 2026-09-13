"""Replay original nominal, self-control and refined C09 inference jobs."""
from pathlib import Path
import argparse,hashlib,json,subprocess,sys,time
R=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--clean-root',type=Path,required=True);a=p.parse_args();C=a.clean_root.resolve()
out=C/'tmp/c13_c09_nominal_reproduction';out.mkdir(exist_ok=False)
plans=['c09_nominal_production_v1','c09_self_production_v1','c09_nominal_refinement_v1'];jobs=[]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
for name in plans:
 plan=C/'tmp'/name/'plan.json';value=json.loads(plan.read_text())
 for rel,digest in value['input_sha256'].items():assert sha(C/rel)==digest,rel
 assert sha(plan.parent/'grids.npz')==value['grids_sha256']
 for job in value['jobs']:jobs.append({'campaign':name,'plan':str(plan.relative_to(C)),'plan_sha256':sha(plan),'job':job['job_id'],'curves':len(job['curves'])})
assert len(jobs)==24 and sum(j['curves'] for j in jobs)==22957
report={'status':'running','jobs':jobs,'completed':[],'scope':'All nominal and self-control posteriors plus the one refined replacement; distance-mixture production is separate.','started_monotonic':time.monotonic()}
def save():
 target=out/'reproduction.json';temp=target.with_suffix('.partial');temp.write_text(json.dumps(report,indent=2)+'\n');temp.replace(target)
save()
for job in jobs:
 name=job['job'];destination=out/name;receipt=out/(name+'_io.json')
 command=[sys.executable,str(R/'scripts/executar_isolado_c13.py'),'--original-root',str(R),'--clean-root',str(C),'--receipt',str(receipt),'scripts/executar_lote_nominal_c09.py','--plan',job['plan'],'--job',name,'--output',str(destination)]
 print(json.dumps({'started':name,'completed':len(report['completed']),'total':len(jobs)}),flush=True)
 with (out/(name+'.log')).open('x') as f:
  process=subprocess.run(command,stdout=f,stderr=subprocess.STDOUT)
 if process.returncode:
  report['status']='failed';report['failed_job']=name;report['returncode']=process.returncode;save();raise SystemExit(process.returncode)
 path=destination/'posteriors.json';rows=json.loads(path.read_text());assert len(rows)==job['curves']
 report['completed'].append({'job':name,'curves':len(rows),'posteriors_sha256':sha(path),'receipt':str(receipt)});save()
 print(json.dumps({'completed_job':name,'curves':len(rows),'completed':len(report['completed']),'total':len(jobs)}),flush=True)
report['status']='complete';report['wall_seconds']=time.monotonic()-report.pop('started_monotonic');save()
print(json.dumps({'status':'complete','jobs':len(jobs),'curves_including_refined_replacement':22957}),flush=True)
