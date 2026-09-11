"""Independent analytic five-dimensional product-normal reference for the actual engine.

This detects integration and quantile failures; it does not validate physical PTA SBC.
"""
from pathlib import Path
import json
import numpy as np
from scipy.stats import norm
from inference_pilot import integrate_level

ROOT=Path(__file__).resolve().parents[1]


class Provider:
    def evaluate(self,x):return x


class ProductDensity:
    names=['A0_CN','A_CN','B_CN','A_G','B_G']
    n=1
    def __init__(self):
        self.means=np.array([.431,.613,.273,.527,.381]);self.sigmas=np.array([.11,.10,.13,.12,.09])
    def prepare(self,u):return None
    def __call__(self,eta,u,basis=None):
        ll=norm.logpdf(u,self.means[0],self.sigmas[0])+norm.logpdf(eta,self.means[1:],self.sigmas[1:]).sum(axis=1)
        return np.repeat(ll[:,None],5,axis=1)


def main():
    config=dict(prior=dict(bounds=[[0,1]]*5),quantiles=[.05,.5,.9,.95])
    like=ProductDensity();lo=norm.cdf(-like.means/like.sigmas);hi=norm.cdf((1-like.means)/like.sigmas)
    z=np.sum(np.log(hi-lo));qs=norm.ppf(lo[:,None]+np.array(config['quantiles'])*(hi-lo)[:,None],loc=like.means[:,None],scale=like.sigmas[:,None])
    truth=np.array([[.328,.475,.522,.684,.497]])
    pits=(norm.cdf((truth[0]-like.means)/like.sigmas)-lo)/(hi-lo)
    results=[]
    for nodes,power,seed in [(65,11,73001),(129,14,73001),(129,14,73002),(129,16,73001),(129,16,73002)]:
        level=dict(name=f'analytic_{nodes}_{power}_{seed}',mass_nodes=nodes,nuisance_power=power,scrambles=4,seed=seed)
        out=integrate_level(level,config,None,Provider(),like,truth,ROOT/'results/analytic_validation',batch=2048)
        result=dict(level=level,log_evidence_error=float(np.array(out['log_evidence'])[0,0]-z),maximum_parameter_quantile_error=float(np.max(abs(np.array(out['quantiles'])[0,0]-qs))),parameter_max_quantile_errors=np.max(abs(np.array(out['quantiles'])[0,0]-qs),axis=1).tolist(),maximum_pit_error=float(np.max(abs(np.array(out['pit'])[0,0]-pits))),seconds=out['wall_seconds'])
        results.append(result);print(json.dumps(result),flush=True)
    status=all(abs(r['log_evidence_error'])<.001 and r['maximum_parameter_quantile_error']<.001 and r['maximum_pit_error']<.001 for r in results[-2:])
    report=dict(status='PASS_analytic_reference_0.001' if status else 'FAIL_analytic_reference_0.001',scope='Actual continuous mass/trapezoid and nuisance Sobol engine; analytic five-dimensional target. Not PTA calibration.',analytic_log_evidence=z,analytic_quantiles=qs.tolist(),records=results)
    (ROOT/'results/analytic_validation.json').write_text(json.dumps(report,indent=2)+'\n')
    if not status:raise RuntimeError('Analytic integration reference unresolved.')


if __name__=='__main__':main()
