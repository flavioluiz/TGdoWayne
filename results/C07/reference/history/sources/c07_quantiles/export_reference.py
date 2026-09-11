"""Portable comparison reference with explicit vertical intervals at bracket ends."""
import json,hashlib
from pathlib import Path
import numpy as np
from cubature import continuous_cdf,continuous_ppf
from bounded import HERE

levels=[.05,.5,.9,.95];names=['u','log10_Agw','gamma_gw','log10_Ar','log10_EFAC'];bounds=np.array([[0,1],[-16,-14],[3,5.5],[-17,-14.5],[-np.log10(2),np.log10(2)]])
quantiles=np.empty((5,4));brackets=np.empty((5,4,2));cdf=np.empty((5,4,2));spread=np.empty_like(cdf);omission=np.zeros_like(cdf);mid_cdf_envelope=np.empty_like(cdf);source=[]
mass_rules=[]
for filename in ['A0_d14_GL20_full_truncated_cdf.json','A0_d14_GL32_20_12_full_truncated_cdf.json']:
    path=HERE.parent/'c07_cubature/results'/filename;d=json.loads(path.read_text());source.append(path)
    mass=np.array(d['masses']);lm=np.array(d['log_mass_marginal'])
    beta=np.array([0,.0002,.0005,.001,.002,.005,.01,.02,.05,.1,.15]);small=np.unique(np.r_[np.linspace(0,1,65),np.sqrt(1-beta**2)])
    take=np.array([int(np.where(mass==u)[0][0]) for u in small])
    for index in [take,np.arange(len(mass))]:
        m=mass[index];p=np.exp(lm[index]-lm[index].max());mass_rules.append((m,p))
for j,p in enumerate(levels):
    qs=[continuous_ppf(m,d,p) for m,d in mass_rules]
    lo=min(qs)-1e-10;hi=max(qs)+1e-10;quantiles[0,j]=.5*(lo+hi);brackets[0,j]=[lo,hi]
    values=np.array([[continuous_cdf(m,d,x) for x in [lo,hi]] for m,d in mass_rules])
    cdf[0,j]=values[-1];spread[0,j]=np.max(abs(values-values[-1]),axis=0)
    mid_cdf_envelope[0,j]=[values[:,0].min(),values[:,1].max()]
for param in [1,2,3,4]:
    for j,p in enumerate(levels):
        path=HERE/'results'/f'quantile_parameter{param}_p{p:g}.json';source.append(path);r=json.loads(path.read_text())
        quantiles[param,j]=r['quantile_common_midpoint'];brackets[param,j]=r['bracket'];rows=r['linear_quantile_estimates_by_rule']
        values=np.array([[row['lower_endpoint']['cdf_lower'],row['upper_endpoint']['cdf_lower']] for row in rows]);upper=np.array([[row['lower_endpoint']['cdf_upper'],row['upper_endpoint']['cdf_upper']] for row in rows])
        cdf[param,j]=values[-1];spread[param,j]=np.max(abs(values-values[-1]),axis=0);omission[param,j]=np.max(upper-values,axis=0)
        mid_cdf_envelope[param,j]=[values[:,0].min(),upper[:,1].max()]
vertical=np.maximum(abs(mid_cdf_envelope[:,:,0]-levels),abs(mid_cdf_envelope[:,:,1]-levels))
out=dict(scope='Selected A0_CN datum14 reference, no all-target or SBC approval',model='A0_CN',data_index_zero_based=14,
         parameters=names,probabilities=levels,prior_bounds_original=bounds.tolist(),coordinates='Original frozen parameters: dimensionless u, base10 log amplitudes/EFAC, dimensionless spectral index',
         quantiles_original=quantiles.tolist(),brackets_original=brackets.tolist(),
         endpoint_CDF_fine139=cdf.tolist(),endpoint_CDF_resolution_spread=spread.tolist(),endpoint_CDF_omission_bound=omission.tolist(),
         midpoint_CDF_envelope_by_monotonicity=mid_cdf_envelope.tolist(),midpoint_CDF_deviation_from_p_envelope=vertical.tolist(),
         maximum_midpoint_CDF_deviation_envelope=float(vertical.max()),midpoint_CDF_actually_evaluated=False,
         nuisance_midpoint_horizontal_bracket_error_fraction_prior=.00045,
         nuisance_between_rule_quantile_difference_bracket_bound_fraction_prior=.0009,
         mass_bracket_method='Envelope of quantiles of4 numerical rules:20³/32×20×12 and75/139 mass nodes, with1e-10 endpoint padding; CDF values evaluated directly from positive piecewise-linear marginals.',
         important_limit='Resolution spread is an observed numerical comparison, not an analytic universal error bound. CDF at midpoint was NOT equated to p using only horizontal accuracy.',
         array_shapes={'quantiles_original':[5,4],'brackets_and_CDF_arrays':[5,4,2]},
         source_sha256={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in source})
(HERE/'results/posterior_reference.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps({k:out[k] for k in ['array_shapes','maximum_midpoint_CDF_deviation_envelope','midpoint_CDF_deviation_from_p_envelope']},indent=2))
