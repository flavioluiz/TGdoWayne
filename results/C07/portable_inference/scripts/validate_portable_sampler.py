from pathlib import Path
import argparse,json,sys
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
ap=argparse.ArgumentParser();ap.add_argument('--output',type=Path,required=True);args=ap.parse_args()
from inference.campaign_io import write_json_new
from inference.mh_training import TargetSeededMH as BatchedMH
from scipy.special import expit,betaln
from scipy.stats import beta
from time import perf_counter
# Independent analytic law: posterior consists of five non-uniform Beta laws,
# including a singular boundary density and asymmetric nuisance coordinates.
a=np.array([2.,.7,5.,2.,8.]);b=np.array([3.,4.,2.,2.,1.2])
def target(z,ids):
    x=expit(z);logx=-np.logaddexp(0,-z);log1x=-np.logaddexp(0,z)
    ll=np.sum((a-1)*logx+(b-1)*log1x-betaln(a,b),axis=-1)
    return ll+np.sum(logx+log1x,axis=-1),ll
sampler=BatchedMH(target,[0],seed=907120109,nuisance_probability=.2,independence_probability=.45,student_scales=(1.,3.),student_weights=(.75,.25),adaptation_window=4000);t=perf_counter()
for _ in range(4000):sampler.step(adapt=True)
sampler.freeze();draw=[]
for _ in range(32768):draw.append(sampler.step()[0][0])
x=np.asarray(draw);probs=np.array([.05,.5,.9,.95]);cuts=beta.ppf(probs[None,:],a[:,None],b[:,None]);est=np.mean(x[:,:,:,None]<=cuts[None,None,:,:],axis=(0,1))
# Independent batch-means standard errors, 64 batches per chain.
ind=(x[:,:,:,None]<=cuts[None,None,:,:]).reshape(64,512,4,5,4).mean(axis=1);se=np.std(ind,axis=(0,1),ddof=1)/np.sqrt(64*4)
error=abs(est-probs);passed=bool(np.all(error<=4*se+.0002) and np.max(se)<.006)
result=dict(analytic_posterior='five independent Beta laws on prior cube',alpha=a.tolist(),beta=b.tolist(),draws_per_chain=len(x),chains=4,mean_cdf=est.tolist(),mcse_batch=se.tolist(),maximum_standardized_error=float(np.max(error/se)),passes=passed,seconds=perf_counter()-t,sampler=sampler.metadata())
write_json_new(args.output,result);print(json.dumps({k:v for k,v in result.items() if k!='sampler'},indent=2))
if not passed:raise RuntimeError('Analytic target sampler validation failed.')
