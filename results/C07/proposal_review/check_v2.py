from pathlib import Path
import hashlib,json,sys
import numpy as np
ROOT=Path.cwd();HERE=Path(__file__).resolve().parent;S=ROOT/'tmp/c07_sampler';sys.path.insert(0,str(S))
from mixture_proposal import GaussianDefensiveProposal as V1
from mixture_proposal_v2 import GaussianDefensiveProposal as V2
p=S/'mixture_proposal_v2.py';saved=HERE/'executed_sources/tmp/c07_sampler/mixture_proposal_v2.py';saved.write_bytes(p.read_bytes())
base=dict(weights=np.array([[1.]]),means=np.zeros((1,1,2)),covariances=np.eye(2)[None,None],global_mean=np.zeros((1,2)),global_cholesky=np.eye(2)[None]);tests=[]
for name,change in [('nontriangular_global_cholesky',{'global_cholesky':np.array([[[1.,.7],[0.,1.]]])}),('negative_global_diagonal',{'global_cholesky':-np.eye(2)[None]}),('asymmetric_covariance',{'covariances':np.array([[[[1.,.7],[0.,1.]]]])}),('nan_student_df',{'student_df':float('nan')}),('near_but_not_normalized_weights',{'weights':np.array([[1.000001]])})]:
    rejected=False
    try:V2(**{**base,**change})
    except ValueError:rejected=True
    assert rejected;tests.append({'case':name,'rejected':True})
meta=json.loads((S/'results/mixture_training.json').read_text());r=meta['records'];args=[np.array([a[key] for a in r]) for key in ['weights','means','covariances','global_mean','global_cholesky']];old=V1(*args);new=V2(*args)
z=np.random.default_rng(907102002).normal(size=(16*257,5))*5
error=float(np.max(abs(old.logpdf(z)-new.logpdf(z))));assert error<1e-12
rng1=[np.random.default_rng(s) for s in np.random.SeedSequence(907102003).spawn(64)];rng2=[np.random.default_rng(s) for s in np.random.SeedSequence(907102003).spawn(64)]
first=old.sample(rng1);second=new.sample(rng2);assert np.array_equal(first,second)
report={'status':'PASS','invalid_inputs':tests,'valid_density_max_abs_difference':error,'valid_samples_bit_identical':True,'input_weight_sum_max_error':new.input_weight_sum_max_error,'v2_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'scope':'Explicit roundoff normalization of valid weight sums; no covariance repair; historical v1 remains unchanged.'}
(HERE/'v2_audit.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
