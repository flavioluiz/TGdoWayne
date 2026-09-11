"""Paired CPU benchmark, every target and both approved-pilot levels.

Loads only needed arrays; load/decompression is timed separately. Calls alternate
reference/optimized order. No source/protocol is modified or globally patched.
"""
from pathlib import Path
import hashlib,json,sys,time
import numpy as np
ROOT=Path.cwd();HERE=Path(__file__).resolve().parent;sys.path[:0]=[str(ROOT/'src'),str(HERE)]
from inference import iid_diagnostics as ref
import iid_optimized as opt
from test_optimized import compare

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def payload(a,j,cuts,truth_logl,optimized):
    x=a['x_unit'][:,:,j];w=a['log_weights'][:,:,j]
    context=opt.TargetIIDContext(w)if optimized else None
    rows=[]
    for p in range(5):
        t=np.r_[a['truth_unit'][j,p],cuts[p]]
        rows.extend(context.cdf(x[:,:,p],t)if optimized else ref.replicated_cdf(x[:,:,p],w,t))
    rows.extend(context.cdf(a['log_likelihood'][:,:,j],[truth_logl])if optimized else ref.replicated_cdf(a['log_likelihood'][:,:,j],w,[truth_logl]))
    weights=context.weights()if optimized else ref.replicated_weights(w)
    return {'cdf_rows':rows,'weights':weights}

def main():
    rawroot=ROOT/'tmp/c07_iid_gmm_approved/results';data=[];loadtimes=[];paths=[]
    for n in (16384,65536):
        p=rawroot/f'iid_N{n}.npz';paths.append(p);start=time.perf_counter()
        with np.load(p,allow_pickle=False)as f:
            data.append({k:f[k]for k in ['x_unit','log_weights','log_likelihood','truth_unit','probabilities','targets']})
        loadtimes.append(time.perf_counter()-start)
    truthpath=rawroot/'truth_likelihood.json';truth=json.loads(truthpath.read_text());rows=[];maxdiff=0.;different=0
    for level,a in enumerate(data):
        for j,target in enumerate(a['targets']):
            low=data[0];q=np.array([ref.weighted_quantiles(low['x_unit'][:,:,j,p].ravel(),low['log_weights'][:,:,j].ravel(),low['probabilities'])for p in range(5)])
            outputs={};times={}
            for name in (['reference','optimized']if (level*16+j)%2==0 else ['optimized','reference']):
                start=time.perf_counter();outputs[name]=payload(a,j,q,truth['truth_log_likelihood'][j],name=='optimized');times[name]=time.perf_counter()-start
            differences=compare(outputs['reference'],outputs['optimized']);maximum=max((d['absolute_difference']for d in differences),default=0.)
            maxdiff=max(maxdiff,maximum);different+=len(differences)
            rows.append({'N':a['x_unit'].shape[1],'target':int(target),'seconds':times,'speedup':times['reference']/times['optimized'],
                'maximum_field_difference':maximum,'different_float_fields':len(differences),'all_flags_exact':True})
    paths.extend([Path(__file__),HERE/'iid_optimized.py',HERE/'test_optimized.py',Path(ref.__file__),truthpath])
    result={'label':'PAIRED_IID_CHECKER_BENCHMARK_ALL16_TARGETS_BOTH_LEVELS','rows':rows,
        'load_and_decompression_seconds':loadtimes,'paired_median_speedup':float(np.median([x['speedup']for x in rows])),
        'reference_total_seconds':sum(x['seconds']['reference']for x in rows),
        'optimized_total_seconds':sum(x['seconds']['optimized']for x in rows),
        'maximum_field_difference':maxdiff,'different_float_fields':different,'all_flags_exact':True,
        'source_hashes':{str(p):sha(p)for p in paths}}
    (HERE/'results/benchmark.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items()if k not in ['rows','source_hashes']},indent=2))

if __name__=='__main__':main()
