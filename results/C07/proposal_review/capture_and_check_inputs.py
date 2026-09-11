from pathlib import Path
import hashlib,json,sys
import numpy as np
ROOT=Path.cwd();HERE=ROOT/'tmp/c07_proposal_review';S=ROOT/'tmp/c07_sampler';sys.path[:0]=[str(ROOT/'src'),str(S)]
from mixture_proposal import GaussianDefensiveProposal
paths=[S/f for f in ['mixture_proposal.py','mh_mixture.py','fit_mixture.py','run_mixture.py','linalg_batch.py','pointwise.py']]+[S/'results'/f for f in ['mixture_training.json','pilot553_refresh.json','pilot553_mixture.json']]+[ROOT/'tmp/c07_efficiency/proposal.py']
manifest={}
for p in paths:
 data=p.read_bytes();dest=HERE/'executed_sources'/p.relative_to(ROOT);dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(data);manifest[str(p.relative_to(ROOT))]=hashlib.sha256(data).hexdigest()
(HERE/'source_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
doc=json.loads((S/'results/mixture_training.json').read_text());records=doc['records'];weights=np.array([r['weights'] for r in records]);means=np.array([r['means'] for r in records]);cov=np.array([r['covariances'] for r in records]);gm=np.array([r['global_mean'] for r in records]);gc=np.array([r['global_cholesky'] for r in records]);q=GaussianDefensiveProposal(weights,means,cov,gm,gc)
valid=dict(targets=doc['targets'],minimum_component_weight=float(weights.min()),maximum_weight_sum_difference=float(abs(weights.sum(axis=1)-1).max()),minimum_covariance_eigenvalue=float(np.linalg.eigvalsh(cov).min()),maximum_covariance_asymmetry=float(abs(cov-cov.swapaxes(-1,-2)).max()),minimum_global_cholesky_diagonal=float(np.diagonal(gc,axis1=-2,axis2=-1).min()),maximum_global_upper_triangle=float(abs(np.triu(gc,1)).max()))
# Counterexamples concern invalid-input rejection, not the valid trained fixture.
base=dict(weights=np.array([[1.]]),means=np.zeros((1,1,2)),covariances=np.eye(2)[None,None],global_mean=np.zeros((1,2)),global_cholesky=np.eye(2)[None]);cases=[]
for name,change in [('nontriangular_global_cholesky',{'global_cholesky':np.array([[[1.,.7],[0.,1.]]])}),('negative_global_diagonal',{'global_cholesky':-np.eye(2)[None]}),('asymmetric_covariance',{'covariances':np.array([[[[1.,.7],[0.,1.]]]])}),('nan_student_df',{'student_df':float('nan')}),('near_but_not_normalized_weights',{'weights':np.array([[1.000001]])})]:
 try:
  with np.errstate(all='ignore'):
   instance=GaussianDefensiveProposal(**{**base,**change});pdf=instance.logpdf(np.zeros((1,2)))
  accepted=True;finite=bool(np.isfinite(pdf).all())
 except (ValueError,np.linalg.LinAlgError):accepted=False;finite=None
 cases.append(dict(case=name,invalid_constructor_accepted=accepted,logpdf_at_zero_finite=finite))
(HERE/'input_review.json').write_text(json.dumps({'valid_training_fixture':valid,'invalid_input_counterexamples':cases},indent=2)+'\n');print(json.dumps({'valid_training_fixture':valid,'invalid_input_counterexamples':cases},indent=2))
