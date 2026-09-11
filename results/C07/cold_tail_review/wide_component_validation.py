"""Engineering-only validation of the fixed local Gaussian scale mixture."""
import os
os.environ['VECLIB_MAXIMUM_THREADS']='1'
from pathlib import Path
import hashlib,json,sys
import numpy as np
from scipy.stats import norm,t,multivariate_normal,multivariate_t
from scipy.special import logsumexp
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE/'replay_sources/src'))
from inference.gmm_density import MultipleRHSGaussianDefensiveProposal
from inference.campaign_iid import sample_single_target

def widen(row):
 row=dict(row);w=np.array(row['weights']);m=np.array(row['means']);c=np.array(row['covariances']);row['weights']=np.r_[w*(.75/.85),w*(.10/.85)].tolist();row['means']=np.r_[m,m].tolist();row['covariances']=np.r_[c,9*c].tolist();return row

def density(row):return MultipleRHSGaussianDefensiveProposal(*[np.asarray(row[k])[None] for k in ['weights','means','covariances','global_mean','global_cholesky']],defensive_fraction=.15,student_df=5,student_scale=3)

def main():
 cfg=dict(seed=907140110,N=65536,projection_seed=907140111,alpha_family=.01,projections=8,thresholds_per_projection=5,no_likelihood_calls=True)
 with (HERE/'wide_validation_config.json').open('x') as f:json.dump(cfg,f,indent=2);f.write('\n')
 row=json.loads((ROOT/'tmp/c07_integrated_engineering/proposals/target_000025.json').read_text());b=widen(row);q=density(b);z,component=sample_single_target(q,np.random.default_rng(cfg['seed']),cfg['N']);lq=q.logpdf(z)
 checkpoints=z[np.linspace(0,len(z)-1,257).astype(int)];terms=[np.log(.85*w)+multivariate_normal.logpdf(checkpoints,mean=m,cov=c) for w,m,c in zip(b['weights'],b['means'],b['covariances'])];L=np.array(b['global_cholesky']);terms.append(np.log(.15)+multivariate_t.logpdf(checkpoints,loc=b['global_mean'],shape=5.4*L@L.T,df=5));err=float(np.max(abs(q.logpdf(checkpoints)-logsumexp(terms,axis=0))))
 dr=np.random.default_rng(cfg['projection_seed']).normal(size=(3,5));dr/=np.linalg.norm(dr,axis=1)[:,None];directions=np.r_[np.eye(5),dr];mixw=np.r_[.85*q.weights[0],.15];means=np.r_[q.means[0],q.global_mean];covs=np.concatenate((q.cov[0],(9*L@L.T)[None]));center=np.einsum('k,kd->d',mixw,means);cov=np.einsum('k,kij->ij',mixw,covs+np.einsum('ki,kj->kij',means-center,means-center));rows=[]
 critical=float(norm.ppf(1-cfg['alpha_family']/(2*40)))
 for j,d in enumerate(directions):
  loc=means@d;var=np.einsum('i,kij,j->k',d,covs,d);thresholds=center@d+np.sqrt(d@cov@d)*np.array([-2,-1,0,1,2]);expected=(norm.cdf((thresholds[:,None]-loc[:-1])/np.sqrt(var[:-1]))*mixw[:-1]).sum(axis=1)+.15*t.cdf((thresholds-loc[-1])/np.sqrt(var[-1]*3/5),df=5);empirical=np.mean((z@d)[:,None]<=thresholds,axis=0);se=np.sqrt(expected*(1-expected)/len(z));standard=(empirical-expected)/se
  rows.extend(dict(projection=j,threshold=float(thr),expected_cdf=float(p),sample_cdf=float(ph),standardized_error=float(st),pass_family=bool(abs(st)<=critical)) for thr,p,ph,st in zip(thresholds,expected,empirical,standard))
 old=density(row);lower_bound=np.log(.75/.85);bound=float(np.min(q.logpdf(checkpoints)-old.logpdf(checkpoints)));assert err<1e-10 and all(r['pass_family'] for r in rows) and bound>=lower_bound-1e-13
 report=dict(status='PURE_PROPOSAL_ENGINEERING_PASS_NOT_POSTERIOR_APPROVAL',config=cfg,logpdf_scipy_max_error=err,density_ratio_lower_bound=.75/.85,minimum_log_ratio_on_test_points=bound,projection_cdf_max_standardized_error=max(abs(r['standardized_error']) for r in rows),family_critical_normal=critical,rows=rows,component_counts=np.bincount(component,minlength=9).tolist(),source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),likelihood_calls=0,uses_truth=False)
 with (HERE/'results/wide_validation.json').open('x') as f:json.dump(report,f,indent=2);f.write('\n')
 print(json.dumps({k:v for k,v in report.items() if k!='rows'},indent=2))
if __name__=='__main__':main()
