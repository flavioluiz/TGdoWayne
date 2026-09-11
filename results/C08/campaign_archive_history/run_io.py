"""Bounded transport-only invocation recorder; no scientific imports."""
from pathlib import Path
import hashlib,json,resource,subprocess,sys,time
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
script=HERE/'scripts/campanha_compressao.py'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
stage=sys.argv[1]
bundle=HERE/'bundle_engineering_main_v2'
if stage=='pack':
    args=['empacotar','--inventario',str(HERE/'inventory_engineering_main_v2.json'),'--repositorio',str(ROOT),'--saida',str(bundle)]
elif stage=='verify':args=['verificar','--pacote',str(bundle),'--dependencias',str(ROOT)]
elif stage=='restore':args=['restaurar','--pacote',str(bundle),'--destino',str(HERE/'restored_engineering_main_v2')]
else:raise ValueError(stage)
command=[sys.executable,str(script),*args]
intent=dict(command=command,source_sha256=sha(script),stage=stage,new_physics_calls=0,
    original_inventory_sha256=sha(HERE/'inventory_engineering_main_v2.json'),rss_accounting='Darwin ru_maxrss bytes',
    maximum_archive_bytes=90*1024**2,maximum_restored_bytes=2*1024**3)
with (HERE/f'{stage}_intent.json').open('x') as f:json.dump(intent,f,indent=2);f.write('\n')
start=time.monotonic();r=subprocess.run(command,capture_output=True,text=True);usage=resource.getrusage(resource.RUSAGE_CHILDREN)
report=dict(**intent,exit_code=r.returncode,wall_seconds=time.monotonic()-start,child_CPU_seconds=usage.ru_utime+usage.ru_stime,
    maximum_child_RSS_bytes=usage.ru_maxrss,stdout=r.stdout,stderr=r.stderr)
with (HERE/f'{stage}_result.json').open('x') as f:json.dump(report,f,indent=2);f.write('\n')
print(json.dumps(report,indent=2));sys.exit(r.returncode)
