"""Cheap IID/AR1 diagnostics validation; does not read or simulate PTA data."""
from pathlib import Path
import hashlib,json,sys,time
import numpy as np
import scipy
from scipy import stats
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from inference.mcmc_diagnostics import (rank_rhat,effective_sample_size,bulk_tail_ess,
    cdf_summary,quantile_summary,randomized_exchangeable_rank)


def ar1(rng, n, chains, rho):
    x=np.empty((n,chains));x[0]=rng.normal(size=chains)
    epsilon=rng.normal(size=(n-1,chains))*np.sqrt(1-rho*rho)
    for i in range(1,n): x[i]=rho*x[i-1]+epsilon[i-1]
    return x


def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    started=time.perf_counter()
    cfg=json.loads((ROOT/'configs/calibration/diagnostics_mcmc_v2.json').read_text());t=cfg['toy']
    rng=np.random.default_rng(t['seed']); m=cfg['chains'];rho=t['ar1_rho']
    iid=rng.normal(size=(t['iid_draws_per_chain'],m))
    correlated=ar1(rng,t['ar1_draws_per_chain'],m,rho)
    expected_mean=correlated.size*(1-rho)/(1+rho)
    tau_indicator=1+4/np.pi*np.arcsin(rho**np.arange(1,10000)).sum()
    expected_indicator=correlated.size/tau_indicator
    iid_ess=effective_sample_size(iid); ar_ess=effective_sample_size(correlated)
    ar_cdf=cdf_summary(correlated,0)
    estimates=[];mcse=[]
    for _ in range(t['cdf_replications']):
        x=ar1(rng,t['cdf_draws_per_chain'],m,rho)
        result=cdf_summary(x,0)
        estimates.append(result['estimate']);mcse.append(result['mcse'])
    ratio=float(np.std(estimates,ddof=1)/np.sqrt(np.mean(np.square(mcse))))
    rrng=np.random.default_rng(t['ranks_seed']);independent_ranks=[];correlated_ranks=[]
    for _ in range(t['rank_replications']):
        true=float(rrng.normal())
        independent_ranks.append(randomized_exchangeable_rank(rrng.normal(size=t['rank_draws']),true,rrng)['randomized_pit'])
        chain=ar1(rrng,t['rank_draws'],1,t['rank_ar1_rho'])[:,0]
        correlated_ranks.append(randomized_exchangeable_rank(chain,true,rrng)['randomized_pit'])
    independent_ks=stats.kstest(independent_ranks,'uniform',method='exact')
    correlated_ks=stats.kstest(correlated_ranks,'uniform',method='exact')
    tol=t['ess_relative_error_tolerance'];lo,hi=t['mcse_empirical_ratio_interval']
    checks={
      'iid_ess_relative_error':abs(iid_ess['ess']/iid.size-1)<=tol,
      'ar1_mean_ess_relative_error':abs(ar_ess['ess']/expected_mean-1)<=tol,
      'ar1_indicator_ess_relative_error':abs(ar_cdf['ess']/expected_indicator-1)<=tol,
      'empirical_cdf_sd_to_estimated_mcse':lo<=ratio<=hi,
    }
    checks={name:bool(value) for name,value in checks.items()}
    result={
      'label':t['label'],'seed':t['seed'],'rank_seed':t['ranks_seed'],
      'config_sha256':sha(ROOT/'configs/calibration/diagnostics_mcmc_v2.json'),
      'source_sha256':{str(p.relative_to(ROOT)):sha(p) for p in [ROOT/'src/inference/mcmc_diagnostics.py',Path(__file__)]},
      'dependencies':{'numpy':np.__version__,'scipy':scipy.__version__},
      'iid':{'draws':iid.size,'ess':iid_ess,'rhat':rank_rhat(iid),'bulk_tail':bulk_tail_ess(iid)},
      'ar1':{'rho':rho,'draws':correlated.size,'theoretical_mean_ess':float(expected_mean),
             'theoretical_indicator_at_zero_ess':float(expected_indicator),'mean_ess':ar_ess,
             'cdf':ar_cdf,'rhat':rank_rhat(correlated),'bulk_tail':bulk_tail_ess(correlated),
             'quantile90':quantile_summary(correlated,.9)},
      'repeated_cdf_mcse':{'replications':len(estimates),'draws_per_chain':t['cdf_draws_per_chain'],
             'empirical_sd':float(np.std(estimates,ddof=1)),'root_mean_squared_estimated_mcse':float(np.sqrt(np.mean(np.square(mcse)))),
             'ratio':ratio,'mean_bias':float(np.mean(estimates)-.5)},
      'randomized_ranks':{'replications':t['rank_replications'],'posterior_draws':t['rank_draws'],
             'iid':{'KS_D':float(independent_ks.statistic),'p':float(independent_ks.pvalue)},
             'stationary_ar1':{'rho':t['rank_ar1_rho'],'KS_D':float(correlated_ks.statistic),'p':float(correlated_ks.pvalue)},
             'warning':'Jitter within rank cells cannot cure nonexchangeable correlated posterior draws. KS observations are reported without seed selection; not unit-test acceptance.'},
      'predeclared_numeric_checks':checks,'all_numeric_checks_pass':all(checks.values()),
      'elapsed_seconds':time.perf_counter()-started,'PTA_data_read':False,'PTA_SBC_executed':False,
    }
    (ROOT/'results/C07/mcmc_toy').mkdir(parents=True,exist_ok=True)
    (ROOT/'results/C07/mcmc_toy/toy_summary.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    np.savez_compressed(ROOT/'results/C07/mcmc_toy/toy_validation_arrays.npz',cdf_estimates=estimates,cdf_mcse=mcse,
                        iid_randomized_ranks=independent_ranks,ar1_randomized_ranks=correlated_ranks)
    print(json.dumps({'checks':checks,'ar1_mean_ess_relative':ar_ess['ess']/expected_mean,
                      'ar1_indicator_ess_relative':ar_cdf['ess']/expected_indicator,'mcse_ratio':ratio,
                      'ranks':result['randomized_ranks'],'elapsed_seconds':result['elapsed_seconds']},indent=2))
    return 0 if all(checks.values()) else 1


if __name__=='__main__':raise SystemExit(main())
