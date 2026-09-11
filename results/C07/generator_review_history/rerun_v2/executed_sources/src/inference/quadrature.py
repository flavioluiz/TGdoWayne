"""Continuous-prior integration utilities; numerical acceptance is assessed externally."""
from pathlib import Path
from time import perf_counter
import json
import numpy as np
from scipy.special import logsumexp
from scipy.stats import qmc

def continuous_cdf(nodes_x,density,x):
    """Exact CDF of positive piecewise-linear unnormalized density, no atoms."""
    nodes_x=np.asarray(nodes_x);density=np.asarray(density)
    area=np.diff(nodes_x)*.5*(density[:-1]+density[1:])
    total=area.sum();cdf=np.concatenate(([0.],np.cumsum(area)))
    x=float(x)
    if x<=nodes_x[0]:return 0.
    if x>=nodes_x[-1]:return 1.
    i=np.searchsorted(nodes_x,x)-1;t=x-nodes_x[i];dx=nodes_x[i+1]-nodes_x[i]
    return float((cdf[i]+density[i]*t+.5*(density[i+1]-density[i])*t*t/dx)/total)


def continuous_ppf(x,density,p):
    from scipy.optimize import brentq
    return float(brentq(lambda u:continuous_cdf(x,density,u)-p,float(x[0]),float(x[-1]),xtol=2e-13))


def trapezoid_weights(x):
    w=np.zeros(len(x));d=np.diff(x)/2;w[:-1]+=d;w[1:]+=d
    return w


def integrate_level(level,config,e,provider,likelihood,truth,outdir,*,batch=256,proposal_sampler=None):
    """Stream mass slices. Nuisance Sobol weights approximate continuous integrals.

    Marginal nuisance quantiles use weighted midpoint-CDF interpolation, which is
    checked by level/scramble comparison; the points are not posterior draws.
    """
    outdir=Path(outdir);outdir.mkdir(parents=True,exist_ok=True)
    t0=perf_counter();bounds=np.array(config['prior']['bounds']);r=level['scrambles'];n=2**level['nuisance_power'];m=len(likelihood.names)*len(truth)
    mass=np.linspace(*bounds[0],level['mass_nodes'])
    if 'endpoint_beta_nodes' in level:
        if not np.array_equal(bounds[0],[0,1]):raise ValueError('Endpoint beta transform is defined here only for u in [0,1].')
        mass=np.unique(np.r_[mass,np.sqrt(1-np.asarray(level['endpoint_beta_nodes'])**2)])
    mw=trapezoid_weights(mass)/(bounds[0,1]-bounds[0,0])
    children=np.random.SeedSequence(level['seed']).spawn(r)
    if proposal_sampler is None:
        eta=np.stack([qmc.Sobol(4,scramble=True,seed=np.random.default_rng(child)).random_base2(level['nuisance_power']) for child in children])
        logq=np.zeros(eta.shape[:2])
    else:
        samples=[proposal_sampler(level['nuisance_power'],child) for child in children]
        eta=np.stack([s[0] for s in samples]);logq=np.stack([s[1] for s in samples]);n=eta.shape[1]
        if eta.shape!=(r,n,4) or logq.shape!=(r,n) or not np.isfinite(eta).all() or not np.isfinite(logq).all():raise ValueError('Invalid continuous proposal sample/density.')
    eta=bounds[1:,0]+eta*(bounds[1:,1]-bounds[1:,0])
    log_marginal=np.empty((len(mass),r,m));log_eta_weights=np.full((r,n,m),-np.inf)
    # Diagnostic log L(theta_true; observed data), not simply the truth coordinate.
    threshold=[]
    for index,theta in enumerate(truth):
        all_ll=likelihood(theta[None,1:],provider.evaluate(float(theta[0])))[0]
        threshold.append(all_ll[np.arange(5)*len(truth)+index])
    threshold=np.array(threshold).T.reshape(m)
    dep_numerator=np.full((r,m),-np.inf);dep_prior=np.zeros((r,m))
    for j,u in enumerate(mass):
        gamma=provider.evaluate(float(u));basis=likelihood.prepare(gamma)
        for scramble in range(r):
            lls=[]
            for start in range(0,n,batch):lls.append(likelihood(eta[scramble,start:start+batch],gamma,basis))
            ll=np.concatenate(lls,axis=0)
            target=ll-logq[scramble,:,None]
            log_marginal[j,scramble]=logsumexp(target,axis=0)-np.log(n)
            log_eta_weights[scramble]=np.logaddexp(log_eta_weights[scramble],target+np.log(mw[j]))
            mask=ll<=threshold[None]
            dep_numerator[scramble]=np.logaddexp(dep_numerator[scramble],logsumexp(np.where(mask,target,-np.inf),axis=0)-np.log(n)+np.log(mw[j]))
            dep_prior[scramble]+=np.mean(mask*np.exp(-logq[scramble,:,None]),axis=0)*mw[j]
        if j%16==0:print(f'{level["name"]}: mass {j+1}/{len(mass)} elapsed {perf_counter()-t0:.1f}s',flush=True)
    per_r_logz=logsumexp(log_marginal+np.log(mw)[:,None,None],axis=0)
    logz=logsumexp(per_r_logz,axis=0)-np.log(r)
    lmd=logsumexp(log_marginal,axis=1)-np.log(r)
    density=np.exp(lmd-lmd.max(axis=0))
    quant=np.empty((m,5,len(config['quantiles'])));pit=np.empty((m,5));mean=np.empty((m,5));sd=np.empty((m,5))
    ess=np.empty(m);maxw=np.empty(m);klmass=np.empty(m)
    samples=eta.reshape(r*n,4);logew=log_eta_weights.reshape(r*n,m);weights=np.exp(logew-logsumexp(logew,axis=0))
    real_truth=np.tile(truth,(5,1))
    for col in range(m):
        quant[col,0]=[continuous_ppf(mass,density[:,col],p) for p in config['quantiles']]
        pit[col,0]=continuous_cdf(mass,density[:,col],real_truth[col,0])
        norm=density[:,col]@mw;d=density[:,col]/norm
        mean[col,0]=(mass*d)@mw;sd[col,0]=np.sqrt(max(0,(mass*mass*d)@mw-mean[col,0]**2))
        klmass[col]=np.sum(mw*d*np.log(np.maximum(d,1e-300)))
        wc=weights[:,col];ess[col]=1/np.sum(wc*wc);maxw[col]=wc.max()
        for par in range(4):
            order=np.argsort(samples[:,par],kind='stable');xx=samples[order,par];ww=wc[order];cdf=np.cumsum(ww)-.5*ww
            xx=np.concatenate(([bounds[par+1,0]],xx,[bounds[par+1,1]]));cdf=np.concatenate(([0.],cdf,[1.]))
            quant[col,par+1]=np.interp(config['quantiles'],cdf,xx)
            pit[col,par+1]=np.interp(real_truth[col,par+1],xx,cdf)
            mean[col,par+1]=wc@samples[:,par]
            sd[col,par+1]=np.sqrt(max(0,wc@(samples[:,par]**2)-mean[col,par+1]**2))
    zratio=np.exp(per_r_logz-logz)
    dep=np.exp(logsumexp(dep_numerator,axis=0)-np.log(r)-logz)
    output=dict(level=level,wall_seconds=perf_counter()-t0,parameter_points=int(len(mass)*r*n),likelihood_values=int(len(mass)*r*n*m),methods=likelihood.names,realizations=len(truth),log_evidence=logz.reshape(5,-1).tolist(),log_evidence_by_scramble=per_r_logz.reshape(r,5,-1).tolist(),evidence_relative_standard_error=(zratio.std(axis=0,ddof=1)/np.sqrt(r)).reshape(5,-1).tolist(),quantiles=quant.reshape(5,len(truth),5,-1).tolist(),pit=pit.reshape(5,len(truth),5).tolist(),posterior_mean=mean.reshape(5,len(truth),5).tolist(),posterior_sd=sd.reshape(5,len(truth),5).tolist(),mass_marginal_kl_from_prior=klmass.reshape(5,-1).tolist(),nuisance_quadrature_weight_concentration_ess=ess.reshape(5,-1).tolist(),maximum_nuisance_weight=maxw.reshape(5,-1).tolist(),data_dependent_loglikelihood_pit=dep.reshape(5,-1).tolist(),ignored_data_prior_loglikelihood_pit=dep_prior.mean(axis=0).reshape(5,-1).tolist(),converged=False,sbc500_completed=False)
    (outdir/(level['name']+'.json')).write_text(json.dumps(output,indent=2)+'\n')
    output['integration_measure']='continuous prior with deterministic-mixture importance correction' if proposal_sampler else 'continuous prior with uniform Sobol nuisance integration'
    output['kernel']=type(likelihood).__name__
    output['proposal_integral_of_original_prior_by_scramble']=np.mean(np.exp(-logq),axis=1).tolist()
    output['ignored_data_prior_loglikelihood_pit']=(dep_prior.mean(axis=0)/np.mean(np.exp(-logq))).reshape(5,-1).tolist()
    (outdir/(level['name']+'.json')).write_text(json.dumps(output,indent=2)+'\n')
    np.savez_compressed(outdir/(level['name']+'_marginals.npz'),mass=mass,log_mass_marginal_by_scramble=log_marginal,eta=eta,log_eta_weights=log_eta_weights,log_proposal_density_in_unit_cube=logq)
    return output
