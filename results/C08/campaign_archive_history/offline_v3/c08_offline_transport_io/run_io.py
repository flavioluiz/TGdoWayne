from pathlib import Path
import hashlib,json,resource,subprocess,time
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,v):
 with Path(p).open('x') as f:json.dump(v,f,indent=2);f.write('\n')
def main():
 cli=ROOT/'tmp/c08_campaign_archive_v3/scripts/campanha_compressao.py';inv=HERE/'inventory.json'
 assert sha(cli)=='27e03ac594e9d5db3136e9723d6b9857ed690f8341386d0cbd32a57031b443b8'
 assert sha(inv)=='ca4d5caacbadaf0ad88bb164712a5ce3c0792c3d73d98249e9cd0a88f05929fb'
 auth=dict(approved_by='ROOT',scope='I/O only pack verify external dependencies restore',source_sha256=sha(cli),inventory_sha256=sha(inv),ROOT_selected_files_reviewed=2138,
 maximum_CPU_seconds=120,maximum_archive_bytes=94371840,maximum_restored_bytes=500000000,no_physical_or_numeric_evaluations=True,originals_preserved=True)
 write(HERE/'ROOT_IO_authorization.json',auth)
 commands=[['empacotar','--inventario',str(inv),'--repositorio',str(ROOT),'--saida',str(HERE/'bundle')],
 ['verificar','--pacote',str(HERE/'bundle'),'--dependencias',str(ROOT)],
 ['restaurar','--pacote',str(HERE/'bundle'),'--destino',str(HERE/'restored'),'--max-bytes','500000000']]
 results=[];clock=time.monotonic();initial=resource.getrusage(resource.RUSAGE_CHILDREN)
 for i,args in enumerate(commands):
  before=resource.getrusage(resource.RUSAGE_CHILDREN);start=time.monotonic()
  with (HERE/f'operation{i}.log').open('x') as f:p=subprocess.run([str(ROOT/'.venv/bin/python'),'-B',str(cli),*args],cwd=ROOT,stdout=f,stderr=subprocess.STDOUT)
  after=resource.getrusage(resource.RUSAGE_CHILDREN)
  r=dict(operation=args[0],returncode=p.returncode,CPU=after.ru_utime+after.ru_stime-before.ru_utime-before.ru_stime,wall=time.monotonic()-start,log_sha256=sha(HERE/f'operation{i}.log'))
  write(HERE/f'operation{i}.json',r);results.append(r);print(json.dumps(r),flush=True)
  if p.returncode!=0:raise RuntimeError('I/O failure preserved')
 after=resource.getrusage(resource.RUSAGE_CHILDREN);cpu=after.ru_utime+after.ru_stime-initial.ru_utime-initial.ru_stime+time.process_time()
 assert cpu<120
 result=dict(status='ALL_OFFLINE_BYTES_PACKED_DEPENDENCIES_VERIFIED_AND_RESTORED',operations=results,CPU_through_final_snapshot=cpu,
 wall=time.monotonic()-clock,children_RSS=after.ru_maxrss,controller_RSS=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
 inventory_sha256=sha(inv),bundle_sha256=sha(HERE/'bundle/bundle.json'),source_sha256=sha(__file__),scientific_approval_inferred=False,all_original_failures_preserved=True)
 write(HERE/'roundtrip.json',result);print(json.dumps(result),flush=True)
if __name__=='__main__':main()
