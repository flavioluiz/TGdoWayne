"""Validate timing-projected Fourier covariance against independent simulations."""
import os
for name in ('OPENBLAS_NUM_THREADS', 'OMP_NUM_THREADS', 'VECLIB_MAXIMUM_THREADS'):
    os.environ[name] = '1'
from pathlib import Path
import argparse
import hashlib
import json
import math
import time
import numpy as np
from scipy.stats import norm

ROOT = Path(__file__).resolve().parents[1]

def run(output):
    cfgpath = ROOT / 'configs/experiments/c13_timing_projection.json'
    cfg = json.loads(cfgpath.read_text())
    output.mkdir(parents=True, exist_ok=False)
    (output / 'config.json').write_text(json.dumps(cfg, indent=2)+'\n')
    n, k, count = cfg['samples'], cfg['positive_fourier_modes'], cfg['realizations']
    tol = cfg['validation']['linear_algebra_relative_tolerance']
    rng = np.random.default_rng(cfg['seed'])
    regular = np.arange(n) * cfg['duration_years'] / n
    jitter = rng.uniform(-1, 1, n) * cfg['jitter_fraction_of_cadence'] * cfg['duration_years']/n
    all_arrays, records = {}, []
    start = time.process_time()
    # A simultaneous normal-approximation threshold for all real covariance entries.
    comparisons = 2*len(cfg['fits'])*(2*k)*(2*k+1)//2
    zlimit = norm.isf(cfg['validation']['family_error_probability']/(2*comparisons))
    assert zlimit < cfg['validation']['monte_carlo_max_absolute_standardized_covariance_error']
    for sampling, times in [('regular', regular), ('jittered', regular+jitter)]:
        f = np.arange(1, k+1)/cfg['duration_years']
        D = np.exp(-2j*np.pi*f[:,None]*times[None,:])/np.sqrt(n)
        modes = np.arange(1, cfg['red_modes']+1)
        phase = 2*np.pi*times[:,None]*modes[None,:]/cfg['duration_years']
        design = np.sqrt(2/n)*np.concatenate((np.cos(phase),np.sin(phase)),axis=1)
        spectrum = cfg['red_first_mode_variance_ns2']*modes**(-cfg['red_spectral_index'])
        factor = design*np.sqrt(np.tile(spectrum,2))[None,:]
        white = cfg['white_sigma_ns']
        K = white**2*np.eye(n)+factor@factor.T
        tau = (times-np.mean(times))/cfg['duration_years']
        spin = np.column_stack((np.ones(n),tau,tau**2))
        annual = np.column_stack((spin,np.sin(2*np.pi*times),np.cos(2*np.pi*times)))
        configurations = {}
        for fit in cfg['fits']:
            M = {'none':np.zeros((n,0)), 'spin':spin, 'spin_annual':annual}[fit]
            U = np.linalg.qr(M,mode='reduced')[0] if M.shape[1] else M
            Q = np.eye(n)-U@U.T
            assert np.linalg.norm(Q@Q-Q) < tol*n
            assert np.linalg.norm(Q@M) < tol*max(1,np.linalg.norm(M))
            A = D@Q
            C, P = A@K@A.conj().T, A@K@A.T
            real = np.block([[np.real(C+P),-np.imag(C-P)],
                             [np.imag(C+P),np.real(C-P)]])/2
            B = np.concatenate((A.real,A.imag),axis=0)
            assert np.allclose(real,B@K@B.T,rtol=tol,atol=tol*np.linalg.norm(real))
            # Check the deterministic injection separately: it changes the mean,
            # while fitting removes its span. It is not a source of covariance.
            coefficients = np.linspace(-30,30,M.shape[1])
            injection = M@coefficients
            assert np.linalg.norm(Q@injection) < tol*max(1,np.linalg.norm(injection))
            sd = np.sqrt(C.diagonal().real)
            rho = C/sd[:,None]/sd[None,:]
            eta = P/sd[:,None]/sd[None,:]
            entry = dict(sampling=sampling,fit=fit,timing_parameters=M.shape[1],
                covariance_rank=int(np.linalg.matrix_rank(real)),
                maximum_cross_frequency_correlation=float(np.max(abs(rho-np.diag(np.diag(rho))))),
                maximum_normalized_pseudocovariance=float(np.max(abs(eta))),
                pseudo_frobenius_ratio=float(np.linalg.norm(P)/np.linalg.norm(C)))
            configurations[fit] = dict(M=M,Q=Q,real=real,sum=np.zeros(2*k),second=np.zeros((2*k,2*k)),entry=entry)
            prefix=sampling+'_'+fit
            for name,value in [('C',C),('P',P),('real_covariance',real),('correlation',rho),('pseudocorrelation',eta)]:
                all_arrays[prefix+'_'+name]=value
            # Monochromatic time-domain residual-energy transfer, averaged over phase.
            test_f=np.sort(np.unique(np.r_[np.linspace(.01,3,400),1.0]))
            wave=np.exp(2j*np.pi*times[:,None]*test_f[None,:])
            projected=Q@wave
            transfer=np.sum(abs(projected)**2,axis=0)/n
            assert np.all(transfer>=-tol) and np.all(transfer<=1+tol)
            if fit=='spin_annual':assert transfer[np.where(test_f==1)[0][0]]<tol
            all_arrays[prefix+'_transfer']=transfer
            all_arrays['transfer_frequency_per_year']=test_f
        if sampling=='regular':
            baseline=configurations['none']['entry']
            assert baseline['maximum_cross_frequency_correlation']<tol
            assert baseline['maximum_normalized_pseudocovariance']<tol
        for offset in range(0,count,cfg['batch_size']):
            size=min(cfg['batch_size'],count-offset)
            # Direct independent white-noise and sine/cosine generation in time.
            x=white*rng.standard_normal((size,n))+rng.standard_normal((size,2*len(modes)))@factor.T
            for fit, data in configurations.items():
                M=data['M'];injection=M@np.linspace(-30,30,M.shape[1])
                observed=x+injection
                # Fit each realization with lstsq, independent of the Q formula.
                if M.shape[1]:
                    estimate=np.linalg.lstsq(M,observed.T,rcond=None)[0]
                    residual=observed-estimate.T@M.T
                else:residual=observed
                q=residual@D.T
                y=np.concatenate((q.real,q.imag),axis=1)
                data['sum']+=y.sum(axis=0);data['second']+=y.T@y
        for fit,data in configurations.items():
            empirical=(data['second']-np.outer(data['sum'],data['sum'])/count)/(count-1)
            exact=data['real'];standard_error=np.sqrt((np.outer(np.diag(exact),np.diag(exact))+exact**2)/(count-1))
            standardized=abs(empirical-exact)/standard_error
            maximum=float(np.max(standardized))
            assert maximum<zlimit,(sampling,fit,maximum,zlimit)
            data['entry'].update(maximum_standardized_covariance_error=maximum,
                empirical_relative_frobenius_error=float(np.linalg.norm(empirical-exact)/np.linalg.norm(exact)))
            records.append(data['entry']);all_arrays[sampling+'_'+fit+'_empirical_real_covariance']=empirical
        all_arrays[sampling+'_times_years']=times
    np.savez_compressed(output/'matrices.npz',**all_arrays)
    result=dict(passed=True,scope=cfg['scope'],realizations_per_sampling=count,records=records,
        monte_carlo_validation=dict(comparisons=comparisons,simultaneous_normal_approximation_z_limit=float(zlimit),
            family_error_probability=cfg['validation']['family_error_probability'],
            note='Gaussian covariance has Wishart moments; z thresholds use its large-sample normal approximation.'),
        CPU_seconds=time.process_time()-start,
        source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        config_sha256=hashlib.sha256(cfgpath.read_bytes()).hexdigest(),
        matrices_sha256=hashlib.sha256((output/'matrices.npz').read_bytes()).hexdigest())
    (output/'results.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=ROOT/'results/C13/timing_projection')
    run(parser.parse_args().output)
