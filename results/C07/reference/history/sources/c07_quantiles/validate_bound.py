"""Independent numerical integral check and frozen unpruned numerator comparison."""
import json,time
from pathlib import Path
import numpy as np
from scipy.integrate import quad
from cubature import mass_integral,diagnostic_cuts
from bounded import HERE,CDFEvaluator,bounded_mass_integral,truncated_box

def main():
    start=time.perf_counter();rng=np.random.default_rng(7110201);algebra=[]
    for _ in range(60):
        M=int(rng.choice([1,12,48]));chi=10.**rng.uniform(-5,5);lo=rng.uniform(-.4,.1);hi=lo+rng.uniform(.00001,.6)
        tstar=np.clip(.5*np.log10(chi/M),lo,hi)
        logL=lambda t:-2*M*np.log(10)*t-chi*10.**(-2*t)
        peak=logL(tstar)
        value,error=quad(lambda t:np.exp(logL(t)-peak),lo,hi,epsabs=1e-12,epsrel=1e-12,limit=200)
        bound=hi-lo
        if value>bound*(1+1e-12):raise AssertionError((M,chi,lo,hi,value,bound))
        algebra.append(dict(M=M,chi=chi,interval=[lo,hi],scaled_integral=value,scaled_bound=bound))
    engine=CDFEvaluator((32,20,12),mass_count=129)
    cuts,_=diagnostic_cuts(engine.cfg,engine.data,14);u=.5;Gamma=engine.table.get(u);rows=[]
    # Full fixed-mass reference includes all20 numerators without omission.
    ref=json.loads((HERE.parent/'c07_cubature/results/A0_d14_GL32_20_12_mass_truncated_cdf.json').read_text())
    denominator=ref['log_evidence']
    for j,cut in enumerate(cuts):
        small,lf=truncated_box(engine.box,cut['parameter'],cut['value'])
        threshold=denominator+np.log(1e-12)-np.log(9*np.prod(engine.orders))-lf
        before=time.perf_counter();v,upper,r=bounded_mass_integral(Gamma,engine.e,engine.q,small,engine.orders,log_point_cut=threshold)
        probability=np.exp(v+lf-denominator);bound=np.exp(upper+lf-denominator)
        old=ref['original_nuisance_CDF_at_frozen_cuts'][j];delta=probability-old
        # Floating-point noise of the fully evaluated numerical integral is
        # distinct from the mathematical enclosure of omitted positive nodes.
        if delta>1e-12 or -delta>bound+1e-12:raise AssertionError((j,delta,bound))
        rows.append(dict(cut=cut,absolute_difference=abs(delta),omission_error_bound=bound,
                         gamma_fraction=r['exact_gamma_nodes']/r['nodes'],seconds=time.perf_counter()-before))
    result=dict(status='PASS',analytic_peak_checks=60,unpruned_comparisons=20,
                maximum_CDF_difference=max(r['absolute_difference'] for r in rows),
                maximum_omission_CDF_bound=max(r['omission_error_bound'] for r in rows),
                mean_fraction_gamma_evaluated=float(np.mean([r['gamma_fraction'] for r in rows])),
                bounded20_CDF_seconds=sum(r['seconds'] for r in rows),unpruned21_integrals_seconds=ref['seconds'],
                total_seconds=time.perf_counter()-start,rows=rows)
    (HERE/'results').mkdir(exist_ok=True);(HERE/'results/bound_validation.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k!='rows'},indent=2))

if __name__=='__main__':main()
