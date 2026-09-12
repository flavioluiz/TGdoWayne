"""Independent aggregation audit; does not rerun likelihoods or import SBC helpers."""
from pathlib import Path
import hashlib
import json
import math
import numpy as np
from scipy import stats

ROOT = Path(__file__).resolve().parents[1]
def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()
def close(actual, expected):
    if not np.allclose(actual, expected, rtol=2e-11, atol=2e-14):
        raise AssertionError((actual, expected))
def coverage(intervals, low, high):
    certain = sum(a >= low and b <= high for a,b in intervals)
    possible = sum(b >= low and a <= high for a,b in intervals)
    n = len(intervals)
    # Enumerate the binomial probability-ordering definition independently.
    pmf = stats.binom.pmf(np.arange(n+1), n, high-low)
    pv = [min(1., math.fsum(pmf[pmf <= pmf[k]*(1+1e-7)])) for k in range(certain, possible+1)]
    cp = [0. if certain == 0 else stats.beta.ppf(.025,certain,n-certain+1),
          1. if possible == n else stats.beta.ppf(.975,possible+1,n-possible)]
    return certain, possible, min(pv), max(pv), cp

def main():
    path=ROOT/'results/C11/production_synthesis/synthesis.json'
    s=json.loads(path.read_text()); bindings={str(path.relative_to(ROOT)):digest(path)}
    calculated={}; info=[]; allrows={}; checks=0
    for product in s['products']:
        p=ROOT/product['path']; assert digest(p)==product['sha256']; bindings[product['path']]=digest(p)
        rows=json.loads(p.read_text())['rows']; assert [r['id'] for r in rows]==list(range(596))
        prior=[r for r in rows if r['SBC']]; assert [r['id'] for r in prior]==list(range(500))
        key=(product['population'],product['model']); allrows[key]=rows
        assert product['mass_unresolved']==sum(not r['finite_mass_controls_passed'] for r in rows)
        assert product['event_unresolved']==sum(not r['event_resolved'] for r in rows)
        for r in rows:
            for field,flag in [('mass_PIT_operational_interval','finite_mass_controls_passed'),('logL_PIT_operational_interval','event_resolved')]:
                a,b=r[field]; assert 0<=a<=b<=1
                if not r[flag]: assert [a,b]==[0.,1.]
        for test,field in [('KS_mass_PIT','mass_PIT_operational_interval'),('KS_logL_PIT','logL_PIT_operational_interval')]:
            lo=sorted(r[field][0] for r in prior); hi=sorted(r[field][1] for r in prior); n=len(prior)
            dlow=max([0.]+[(i+1)/n-hi[i] for i in range(n)]+[lo[i]-i/n for i in range(n)])
            dhigh=max([(i+1)/n-lo[i] for i in range(n)]+[hi[i]-i/n for i in range(n)])
            calculated[key+(test,)]=(stats.kstwo.sf(dhigh,n),stats.kstwo.sf(dlow,n))
        intervals=[r['mass_PIT_operational_interval'] for r in prior]
        for test,low,high in [(f'coverage_{v}',0.,v) for v in (.05,.5,.9,.95)]+[('central_05_95',.05,.95)]:
            c=coverage(intervals,low,high); calculated[key+(test,)]=c[2:4]
            target=next(r for family in s['SBC_families'].values() for r in family if (r['population'],r['model'],r['test'])==key+(test,))
            assert (target['certainly_covered'],target['possibly_covered'])==c[:2]
            close(target['binomial_interval_union'],c[4]); checks+=1
        kl=np.array([r['KL'] for r in prior])
        info.append(dict(population=key[0],model=key[1],prior_replicates=500,mean_KL_nats=float(kl.mean()),median_KL_nats=float(np.median(kl)),MCSE_mean_KL=float(kl.std(ddof=1)/np.sqrt(500)),event_unresolved_prior=sum(not r['event_resolved'] for r in prior),event_unresolved_all=product['event_unresolved']))
    decisions={}
    for family,tests in s['SBC_families'].items():
        assert len(tests)=={'correct':42,'approximate':84}[family]
        for t in tests:
            close([t['pvalue_lower'],t['pvalue_upper']],calculated[t['population'],t['model'],t['test']]); checks+=1
        adjusted=[]
        for index in (0,1):
            values=[calculated[t['population'],t['model'],t['test']][index] for t in tests]
            order=sorted(range(len(values)),key=values.__getitem__); result=[0.]*len(values); running=0.
            for rank,j in enumerate(order): running=max(running,min(1.,(len(values)-rank)*values[j])); result[j]=running
            adjusted.append(result)
        flagged=[]
        for j,t in enumerate(tests):
            close([t['holm_lower'],t['holm_upper']],[adjusted[0][j],adjusted[1][j]])
            assert t['persistent_rejection']==(adjusted[1][j]<=.05)
            assert t['rejection_not_excluded']==(adjusted[0][j]<=.05)
            if t['rejection_not_excluded']: flagged.append({k:t[k] for k in ('population','model','test','holm_lower','holm_upper','persistent_rejection')})
            checks+=1
        decisions[family]=dict(tests=len(tests),persistent=sum(t['persistent_rejection'] for t in tests),indeterminate=sum(t['rejection_not_excluded'] and not t['persistent_rejection'] for t in tests),flagged=flagged)
    for cell in s['fixed_recovery']:
        rows=[r for r in allrows[cell['population'],cell['model']] if r['family']==cell['cell']]
        assert len(rows)==32 and all(not r['SBC'] for r in rows)
        c=coverage([r['mass_PIT_operational_interval'] for r in rows],.05,.95)
        assert cell['central90_count_bounds']==list(c[:2]); close(cell['binomial_interval_union'],c[4]); checks+=1
    contrasts=[]
    for population in ('P12K4','P16K8'):
        a=np.array([r['KL'] for r in allrows[population,'A_G'][:500]])
        b=np.array([r['KL'] for r in allrows[population,'B_G'][:500]])
        d=a-b; contrasts.append(dict(population=population,contrast='A_G minus B_G',mean_KL_difference_nats=float(d.mean()),MCSE=float(d.std(ddof=1)/np.sqrt(500)),replicates=500))
    result=dict(schema='C11_AGGREGATION_AUDIT_v1',passed=True,checks=checks,observations=596,posterior_targets=10728,SBC_per_product=500,decisions=decisions,prior_information=info,paired_information=contrasts,input_sha256=bindings,script_sha256=digest(Path(__file__)),scope='Independent aggregation from retained functional outputs; finite functional validation is separate. KS survival function uses SciPy in both implementations. MCSE describes simulation variation, not numerical systematic error; KL under approximate models is descriptive, not mutual information.')
    out=ROOT/'results/C11/statistical_audit.json'; out.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    print(json.dumps(dict(passed=True,checks=checks,decisions=decisions,paired_information=contrasts)))
if __name__=='__main__':main()
