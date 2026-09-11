"""Exploratory density/Cholesky audit of replayed largest weights; no truth access."""
import os
os.environ['VECLIB_MAXIMUM_THREADS']='1'
from pathlib import Path
import hashlib,json,sys
import numpy as np
from scipy.special import expit,logsumexp
from scipy.stats import multivariate_normal,multivariate_t
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE/'replay_sources/src'))
from inference.campaign_training import validate_proposal
from inference.gmm_density import MultipleRHSGaussianDefensiveProposal
from inference.iid_diagnostics import replicated_cdf,replicated_weights,json_safe
from inference.model import experiment
from inference.orf_interpolation import EvenThresholdCubicORF
from inference.likelihood_reference import Likelihood

def prop(row):return MultipleRHSGaussianDefensiveProposal(*[np.asarray(row[k])[None] for k in ['weights','means','covariances','global_mean','global_cholesky']],defensive_fraction=.15,student_df=5.,student_scale=3.)
def scipy_terms(q,z):
 terms=[np.log(.85*q.weights[0,k])+multivariate_normal.logpdf(z,mean=q.means[0,k],cov=q.cov[0,k]) for k in range(4)]
 terms.append(np.log(.15)+multivariate_t.logpdf(z,loc=q.global_mean[0],shape=5.4*q.global_chol[0]@q.global_chol[0].T,df=5))
 return np.array(terms).T

def main():
 cfg=json.loads((HERE/'config.json').read_text());rows={'original8192':json.loads((ROOT/'tmp/c07_integrated_engineering/proposals/target_000025.json').read_text())}
 for steps in [8192,32768]:rows[f'new{steps}']=next(r for r in json.loads((HERE/'results'/f'train{steps}_proposals.json').read_text())['records'] if r['target']==25)
 qs={k:prop(r) for k,r in rows.items()};datasets={}
 a=[np.load(HERE/'replay_raw'/f'target_000025_N65536_rep_{r:02d}.npz') for r in range(4)];datasets['original8192']={k:np.stack([d[k] for d in a]) for k in ['x_unit','z','log_likelihood','log_proposal','log_prior_logit','log_weights','proposal_component']}
 for steps in [8192,32768]:
  with np.load(HERE/'results'/f'train{steps}_iid_N65536.npz') as d:datasets[f'new{steps}']={k:d[k][:,:,0] for k in ['x_unit','z','log_likelihood','log_proposal','log_prior_logit','log_weights','proposal_component']}
 old=datasets['original8192'];ix=np.argsort(old['log_weights'].ravel())[-20:][::-1];z=old['z'].reshape(-1,5)[ix];x=old['x_unit'].reshape(-1,5)[ix];ll=old['log_likelihood'].ravel()[ix];pn=np.exp(old['log_weights'].ravel()-logsumexp(old['log_weights']))[ix];top=[];logqs={k:q.logpdf(z) for k,q in qs.items()};scientific_checks={}
 for key,q in qs.items():
  ts=scipy_terms(q,z);scientific_checks[key]=dict(max_logpdf_difference_scipy=float(np.max(abs(logsumexp(ts,axis=1)-logqs[key]))))
 cfgexp=json.loads((ROOT/cfg['experiment']).read_text());bounds=np.array(cfgexp['prior']['bounds']);theta=bounds[:,0]+x*np.diff(bounds,axis=1)[:,0];e=experiment(cfgexp)
 with np.load(ROOT/cfg['data']) as d:reference=Likelihood(e,d['q'],d['x_physical'],d['x_gaussian'])
 with np.load(ROOT/cfg['table']) as d:table=EvenThresholdCubicORF(d['nodes'],d['matrices'],coordinate='beta')
 direct=[]
 for th in theta:direct.append(float(reference(th[None,1:],table(th[0]))[0,25]))
 terms=scipy_terms(qs['original8192'],z);respons=np.exp(terms-logsumexp(terms,axis=1)[:,None])
 for j,i in enumerate(ix):
  maha=[float(np.linalg.norm(np.linalg.solve(qs['original8192'].chol[0,k],z[j]-qs['original8192'].means[0,k]))**2) for k in range(4)]
  top.append(dict(rep=int(i//65536),index=int(i%65536),normalized_weight=float(pn[j]),x_unit=x[j].tolist(),theta=theta[j].tolist(),z=z[j].tolist(),draw_component=int(old['proposal_component'].ravel()[i]),log_likelihood=float(ll[j]),direct_cholesky_log_likelihood=direct[j],logpdf={k:float(v[j]) for k,v in logqs.items()},new_to_old_density_ratios={k:float(np.exp(v[j]-logqs['original8192'][j])) for k,v in logqs.items() if k!='original8192'},old_density_responsibilities=respons[j].tolist(),old_gaussian_mahalanobis_squared=maha))
 descriptions=[]
 for key,r in rows.items():
  q=qs[key];descriptions.append(dict(name=key,weights=q.weights[0].tolist(),logit_means=q.means[0].tolist(),unit_at_logit_mean=expit(q.means[0]).tolist(),logit_marginal_standard_deviations=np.sqrt(np.diagonal(q.cov[0],axis1=-2,axis2=-1)).tolist(),covariance_eigenvalues=np.linalg.eigvalsh(q.cov[0]).tolist(),global_mean=q.global_mean[0].tolist(),global_marginal_sd=np.sqrt(np.sum(q.global_chol[0]**2,axis=1)).tolist()))
 regions=[]
 for key,d in datasets.items():
  zz=d['z'].reshape(-1,5);xx=d['x_unit'];lw=d['log_weights'];lold=qs['original8192'].logpdf(zz).reshape(lw.shape);summary=replicated_weights(lw);fixed_logZ=-75.3386 # descriptive approximation from new independent estimates, not an oracle
  ratio=np.exp(d['log_likelihood']+d['log_prior_logit']-lold-fixed_logZ)
  tests={'Agw_gt_0.99':xx[:,:,1]>.99,'Agw_gt_0.999':xx[:,:,1]>.999,'Agw_gt_0.99_gamma_lt_0.75':(xx[:,:,1]>.99)&(xx[:,:,2]<.75),'old_p_over_q_gt100':ratio>100,'old_p_over_q_gt1000':ratio>1000}
  regionrows=[]
  for name,mask in tests.items():
   cdf=replicated_cdf(mask.astype(float),lw,[.5])[0];regionrows.append(dict(region=name,posterior_probability=1-cdf['estimate'],probability_mcse=cdf['mcse'],proposal_draw_fraction=float(mask.mean()),proposal_draw_count=int(mask.sum())))
  regions.append(dict(proposal=key,weights=summary,regions=regionrows))
 report=dict(status='EXPLORATORY_ORIGINAL_TAIL_AUDIT',uses_truth=False,original_replay_all_raw_sha_identical=True,top_weights=top,logpdf_scipy=scientific_checks,max_native_vs_direct_cholesky_logL=float(np.max(abs(ll-np.array(direct)))),proposal_shapes=descriptions,exploratory_regions=regions,source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),limitations=['Regions selected after seeing original weight coordinates are exploratory, not newly approved precision criteria.','Direct Cholesky recomputes C and moments from the same approved interpolated Gamma; it is not a new exact ORF integral.','No new truth accessed or fitting to production. Different proposal seeds both matter; neither proves every cold fit robust.','old p/q thresholds use a rounded approximate logZ=-75.3386 and are descriptive only.'])
 with (HERE/'results/tail_audit.json').open('x') as f:json.dump(json_safe(report),f,indent=2);f.write('\n')
 print(json.dumps(json_safe(dict(logpdf_scipy=scientific_checks,max_native_vs_direct_cholesky_logL=report['max_native_vs_direct_cholesky_logL'],top=top[:2],regions=regions)),indent=2))
if __name__=='__main__':main()
