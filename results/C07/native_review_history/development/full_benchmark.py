from pathlib import Path
import ctypes,sys,time,json,hashlib
import numpy as np
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'tmp/c07_sampler')]
from inference.model import experiment
from cubic_even import EvenThresholdCubicORF
from cubic import CubicPointLikelihood
from linalg_batch import forward_substitution

lib=ctypes.CDLL(str(HERE/'full.dylib'))
ptr=np.ctypeslib.ndpointer(dtype=np.float64,flags='C_CONTIGUOUS')
cp=np.ctypeslib.ndpointer(dtype=np.complex128,flags='C_CONTIGUOUS')
idx=np.ctypeslib.ndpointer(dtype=np.int64,flags='C_CONTIGUOUS')
lib.full_likelihood.argtypes=[ctypes.c_size_t]*5+[idx,ptr,idx]+[ptr]*5+[cp]+[ptr]*3+[cp]+[ptr]*3
lib.full_likelihood.restype=ctypes.c_int64
class NativePrototype:
 def __init__(self,model):
  self.model=model;self.e=model.e;self.n=model.n;self.table=model.table
  self.K=len(self.e['f']);self.P=len(self.e['points']);self.D=len(self.e['H'])
  il,jl=np.tril_indices(self.D)
  self.packed=np.ascontiguousarray(model.covbank[...,il,jl])
  self.red2=np.ascontiguousarray(self.e['red']**2);self.white2=np.ascontiguousarray(self.e['sigma']**2)
  self.q=np.ascontiguousarray(model.data['q']);self.y=np.ascontiguousarray(model.y);self.z=np.ascontiguousarray(model.z)
  self.means=np.ascontiguousarray(model.meanbank);self.gamma=np.ascontiguousarray(self.table.coeff)
  self.weights=np.ascontiguousarray(self.e['weights'])
 def __call__(self,theta,targets):
  theta=np.asarray(theta,float);targets=np.asarray(targets)
  if theta.ndim!=2 or theta.shape[1]!=5 or targets.shape!=(len(theta),) or targets.dtype.kind not in 'iu' or not np.isfinite(theta).all():raise ValueError('invalid batch')
  if np.any((targets<0)|(targets>=5*self.n)):raise ValueError('invalid target')
  seg,f=self.table.location(theta[:,0]);pg,pr,pw=self.model.weights(theta);out=np.empty(len(theta))
  args=[np.ascontiguousarray(seg,dtype=np.int64),np.ascontiguousarray(f),np.ascontiguousarray(targets,dtype=np.int64),
        np.ascontiguousarray(pg),np.ascontiguousarray(pr),np.ascontiguousarray(pw),self.means,self.packed,self.gamma,
        self.red2,self.white2,self.weights,self.q,self.y,self.z,out]
  err=lib.full_likelihood(len(theta),self.n,self.K,self.P,self.D,*args)
  if err:raise np.linalg.LinAlgError(f'native failure point {err}')
  if not np.isfinite(out).all():raise ValueError('nonfinite likelihood')
  return out

def main():
 cfg=json.loads((ROOT/'configs/calibration/pilot_initial.json').read_text());e=experiment(cfg)
 data=dict(np.load(ROOT/'results/C07/fixtures/pilot_data.npz'))
 path=ROOT/'tmp/c07_sampler/results/table_beta8193_local.npz';tab=np.load(path)
 start=time.perf_counter();table=EvenThresholdCubicORF(tab['nodes'],tab['matrices']);model=CubicPointLikelihood(e,data,table);model.solve=forward_substitution
 native=NativePrototype(model);print('initialization',time.perf_counter()-start,flush=True)
 bounds=np.array(cfg['prior']['bounds']);rng=np.random.default_rng(707950002);rows=[]
 for name,x,ids in [('prior',rng.random((16384,5)),np.arange(16384)%80)]:
  theta=bounds[:,0]+x*np.diff(bounds,axis=1)[:,0];all0=[];all1=[];timings={'numpy':[],'native':[]}
  for j in range(0,len(theta),1024):
   a=theta[j:j+1024];t=ids[j:j+1024]
   start=time.perf_counter();v0=model(a,t);timings['numpy'].append(time.perf_counter()-start)
   start=time.perf_counter();v1=native(a,t);timings['native'].append(time.perf_counter()-start)
   all0.append(v0);all1.append(v1)
  aa=np.concatenate(all0);bb=np.concatenate(all1);diff=abs(aa-bb)
  relevant=np.zeros(len(ids),bool)
  for target in np.unique(ids):
   ix=ids==target;relevant[ix]=aa[ix]>=aa[ix].max()-30
  rows.append(dict(name=name,N=len(theta),max_abs_logL=float(diff.max()),max_abs_relevant=float(diff[relevant].max()),
      maximum_relative=float(np.max(diff/(1+abs(aa)))),timings=timings,speedup=float(sum(timings['numpy'])/sum(timings['native']))))
 sources=[Path(__file__),HERE/'full.cpp'];result=dict(cases=rows,source_sha256={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources},table_sha256=hashlib.sha256(path.read_bytes()).hexdigest())
 (HERE/'full_benchmark.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
