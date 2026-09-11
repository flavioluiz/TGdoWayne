from pathlib import Path
import ctypes,sys,time,json,hashlib
import numpy as np
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'tmp/c07_sampler')]
from inference.model import experiment
from cubic_even import EvenThresholdCubicORF
from cubic import CubicPointLikelihood

lib=ctypes.CDLL(str(HERE/'contract.dylib'))
ptr=np.ctypeslib.ndpointer(dtype=np.float64,flags='C_CONTIGUOUS')
idx=np.ctypeslib.ndpointer(dtype=np.int64,flags='C_CONTIGUOUS')
lib.contract_moments.argtypes=[ctypes.c_size_t]*3+[idx]+[ptr]*8
lib.contract_moments.restype=None

def native(model,theta):
    segment,f=model.table.location(theta[:,0])
    pg,pr,pw=model.weights(theta)
    n=len(theta);k=model.meanbank.shape[1];d=model.meanbank.shape[-1]
    mu=np.empty((n,k,d));cov=np.empty((n,k,d,d))
    lib.contract_moments(n,k,d,np.ascontiguousarray(segment,dtype=np.int64),np.ascontiguousarray(f),
        np.ascontiguousarray(pg),np.ascontiguousarray(pr),np.ascontiguousarray(pw),
        model.meanbank,model.covbank,mu,cov)
    return mu,cov

def main():
    cfg=json.loads((ROOT/'configs/calibration/pilot_initial.json').read_text());e=experiment(cfg)
    data=dict(np.load(ROOT/'results/C07/fixtures/pilot_data.npz'))
    tablepath=ROOT/'tmp/c07_sampler/results/table_beta8193_local.npz'
    if not tablepath.exists():
        raise FileNotFoundError(tablepath)
    tab=np.load(tablepath)
    print('table keys',tab.files,flush=True)
    nodes=tab['nodes'];matrices=tab['matrices']
    start=time.perf_counter();table=EvenThresholdCubicORF(nodes,matrices);model=CubicPointLikelihood(e,data,table)
    print('initialization seconds',time.perf_counter()-start,flush=True)
    rng=np.random.default_rng(707950001);bounds=np.array(cfg['prior']['bounds'])
    theta=bounds[:,0]+rng.random((4096,5))*np.diff(bounds,axis=1)[:,0]
    a=model.moments(theta);b=native(model,theta)
    differences=[float(np.max(abs(x-y)/(1+abs(x)))) for x,y in zip(a,b)]
    timings={}
    for name,fn in [('numpy',model.moments),('native',lambda t:native(model,t))]:
        times=[]
        for _ in range(8):
            s=time.perf_counter();fn(theta);times.append(time.perf_counter()-s)
        timings[name]=times
    original=model.moments
    ll0=model(theta,np.arange(len(theta))%80)
    model.moments=lambda t:native(model,t)
    ll1=model(theta,np.arange(len(theta))%80)
    model.moments=original
    result={'parameters':len(theta),'moment_scaled_errors':differences,
            'max_loglikelihood_absolute_difference':float(np.max(abs(ll0-ll1))),
            'median_speedup':float(np.median(timings['numpy'])/np.median(timings['native'])),
            'timings_seconds':timings,
            'source_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in [Path(__file__),HERE/'contract.cpp']}}
    (HERE/'benchmark.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
