"""Two independent IID importance levels under a frozen, numerically validated ORF8336 table."""
from pathlib import Path
import hashlib,json,os,platform,sys,time
import numpy as np
import scipy
from scipy.special import expit
ROOT=Path.cwd();HERE=Path(__file__).resolve().parent;SAMPLER=ROOT/'tmp/c07_sampler'
sys.path[:0]=[str(ROOT/'src'),str(SAMPLER),str(HERE)]
from inference.model import experiment
from inference.likelihood_reference import Likelihood
from cubic import CubicPointLikelihood
from cubic_even import EvenThresholdCubicORF
from linalg_batch import forward_substitution
from proposal import unit_log_prior_jacobian
from gaussian_adapter import GaussianIIDAdapter

TARGETS=np.array([0,3,8,9,11,14,20,25,28,35,46,51,52,62,67,78])
LEVELS=[16384,65536];REPLICATES=4;SEED=907102102;BATCH=512
CONFIG=ROOT/'configs/calibration/pilot_initial.json';DATA=ROOT/'results/C07/fixtures/pilot_data.npz'
PROPOSAL=SAMPLER/'results/pilot553_refresh.json';TABLE=SAMPLER/'results/table_beta8193_local.npz'
TRAINING=SAMPLER/'results/mixture_training.json'
RESULTS=HERE/'results';RESULTS.mkdir(exist_ok=True)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def main():
    if (RESULTS/'summary.json').exists() or any(RESULTS.glob('iid_N*.npz')):raise FileExistsError('Preserve the existing IID experiment; use a new directory for another execution.')
    cfg=json.loads(CONFIG.read_text());fit=json.loads(PROPOSAL.read_text());e=experiment(cfg)
    with np.load(DATA,allow_pickle=False) as p:data={k:p[k].copy() for k in p.files}
    assert sha(CONFIG)==fit['config_sha256'] and sha(DATA)==fit['data_sha256']
    validation=json.loads((SAMPLER/'results/dense_local_validation.json').read_text())
    assert validation['passes_tested_domain'] and sha(TABLE)==validation['table_sha256'][str(TABLE)]
    index=np.array([fit['targets'].index(int(t)) for t in TARGETS]);mean=np.asarray(fit['mean'])[index];chol=np.asarray(fit['cholesky'])[index]
    training=json.loads(TRAINING.read_text())
    assert training['targets']==TARGETS.tolist()
    proposal=GaussianIIDAdapter(training)
    bounds=np.asarray(cfg['prior']['bounds']);width=np.diff(bounds,axis=1).ravel()
    # Arrays: retained z,x and four scalar logs, plus components; moment banks,
    # cubic table and a conservative allowance for likelihood batch intermediates.
    retained=REPLICATES*max(LEVELS)*len(TARGETS)*(2*5*8+4*8+1)
    estimate=int(max(3*1024**3,3*retained+1024**3))
    workload=int(sum(LEVELS)*REPLICATES*len(TARGETS))
    if estimate>3*1024**3 or workload>6_000_000:raise RuntimeError('Explicit IID experiment budget exceeded.')
    config=dict(targets=TARGETS.tolist(),levels=LEVELS,replicates=REPLICATES,seed=SEED,batch=BATCH,
                family='four_gaussians_plus_defensive_student',student_df=training['student_df'],student_scale=training['student_scale'],defensive_fraction=training['defensive_student_fraction'],training_file=str(TRAINING),training_sha256=sha(TRAINING),proposal_component_recording='255 means unknown: frozen sampler does not expose component labels; density is always the full mixture.',child_rng_recipe='Each replicate RNG supplies four uint32 entropy words; SeedSequence(entropy).spawn(N) supplies one IID column per child.',
                mean=mean.tolist(),cholesky=chol.tolist(),mh_logscale_used=False,
                maximum_likelihood_values=6_000_000,estimated_peak_numeric_bytes=estimate,maximum_estimated_numeric_bytes=3*1024**3,
                actual_likelihood_values=workload,proposal_fit=str(PROPOSAL),table=str(TABLE),
                scope='Selected16 targets, fresh IID importance only. ORF8336 passes the frozen numerical test domain; no SBC500. Proposal training remains historical, independent of this production.',
                coordinates='z in R5; x_unit=sigmoid(z); physical=lower+width*x_unit',
                full_weight='L(theta)*prod(sigmoid(z)*sigmoid(-z))/q_z(z); rectangular-prior volume cancels exactly.',
                numpy=np.__version__,scipy=scipy.__version__,platform=platform.platform(),VECLIB_MAXIMUM_THREADS=os.environ.get('VECLIB_MAXIMUM_THREADS','unset'))
    (HERE/'config.json').write_text(json.dumps(config,indent=2)+'\n')
    paths=[Path(__file__),HERE/'PROSPECTIVO.json',SAMPLER/'results/dense_local_validation.json',HERE/'proposal.py',HERE/'gaussian_adapter.py',CONFIG,DATA,PROPOSAL,TABLE,TRAINING]+[SAMPLER/name for name in ['cubic.py','cubic_even.py','pointwise.py','linalg_batch.py','mixture_proposal.py','mixture_proposal_v2.py']]+[ROOT/'src/inference'/name for name in ['model.py','likelihood_reference.py']]
    paths+=list((ROOT/'src/pta').glob('*.py'))
    source={str(p.relative_to(ROOT)):sha(p) for p in paths}
    snapshot=HERE/'executed_sources'
    for p in paths:
        # Input tables/data are hashed in place; source and configuration bytes saved.
        if p.suffix in ['.py','.json']:
            target=snapshot/p.relative_to(ROOT);target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(p.read_bytes())
    (HERE/'source_manifest.json').write_text(json.dumps(source,indent=2)+'\n')
    begin=time.perf_counter()
    with np.load(TABLE,allow_pickle=False) as p:table=EvenThresholdCubicORF(p['nodes'],p['matrices'],coordinate='beta')
    likelihood=CubicPointLikelihood(e,data,table);likelihood.solve=forward_substitution
    setup_seconds=time.perf_counter()-begin
    # Independent reference evaluates the same interpolated Gamma, isolating the
    # pointwise likelihood implementation from interpolation accuracy.
    reference=Likelihood(e,data['q'],data['x_physical'],data['x_gaussian'])
    theta=bounds[:,0]+width*expit(mean)
    actual=likelihood(theta,TARGETS);expected=np.array([reference(t[None,1:],table(np.array([t[0]]))[0])[0,target] for t,target in zip(theta,TARGETS)])
    error=float(np.max(abs(actual-expected)))
    if error>1e-7:raise AssertionError(('Likelihood implementation mismatch at matched interpolated Gamma',error))
    seed_children=np.random.SeedSequence(SEED).spawn(len(LEVELS)*REPLICATES)
    rows=[]
    for level,n in enumerate(LEVELS):
        start=time.perf_counter();zs=[];xs=[];lls=[];lqs=[];lps=[];lws=[];components=[];replicate_rows=[]
        for r in range(REPLICATES):
            child=seed_children[level*REPLICATES+r];rng=np.random.default_rng(child);t0=time.perf_counter()
            z,component=proposal.sample(rng,n);x=expit(z);logq=proposal.logpdf(z);logprior=unit_log_prior_jacobian(z)
            physical=(bounds[:,0]+width*x).reshape(-1,5);ids=np.broadcast_to(TARGETS,(n,len(TARGETS))).ravel();ll=np.empty(len(ids))
            for first in range(0,len(ids),BATCH):ll[first:first+BATCH]=likelihood(physical[first:first+BATCH],ids[first:first+BATCH])
            ll=ll.reshape(n,len(TARGETS));logw=ll+logprior-logq
            if not all(np.isfinite(a).all() for a in [z,x,ll,logq,logprior,logw]):raise ArithmeticError('Nonfinite sample or importance weight.')
            zs.append(z);xs.append(x);lls.append(ll);lqs.append(logq);lps.append(logprior);lws.append(logw);components.append(component.astype(np.uint8))
            row=dict(replicate=r,spawn_key=list(child.spawn_key),seconds=time.perf_counter()-t0,
                     saturated_coordinate_count=int(np.count_nonzero((x==0)|(x==1))),maximum_abs_logit=float(np.max(abs(z))))
            replicate_rows.append(row);print(json.dumps(dict(level_N=n,**row)),flush=True)
        payload=dict(z=np.asarray(zs),x_unit=np.asarray(xs),log_weights=np.asarray(lws),log_likelihood=np.asarray(lls),
                     log_proposal=np.asarray(lqs),log_prior_logit=np.asarray(lps),proposal_component=np.asarray(components),
                     targets=TARGETS,truth_unit=(data['truth'][TARGETS%len(data['q'])]-bounds[:,0])/width,prior_bounds=bounds,
                     probabilities=np.asarray(cfg['quantiles']),models=np.asarray(cfg['models']),seed=SEED)
        dest=RESULTS/f'iid_N{n}.npz'
        with dest.open('xb') as f:np.savez_compressed(f,**payload)
        row=dict(N=n,replicates=replicate_rows,seconds=time.perf_counter()-start,output=str(dest.relative_to(ROOT)),sha256=sha(dest),bytes=dest.stat().st_size)
        rows.append(row)
        del payload,zs,xs,lls,lqs,lps,lws,components
    unchanged=all(sha(ROOT/p)==digest for p,digest in source.items())
    if not unchanged:raise RuntimeError('A frozen input or source changed during IID production.')
    summary=dict(status='IID_PRODUCED_AWAITING_DIAGNOSTICS_APPROVED_ORF8336',configuration=config,levels=rows,
                 likelihood_reference_max_abs_difference=error,reference_comparison='Same interpolated matrices; independent table validation is in dense_local_validation.json.',
                 setup_seconds=setup_seconds,total_seconds=time.perf_counter()-begin,source_unchanged=True,source_sha256=source,
                 cubic_fallback_intervals=table.fallback.tolist(),production_adaptation=False,prior_replaced=False,posterior_calibration_claimed=False)
    (RESULTS/'summary.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps({k:summary[k] for k in ['status','likelihood_reference_max_abs_difference','setup_seconds','total_seconds']},indent=2))
if __name__=='__main__':main()
