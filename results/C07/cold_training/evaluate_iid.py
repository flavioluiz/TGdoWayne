"""Independent IID evaluation of two already-frozen cold proposals."""
from pathlib import Path
import hashlib,json,resource,sys,time
import numpy as np
from scipy.special import expit
ROOT=Path.cwd();HERE=Path(__file__).resolve().parent;S=ROOT/'tmp/c07_sampler';M=ROOT/'tmp/c07_memory_kernel'
sys.path[:0]=[str(ROOT/'src'),str(S),str(M),str(ROOT/'tmp/c07_iid_gmm')]
from inference.model import experiment
from cubic_even import EvenThresholdCubicORF
from preallocated_cubic import PreallocatedCubicPointLikelihood
from linalg_batch import forward_substitution
from gaussian_adapter import GaussianIIDAdapter
from proposal import unit_log_prior_jacobian
TABLE=S/'results/table_beta8193_local.npz';CONFIG=ROOT/'configs/calibration/pilot_initial.json';DATA=ROOT/'results/C07/fixtures/pilot_data.npz'
N=32768;R=4;TARGETS=np.array([62]);BATCH=512

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def main():
    settings=dict(N=N,replicates=R,targets=TARGETS.tolist(),training_steps=[4096,8192],seeds=[907103301,907103302],maximum_likelihood_values=300000,maximum_estimated_numeric_bytes=2*1024**3,
                  scope='Selected pilot target only. Proposals frozen before this production. Truth loaded only after training for output diagnostics, never to choose samples or proposals.')
    if 2*N*R>settings['maximum_likelihood_values']:raise RuntimeError('Budget exceeded.')
    (HERE/'evaluation_config.json').write_text(json.dumps(settings,indent=2)+'\n')
    files=[Path(__file__),CONFIG,DATA,TABLE,M/'preallocated_cubic.py',S/'cubic_even.py',S/'cubic.py',S/'pointwise.py',S/'linalg_batch.py',S/'mixture_proposal.py',S/'mixture_proposal_v2.py',ROOT/'tmp/c07_iid_gmm/gaussian_adapter.py',ROOT/'tmp/c07_iid_gmm/proposal.py']+[HERE/'results'/f'warmup{s}_proposal.json' for s in settings['training_steps']]
    sources={str(p.relative_to(ROOT)):sha(p) for p in files}
    for p in files:
        if p.suffix in ['.py','.json']:
            out=HERE/'evaluation_sources'/p.relative_to(ROOT);out.parent.mkdir(parents=True,exist_ok=True);out.write_bytes(p.read_bytes())
    (HERE/'evaluation_source_manifest.json').write_text(json.dumps(sources,indent=2)+'\n')
    cfg=json.loads(CONFIG.read_text());e=experiment(cfg);bounds=np.array(cfg['prior']['bounds']);width=np.diff(bounds,axis=1).ravel()
    with np.load(DATA,allow_pickle=False) as p:data={k:p[k].copy() for k in ['q','x_physical','x_gaussian','truth']}
    with np.load(TABLE,allow_pickle=False) as p:nodes=p['nodes'];matrices=p['matrices']
    start=time.perf_counter();table=EvenThresholdCubicORF(nodes,matrices,coordinate='beta');lk=PreallocatedCubicPointLikelihood(e,data,table);lk.solve=forward_substitution
    setup_seconds=time.perf_counter()-start
    print(json.dumps(dict(setup_complete=True,seconds=setup_seconds,maxrss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)),flush=True)
    rows=[]
    for steps,seed in zip(settings['training_steps'],settings['seeds']):
        dest=HERE/'results'/f'cold{steps}_iid_N{N}.npz'
        if dest.exists():raise FileExistsError('Preserve the earlier independent evaluation.')
        trained=json.loads((HERE/'results'/f'warmup{steps}_proposal.json').read_text());q=GaussianIIDAdapter(trained)
        xs=[];zs=[];lls=[];lqs=[];lps=[];lws=[];rep=[];started=time.perf_counter()
        for r,child in enumerate(np.random.SeedSequence(seed).spawn(R)):
            before=time.perf_counter();z,_=q.sample(np.random.default_rng(child),N);x=expit(z);logq=q.logpdf(z);logprior=unit_log_prior_jacobian(z)
            theta=(bounds[:,0]+width*x).reshape(-1,5);ids=np.full(len(theta),62);ll=np.empty(len(theta))
            for first in range(0,len(theta),BATCH):ll[first:first+BATCH]=lk(theta[first:first+BATCH],ids[first:first+BATCH])
            ll=ll[:,None];logw=ll+logprior-logq
            if not all(np.isfinite(a).all() for a in [ll,logw,logq,logprior]):raise ArithmeticError('Nonfinite IID value.')
            xs.append(x);zs.append(z);lls.append(ll);lqs.append(logq);lps.append(logprior);lws.append(logw)
            rep.append(dict(replicate=r,spawn_key=list(child.spawn_key),seconds=time.perf_counter()-before));print(json.dumps(dict(training_steps=steps,**rep[-1])),flush=True)
        with dest.open('xb') as f:np.savez_compressed(f,x_unit=np.array(xs),z=np.array(zs),log_weights=np.array(lws),log_likelihood=np.array(lls),log_proposal=np.array(lqs),log_prior_logit=np.array(lps),targets=TARGETS,truth_unit=(data['truth'][[14]]-bounds[:,0])/width,prior_bounds=bounds,probabilities=cfg['quantiles'],models=cfg['models'])
        truth_ll=lk(data['truth'][[14]],TARGETS)
        (HERE/'results'/f'cold{steps}_truth_likelihood.json').write_text(json.dumps(dict(targets=[62],truth_log_likelihood=truth_ll.tolist(),table_sha256=sha(TABLE),data_sha256=sha(DATA),source_sha256=sources),indent=2)+'\n')
        rows.append(dict(training_steps=steps,seed=seed,replicates=rep,seconds=time.perf_counter()-started,file=str(dest.relative_to(ROOT)),sha256=sha(dest)))
    assert all(sha(ROOT/p)==h for p,h in sources.items())
    result=dict(status='INDEPENDENT_IID_EVALUATION_COMPLETED_AWAITING_DIAGNOSTICS',settings=settings,levels=rows,setup_seconds=setup_seconds,source_unchanged=True,source_sha256=sources,darwin_maxrss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    (HERE/'results/evaluation_summary.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(rows,indent=2),flush=True)
if __name__=='__main__':main()
