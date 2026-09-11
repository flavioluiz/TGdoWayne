"""Explicit paths, observation-only loading, immutable records and deterministic seeds."""
from pathlib import Path
import hashlib,json,os,tempfile
import numpy as np

MODELS=('A0_CN','A_CN','B_CN','A_G','B_G')
OBSERVATION_FIELDS=('q','x_physical','x_gaussian')

def sha256(path):
 h=hashlib.sha256()
 with Path(path).open('rb') as f:
  for block in iter(lambda:f.read(1024**2),b''):h.update(block)
 return h.hexdigest()

def canonical_hash(value):return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()

def positive_int(value,name,allow_zero=False):
 if isinstance(value,(bool,np.bool_)) or not isinstance(value,(int,np.integer)) or value<(0 if allow_zero else 1):raise ValueError(name+' must be an explicit integer in range.')
 return int(value)

def read_json(path):
 with Path(path).open() as f:return json.load(f)

def load_observations(path,exp):
 # Deliberately do not iterate over NPZ arrays or deserialize the truth member.
 with np.load(path,allow_pickle=False) as p:
  data={k:p[k].copy() for k in OBSERVATION_FIELDS}
  for key,expected in [('directions',exp['points']),('distances_ly',exp['distance_ly']),('sigma',exp['sigma']),('red_pattern',exp['red']),('frequency_hz',exp['f']),('scale',exp['scale'])]:
   if key not in p or not np.array_equal(p[key],expected):raise ValueError('Dataset geometry/scaling differs: '+key)
 n=len(data['q']);K=len(exp['f']);P=len(exp['points']);D=len(exp['H'])
 if n<1 or data['q'].shape!=(n,K,P) or any(data[k].shape!=(n,K,D) for k in ['x_physical','x_gaussian']):raise ValueError('Observation dimensions do not match the experiment.')
 if not all(np.isfinite(a).all() for a in data.values()):raise ValueError('Nonfinite observations.')
 return data

def target_ids(settings,n):
 models=settings.get('models',list(MODELS))
 if len(set(models))!=len(models) or any(m not in MODELS for m in models):raise ValueError('Unsupported/duplicate model. C_full/C_beta need their own approved response, not this physical table.')
 ids=settings.get('targets')
 if ids is None:ids=[MODELS.index(m)*n+j for m in models for j in range(n)]
 if not isinstance(ids,list) or not ids or any(isinstance(t,bool) or not isinstance(t,int) or not 0<=t<5*n or MODELS[t//n] not in models for t in ids) or len(ids)!=len(set(ids)):raise ValueError('Invalid explicit global targets.')
 return np.asarray(ids,int)

def rng_for(master_seed,stage,target,replicate):
 values=[positive_int(master_seed,'seed',True),positive_int(stage,'stage'),positive_int(target,'target',True),positive_int(replicate,'replicate',True)]
 return np.random.default_rng(np.random.SeedSequence(values))

def atomic_new(path,writer):
 path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
 fd,name=tempfile.mkstemp(dir=path.parent,prefix='.incomplete_');os.close(fd)
 try:
  writer(Path(name))
  with open(name,'rb') as f:os.fsync(f.fileno())
  try:os.link(name,path)
  except FileExistsError:raise FileExistsError('Preserve existing output: '+str(path))
 finally:os.unlink(name)

def write_json_new(path,value):
 text=json.dumps(value,sort_keys=True,indent=2,allow_nan=False)+'\n'
 atomic_new(path,lambda p:p.write_text(text))

def write_npz_new(path,**arrays):
 def writer(p):
  with p.open('wb') as f:np.savez_compressed(f,**arrays)
 atomic_new(path,writer)

def verify_record(path,identity,*,status=None):
 record=read_json(path)
 if record.get('identity')!=identity or status and record.get('status')!=status:raise RuntimeError('Checkpoint identity/status mismatch: '+str(path))
 return record
