from pathlib import Path
from time import perf_counter
import json
import numpy as np
from scipy.stats import qmc
from numpy.testing import assert_allclose
from inference_pilot import experiment,ExactNodeORF,Likelihood
from likelihood_fast import FastLikelihood
ROOT=Path(__file__).resolve().parents[1]


def main():
    cfg=json.loads((ROOT/'config.json').read_text());e=experiment(cfg);data=np.load(ROOT/'results/data.npz')
    provider=ExactNodeORF(e,cfg['orf'],ROOT/'results/orf_cache')
    bounds=np.array(cfg['prior']['bounds'])[1:]
    eta=bounds[:,0]+qmc.Sobol(4,scramble=True,seed=7077001).random_base2(9)*np.diff(bounds,axis=1).ravel()
    ref=Likelihood(e,data['q'],data['x_physical'],data['x_gaussian']);fast=FastLikelihood(e,data['q'],data['x_physical'],data['x_gaussian'])
    checks=[]
    for u in [0,.5,.999999875,1]:
        g=provider.evaluate(u);basis=ref.prepare(g);a=ref(eta,g,basis);b=fast(eta,g,basis)
        assert_allclose(a,b,rtol=2e-11,atol=2e-8)
        important=a>a.max(axis=0)-30
        checks.append(dict(u=u,points=len(eta),maximum_abs_logpdf_difference=float(np.max(abs(a-b))),maximum_abs_difference_within_30_logunits_of_peak=float(np.max(abs(a[important]-b[important]))),maximum_relative_difference=float(np.max(abs(a-b)/np.maximum(1,abs(a))))))
    timings=[];g=provider.evaluate(.5)
    for size in [16,500]:
        idx=np.arange(size)%len(data['q'])
        for klass in [Likelihood,FastLikelihood]:
            like=klass(e,data['q'][idx],data['x_physical'][idx],data['x_gaussian'][idx]);basis=like.prepare(g);like(eta[:4],g,basis)
            values=[]
            for trial in range(3):
                t=perf_counter()
                for start in range(0,len(eta),128):like(eta[start:start+128],g,basis)
                values.append(perf_counter()-t)
            timings.append(dict(kernel=klass.__name__,columns_per_method=size,parameter_points=len(eta),seconds=values,median_seconds_per_parameter_point=float(np.median(values)/len(eta))))
    out=dict(status='PASS_reference_equivalence',checks=checks,timings=timings,scope='Repeated datasets for timing; no independent500 draws or posterior/SBC acceptance. Floating-point agreement tested at512 continuous nuisance points and four masses, including the endpoint layer.')
    (ROOT/'results/fast_kernel_validation.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))


if __name__=='__main__':main()
