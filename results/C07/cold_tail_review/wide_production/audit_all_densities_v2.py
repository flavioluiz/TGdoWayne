"""Independent SciPy/parameter-map audit over every transformed proposal."""
import os
os.environ['VECLIB_MAXIMUM_THREADS']='1'
from pathlib import Path
import hashlib,json,sys
import numpy as np
from scipy.special import logsumexp
from scipy.stats import multivariate_normal,multivariate_t
ROOT=Path(__file__).resolve().parents[3];HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'replay_sources/src'))
from inference.gmm_density import MultipleRHSGaussianDefensiveProposal

def qmake(r):return MultipleRHSGaussianDefensiveProposal(*[np.array(r[k])[None] for k in ['weights','means','covariances','global_mean','global_cholesky']],defensive_fraction=.15,student_df=5,student_scale=3)
def main():
 c=json.loads((HERE/'config.json').read_text());results=[]
 for item in c['proposal_records']:
  original=json.loads((ROOT/item['source']).read_text());wide=json.loads((ROOT/item['file']).read_text());a=qmake(original);b=qmake(wide);assert hashlib.sha256((ROOT/item['source']).read_bytes()).hexdigest()==item['source_sha256'];assert hashlib.sha256((ROOT/item['file']).read_bytes()).hexdigest()==item['sha256']
  assert np.array_equal(b.means[0,:4],a.means[0]) and np.array_equal(b.means[0,4:],a.means[0]);assert np.array_equal(b.cov[0,:4],a.cov[0]) and np.array_equal(b.cov[0,4:],9*a.cov[0]);assert np.array_equal(b.global_mean,a.global_mean) and np.array_equal(b.global_chol,a.global_chol);assert np.max(abs(.85*b.weights[0,:4]-.75*a.weights[0]))<1e-15;assert np.max(abs(.85*b.weights[0,4:]-.10*a.weights[0]))<1e-15
  with np.load(HERE/'raw'/f'target_{item["target"]:06d}_N16384_rep_00.npz') as f:fullz=f['z'];z=fullz[::512];stored=f['log_proposal'][::512]
  terms=[np.log(.85*w)+multivariate_normal.logpdf(z,mean=m,cov=C) for w,m,C in zip(b.weights[0],b.means[0],b.cov[0])];L=b.global_chol[0];terms.append(np.log(.15)+multivariate_t.logpdf(z,loc=b.global_mean[0],shape=5.4*L@L.T,df=5));ld=b.logpdf(fullz)[::512];scipy_error=float(np.max(abs(ld-logsumexp(terms,axis=0))));stored_error=float(np.max(abs(ld-stored)));bound=float(np.min(ld-a.logpdf(z)));print(json.dumps(dict(target=item['target'],scipy_error=scipy_error,stored_error=stored_error,bound=bound)),flush=True);assert scipy_error<1e-10 and stored_error==0 and bound>=np.log(15/17)-1e-13;results.append(dict(target=item['target'],anchors=len(z),scipy_logpdf_max_error=scipy_error,stored_logpdf_max_error=stored_error,minimum_log_density_ratio=bound,minimum_component_eigenvalue=float(np.min(np.linalg.eigvalsh(b.cov))),mapping_exact=True))
 result=dict(status='ALL16_PARAMETER_MAP_AND_SCIPY_DENSITIES_PASS',rows=results,total_anchors=sum(r['anchors'] for r in results),max_scipy_error=max(r['scipy_logpdf_max_error'] for r in results),likelihood_calls=0,uses_truth=False,source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
 with (HERE/'all_densities_audit.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
 print(json.dumps({k:v for k,v in result.items() if k!='rows'},indent=2))
if __name__=='__main__':main()
