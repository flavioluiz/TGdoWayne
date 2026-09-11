"""Independent projection checks and exact RNG-recipe comparison of vectorization."""
import os
os.environ.setdefault('VECLIB_MAXIMUM_THREADS', '1')
from pathlib import Path
import ast, hashlib, json, sys, time
import numpy as np
from scipy.stats import norm, t
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent
sys.path[:0]=[str(ROOT/'tmp/c07_sampler'),str(HERE)]
from multiple_rhs import MultipleRHSGaussianDefensiveProposal
from vector_sample import sample_single_target

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    # Freeze the complete peer files and execute only the two actual functions.
    # This avoids importing an in-development campaign or substituting our formula.
    source=ROOT/'tmp/c07_inference_portable/src/inference/campaign_iid.py'
    helper=source.with_name('campaign_io.py')
    ns={'np':np}
    for path,name in [(helper,'positive_int'),(source,'sample_single_target')]:
        code=path.read_bytes();out=HERE/'sampler_executed_sources'/path.relative_to(ROOT)
        out.parent.mkdir(parents=True,exist_ok=True);out.write_bytes(code)
        module=ast.parse(code);fn=next(x for x in module.body if isinstance(x,ast.FunctionDef) and x.name==name)
        exec(compile(ast.Module(body=[fn],type_ignores=[]),str(out),'exec'),ns)
    reference=ns['sample_single_target']
    training=ROOT/'tmp/c07_sampler/results/mixture_training.json'
    meta=json.loads(training.read_text());directions=np.vstack((np.eye(5),np.arange(1,6)/np.linalg.norm(np.arange(1,6)),np.array([1,-1,1,-1,1])/np.sqrt(5)))
    checks=[];equivalence=[];timings=[];negative=[]
    N=65536;seed=907103502
    for index,row in enumerate(meta['records']):
        q=MultipleRHSGaussianDefensiveProposal(*[np.array([row[k]]) for k in ['weights','means','covariances','global_mean','global_cholesky']],defensive_fraction=meta['defensive_student_fraction'],student_df=meta['student_df'],student_scale=meta['student_scale'])
        rng1=np.random.default_rng(np.random.SeedSequence([seed,index]));rng2=np.random.default_rng(np.random.SeedSequence([seed,index]))
        begin=time.perf_counter();old,c1=reference(q,rng1,N);oldtime=time.perf_counter()-begin
        begin=time.perf_counter();new,c2=sample_single_target(q,rng2,N);newtime=time.perf_counter()-begin
        error=float(abs(old-new).max());logq_error=float(abs(q.logpdf(old)-q.logpdf(new)).max())
        assert error<2e-12 and logq_error<2e-12
        assert np.array_equal(c1,c2) and rng1.bit_generator.state==rng2.bit_generator.state
        equivalence.append(dict(target=row['target'],maximum_sample_absolute_difference=error,maximum_logq_difference=logq_error,components_identical=True,rng_state_identical=True))
        timings.append(dict(target=row['target'],reference_seconds=oldtime,grouped_seconds=newtime))
        # The pushforward onto directions has known univariate mixture CDF.
        # Joint directions test covariance orientation beyond marginal checks.
        for j,v in enumerate(directions):
            means=q.means[0]@v;sd=np.sqrt(np.einsum('i,kij,j->k',v,q.cov[0],v))
            gm=q.global_mean[0]@v;gs=np.sqrt(v@(q.global_chol[0]@q.global_chol[0].T)@v)*np.sqrt((q.nu-2)/q.nu)*q.scale
            for offset in [-1,0,1]:
                cut=gm+offset*gs;prob=(1-q.alpha)*np.dot(q.weights[0],norm.cdf((cut-means)/sd))+q.alpha*t.cdf((cut-gm)/gs,df=q.nu)
                found=float(np.mean(new@v<=cut));se=float(np.sqrt(prob*(1-prob)/N));score=abs(found-prob)/se
                checks.append(dict(target=row['target'],projection=j,cut=float(cut),expected_cdf=float(prob),observed_cdf=found,exact_iid_binomial_se=se,standardized_difference=float(score)))
        if index==0:
            for invalid in [0,-1,True,1.5,np.nan]:
                try:sample_single_target(q,np.random.default_rng(1),invalid)
                except ValueError:negative.append(repr(invalid))
                else:raise AssertionError('Invalid sample count accepted.')
    critical=float(norm.isf(.05/(2*len(checks))));maximum=max(x['standardized_difference'] for x in checks)
    assert maximum<critical
    # These files should be stable during this isolated audit.
    frozen=HERE/'sampler_executed_sources'
    assert source.read_bytes()==(frozen/source.relative_to(ROOT)).read_bytes()
    assert helper.read_bytes()==(frozen/helper.relative_to(ROOT)).read_bytes()
    sources=[Path(__file__),HERE/'vector_sample.py',HERE/'multiple_rhs.py',source,helper,training,ROOT/'tmp/c07_sampler/mixture_proposal_v2.py',ROOT/'tmp/c07_sampler/mixture_proposal.py',ROOT/'tmp/c07_sampler/linalg_batch.py']
    for p in sources:
        out=frozen/p.relative_to(ROOT);out.parent.mkdir(parents=True,exist_ok=True);out.write_bytes(p.read_bytes())
    result=dict(status='PASS_SAME_MIXTURE_AND_VECTOR_RNG_RECIPE',seed=seed,N_per_target=N,targets=len(meta['records']),projection_checks=len(checks),maximum_standardized_cdf_difference=maximum,bonferroni_normal_critical=critical,checks=checks,equivalence=equivalence,timings=timings,invalid_counts_rejected=negative,source_sha256={str(p.relative_to(ROOT)):sha(p) for p in sources},limitations=['Normal/binomial comparison is a finite simulation check, not proof of arbitrary tails.','This seed-per-target vector recipe is a prospective execution distinct from the historical per-column SeedSequence recipe.','Both samplers consume identical PCG64 arrays and end in identical RNG states; BLAS accumulation changes samples by roundoff only.'])
    with (HERE/'sampler_audit.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ['checks','source_sha256']},indent=2))

if __name__=='__main__':main()
