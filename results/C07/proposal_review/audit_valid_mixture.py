"""Independent normalized-density, joint sampling and MC-normalization checks."""
from pathlib import Path
import hashlib,json,sys,time
import numpy as np
from scipy.special import logsumexp
from scipy.stats import multivariate_normal,multivariate_t,norm,t
ROOT=Path.cwd();HERE=Path(__file__).resolve().parent;S=ROOT/'tmp/c07_sampler';sys.path[:0]=[str(S),str(ROOT/'src')]
from mixture_proposal import GaussianDefensiveProposal

def main():
    start=time.perf_counter();meta=json.loads((S/'results/mixture_training.json').read_text());r=meta['records']
    w=np.array([a['weights'] for a in r]);m=np.array([a['means'] for a in r]);c=np.array([a['covariances'] for a in r]);gm=np.array([a['global_mean'] for a in r]);gc=np.array([a['global_cholesky'] for a in r])
    proposal=GaussianDefensiveProposal(w,m,c,gm,gc);T,K,D=m.shape;alpha=.15;nu=5;scale=3
    rng=np.random.default_rng(907101901);z=gm[:,None,:]+rng.normal(size=(T,257,D))*4
    actual=proposal.logpdf(z.reshape(-1,D)).reshape(T,-1);reference=np.empty_like(actual)
    for target in range(T):
        terms=[np.log((1-alpha)*weight)+multivariate_normal.logpdf(z[target],mean=mean,cov=cov) for weight,mean,cov in zip(w[target],m[target],c[target])]
        terms.append(np.log(alpha)+multivariate_t.logpdf(z[target],loc=gm[target],shape=(nu-2)/nu*scale**2*(gc[target]@gc[target].T),df=nu))
        reference[target]=logsumexp(terms,axis=0)
    density_error=float(abs(actual-reference).max());assert density_error<1e-10
    # Sampling API uses target-major batches, one independent RNG per column.
    child=np.random.SeedSequence(907101902).spawn(1024);rngs=[np.random.default_rng(s) for s in child]
    blocks=[proposal.sample(rngs).reshape(T,1024,D) for _ in range(64)]
    samples=np.concatenate(blocks,axis=1);del blocks;N=samples.shape[1]
    directions=np.vstack([np.eye(D),np.arange(1,D+1)/np.linalg.norm(np.arange(1,D+1)),np.array([1.,-1.,1.,-1.,1.])/np.sqrt(5)])
    checks=[]
    for target in range(T):
        for j,v in enumerate(directions):
            mu=m[target]@v;sd=np.sqrt(np.einsum('i,kij,j->k',v,c[target],v));global_mu=gm[target]@v;global_sd=np.sqrt(v@(gc[target]@gc[target].T)@v)*np.sqrt((nu-2)/nu)*scale
            # Fixed cuts from proposal parameters, independent of production samples.
            for offset in [-1.,0.,1.]:
                cut=global_mu+offset*global_sd
                exact=(1-alpha)*np.sum(w[target]*norm.cdf((cut-mu)/sd))+alpha*t.cdf((cut-global_mu)/global_sd,df=nu)
                found=np.mean(samples[target]@v<=cut);se=np.sqrt(exact*(1-exact)/N);score=abs(found-exact)/se
                checks.append(dict(target=int(meta['targets'][target]),projection=j,cut=float(cut),expected_CDF=float(exact),sample_CDF=float(found),exact_binomial_standard_error=float(se),standardized_difference=float(score)))
    maximum=max(a['standardized_difference'] for a in checks);assert maximum<6
    # Independent, heavier Student envelope: E_h[q/h]=1 over all R^5.
    # Here h is t_3(mean=global_mean, shape=4 LL^T), independent of q's sampler.
    replicates=[]
    for replicate in range(4):
        generator=np.random.default_rng(np.random.SeedSequence(907101903,spawn_key=(replicate,)))
        normal=generator.standard_normal((T,16384,D));chi=generator.chisquare(3,size=(T,16384))
        zz=gm[:,None]+2*np.einsum('tij,tnj->tni',gc,normal)*np.sqrt(3/chi)[:,:,None]
        lq=proposal.logpdf(zz.reshape(-1,D)).reshape(T,-1)
        lh=np.array([multivariate_t.logpdf(zz[k],loc=gm[k],shape=4*gc[k]@gc[k].T,df=3) for k in range(T)])
        ratios=np.exp(lq-lh);means=ratios.mean(axis=1);ses=ratios.std(axis=1,ddof=1)/np.sqrt(ratios.shape[1])
        replicates.append(dict(replicate=replicate,N=16384,integral=means.tolist(),MCSE=ses.tolist(),maximum_ratio=ratios.max(axis=1).tolist()))
    estimates=np.array([a['integral'] for a in replicates]);ses=np.array([a['MCSE'] for a in replicates]);pooled=estimates.mean(axis=0);pooled_se=np.sqrt(np.sum(ses**2,axis=0))/4;score=abs(pooled-1)/pooled_se
    assert score.max()<6
    manifest=json.loads((HERE/'source_manifest.json').read_text());unchanged=all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h for p,h in manifest.items());assert unchanged
    result=dict(status='PASS_VALID_FROZEN_TRAINING_FIXTURE',targets=meta['targets'],density_against_scipy_max_abs_difference=density_error,density_points=int(actual.size),
                sampling_N_per_target=N,sampling_joint_projection_CDF_checks=len(checks),maximum_standardized_sampling_CDF_difference=maximum,
                sampling_checks=checks,normalization_replicates=replicates,pooled_normalization=pooled.tolist(),pooled_normalization_MCSE=pooled_se.tolist(),maximum_standardized_normalization_difference=float(score.max()),
                normalization_meaning='Independent IID Student-t3 envelope integrates the entire normalized mixture over R5; finite-run MC check, not an exact integration proof.',
                source_unchanged=True,source_sha256=manifest,audit_source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),seconds=time.perf_counter()-start)
    (HERE/'valid_mixture_audit.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:result[k] for k in ['status','density_against_scipy_max_abs_difference','maximum_standardized_sampling_CDF_difference','maximum_standardized_normalization_difference','seconds']},indent=2))
if __name__=='__main__':main()
