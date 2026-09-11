"""Continuous CDF quantiles: cheap control-variate location, fully checked brackets.

The locator is not used to certify precision. Every final endpoint is evaluated
on139 mass nodes at both nuisance rules and also re-integrated on75 nodes.
"""
import argparse,hashlib,json,time
from pathlib import Path
import numpy as np
from scipy.special import logsumexp
from scipy.interpolate import PchipInterpolator
from bounded import HERE,CDFEvaluator
from cubature import trapezoid_weights

BOUNDS={1:(-16.,-14.),2:(3.,5.5),3:(-17.,-14.5),4:(-np.log10(2),np.log10(2))}
LEVELS=[.05,.5,.9,.95]

def old_cut_indices(engine,param):
    return [j for j,c in enumerate(engine.reference['cdf_cuts']) if c['parameter']==param and c['kind'].startswith('frozen_prior_RQMC_quantile_')]

def reference_coarse_cdf(engine,index):
    old=np.array(engine.reference['masses']);take=np.array([int(np.where(old==u)[0][0]) for u in engine.masses])
    nums=np.array(engine.reference['log_CDF_numerator_mass_marginals'])[take,index]
    return float(np.exp(logsumexp(nums+np.log(engine.mw))-engine.logZ))

def locate(full,small,param,p):
    indices=old_cut_indices(full,param);lo,hi=BOUNDS[param];width=hi-lo
    x=np.array([lo]+[full.reference['cdf_cuts'][j]['value'] for j in indices]+[hi])
    f=np.array([0.]+[full.reference['original_nuisance_CDF_at_frozen_cuts'][j] for j in indices]+[1.])
    inverse=PchipInterpolator(f,x);candidate=float(inverse(p));inv_slope=float(inverse.derivative()(p));history=[]
    for iteration in range(5):
        near=indices[int(np.argmin(abs(np.array([full.reference['cdf_cuts'][j]['value'] for j in indices])-candidate)))]
        origin=full.reference['original_nuisance_CDF_at_frozen_cuts'][near]
        value=small.evaluate(param,candidate)
        approx=origin+np.exp(small.logZ-full.logZ)*(value['cdf_lower']-reference_coarse_cdf(small,near))
        if history and abs(approx-history[-1]['estimated_CDF'])>1e-12:
            secant=(candidate-history[-1]['cut'])/(approx-history[-1]['estimated_CDF'])
            if secant>0:inv_slope=secant
        step=float(np.clip((p-approx)*inv_slope,-.05*width,.05*width))
        history.append(dict(cut=candidate,estimated_CDF=float(approx),proposed_step=step,
                            locator_mass_nodes=len(small.masses),origin_cut_index=near,
                            note='Control-variate location only; its mass error is not assumed bounded.'))
        candidate=float(np.clip(candidate+step,lo+1e-9*width,hi-1e-9*width))
        if abs(step)<=.0001*width:break
    return candidate,history

def summarize_endpoint(value,engine,mass_count):
    m=np.array(value['masses']);num=np.array(value['log_numerator_mass_marginal']);upper=np.array(value['log_omitted_mass_upper'])
    if mass_count==129:take=np.arange(len(m))
    else:
        beta=np.array([0,.0002,.0005,.001,.002,.005,.01,.02,.05,.1,.15]);small=np.unique(np.r_[np.linspace(0,1,mass_count),np.sqrt(1-beta**2)])
        take=np.array([int(np.where(m==u)[0][0]) for u in small])
    subset=m[take];w=trapezoid_weights(subset);oldmass=np.array(engine.reference['masses']);oldtake=np.array([int(np.where(oldmass==u)[0][0]) for u in subset])
    ld=np.array(engine.reference['log_mass_marginal'])[oldtake]
    logZ=float(logsumexp(ld+np.log(w)));f=float(np.exp(logsumexp(num[take]+np.log(w))-logZ));error=float(np.exp(logsumexp(upper[take]+np.log(w))-logZ))
    return dict(mass_nodes=len(take),cdf_lower=f,cdf_upper=f+error,omission_error_bound=error)

def one_quantile(coarse,fine,locator,param,p):
    begin=time.perf_counter();center,history=locate(fine,locator,param,p);lo_prior,hi_prior=BOUNDS[param];width=hi_prior-lo_prior
    attempts=[];half=.00045*width
    for attempt in range(4):
        lo=max(lo_prior+1e-10*width,center-half);hi=min(hi_prior-1e-10*width,center+half)
        rows=[];estimates=[]
        for engine in [coarse,fine]:
            lower=engine.evaluate(param,lo);higher=engine.evaluate(param,hi)
            for mass_count in [65,129]:
                l=summarize_endpoint(lower,engine,mass_count);h=summarize_endpoint(higher,engine,mass_count)
                contained=bool(l['cdf_upper']<p<h['cdf_lower'])
                estimate=lo+(p-l['cdf_lower'])*(hi-lo)/(h['cdf_lower']-l['cdf_lower'])
                rows.append(dict(orders=engine.orders,mass_nodes=l['mass_nodes'],lower_endpoint=l,upper_endpoint=h,
                                 contained=contained,linear_quantile_estimate=float(estimate)))
                if mass_count==129:estimates.append(estimate)
        attempts.append(dict(bracket=[lo,hi],width_fraction_prior=(hi-lo)/width,checks=rows))
        print(json.dumps(dict(parameter=param,probability=p,attempt=attempt+1,bracket=[lo,hi],all_checks_pass=all(r['contained'] for r in rows),elapsed=time.perf_counter()-begin)),flush=True)
        if all(r['contained'] for r in rows):
            return dict(status='PASS_FOR_TESTED_NUMERICAL_RULES',parameter=param,probability=p,
                        quantile_common_midpoint=.5*(lo+hi),bracket=[lo,hi],
                        maximum_midpoint_bracketing_error_fraction_prior=.5*(hi-lo)/width,
                        maximum_between_rule_quantile_difference_bound_fraction_prior=(hi-lo)/width,
                        maximum_point_estimate_difference_fraction_prior=float(np.ptp([r['linear_quantile_estimate'] for r in rows])/width),
                        linear_quantile_estimates_by_rule=rows,locator_history=history,attempts=attempts,seconds=time.perf_counter()-begin,
                        caveat='Brackets certify location for the compared numerical CDFs; quadrature comparison is not a universal analytic posterior-error bound.',
                        source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
        center=float(np.clip(np.mean(estimates),lo_prior+half,hi_prior-half))
    return dict(status='FAIL_BRACKET_WITHIN_BUDGET',parameter=param,probability=p,locator_history=history,attempts=attempts,seconds=time.perf_counter()-begin)

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--parameters',type=int,nargs='+',default=[1,2,3,4]);a=parser.parse_args()
    coarse=CDFEvaluator((20,20,20));fine=CDFEvaluator((32,20,12));locator=CDFEvaluator((32,20,12),mass_count=17)
    begin=time.perf_counter();results=[]
    for param in a.parameters:
        for p in LEVELS:
            filename=HERE/'results'/f'quantile_parameter{param}_p{p:g}.json'
            if filename.exists():
                out=json.loads(filename.read_text());print('Preserving',filename.name,flush=True)
            else:
                out=one_quantile(coarse,fine,locator,param,p);filename.write_text(json.dumps(out,indent=2)+'\n')
            results.append(out)
            if out['status']!='PASS_FOR_TESTED_NUMERICAL_RULES':raise RuntimeError('Quantile bracket failed; preserve evidence, do not weaken criterion.')
    summary=dict(scope='Independent A0 datum14 reference only, no16-target or500-realization campaign',
                 parameter_quantiles_completed=len(results),all_requested_quantiles_pass=all(r['status']=='PASS_FOR_TESTED_NUMERICAL_RULES' for r in results),
                 maximum_midpoint_bracketing_error_fraction_prior=max(r['maximum_midpoint_bracketing_error_fraction_prior'] for r in results),
                 maximum_between_rule_quantile_difference_bound_fraction_prior=max(r['maximum_between_rule_quantile_difference_bound_fraction_prior'] for r in results),
                 maximum_point_estimate_difference_fraction_prior=max(r['maximum_point_estimate_difference_fraction_prior'] for r in results),
                 seconds_this_invocation=time.perf_counter()-begin,results=[{k:r[k] for k in ['parameter','probability','quantile_common_midpoint','bracket','seconds']} for r in results])
    (HERE/'results/quantile_summary.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary,indent=2))

if __name__=='__main__':main()
