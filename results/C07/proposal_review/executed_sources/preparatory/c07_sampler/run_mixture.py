from harness import *
from pointwise import UnitPosterior
from cubic import CertifiedCubicORF,CubicPointLikelihood
from linalg_batch import forward_substitution
from mixture_proposal import GaussianDefensiveProposal
from mh_mixture import FrozenMixtureMH
from inference.mcmc_optimized import target_diagnostics
from time import perf_counter
import hashlib,math
cfg,e,data=load();out=Path(__file__).resolve().parent/'results';training=json.loads((out/'mixture_training.json').read_text());rows=training['records'];ids=np.array(training['targets']);f=np.load(out/'table553.npz');table=CertifiedCubicORF(f['nodes'],f['matrices'],coordinate='alpha');lk=CubicPointLikelihood(e,data,table);lk.solve=forward_substitution;posterior=UnitPosterior(lk,cfg['prior']['bounds'])
q=GaussianDefensiveProposal(np.array([r['weights'] for r in rows]),np.array([r['means'] for r in rows]),np.array([r['covariances'] for r in rows]),np.array([r['global_mean'] for r in rows]),np.array([r['global_cholesky'] for r in rows]))
sampler=FrozenMixtureMH(posterior,ids,q,np.array([r['global_cholesky'] for r in rows]),np.array([r['random_walk_logscale'] for r in rows]),seed=7078611);n=len(ids);count=32768;name='pilot553_mixture';source_files=[Path(__file__),Path(__file__).with_name('mh_mixture.py'),Path(__file__).with_name('mixture_proposal.py'),Path(__file__).with_name('pointwise.py'),Path(__file__).with_name('cubic.py'),Path(__file__).with_name('linalg_batch.py')];sources={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in source_files};t=perf_counter()
draws=np.lib.format.open_memmap(out/(name+'_draws.npy'),mode='w+',dtype='float64',shape=(count,n,4,5));ll=np.lib.format.open_memmap(out/(name+'_loglikelihood.npy'),mode='w+',dtype='float64',shape=(count,n,4))
for _ in range(4096):sampler.step()
sampler.accept[:]=0;sampler.attempt[:]=0;print(json.dumps(dict(burn_in_done=True,seconds=perf_counter()-t)),flush=True)
for i in range(count):
 draws[i],ll[i]=sampler.step()
 if (i+1)%8192==0:print(json.dumps(dict(draw=i+1,seconds=perf_counter()-t)),flush=True)
draws.flush();ll.flush();sampling_seconds=perf_counter()-t
meta=dict(status='numerical_engineering_benchmark_unapproved_ORF553_not_SBC500',targets=ids.tolist(),models=cfg['models'],seed=7078611,chains=4,draws=count,burn_in=4096,thinning=1,production_adaptation=False,proposal_training_sha256=hashlib.sha256((out/'mixture_training.json').read_bytes()).hexdigest(),table_sha256=hashlib.sha256((out/'table553.npz').read_bytes()).hexdigest(),data_sha256=hashlib.sha256(DATA.read_bytes()).hexdigest(),config_sha256=hashlib.sha256(CONFIG.read_bytes()).hexdigest(),source_sha256=sources,source_unchanged_during_run=all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h for p,h in sources.items()),sampling_seconds=sampling_seconds,acceptance=(sampler.accept/sampler.attempt).tolist())
(out/(name+'.json')).write_text(json.dumps(meta,indent=2))
bounds=np.array(cfg['prior']['bounds']);truth=(data['truth'][ids%16]-bounds[:,0])/np.diff(bounds,axis=1)[:,0];lltruth=lk(data['truth'][ids%16],ids);diagnostics=[]
for j,target in enumerate(ids):
 r=target_diagnostics(draws[:,j],truth[j],loglikelihood=ll[:,j],loglikelihood_truth=float(lltruth[j]),names=cfg['parameters']);r['target']=int(target);diagnostics.append(r)
cs=[c for r in diagnostics for c in [*r['truth_cdfs'],*[q['cdf'] for q in r['quantiles']]]];summary=dict(targets=ids.tolist(),passes=sum(r['diagnostic_and_mc_precision_pass'] for r in diagnostics),diagnostic_floors_pass=sum(all(x['diagnostic_floor_pass'] for x in r['convergence'].values()) for r in diagnostics),maximum_rhat=max(x['rhat']['maximum'] for r in diagnostics for x in r['convergence'].values()),maximum_mcse=max(c['mcse'] for c in cs),maximum_tau=max(c.get('tau',float('inf')) for c in cs),cdf_count=len(cs),cdf_exceeds_mcse=sum(c['mcse']>.00335 for c in cs),cdf_bad_batches=sum(not c.get('batch_adequate',False) for c in cs),sampling_seconds=sampling_seconds,diagnostics_seconds=perf_counter()-t-sampling_seconds)
report=dict(summary=summary,diagnostics=diagnostics)
def clean(x):
 if isinstance(x,dict):return {k:clean(v) for k,v in x.items()}
 if isinstance(x,list):return [clean(v) for v in x]
 if isinstance(x,float) and not math.isfinite(x):return None
 return x
(out/(name+'_diagnostics.json')).write_text(json.dumps(clean(report),indent=2,allow_nan=False));print(json.dumps(summary),flush=True)
