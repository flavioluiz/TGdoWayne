"""C08 beta-by-frequency construction, private cache and explicit resource ledger.

No C07 cache semantics are reused. This stage only constructs the harmonically
checked matrices; independent sky and interpolation checks are separate gates.
"""
import os
os.environ['VECLIB_MAXIMUM_THREADS']='1'
from pathlib import Path
from dataclasses import asdict
import argparse,gc,hashlib,json,resource,sys,tempfile,time
import numpy as np
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
sys.path.insert(0,str(HERE/'executed_sources/src'))
from inference.model import experiment,YEAR
from inference.orf_blas import RealHarmonicBasis,TableBudget,estimate

def sha_file(path):
 h=hashlib.sha256()
 with Path(path).open('rb') as f:
  for block in iter(lambda:f.read(1024**2),b''):h.update(block)
 return h.hexdigest()
def canonical(value):return json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False)
def digest(array):
 a=np.asarray(array);return hashlib.sha256(canonical({'shape':a.shape,'dtype':a.dtype.str}).encode()+np.ascontiguousarray(a).tobytes()).hexdigest()
def atomic_new(path,writer):
 path=Path(path);path.parent.mkdir(parents=True,exist_ok=True);fd,name=tempfile.mkstemp(dir=path.parent,prefix='.partial_');os.close(fd)
 try:
  writer(Path(name))
  with open(name,'rb') as f:os.fsync(f.fileno())
  os.link(name,path)
 finally:os.unlink(name)
def write_json(path,value):atomic_new(path,lambda p:p.write_text(json.dumps(value,sort_keys=True,indent=2,allow_nan=False)+'\n'))
def write_npz(path,**arrays):
 def save(p):
  with p.open('wb') as f:np.savez(f,**arrays)
 atomic_new(path,save)
def scalar_int(value,name,minimum=1):
 if isinstance(value,(bool,np.bool_)) or not isinstance(value,(int,np.integer)) or value<minimum:raise ValueError(name+' must be an explicit bounded integer')
 return int(value)
def matrices(values,n,p):
 a=np.asarray(values)
 if a.dtype!=np.dtype('complex128') or a.shape!=(n,p,p) or not np.isfinite(a).all():raise ValueError('Nonfinite/wrong complex128 matrix batch')
 herm=float(np.max(abs(a-a.swapaxes(-1,-2).conj())))
 if herm>1e-12:raise ValueError('Non-Hermitian ORF cache')
 eig=float(np.linalg.eigvalsh(a).min())
 if eig< -1e-12:raise ValueError('ORF cache is not PSD; no clipping')
 return dict(hermiticity_max=herm,minimum_eigenvalue=eig)
def beta_from_u(u):
 a=np.asarray(u)
 if a.dtype.kind not in 'fiu' or a.ndim!=1 or not np.isfinite(a).all() or np.any((a<0)|(a>1)):raise ValueError('Finite real u vector in[0,1] required')
 return np.sqrt((1-a)*(1+a))
def u_from_beta(beta):
 b=np.asarray(beta)
 if b.dtype.kind not in 'fiu' or b.ndim!=1 or not np.isfinite(b).all() or np.any((b<0)|(b>1)):raise ValueError('Finite real beta vector required')
 return np.sqrt((1-b)*(1+b))
def planned_nodes(channel,validation_u):
 if channel==1:return np.asarray(validation_u),np.array([]),np.array([])
 den=131072 if channel==2 else 262144
 fine=np.unique(u_from_beta(np.r_[np.linspace(0,1,8193),np.arange(129)/den]));coarse=np.unique(u_from_beta(np.r_[np.linspace(0,1,4097),np.arange(0,129,2)/den]));direct=u_from_beta(np.array([.001,.05,.5,.9]));request=np.union1d(fine,np.union1d(validation_u,direct));return request,fine,coarse

class Ledger:
 def __init__(self,path,limits,identity):
  self.path=Path(path);self.limits=limits;self.identity=identity;self.totals={k:0 for k in limits};self.events=0
  if self.path.exists():
   for line in self.path.read_text().splitlines():
    r=json.loads(line)
    if r['identity']!=identity or r['index']!=self.events:raise RuntimeError('Ledger identity/order mismatch')
    self._accept(r['kind'],r['amount']);self.events+=1
 def _accept(self,kind,amount):
  amount=scalar_int(amount,'resource charge')
  if kind not in self.limits or self.totals[kind]+amount>self.limits[kind]:raise RuntimeError('Explicit resource ledger budget exceeded')
  self.totals[kind]+=amount
 def charge(self,kind,amount,details):
  self._accept(kind,amount);row=dict(identity=self.identity,index=self.events,kind=kind,amount=int(amount),details=details)
  with self.path.open('a') as f:f.write(canonical(row)+'\n');f.flush();os.fsync(f.fileno())
  self.events+=1

def read_chunk(path,record,u,beta,P):
 with np.load(path,allow_pickle=False) as f:
  if set(f.files)!={'u','beta','Gamma','record'}:raise RuntimeError('Unexpected cache members')
  saved=json.loads(str(f['record']));g=f['Gamma'].copy();old_u=f['u'];old_beta=f['beta']
  if any(saved.get(k)!=v for k,v in record.items()):raise RuntimeError('Cache metadata/signature differs')
  if old_u.dtype!=np.dtype(float) or old_beta.dtype!=np.dtype(float) or not np.array_equal(old_u,u) or not np.array_equal(old_beta,beta):raise RuntimeError('Cache node coordinates differ')
  if saved.get('Gamma_sha256')!=digest(g):raise RuntimeError('Cache matrix digest failed')
  matrices(g,len(u),P);return g

def run(config_path,resume=False):
 cfg=json.loads(Path(config_path).read_text());plan=json.loads((HERE/'preflight_v2.json').read_text())
 if cfg['authorization']['scope']!='C_beta_TABLE_AND_GATES_ONLY' or cfg['authorization']['execution_allowed'] is not True:raise ValueError('Explicit table-only authorization required')
 if cfg['maximum_real_multiplications']>50_000_000_000_000 or cfg['maximum_RSS_bytes']>1610612736 or cfg['workers']!=1 or cfg['blas_threads']!=1:raise ValueError('Authorized budget exceeded')
 if os.environ.get('VECLIB_MAXIMUM_THREADS')!='1':raise RuntimeError('Explicit single BLAS worker required')
 for p,h in cfg['source_sha256'].items():
  if sha_file(ROOT/p)!=h:raise RuntimeError('Frozen source or input changed: '+p)
 config_sha=sha_file(config_path);identity=hashlib.sha256(canonical(cfg).encode()).hexdigest();out=HERE/'results';out.mkdir(exist_ok=True)
 marker=out/'execution_request.json'
 if marker.exists():
  if not resume:raise FileExistsError('Explicit resume required for existing execution')
  if json.loads(marker.read_text())['identity']!=identity:raise RuntimeError('Execution identity changed')
 else:write_json(marker,dict(identity=identity,config_sha256=config_sha,config=cfg))
 ledger=Ledger(out/'resource_ledger.jsonl',dict(real=cfg['maximum_real_multiplications'],angular=cfg['maximum_direct_angular_work'],logL=cfg['maximum_logL_values']),identity)
 def rss(phase):
  peak=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
  if peak>cfg['maximum_RSS_bytes']:raise MemoryError('Observed Darwin peak RSS exceeded explicit process ceiling: '+str(peak))
  return int(peak)
 expcfg=json.loads((HERE/'inputs/experiment.json').read_text());e=experiment(expcfg);P=len(e['points']);y=2*np.pi*e['f'][:,None]*e['distance_ly'][None]*YEAR
 if P!=12 or len(e['f'])!=4 or not np.isfinite(y).all() or y.min()<0 or y.max()>6284:raise ValueError('Frozen phase/geometry domain mismatch')
 validation=np.array(plan['validation_nodes_u']);stage=[];all_start=time.perf_counter();rss('initial')
 try:
  for row in plan['rows']:
   k=row['channel'];request,fine,coarse=planned_nodes(k,validation);beta=beta_from_u(request);N=len(request)
   if N!=row['validation_and_table_unique_evaluations']:raise RuntimeError('Node count changed from frozen preflight')
   channel_signature=hashlib.sha256(canonical(dict(schema='C08_beta_per_channel_v1',identity=identity,channel=k,phase=digest(y[k-1]),directions=digest(e['points']),u=digest(request),beta=digest(beta),coarse=row['coarse'],fine=row['fine'])).encode()).hexdigest();results=[];timings=[];files=[]
   for label,(lmax,nmu) in [('coarse',row['coarse']),('fine',row['fine'])]:
    reserve=row['reserve_bytes'];budget=TableBudget(cfg['maximum_numeric_bytes']-reserve,cfg['maximum_batch_real_multiplications'],8);report=estimate(lmax,nmu,P,8)
    if report['estimated_memory_bytes']+reserve>cfg['maximum_numeric_bytes']:raise MemoryError('Preflight arrays exceed explicit estimate budget')
    values=np.empty((N,P,P),complex);basis=None;start=time.perf_counter();built=0
    for first in range(0,N,cfg['checkpoint_nodes']):
     last=min(N,first+cfg['checkpoint_nodes']);ub=request[first:last];bb=beta[first:last];record=dict(schema='C08_beta_chunk_v1',signature=channel_signature,channel=k,resolution=label,lmax=lmax,nmu=nmu,first=first,last=last,source_identity=identity);dest=out/'chunks'/f'channel{k:02d}_{label}_{first:06d}.npz'
     if dest.exists():
      if not resume:raise FileExistsError('Chunk exists; explicit resume required')
      g=read_chunk(dest,record,ub,bb,P)
     else:
      if basis is None:
       before=time.perf_counter();basis=RealHarmonicBasis(e['points'],lmax=lmax,nmu=nmu,budget=budget,planned_batch=8);built+=time.perf_counter()-before;rss('basis allocated')
      charge=int(2*len(ub)*P*nmu*(lmax-1));ledger.charge('real',charge,dict(channel=k,resolution=label,first=first,last=last));g=np.empty((len(ub),P,P),complex)
      for begin in range(0,len(ub),8):g[begin:begin+8]=basis.evaluate(bb[begin:begin+8],y[k-1])
      stats=matrices(g,len(ub),P);payload=record|stats|dict(Gamma_sha256=digest(g));write_npz(dest,u=ub,beta=bb,Gamma=g,record=canonical(payload))
     values[first:last]=g;files.append(dict(file=str(dest.relative_to(ROOT)),sha256=sha_file(dest)));peak=rss('chunk complete')
     print(json.dumps(dict(channel=k,resolution=label,completed=last,total=N,seconds=time.perf_counter()-start,real_multiplications_charged=ledger.totals['real'],RSS_peak_bytes=peak)),flush=True)
    del basis;gc.collect();timings.append(dict(resolution=label,seconds=time.perf_counter()-start,basis_build_seconds=built));results.append(values)
   matrices(results[0],N,P);matrices(results[1],N,P);error=np.max(abs(results[0]-results[1]),axis=(1,2))
   if not np.isfinite(error).all() or np.any(error>1e-8):raise RuntimeError('Harmonic coarse/fine gate failed; no refinement or tolerance change')
   dest=out/f'channel{k:02d}_matrices.npz';record=dict(schema='C08_beta_channel_v1',identity=identity,signature=channel_signature,channel=k,coarse=row['coarse'],fine=row['fine'],u_sha256=digest(request),beta_sha256=digest(beta),Gamma_coarse_sha256=digest(results[0]),Gamma_fine_sha256=digest(results[1]),errors_sha256=digest(error),maximum_error=float(error.max()),timings=timings)
   arrays=dict(u=request,beta=beta,Gamma_coarse=results[0],Gamma_fine=results[1],errors=error,fine_grid_u=fine,coarse_grid_u=coarse,record=np.array(canonical(record)))
   if dest.exists():
    if not resume:raise FileExistsError(dest)
    with np.load(dest,allow_pickle=False) as saved:
     if set(saved.files)!=set(arrays):raise RuntimeError('Channel checkpoint members changed')
     for key,val in arrays.items():
      if key=='record':
       old=json.loads(str(saved[key]));new=json.loads(str(val));old.pop('timings');new.pop('timings')
       if old!=new:raise RuntimeError('Channel checkpoint identity/digest differs')
      elif not np.array_equal(saved[key],val):raise RuntimeError('Channel checkpoint arrays differ')
   else:write_npz(dest,**arrays)
   stage.append(dict(channel=k,file=str(dest.relative_to(ROOT)),sha256=sha_file(dest),maximum_coarse_fine_difference=float(error.max()),minimum_eigenvalue=float(np.linalg.eigvalsh(results[1]).min()),timings=timings,chunks=files));del results,values;gc.collect();rss('frequency complete')
  for p,h in cfg['source_sha256'].items():
   if sha_file(ROOT/p)!=h:raise RuntimeError('Source/input changed during construction')
  if sha_file(config_path)!=config_sha:raise RuntimeError('Execution configuration changed')
  manifest=dict(status='HARMONIC_MATRICES_COMPLETE_PENDING_INDEPENDENT_GATES',identity=identity,execution_config_sha256=config_sha,rows=stage,real_multiplications_charged=ledger.totals['real'],planned_real_multiplications=plan['planned_real_multiplications'],seconds=time.perf_counter()-all_start,RSS_peak_bytes=rss('end'),no_C07_sources_or_caches_modified=True,workers=1,VECLIB_MAXIMUM_THREADS=os.environ['VECLIB_MAXIMUM_THREADS'],no_posterior_inference=True)
  final=out/'matrix_manifest.json'
  if final.exists():
   if not resume:raise FileExistsError(final)
  else:write_json(final,manifest)
  print(json.dumps({k:v for k,v in manifest.items() if k!='rows'}),flush=True);return manifest
 except Exception as exc:
  failure=out/f'failure_{time.time_ns()}.json';write_json(failure,dict(status='STOPPED_WITHOUT_AUTOMATIC_REFINEMENT',identity=identity,type=type(exc).__name__,message=str(exc),resource_totals=ledger.totals,RSS_peak_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,seconds=time.perf_counter()-all_start));raise

if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('--config',default=str(HERE/'execution_authorized.json'));parser.add_argument('--resume',action='store_true');args=parser.parse_args();run(args.config,args.resume)
