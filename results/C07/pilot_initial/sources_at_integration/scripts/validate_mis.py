"""Analytic check of the actual L/q integration path and complete-net sampler."""
from pathlib import Path
import json,sys
import numpy as np
from scipy.special import logit
from scipy.stats import norm
from inference_pilot import integrate_level
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from validate_quadrature import ProductDensity,Provider
from run_grouped_importance import balanced_sampler,DefensiveLogitMixture


def main():
    target=ProductDensity();mean=target.means[1:];sigma=target.sigmas[1:]
    base=logit(mean);scale=sigma/(mean*(1-mean))
    offsets=np.array([[-.15,0,0,0],[.15,0,0,0],[0,0,-.15,0],[0,0,.15,0]])
    proposal=DefensiveLogitMixture(np.ones(4)/4,base+offsets,np.array([np.diag(scale*scale)]*4),.2)
    sampler=balanced_sampler(proposal)
    config=dict(prior=dict(bounds=[[0,1]]*5),quantiles=[.05,.5,.9,.95])
    lo=norm.cdf(-target.means/target.sigmas);hi=norm.cdf((1-target.means)/target.sigmas)
    logz=np.log(hi-lo).sum();qs=norm.ppf(lo[:,None]+np.array(config['quantiles'])*(hi-lo)[:,None],loc=target.means[:,None],scale=target.sigmas[:,None])
    truth=np.array([[.328,.475,.522,.684,.497]]);pits=(norm.cdf((truth[0]-target.means)/target.sigmas)-lo)/(hi-lo)
    results=[]
    for power,seed in [(13,733001),(13,733002),(14,733001),(14,733002)]:
        level=dict(name=f'analytic_mis_p{power}_{seed}',mass_nodes=129,nuisance_power=power,scrambles=4,seed=seed)
        out=integrate_level(level,config,None,Provider(),target,truth,ROOT/'results/mis_validation',batch=2048,proposal_sampler=sampler)
        result=dict(power=power,seed=seed,log_evidence_error=float(np.array(out['log_evidence'])[0,0]-logz),maximum_quantile_error=float(np.max(abs(np.array(out['quantiles'])[0,0]-qs))),maximum_pit_error=float(np.max(abs(np.array(out['pit'])[0,0]-pits))),integral_original_prior_by_scramble=out['proposal_integral_of_original_prior_by_scramble'],seconds=out['wall_seconds'])
        results.append(result);print(json.dumps(result),flush=True)
    status=all(abs(r['log_evidence_error'])<.001 and r['maximum_quantile_error']<.001 and r['maximum_pit_error']<.001 for r in results[-2:]) and abs(results[-1]['log_evidence_error']-results[-2]['log_evidence_error'])<.001
    report=dict(status='PASS_analytic_MIS_0.001' if status else 'FAIL_analytic_MIS_0.001',records=results,scope='Actual streaming L/q path with complete independent Sobol nets in all five mixture strata; known analytic five-dimensional target; not physical PTA calibration.')
    (ROOT/'results/mis_validation.json').write_text(json.dumps(report,indent=2)+'\n')
    if not status:raise RuntimeError('MIS analytic reference failed.')


if __name__=='__main__':main()
