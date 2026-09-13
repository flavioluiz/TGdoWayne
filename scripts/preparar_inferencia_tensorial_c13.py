"""Resolve every original campaign input by hash before a fresh replay."""
from pathlib import Path
import argparse,hashlib,json,subprocess
R=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--clean-root',type=Path,required=True);a=p.parse_args();C=a.clean_root
old=json.loads((C/'tmp/c13_c07_restored/campaign/campaign_plan.json').read_text())
known={
'data':C/'results/C07/prior_predictive/data.npz',
'truth_data':C/'results/C07/prior_predictive/data.npz',
'truth_logl':C/'results/C07/prior_predictive/truth_log_likelihood.json',
'table':C/'results/C07/orf_interpolation/orf_table_pilot12x4.npz',
'native_library':C/'tmp/c13_c07_native_reference/libpta_likelihood.dylib',
'native_build_manifest':C/'results/C07/training_benchmark/native_provenance/build_manifest.json'}
expected={**old['input_sha256'],**old['extra_input_sha256']}
candidates=list((C/'configs').rglob('*.json'))+list((C/'results/C07/orf_interpolation').glob('*.json'))
sha=lambda x:hashlib.sha256(x.read_bytes()).hexdigest()
for key,digest in expected.items():
 if key not in known:
  hits=[x for x in candidates if sha(x)==digest]
  assert hits,(key,digest)
  known[key]=hits[0]
 assert sha(known[key])==digest,(key,str(known[key]))
args=[]
for key,path in known.items():
 option={'settings':'run-config'}.get(key,key.replace('_','-'))
 args.extend(['--'+option,str(path.relative_to(C))])
args+=['--output','tmp/c13_c07_full_reproduction','--training-threads',str(old['thread_plan']['training']),'--threads',str(old['thread_plan']['production'])]
record={'inputs':{k:{'path':str(v.relative_to(C)),'sha256':expected[k]} for k,v in known.items()},'worker':'scripts/run_calibration_campaign.py','arguments':args,'original_targets':old['targets'],'expected_likelihood_evaluations':old['planned_training_plus_production_likelihood_values'],'scope':'Exact original inputs and thread plan; production requires a successful fresh preflight.'}
(R/'results/C13/c07_full_replay_inputs.json').write_text(json.dumps(record,indent=2)+'\n')
command=[str(R/'.venv/bin/python'),str(R/'scripts/executar_isolado_c13.py'),'--original-root',str(R),'--clean-root',str(C),'--receipt',str(C/'tmp/c13_c07_full_preflight_io.json'),record['worker'],*args,'--plan-file','tmp/c13_c07_full_preflight.json']
with (R/'tmp/c13_c07_full_preflight.log').open('w') as f:subprocess.run(command,check=True,stdout=f,stderr=subprocess.STDOUT)
print(json.dumps({'targets':record['original_targets'],'inputs':len(known),'preflight':'tmp/c13_c07_full_preflight.log'}))
