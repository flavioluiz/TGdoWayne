#!/usr/bin/env python3
"""Reproduce C06 moment checks; no posterior, SBC, coverage, or Gaussianity acceptance."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import platform
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))

import numpy as np
import scipy
from pta.geometry import CheckedPairMatrixBuilder,fibonacci_directions
from pta.simulation import (JULIAN_YEAR_SECONDS,LIGHT_YEAR_METERS,LIGHT_SPEED_M_S,
    SpectralParameters,orf_stack,residual_power_spectrum,residual_covariances,
    normalize_spectra,paired_physical_and_gaussian)
from pta.statistics import (angular_estimators,quadratic_moments,quadratic_cumulants,
    compress_frequencies,compress_independent_moments)
from pta.validation import Resolution,ResourceBudget
import pta.geometry,pta.simulation,pta.statistics,pta.orf,pta.response,pta.validation,pta._domain


def real_components(value):
    a=np.asarray(value)
    return np.stack((a.real,a.imag),axis=-1) if np.iscomplexobj(a) else a


def block_check(block_values,expected,threshold):
    """SE from independent Monte Carlo blocks, around declared population moments."""
    a=real_components(np.asarray(block_values));target=real_components(expected)
    estimate=np.mean(a,axis=0);se=np.std(a,axis=0,ddof=1)/np.sqrt(len(a))
    error=abs(estimate-target)
    roundoff=1e-12*max(1.0,float(np.max(abs(target))))
    z=np.divide(error,se,out=np.zeros_like(error),where=se>roundoff/threshold)
    z[(se<=roundoff/threshold)&(error>roundoff)]=np.inf
    index=np.unravel_index(np.argmax(z),z.shape)
    return {'maximum_standard_errors':float(np.max(z)),
            'maximum_standard_error_index':[int(i) for i in index],
            'maximum_absolute_error':float(np.max(error)),
            'absolute_error_at_max_z':float(error[index]),
            'monte_carlo_se_at_max_z':float(se[index]),
            'components':int(target.size),'threshold_standard_errors':threshold,
            'status':'PASS' if np.max(z)<=threshold else 'FAIL'}


def cumulant_prediction(covariances,matrices,weights,indices):
    # Two views: first channel of A, and the fixed B compression.
    result=[]
    for C,H in [(covariances[0],matrices[i]) for i in indices]:
        k=quadratic_cumulants(C,H)
        result.append((k[0],k[1],k[2]/k[1]**1.5,k[3]/k[1]**2))
    compressed=[]
    for i in indices:
        k=sum(np.array([w,w*w,w**3,w**4])*quadratic_cumulants(C,matrices[i])
              for w,C in zip(weights,covariances))
        compressed.append((k[0],k[1],k[2]/k[1]**1.5,k[3]/k[1]**2))
    return np.array([result,compressed])


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();out=args.output;out.mkdir(parents=True,exist_ok=True)
    config_bytes=args.config.read_bytes();cfg=json.loads(config_bytes)
    start=time.perf_counter();geo=cfg['geometry'];mc=cfg['monte_carlo'];oc=cfg['orf_validation']
    T=cfg['duration_years']*JULIAN_YEAR_SECONDS;dt=T/cfg['sample_count_periodic_grid']
    channels=np.asarray(cfg['positive_fourier_channels'],dtype=int)
    if not np.array_equal(channels,np.arange(1,len(channels)+1)):
        raise ValueError('This reference experiment explicitly uses channels n=1..K.')
    if channels.max()>=cfg['sample_count_periodic_grid']/2:raise ValueError('All channels must be below the regular-grid Nyquist frequency.')
    f=channels/T;directions=fibonacci_directions(geo['count'])
    distances=np.asarray(geo['distances_light_years'])*LIGHT_YEAR_METERS
    sigma=np.asarray(geo['nominal_toa_sigma_nanoseconds'])*1e-9
    red=np.asarray(geo['red_amplitude_pattern']);injected=dict(cfg['injection'])
    u=injected.pop('u_mass_frequency_times_duration')
    # JSON null is an explicit zero amplitude, represented internally by logA=-inf.
    for name in ['log10_gw_amplitude','log10_red_amplitude']:
        if injected[name] is None:injected[name]=-np.inf
    theta=SpectralParameters(**injected)
    builder=CheckedPairMatrixBuilder(coarse=Resolution(**oc['coarse']),fine=Resolution(**oc['fine']),
        pair_budget=ResourceBudget(**oc['pair_budget']),aggregate_work_budget=oc['aggregate_work_budget'],
        atol=oc['atol'],rtol=oc['rtol'])
    reference=f[0];gamma={}
    for model in ['dispersive','C_full','C_beta']:
        print(f'Computing {model} ORF stack with every pair checked.',flush=True)
        gamma[model]=orf_stack(f,u/T,directions,distances,matrix_builder=builder,
                              model=model,reference_frequency_hz=reference)
    normalization=cfg['fixed_normalization']
    fixed_scale=residual_power_spectrum(f,normalization['log10_gw_amplitude'],normalization['gw_slope'])+2*np.median(sigma)**2*dt
    Cphysical={key:residual_covariances(f,g,sigma,red,dt,theta) for key,g in gamma.items()}
    C={key:normalize_spectra(c,fixed_scale) for key,c in Cphysical.items()}
    estimators=angular_estimators(directions,sigma,cross_bins=cfg['estimators']['cross_bins'],auto_bins=cfg['estimators']['auto_bins'])
    H=estimators.matrices;weights=np.asarray(cfg['estimators']['frequency_weights']);indices=cfg['estimators']['cumulant_indices']
    moments={key:quadratic_moments(c,H) for key,c in C.items()}
    compressed={key:compress_independent_moments(*m,weights) for key,m in moments.items()}
    mu,S=moments['dispersive'];muB,SB=compressed['dispersive'];n=len(directions);K=len(f)
    Cflat=np.zeros((K*n,K*n),complex)
    for k in range(K):Cflat[k*n:(k+1)*n,k*n:(k+1)*n]=C['dispersive'][k]
    cumulants=cumulant_prediction(C['dispersive'],H,weights,indices)
    block={key:[] for key in ['q_mean','q_covariance','q_pseudocovariance',
        'physical_A_mean','physical_A_covariance','physical_B_mean','physical_B_covariance',
        'gaussian_A_mean','gaussian_A_covariance','gaussian_B_mean','gaussian_B_covariance',
        'physical_shape','gaussian_shape']}
    rng=np.random.default_rng(mc['seed']);saved={};tMC=time.perf_counter()
    print(f"Drawing {mc['blocks']*mc['draws_per_block']} paired physical/control realizations.",flush=True)
    for iblock in range(mc['blocks']):
        q,physical,control=paired_physical_and_gaussian(C['dispersive'],H,mc['draws_per_block'],rng)
        qflat=q.reshape(len(q),K*n)
        block['q_mean'].append(qflat.mean(axis=0))
        block['q_covariance'].append(np.einsum('ra,rb->ab',qflat,qflat.conj())/len(q))
        block['q_pseudocovariance'].append(np.einsum('ra,rb->ab',qflat,qflat)/len(q))
        for name,y in [('physical',physical),('gaussian',control)]:
            yB=compress_frequencies(y,weights);center=y-mu;centerB=yB-muB
            block[f'{name}_A_mean'].append(y.mean(axis=0))
            block[f'{name}_A_covariance'].append(np.einsum('rki,rkj->kij',center,center)/len(q))
            block[f'{name}_B_mean'].append(yB.mean(axis=0))
            block[f'{name}_B_covariance'].append(centerB.T@centerB/len(q))
            selected=np.stack((y[:,0,indices],yB[:,indices]),axis=1)
            z=(selected-cumulants[:,:,0])/np.sqrt(cumulants[:,:,1])
            block[f'{name}_shape'].append(np.stack((np.mean(z**3,axis=0),np.mean(z**4,axis=0)-3),axis=-1))
        if iblock==0:
            ns=mc['saved_draws'];saved={'fourier_normalized':q[:ns],
                'physical_A':physical[:ns],'physical_B':compress_frequencies(physical[:ns],weights),
                'gaussian_A':control[:ns],'gaussian_B':compress_frequencies(control[:ns],weights)}
    mc_seconds=time.perf_counter()-tMC
    expected={'q_mean':np.zeros(K*n,dtype=complex),'q_covariance':Cflat,'q_pseudocovariance':np.zeros_like(Cflat),
        'physical_A_mean':mu,'physical_A_covariance':S,'physical_B_mean':muB,'physical_B_covariance':SB,
        'gaussian_A_mean':mu,'gaussian_A_covariance':S,'gaussian_B_mean':muB,'gaussian_B_covariance':SB,
        'physical_shape':cumulants[:,:,2:],'gaussian_shape':np.zeros((2,len(indices),2))}
    checks={key:block_check(values,expected[key],mc['maximum_standard_errors']) for key,values in block.items()}
    comparisons={}
    for model in ['C_full','C_beta']:
        model_mu,model_S=moments[model];model_muB,model_SB=compressed[model]
        comparisons[model]={
            'maximum_abs_ORF_difference':float(np.max(abs(gamma[model]-gamma['dispersive']))),
            'A_mean_difference_in_true_marginal_sd':float(np.max(abs(model_mu-mu)/np.sqrt(np.diagonal(S,axis1=-2,axis2=-1)))),
            'A_covariance_relative_frobenius_difference':float(np.linalg.norm(model_S-S)/np.linalg.norm(S)),
            'B_mean_difference_in_true_marginal_sd':float(np.max(abs(model_muB-muB)/np.sqrt(np.diag(SB)))),
            'B_covariance_relative_frobenius_difference':float(np.linalg.norm(model_SB-SB)/np.linalg.norm(SB)),
            'interpretation':'Conditional predicted-moment differences at one injection; not posterior bias, KL, information loss, or coverage.'}
    source_modules=[pta.geometry,pta.simulation,pta.statistics,pta.orf,pta.response,pta.validation,pta._domain]
    source_hash={module.__name__:hashlib.sha256(Path(module.__file__).read_bytes()).hexdigest() for module in source_modules}
    report={'stage':'C06','status':'PASS' if all(x['status']=='PASS' for x in checks.values()) else 'FAIL',
        'scope':cfg['scope'],'config':cfg,'config_sha256':hashlib.sha256(config_bytes).hexdigest(),
        'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'source_sha256':source_hash,
        'versions':{'python':platform.python_version(),'numpy':np.__version__,'scipy':scipy.__version__,'platform':platform.platform()},
        'experiment':{'pulsars':n,'frequencies':K,'frequencies_hz':f.tolist(),
            'duration_seconds':T,'cadence_seconds':dt,'cadence_days':dt/86400,
            'response_reference_frequency_hz':reference,'spectral_pivot_hz':1/JULIAN_YEAR_SECONDS,
            'maximum_fL_over_c':float(np.max(f[:,None]*distances[None,:]/LIGHT_SPEED_M_S)),
            'pseudocovariance':'P=0 by construction; all inter-frequency blocks vanish in this declared periodic Fourier experiment.',
            'units':'C and fixed_scale: s^3; physical q: s^(3/2), q_normalized=q/sqrt(fixed_scale). Saved quadratics use normalized q and are dimensionless.',
            'phase':'r(t)=sqrt(2/T) Re sum q_n exp(+i2pi f_n t); ORF_ab=E[q_a q_b*]/Pgw for the signal.',
            'estimator_metadata':estimators.metadata,'estimator_labels':list(estimators.labels),
            'fixed_scale_psd_seconds_cubed':fixed_scale.tolist(),
            'minimum_ORF_eigenvalue':float(np.linalg.eigvalsh(gamma['dispersive']).min()),
            'minimum_normalized_C_eigenvalue':float(np.linalg.eigvalsh(C['dispersive']).min()),
            'maximum_C_condition_number':float(max(np.linalg.cond(x) for x in C['dispersive'])),
            'maximum_abs_imaginary_ORF':float(np.max(abs(gamma['dispersive'].imag)))},
        'monte_carlo':{'seed':mc['seed'],'independent_blocks':mc['blocks'],
            'draws_per_block':mc['draws_per_block'],'total_realizations':mc['blocks']*mc['draws_per_block'],
            'paired_control':'Same latent independent normals; correct CN and real-normal marginals. Pairing does not imply variance reduction or equality of experiments.',
            'shape_estimation':'Third/fourth central population moments use exact population centering/scaling, then independent block standard errors.',
            'threshold_note':'Predeclared empirical Monte Carlo regression threshold; not a simultaneous confidence theorem.'},
        'checks':checks,'cumulants':{'views':['A_first_frequency','B_fixed_compression'],
            'labels':[estimators.labels[i] for i in indices],
            'physical_theory_skewness_excess_kurtosis':cumulants[:,:,2:].tolist(),
            'physical_estimate':np.mean(block['physical_shape'],axis=0).tolist(),
            'gaussian_control_theory':'Zero skewness and excess kurtosis by construction.',
            'gaussian_control_estimate':np.mean(block['gaussian_shape'],axis=0).tolist()},
        'model_comparisons':comparisons,'orf_validation':builder.summary(),
        'cost_seconds':{'monte_carlo_and_block_moments':mc_seconds,'total_before_serialization':time.perf_counter()-start},
        'not_executed':['Posterior computation','SBC','conditional coverage','500-realization inference campaign','parameter prior sensitivity','window/timing-model mixing','distance uncertainty marginalization'],
        'interpretation':'Pass verifies simulation and first/second/higher moments at the declared configuration. Nonzero physical skewness/kurtosis prevents calling the Gaussian A/B likelihood exact.'}
    (out/'summary.json').write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
    (out/'orf_audit.json').write_text(json.dumps(builder.records,indent=2,allow_nan=False)+'\n')
    np.savez_compressed(out/'fixture.npz',directions=directions,distances_m=distances,
        frequencies_hz=f,nominal_toa_sigma_seconds=sigma,red_amplitude_pattern=red,
        fixed_scale_psd_seconds_cubed=fixed_scale,estimator_matrices=H,frequency_weights=weights,
        **{f'Gamma_{key}':value for key,value in gamma.items()},
        **{f'C_normalized_{key}':value for key,value in C.items()},**saved)
    print(json.dumps({'status':report['status'],'maximum_z':max(x['maximum_standard_errors'] for x in checks.values()),
                     'cost_seconds':report['cost_seconds'],'orf':builder.summary()},indent=2),flush=True)
    if report['status']!='PASS':raise SystemExit('Moment regression criterion failed; inspect summary.json.')


if __name__=='__main__':main()
