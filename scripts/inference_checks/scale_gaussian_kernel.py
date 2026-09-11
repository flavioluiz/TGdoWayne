"""Physical-kernel reconstruction, scale integrals, and data-dependent CDF checks."""
from pathlib import Path
from time import perf_counter
import hashlib,json
import numpy as np
from numpy.testing import assert_allclose
from scipy.integrate import quad
from scipy.optimize import brentq
from scipy.stats import qmc
import sys
from pathlib import Path
REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
OUTPUT = REPO / "results/C07/validation"
OUTPUT.mkdir(parents=True, exist_ok=True)

from inference.model import experiment
from inference.orf_backend import ExactNodeORF
from inference.likelihood import FastLikelihood
from inference.scale_cn import LogAmplitudeBox
from inference.scale_kernel import GaussianScaleKernel
from inference.scale_gaussian import gaussian_log_scale_integral,gaussian_conditional_scale_cdf,gaussian_conditional_loglike_cdf,gaussian_scale_loglike

ROOT=OUTPUT


def main():
    start=perf_counter();cfg=json.loads((REPO/'configs/calibration/pilot_initial.json').read_text());e=experiment(cfg);data=np.load(REPO/'results/C07/fixtures/pilot_data.npz')
    provider=ExactNodeORF(e,cfg['orf'],REPO/'results/C07/fixtures/orf_cache')
    scale=GaussianScaleKernel(e,data['x_physical'],data['x_gaussian'])
    full=FastLikelihood(e,data['q'],data['x_physical'],data['x_gaussian'])
    prior=LogAmplitudeBox();ratio=prior.sample_ratio_prior(qmc.Sobol(3,scramble=True,seed=78111).random_base2(4))
    records=[]
    for u in [0,.5,1]:
        gamma=provider.evaluate(u);a,b=scale.coefficients(ratio[:,:3],gamma)
        errors=[]
        for fraction in [.05,.5,.95]:
            t=ratio[:,3]+fraction*(ratio[:,4]-ratio[:,3])
            eta=np.column_stack((ratio[:,0]+t,ratio[:,2],ratio[:,1]+t,t))
            original=full(eta,gamma)
            aa=a.loglike(t[:,None]);bb=b.loglike(t[:,None])
            reconstructed=np.concatenate((aa[:,:16],bb[:,:16],aa[:,16:],bb[:,16:]),axis=1)
            expected=original[:,16:]
            assert_allclose(reconstructed,expected,rtol=2e-11,atol=2e-8)
            errors.append(float(np.max(abs(reconstructed-expected))))
        marginalized,diag=scale.marginalized(ratio[:,:3],gamma,ratio[:,3],ratio[:,4],coarse_order=32,fine_order=64)
        # An independent GL rule directly averages the original full covariance likelihood in t.
        checks=[]
        from scipy.special import logsumexp,roots_legendre
        for index in [0,7,15]:
            references=[]
            for order in [96,192,384,768]:
                nodes,weights=roots_legendre(order)
                t=(ratio[index,3]+ratio[index,4])/2+(ratio[index,4]-ratio[index,3])/2*nodes
                eta=np.column_stack((ratio[index,0]+t,np.full(len(t),ratio[index,2]),ratio[index,1]+t,t))
                original=full(eta,gamma)[:,16:]
                references.append(logsumexp(original+np.log(weights[:,None]/2),axis=0))
            error=float(np.max(abs(marginalized[index]-references[-1])))
            reference_refinement=float(np.max(abs(references[-1]-references[-2])))
            assert error<1e-7 and reference_refinement<1e-7,(u,index,error,reference_refinement)
            checks.append(dict(ratio_index=index,maximum_log_integral_error=error,reference_orders=[96,192,384,768],reference_refinement=reference_refinement,coarse_reference_error=float(np.max(abs(marginalized[index]-references[0])))))
        records.append(dict(u=u,maximum_reconstruction_errors=errors,quadrature_diagnostics=diag,independent_direct_scale_checks=checks))
    # Log-likelihood CDF compared with scalar bracketing and t-domain adaptive quadrature.
    chi,b,c,ld,d=8.,-2.,3.,.7,10;lo,hi=-np.log10(2),np.log10(2)
    grid=np.linspace(lo,hi,2001)
    ll=lambda t:float(gaussian_scale_loglike(t,chi,b,c,ld,d))
    peak=max(map(ll,grid));norm=quad(lambda t:np.exp(ll(t)-peak),lo,hi,epsabs=1e-12,epsrel=1e-11)[0]
    pit_records=[]
    for point in [-.25,-.1,-.025,0.,.04,.1,.25]:
        threshold=ll(point);vals=np.array([ll(x)-threshold for x in grid]);roots=[]
        for left,right,fa,fb in zip(grid[:-1],grid[1:],vals[:-1],vals[1:]):
            if fa*fb<0:roots.append(brentq(lambda t:ll(t)-threshold,left,right,xtol=1e-14))
        edges=np.r_[lo,roots,hi];prob=0.;prior_prob=0.
        for left,right in zip(edges[:-1],edges[1:]):
            if ll((left+right)/2)<=threshold:
                prob+=quad(lambda t:np.exp(ll(t)-peak),left,right,epsabs=1e-12,epsrel=1e-11)[0]/norm
                prior_prob+=(right-left)/(hi-lo)
        got=gaussian_conditional_loglike_cdf(threshold,chi,b,c,ld,d,lo,hi,coarse_order=32,fine_order=64)
        gp=gaussian_conditional_loglike_cdf(threshold,chi,b,c,ld,d,lo,hi,coarse_order=32,fine_order=64,under_prior=True)
        assert abs(got-prob)<1e-9 and abs(gp-prior_prob)<1e-10
        pit_records.append(dict(t=point,posterior_cdf=float(got),reference_error=float(got-prob),prior_cdf=float(gp),prior_reference_error=float(gp-prior_prob)))
    # Same support, normalization and sufficient-coefficient calculation for500 data columns: timing only.
    idx=np.arange(500)%16;large=GaussianScaleKernel(e,data['x_physical'][idx],data['x_gaussian'][idx]);gamma=provider.evaluate(.5)
    timing=[]
    for instance,label in [(scale,'16 saved datasets'),(large,'500 columns by repeating saved data; not500 realizations')]:
        t0=perf_counter();aa,bb=instance.coefficients(ratio[:8,:3],gamma);coefficient_seconds=perf_counter()-t0
        t0=perf_counter();value,diagnostic=instance.marginalized(ratio[:8,:3],gamma,ratio[:8,3],ratio[:8,4],coarse_order=32,fine_order=64,maximum_evaluations=20_000_000);seconds=perf_counter()-t0
        timing.append(dict(label=label,ratio_points=8,coefficient_seconds=coefficient_seconds,marginalized_seconds_including_coefficients=seconds,shape=list(value.shape),diagnostics=diagnostic))
    source_hashes={str(p.relative_to(REPO)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [REPO/'src/pta/simulation.py',REPO/'src/pta/statistics.py',REPO/'configs/calibration/pilot_initial.json',REPO/'results/C07/fixtures/pilot_data.npz']}
    out=dict(status='PASS_same_A_B_G_families_and_conditional_prior',seconds=perf_counter()-start,records=records,loglike_cdf_records=pit_records,timings=timing,source_hashes=source_hashes,production_executed=False)
    (ROOT/'validation_kernel.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(dict(status=out['status'],seconds=out['seconds'],timings=timing),indent=2))


if __name__=='__main__':main()
