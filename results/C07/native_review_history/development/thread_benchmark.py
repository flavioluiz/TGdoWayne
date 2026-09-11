from full_benchmark import *
from concurrent.futures import ThreadPoolExecutor

def main():
 cfg=json.loads((ROOT/'configs/calibration/pilot_initial.json').read_text());e=experiment(cfg);data=dict(np.load(ROOT/'results/C07/fixtures/pilot_data.npz'))
 path=ROOT/'tmp/c07_sampler/results/table_beta8193_local.npz';tab=np.load(path)
 table=EvenThresholdCubicORF(tab['nodes'],tab['matrices']);model=CubicPointLikelihood(e,data,table);model.solve=forward_substitution;native=NativePrototype(model)
 rng=np.random.default_rng(707950003);bounds=np.array(cfg['prior']['bounds']);theta=bounds[:,0]+rng.random((65536,5))*np.diff(bounds,axis=1)[:,0];ids=np.arange(len(theta))%80
 tasks=[(theta[j:j+2048],ids[j:j+2048]) for j in range(0,len(theta),2048)]
 reference=np.concatenate([native(*t) for t in tasks]);results=[]
 for threads in [1,2,4,6]:
  times=[]
  with ThreadPoolExecutor(max_workers=threads) as pool:
   for _ in range(4):
    start=time.perf_counter();out=np.concatenate(list(pool.map(lambda pair:native(*pair),tasks)));times.append(time.perf_counter()-start)
    np.testing.assert_array_equal(out,reference)
  results.append({'threads':threads,'times':times,'median':float(np.median(times)),'all_outputs_bitwise_equal':True})
 result={'N':len(theta),'batch':2048,'cases':results,'source_sha256':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [Path(__file__),HERE/'full_benchmark.py',HERE/'full.cpp']},'note':'Same fixed input arrays; no random number generation in worker threads. Shared read-only banks; elapsed times depend on concurrent machine load.'}
 (HERE/'thread_benchmark.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
