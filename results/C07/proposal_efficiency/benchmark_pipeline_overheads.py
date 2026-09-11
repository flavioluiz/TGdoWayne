"""Proposal and lossless temporary I/O costs; no new scientific production."""
import os
os.environ.setdefault('VECLIB_MAXIMUM_THREADS','1')
from pathlib import Path
import hashlib,json,sys,time
import numpy as np
from scipy.special import expit
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent
sys.path[:0]=[str(ROOT/'tmp/c07_sampler'),str(ROOT/'tmp/c07_iid_gmm'),str(HERE)]
from multiple_rhs import MultipleRHSGaussianDefensiveProposal
from gaussian_adapter import GaussianIIDAdapter
from vector_sample import sample_single_target

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    trained=ROOT/'tmp/c07_cold_training/results/warmup8192_proposal.json'
    meta=json.loads(trained.read_text());old=GaussianIIDAdapter(meta)
    q=MultipleRHSGaussianDefensiveProposal(*[np.array([r[k] for r in meta['records']]) for k in ['weights','means','covariances','global_mean','global_cholesky']],defensive_fraction=meta['defensive_student_fraction'],student_df=meta['student_df'],student_scale=meta['student_scale'])
    N=65536;timings=[]
    for repeat in range(3):
        a=np.random.default_rng(907103503+repeat);b=np.random.default_rng(907103513+repeat)
        t=time.perf_counter();z,_=old.sample(a,N);old_sample=time.perf_counter()-t
        t=time.perf_counter();old.logpdf(z);old_density=time.perf_counter()-t
        t=time.perf_counter();new,_=sample_single_target(q,b,N);new_sample=time.perf_counter()-t
        t=time.perf_counter();q.logpdf(new);new_density=time.perf_counter()-t
        t=time.perf_counter();expit(new);(-np.logaddexp(0,-new)-np.logaddexp(0,new)).sum(axis=1);jac=time.perf_counter()-t
        timings.append(dict(repeat=repeat,old_sample_seconds=old_sample,old_density_seconds=old_density,new_sample_seconds=new_sample,new_density_seconds=new_density,expit_and_exact_jacobian_seconds=jac))
    source=ROOT/'tmp/c07_cold_final/results/cold8192_iid_N65536.npz'
    with np.load(source,allow_pickle=False) as p:
        arrays={k:p[k][0,:,0].copy() for k in ['z','x_unit','log_likelihood','log_weights','log_proposal','log_prior_logit']}
    arrays['proposal_component']=np.full(N,255,np.uint8)
    arrays['target']=np.array(62);arrays['replicate']=np.array(0)
    folder=HERE/'io_benchmark_files';folder.mkdir(exist_ok=False)
    records=[]
    for compressed in [True,False]:
        for repeat in range(3):
            path=folder/f'{"compressed" if compressed else "stored"}_{repeat}.npz'
            t=time.perf_counter()
            with path.open('xb') as f:(np.savez_compressed if compressed else np.savez)(f,**arrays)
            write_seconds=time.perf_counter()-t
            t=time.perf_counter();digest=sha(path);hash_seconds=time.perf_counter()-t
            t=time.perf_counter()
            with np.load(path,allow_pickle=False) as p:
                for key,value in arrays.items():assert np.array_equal(p[key],value)
            read_verify_seconds=time.perf_counter()-t
            records.append(dict(compressed=compressed,repeat=repeat,bytes=path.stat().st_size,write_seconds=write_seconds,hash_seconds=hash_seconds,read_and_exact_verify_seconds=read_verify_seconds,sha256=digest))
    report=dict(scope='Timing only; two RNG recipes generate different independent streams with unchanged proposal distribution. No posterior/precision claim.',N=N,proposal_timings=timings,io_timings=records,all_io_arrays_equal=True,compression_is_lossless=True,source_sha256={str(p.relative_to(ROOT)):sha(p) for p in [trained,source,Path(__file__),HERE/'multiple_rhs.py',HERE/'vector_sample.py',ROOT/'tmp/c07_iid_gmm/gaussian_adapter.py']})
    with (HERE/'pipeline_overheads.json').open('x') as f:json.dump(report,f,indent=2);f.write('\n')
    print(json.dumps(report,indent=2))

if __name__=='__main__':main()
