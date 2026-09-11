"""Independent analytic normal-normal and rare-mode TOYs; never PTA SBC."""
from pathlib import Path
import hashlib,json,sys,time
import numpy as np
import scipy
from scipy.special import logsumexp
from scipy.stats import norm,t,ncx2
HERE=Path.cwd();OUTPUT=Path(__file__).resolve().parent/'results/toy'
sys.path.insert(0,str(HERE/'src'))
from iid_optimized import iid_cdf,replicated_cdf,weight_summary,json_safe

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def main():
    config=json.loads((HERE/'configs/calibration/diagnostics_iid_v1.json').read_text());c=config['toy']
    dest=OUTPUT/'toy_summary.json'
    if dest.exists():raise FileExistsError('Preserve the existing TOY; use a separate package for another run')
    dest.parent.mkdir(parents=True,exist_ok=True)
    begin=time.perf_counter();rng=np.random.default_rng(c['seed'])
    m=c['normal_target_mean'];sd=c['normal_target_sd'];nu=c['proposal_df']
    scales=np.asarray(c['proposal_covariance_scales']);mix=np.asarray(c['proposal_weights'])
    sigma2=sd**2/(1-sd**2);y=m/(1-sd**2);logz=norm.logpdf(y,scale=np.sqrt(1+sigma2))
    probs=np.asarray(c['probabilities']);cuts=m+sd*norm.ppf(probs)
    true_logl=norm.logpdf(0,loc=y,scale=np.sqrt(sigma2))
    logl_cdf=ncx2.sf((y/sd)**2,df=1,nc=((m-y)/sd)**2)
    truth=np.r_[probs,logl_cdf]
    rows=[];archive={};checks=[]
    for n in c['levels']:
        estimates=[];ses=[];operational=[];logzs=[];logz_ses=[];rare=[]
        for campaign in range(c['campaigns']):
            shape=(c['replications'],n)
            component=rng.choice(len(mix),size=shape,p=mix)
            x=m+sd*scales[component]*np.sqrt((nu-2)/nu)*rng.standard_t(nu,size=shape)
            logq=logsumexp(np.stack([np.log(w)+t.logpdf(x,nu,loc=m,scale=sd*s*np.sqrt((nu-2)/nu)) for w,s in zip(mix,scales)]),axis=0)
            logw=logz+norm.logpdf(x,loc=m,scale=sd)-logq
            ll=norm.logpdf(x,loc=y,scale=np.sqrt(sigma2))
            pooled=iid_cdf(x.ravel(),logw.ravel(),cuts)+iid_cdf(ll.ravel(),logw.ravel(),[true_logl])
            replicated=replicated_cdf(x,logw,cuts)+replicated_cdf(ll,logw,[true_logl])
            estimates.append([a['estimate'] for a in pooled]);ses.append([a['mcse'] for a in pooled]);operational.append([a['mcse'] for a in replicated])
            ws=weight_summary(logw.ravel());logzs.append(ws['log_evidence']);logz_ses.append(ws['log_evidence_delta_mcse'])
            # Prespecified misspecified proposal with a very rarely visited defense.
            rare_component=rng.random(shape)<c['rare_defensive_probability']
            xr=rng.normal(size=shape)*np.where(rare_component,c['rare_defensive_sd'],1.)
            logtarget=logsumexp(np.stack([np.log(.95)+norm.logpdf(xr),np.log(.05)+norm.logpdf(xr,loc=c['rare_target_mode_mean'])]),axis=0)
            logproposal=logsumexp(np.stack([np.log1p(-c['rare_defensive_probability'])+norm.logpdf(xr),np.log(c['rare_defensive_probability'])+norm.logpdf(xr,scale=c['rare_defensive_sd'])]),axis=0)
            wr=logtarget-logproposal;cr=replicated_cdf(xr,wr,[6.])[0];wsr=weight_summary(wr.ravel())
            rare.append({'estimate':cr['estimate'],'mcse':cr['mcse'],'precision_pass':cr['precision_pass'],
                'status':cr['status'],'all_replications_resolved':cr['all_replications_resolved'],
                'weight_ess_fraction':wsr['weight_ess_concentration_only']/xr.size,
                'log_evidence':wsr['log_evidence'],'log_evidence_mcse':wsr['log_evidence_delta_mcse'],
                'defensive_draws':int(rare_component.sum()),'largest_weight':wsr['maximum_normalized_weight'],
                'guard_pass':wsr['single_deletion_guard_pass']})
        est=np.asarray(estimates);se=np.asarray(ses);op=np.asarray(operational)
        rms=np.sqrt(np.mean(se**2,axis=0));emp=np.std(est,axis=0,ddof=1);bias=est.mean(axis=0)-truth
        zerr=(np.asarray(logzs)-logz);zse=np.asarray(logz_ses)
        negative_flags=np.mean([not a['precision_pass'] or not a['guard_pass'] for a in rare])
        row={'N_per_replication':n,'R':c['replications'],'campaigns':c['campaigns'],
            'truth_cdfs':truth,'mean_estimates':est.mean(axis=0),'empirical_sd':emp,'rms_influence_mcse':rms,
            'empirical_sd_over_rms_mcse':emp/rms,'bias':bias,'bias_over_standard_error_of_mean':bias/(emp/np.sqrt(len(est))),
            'operational_mcse_mean':np.mean(op,axis=0),'operational_precision_pass_fraction':np.mean(op<=config['cdf_mcse_target'],axis=0),
            'log_evidence_truth':logz,'log_evidence_empirical_sd':float(np.std(zerr,ddof=1)),
            'log_evidence_rms_mcse':float(np.sqrt(np.mean(zse**2))),
            'negative_exact_cdf':float(.95*norm.cdf(6)+.05*norm.cdf(6,loc=12)),
            'negative_fraction_flagged':negative_flags,'negative_runs':rare}
        rows.append(row);archive[f'N{n}_estimates']=est;archive[f'N{n}_influence_mcse']=se;archive[f'N{n}_operational_mcse']=op
        lo,hi=c['variance_check_empirical_sd_over_rms_influence_se_interval']
        checks.extend([{'name':f'N{n}_variance_calibration','pass':bool(np.all((emp/rms>=lo)&(emp/rms<=hi)))},
            {'name':f'N{n}_bias','pass':bool(np.max(abs(bias/(emp/np.sqrt(len(est)))))<=c['bias_check_max_standard_errors'])},
            {'name':f'N{n}_negative_control','pass':bool(negative_flags>=c['negative_control_min_fraction_flagged'])}])
    ratio=np.asarray(rows[1]['rms_influence_mcse'])/np.asarray(rows[0]['rms_influence_mcse']);lo,hi=c['refinement_rms_mcse_ratio_interval']
    checks.append({'name':'N_refinement_MCSE','pass':bool(np.all((ratio>=lo)&(ratio<=hi)))})
    result={'label':'ANALYTIC_TOY_ONLY_NOT_PTA_SBC','config':config,'results':rows,'refinement_mcse_ratio':ratio,
        'checks':checks,'all_predeclared_checks_pass':all(a['pass'] for a in checks),'seconds':time.perf_counter()-begin,
        'numpy':np.__version__,'scipy':scipy.__version__,
        'source_hashes':{str(p.relative_to(HERE)):sha(p) for p in [Path(__file__),HERE/'configs/calibration/diagnostics_iid_v1.json',HERE/'src/inference/iid_diagnostics.py',Path(__file__).resolve().parent/'iid_optimized.py']}}
    np.savez_compressed(OUTPUT/'toy_arrays.npz',**archive)
    dest.write_text(json.dumps(json_safe(result),indent=2,allow_nan=False)+'\n')
    print(json.dumps(json_safe({k:result[k] for k in ['checks','all_predeclared_checks_pass','seconds','refinement_mcse_ratio']}),indent=2))

    return 0 if result['all_predeclared_checks_pass'] else 1

if __name__=='__main__':raise SystemExit(main())
