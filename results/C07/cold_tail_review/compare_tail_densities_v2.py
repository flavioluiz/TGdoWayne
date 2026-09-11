"""Planning-only density comparisons on existing clouds; no new posterior estimate."""
import os
os.environ['VECLIB_MAXIMUM_THREADS']='1'
from pathlib import Path
import hashlib,json,sys
import numpy as np
from scipy.special import logsumexp
from scipy.stats import multivariate_normal,multivariate_t
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE/'replay_sources/src'))
from inference.gmm_density import MultipleRHSGaussianDefensiveProposal

def qmake(row,nu=5):return MultipleRHSGaussianDefensiveProposal(*[np.asarray(row[k])[None] for k in ['weights','means','covariances','global_mean','global_cholesky']],defensive_fraction=.15,student_df=nu,student_scale=3.)
def scipyq(row,z,nu):
 L=np.array(row['global_cholesky']);terms=[np.log(.85*w)+multivariate_normal.logpdf(z,mean=m,cov=c) for w,m,c in zip(row['weights'],row['means'],row['covariances'])];terms.append(np.log(.15)+multivariate_t.logpdf(z,loc=row['global_mean'],shape=((nu-2)/nu)*9*(L@L.T),df=nu));return logsumexp(terms,axis=0)

def main():
 row=json.loads((ROOT/'tmp/c07_integrated_engineering/proposals/target_000025.json').read_text());q5=qmake(row);q3=qmake(row,3);new=next(r for r in json.loads((HERE/'results/train8192_proposals.json').read_text())['records'] if r['target']==25);qnew=qmake(new)
 ds=[np.load(HERE/'replay_raw'/f'target_000025_N65536_rep_{r:02d}.npz') for r in range(4)];z=np.concatenate([d['z'] for d in ds]);lw=np.concatenate([d['log_weights'] for d in ds]);lq=np.concatenate([d['log_proposal'] for d in ds]);oldnorm=np.exp(lw-logsumexp(lw));ix=np.argsort(lw)[-20:][::-1];a=q5.logpdf(z);b=q3.logpdf(z);mix=np.logaddexp(a,qnew.logpdf(z))-np.log(2)
 # Existing guarded Gaussian mixture can also express a FIXED local wide copy.
 # 0.75*GM(C)+0.10*GM(9C)+0.15*Studentglobal. No fit or new likelihood call.
 broad=dict(row);w=np.array(row['weights']);m=np.array(row['means']);c=np.array(row['covariances']);broad['weights']=np.r_[w*(.75/.85),w*(.10/.85)].tolist();broad['means']=np.r_[m,m].tolist();broad['covariances']=np.r_[c,9*c].tolist();qbroad=qmake(broad);wide=qbroad.logpdf(z)
 sci5=scipyq(row,z[ix],5);sci3=scipyq(row,z[ix],3);checks=dict(current_vs_stored_max=float(np.max(abs(a-lq))),nu5_scipy_max=float(np.max(abs(a[ix]-sci5))),nu3_scipy_max=float(np.max(abs(b[ix]-sci3))))
 from scipy.special import gammaln
 local_terms=[]
 for k in range(4):
  delta=z-q5.means[0,k];r2=np.sum((q5.inverse_chol[0,k]@delta.T)**2,axis=0);constant=gammaln(5)-gammaln(2.5)-2.5*np.log(3*np.pi)-np.log(np.diag(q5.chol[0,k])).sum();local_terms.append(np.log(.85*q5.weights[0,k])+constant-5*np.log1p(r2/3))
 L=q5.global_chol[0];global_term=np.log(.15)+multivariate_t.logpdf(z,loc=q5.global_mean[0],shape=5.4*(L@L.T),df=5);local_terms.append(global_term);local_student=logsumexp(local_terms,axis=0)
 local_scipy_terms=[np.log(.85*w)+multivariate_t.logpdf(z[ix],loc=m,shape=.6*np.array(c),df=5) for w,m,c in zip(row["weights"],row["means"],row["covariances"])]+[global_term[ix]]
 checks["local_student5_scipy_max"]=float(np.max(abs(local_student[ix]-logsumexp(local_scipy_terms,axis=0))))
 ratios={'local_student5_equal_component_covariance':local_student-a,'nu3_same_global_covariance':b-a,'half_original_half_new8192':mix-a,'local_wide_gaussians_covariance_x9':wide-a}
 tops=[];delta=z[ix]-q5.global_mean[0];maha=np.sum(np.linalg.solve(q5.global_chol[0],delta.T)**2,axis=0)
 for j,i in enumerate(ix):tops.append(dict(rep=int(i//65536),index=int(i%65536),original_normalized_weight=float(oldnorm[i]),logit=z[i].tolist(),global_mahalanobis_squared_before_scale=float(maha[j]),global_scaled_mahalanobis_squared=float(maha[j]/9),density_ratios={k:float(np.exp(v[i])) for k,v in ratios.items()},old_unormalized_weight_divided_by_new_density_ratio={k:float(np.exp(lw[i]-v[i])) for k,v in ratios.items()}))
 # Replacing denominator does NOT retarget the already sampled q5 cloud.
 # This section is explicitly a pointwise stress metric, not SNIS with qnew.
 cloud=[]
 for name,lr in ratios.items():
  altered=lw-lr;normalized=np.exp(altered-logsumexp(altered))
  cloud.append(dict(candidate=name,original_posterior_weighted_mean_density_ratio=float(np.sum(oldnorm*np.exp(lr))),original_posterior_weight_fraction_q_reduced_by_more_than_2=float(oldnorm[lr< -np.log(2)].sum()),stress_only_renormalized_max_weight=float(normalized.max()),stress_only_renormalized_ESS=float(1/np.sum(normalized**2)),NOT_VALID_NEW_PROPOSAL_INFERENCE=True))
 # For t with covariance held fixed, q3/q5 as radius r^2 grows is analytic.
 radii=np.array([0,1,3,10,30,100,300,1000,10000.]);d=5
 from scipy.special import gammaln
 def logt(nu,r2):return gammaln((nu+d)/2)-gammaln(nu/2)-d/2*np.log((nu-2)*np.pi)-.5*(nu+d)*np.log1p(r2/(nu-2))
 rr=logt(3,radii)-logt(5,radii)
 result=dict(status='PLANNING_ONLY_NO_NEW_DRAWS_NO_POSTERIOR_REWEIGHTING_CLAIM',uses_truth=False,checks=checks,largest_old_weights=tops,cloud_stress_only=cloud,t3_over_t5_at_equal_covariance_by_radius_squared=[dict(r2=float(r),density_ratio=float(np.exp(v))) for r,v in zip(radii,rr)],candidate_local_wide_formula='0.75 GM(C) + 0.10 GM(9C) + 0.15 Student5(global covariance9LLT)',asymptotic='For d=5 and equal covariance, q3/q5=(3/8)*3**(5/2)*(1+r2/3)**5/(1+r2)**4 ~ r2/(8*3**(3/2)); r2 is Mahalanobis distance squared in the equal-covariance matrix. Both retain exponential-logit-prior domination asymptotically.',source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),limitations=['No new samples or likelihood calls. Altered-denominator cloud metrics are NOT posterior or precision estimates under qnew.','Candidate local wide density is descriptive; no implementation change adopted.','Larger asymptotic tail does not imply greater density at observed moderate radius.','Point selection uses old production only for development, never hidden refitting. A new adopted proposal needs independent production and unchanged diagnostic protocol.'])
 with (HERE/'results/tail_density_comparison_v2.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
 print(json.dumps(dict(checks=checks,top=tops[:3],cloud=cloud,radial=result['t3_over_t5_at_equal_covariance_by_radius_squared']),indent=2))
if __name__=='__main__':main()
