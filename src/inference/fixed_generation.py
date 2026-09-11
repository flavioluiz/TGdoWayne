"""Fixed-truth C07 data only, with explicit missing truths for an absent GW signal."""
from numbers import Integral
import numpy as np
from inference.model import experiment, covariance_batch, YEAR
from inference.likelihood_reference import cn_logpdf
from inference.campaign_io import MODELS
from pta.simulation import paired_physical_and_gaussian

PARAMETERS = ['u','log10_Agw','gamma_gw','log10_Ar','log10_EFAC']
SCENARIOS = ['mass_zero_signal_present','near_kinematic_edge','no_gravitational_signal']


def validate_design(config, protocol):
    if config['parameters'] != PARAMETERS or protocol['parameter_order'] != PARAMETERS:
        raise ValueError('The five original C07 parameter coordinates are required.')
    if config['models'] != list(MODELS) or protocol['models'] != ['A0_CN']:
        raise ValueError('Runtime admits five models; this fixed experiment plans only A0_CN.')
    n=protocol['repetitions_per_scenario']
    if isinstance(n,(bool,np.bool_)) or not isinstance(n,Integral) or n != 32:
        raise ValueError('The fixed protocol requires 32 replications per scenario.')
    rows=protocol['scenarios']
    if [r['id'] for r in rows] != SCENARIOS or config['n_realizations'] != 3*n:
        raise ValueError('Exactly three ordered scenarios and 96 rows are required.')
    if config['positive_channels'] != [1,2,3,4] or config['fixed_red_slope'] != 4:
        raise ValueError('Four channels and fixed red slope four are required.')
    bounds=np.asarray(config['prior']['bounds'],float)
    if (config['prior']['kind']!='independent uniform in these coordinates' or
        bounds.shape!=(5,2) or not np.isfinite(bounds).all() or
        np.any(bounds[:,1]<=bounds[:,0]) or not np.array_equal(bounds[0],[0,1])):
        raise ValueError('The finite C07 signal-plus-noise prior is required.')
    for j,row in enumerate(rows):
        if not isinstance(row['signal_present'],bool) or row['signal_present'] != (j<2):
            raise ValueError('Signal-presence flags differ from the fixed protocol.')
        if isinstance(row['data_seed'],(bool,np.bool_)) or not isinstance(row['data_seed'],Integral) or row['data_seed']<0:
            raise ValueError('Explicit nonnegative integer seed required.')
        truth=row['truth']; expected=PARAMETERS if j<2 else PARAMETERS[3:]
        if len(truth)!=5 or row['coverage_parameters'] != expected:
            raise ValueError('Truth and coverage mask differ from the scenario.')
        if j==2 and truth[:3] != [None,None,None]:
            raise ValueError('GW mass/amplitude/slope have no generating truth without a GW.')
        for k in range(0 if j<2 else 3,5):
            if isinstance(truth[k],bool) or not np.isscalar(truth[k]) or not np.isfinite(truth[k]) or not bounds[k,0]<=truth[k]<=bounds[k,1]:
                raise ValueError('Every defined truth must lie within its declared coordinate bounds.')
    if rows[0]['truth'][0]!=0. or rows[1]['truth'][0]!=.995:
        raise ValueError('The fixed signal masses must be exactly 0 and .995.')
    if len(set(r['data_seed'] for r in rows))!=3:
        raise ValueError('Three independent scenario streams are required.')
    return experiment(config)


def fixed_covariance(row, exp, provider):
    """Return normalized C, explicit GW part and noise part, without a fake GW amplitude."""
    theta=row['truth']; K,P=len(exp['f']),len(exp['points'])
    ar,efac=float(theta[3]),float(theta[4])
    red=10**(2*ar)*YEAR**3/(12*np.pi*np.pi)*(exp['f']*YEAR)**(-4)/exp['scale']
    white=10**(2*efac)*2*exp['dt']/exp['scale']
    noise=np.zeros((K,P,P),dtype=complex); ii=np.arange(P)
    noise[:,ii,ii]=red[:,None]*exp['red'][None,:]**2+white[:,None]*exp['sigma'][None,:]**2
    if row['signal_present']:
        gamma=provider.evaluate(float(theta[0]))
        total,weights=covariance_batch(np.asarray(theta[1:],float)[None],gamma,exp)
        gw=weights[0,:,0,None,None]*gamma
        total=total[0]
        np.testing.assert_allclose(total,gw+noise,rtol=1e-14,atol=1e-14)
    else:
        # No ORF request, no finite log-amplitude stand-in, no evaluation of NaN mass/slope.
        gw=np.zeros((K,P,P),dtype=complex)
        total=noise.copy()
    np.linalg.cholesky(total)
    return total,gw,noise


def generate_fixed_fixture(config, protocol, provider):
    """Return 96 rows in scenario-major order, explicit masks and source covariances.

    Each scenario uses its own declared PCG64 stream; each row calls the same
    paired physical/Gaussian generator used by the continuous-prior experiment.
    Gaussian observations are retained for loader compatibility, not fitted here.
    """
    exp=validate_design(config,protocol)
    n=protocol['repetitions_per_scenario']
    covariance=[];gw_covariance=[];noise_covariance=[]
    # Check both signal-node payloads before drawing observations.
    for row in protocol['scenarios']:
        c,g,w=fixed_covariance(row,exp,provider)
        covariance.append(c);gw_covariance.append(g);noise_covariance.append(w)
    q=[];physical=[];gaussian=[];truth=[];defined=[];logl=[];logl_defined=[];structural=[]
    for j,row in enumerate(protocol['scenarios']):
        rng=np.random.default_rng(row['data_seed'])
        theta=np.array([np.nan if v is None else v for v in row['truth']],float)
        mask=np.isfinite(theta)
        for unused in range(n):
            coef,obs,control=paired_physical_and_gaussian(covariance[j],exp['H'],1,rng)
            q.append(coef[0]);physical.append(obs[0]);gaussian.append(control[0])
            truth.append(theta.copy());defined.append(mask.copy())
            has_logl=bool(row['signal_present'])
            logl_defined.append(has_logl)
            # This is signal-model logL at a defined five-parameter truth only.
            logl.append(float(cn_logpdf(covariance[j][None],coef)[0,0]) if has_logl else np.nan)
            s=np.zeros(5,bool);s[0]=(j==0);structural.append(s)
    arrays=dict(truth=np.array(truth),truth_defined=np.array(defined),
        coverage_parameter_defined=np.array(defined),
        log_likelihood_at_truth=np.array(logl),log_likelihood_at_truth_defined=np.array(logl_defined),
        structural_lower_boundary_pit=np.array(structural),
        scenario_index=np.repeat(np.arange(3),n),replicate_within_scenario=np.tile(np.arange(n),3),
        target=np.arange(3*n),signal_present=np.repeat([True,True,False],n),
        q=np.array(q),x_physical=np.array(physical),x_gaussian=np.array(gaussian),
        directions=exp['points'],distances_ly=exp['distance_ly'],sigma=exp['sigma'],
        red_pattern=exp['red'],frequency_hz=exp['f'],scale=exp['scale'],
        covariance_by_scenario=np.array(covariance),
        gw_covariance_by_scenario=np.array(gw_covariance),noise_covariance_by_scenario=np.array(noise_covariance))
    return arrays
