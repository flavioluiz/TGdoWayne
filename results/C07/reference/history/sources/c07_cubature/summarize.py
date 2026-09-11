"""Summarize completed comparisons, explicitly excluding untested nuisance quantiles."""
import json
import numpy as np
from scipy.special import logsumexp
from cubature import HERE,PILOT,trapezoid_weights,continuous_cdf,continuous_ppf

def read(name):
    path=HERE/'results'/name
    return json.loads(path.read_text()) if path.exists() else None

def pair(a,b):
    if a is None or b is None:return None
    cuts_a=a['cdf_cuts'];cuts_b=b['cdf_cuts']
    if cuts_a!=cuts_b:raise AssertionError('Different frozen CDF cuts.')
    ca=np.array(a['original_nuisance_CDF_at_frozen_cuts']);cb=np.array(b['original_nuisance_CDF_at_frozen_cuts'])
    diff=abs(cb-ca);pit=np.array([c['kind']=='truth_PIT_diagnostic_only' for c in cuts_a])
    out=dict(absolute_log_evidence_difference=abs(b.get('log_evidence',b.get('log_evidence_conditional_mass'))-a.get('log_evidence',a.get('log_evidence_conditional_mass'))),
             maximum_CDF_difference_at_frozen_cuts=float(diff.max()),maximum_nuisance_PIT_difference=float(diff[pit].max()),
             CDF_difference_by_cut=diff.tolist(),nuisance_quantiles_assessed=False,
             does_not_certify_uniform_CDF_error=True,does_not_authorize_SBC500=True)
    out['tested_logZ_and_CDF_criteria_pass']=bool(out['absolute_log_evidence_difference']<=.001 and diff.max()<=.002)
    if 'mass_quantiles' in a and 'mass_quantiles' in b:
        out['maximum_mass_quantile_difference']=float(np.max(abs(np.array(a['mass_quantiles'])-b['mass_quantiles'])))
        out['mass_PIT_difference']=abs(a['mass_PIT']-b['mass_PIT'])
    return out

def mass_refinement(d):
    if d is None:return None
    mass=np.array(d['masses']);lm=np.array(d['log_mass_marginal'])
    beta=np.array([0,.0002,.0005,.001,.002,.005,.01,.02,.05,.1,.15])
    coarse=np.unique(np.r_[np.linspace(0,1,65),np.sqrt(1-beta**2)])
    take=np.array([int(np.where(mass==u)[0][0]) for u in coarse])
    results=[]
    qlevels=[.05,.5,.9,.95]
    for indices in [take,np.arange(len(mass))]:
        m=mass[indices];l=lm[indices];w=trapezoid_weights(m);lz=float(logsumexp(l+np.log(w)));p=np.exp(l-l.max())
        r=dict(nodes=len(m),log_evidence=lz,log_evidence_fixed_u0=float(l[0]),log_BF_free_fixed=lz-float(l[0]),
               mass_quantiles=[continuous_ppf(m,p,q) for q in qlevels],
               mass_CDF=[continuous_cdf(m,p,x) for x in np.linspace(0,1,201)])
        if 'log_CDF_numerator_mass_marginals' in d:
            lc=np.array(d['log_CDF_numerator_mass_marginals'])[indices]
            r['nuisance_CDF']=np.exp(logsumexp(lc+np.log(w)[:,None],axis=0)-lz).tolist()
        results.append(r)
    a,b=results
    comp=dict(absolute_log_evidence_difference=abs(a['log_evidence']-b['log_evidence']),
              maximum_mass_quantile_difference=float(np.max(abs(np.array(a['mass_quantiles'])-b['mass_quantiles']))),
              maximum_mass_CDF_difference_on201_grid=float(np.max(abs(np.array(a['mass_CDF'])-b['mass_CDF']))),
              nuisance_quantiles_assessed=False)
    if 'nuisance_CDF' in a:comp['maximum_nuisance_CDF_difference_at_frozen_cuts']=float(np.max(abs(np.array(a['nuisance_CDF'])-b['nuisance_CDF'])))
    return dict(comparison=comp,results=results)

def main():
    c=[read(f'A0_d14_GL{n}_full_cdf.json') for n in [12,20,32]]
    tc=read('A0_d14_GL20_full_truncated_cdf.json');tf=read('A0_d14_GL32_20_12_full_truncated_cdf.json')
    out=dict(scope='Only the comparisons explicitly present are executed; finite CDF cuts are not nuisance quantile certification.',
             conditional_scale_route={'12_to20':pair(c[0],c[1]),'20_to32':pair(c[1],c[2])},
             truncated_box_route={'20cubed_to32_20_12':pair(tc,tf)},
             target_specific_mass_refinement_conditional=mass_refinement(c[2]),
             target_specific_mass_refinement_truncated=mass_refinement(tf),
             completed_SBC500=False,all16_targets_approved=False)
    if c[2]:
        ref=json.loads((PILOT/'results/endpoint_129_13_independent.json').read_text())
        old=float(np.array(ref['log_evidence'])[0,14]);new=c[2]['log_evidence']
        out['prior_RQMC_reference_comparison']=dict(reference='endpoint_129_13_independent',same139_mass_nodes=True,
            old_logZ=old,deterministic_logZ=new,difference=new-old,
            old_mass_quantiles=np.array(ref['quantiles'])[0,14,0].tolist(),deterministic_mass_quantiles=c[2]['mass_quantiles'],
            note='The older RQMC result failed its own integration checks; it is not an absolute reference.')
    (HERE/'results/comparison.json').write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps({k:v for k,v in out.items() if not k.startswith('target_specific')},indent=2))
    for key in ['target_specific_mass_refinement_conditional','target_specific_mass_refinement_truncated']:
        if out[key]:print(key,json.dumps(out[key]['comparison']))

if __name__=='__main__':main()
