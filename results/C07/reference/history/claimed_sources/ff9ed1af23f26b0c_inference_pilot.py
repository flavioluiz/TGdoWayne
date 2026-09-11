"""Executable staged C07 integration; explicit finite quadrature of a continuous target.

No categorical mass prior, posterior sampling, SBC acceptance, or ORF interpolation.
"""
from pathlib import Path
from functools import lru_cache
from time import perf_counter
import hashlib
import json
import numpy as np
from scipy.special import roots_legendre, logsumexp
from scipy.stats import qmc
from pta import transfer
from pta.orf import raw_direct_orf
from pta.simulation import JULIAN_YEAR_SECONDS as YEAR, SpectralParameters, residual_power_spectrum, residual_covariances, paired_physical_and_gaussian
from pta.statistics import angular_estimators, quadratic_moments, compress_independent_moments, compress_frequencies


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def experiment(config):
    n=config['n_pulsars'];i=np.arange(n)
    z=1-2*(i+.5)/n;phi=np.pi*(3-np.sqrt(5))*i
    p=np.column_stack((np.sqrt(1-z*z)*np.cos(phi),np.sqrt(1-z*z)*np.sin(phi),z))
    seeds=config['geometry_seeds'];lo,hi=config['distance_range_light_years']
    d=np.linspace(lo,hi,n)[np.random.default_rng(seeds[0]).permutation(n)]
    sigma=np.geomspace(1e-7,5e-7,n)[np.random.default_rng(seeds[1]).permutation(n)]
    red=np.geomspace(.5,2,n)[np.random.default_rng(seeds[2]).permutation(n)]
    T=config['duration_years']*YEAR
    dt=T/int(np.ceil(T/(config['cadence_days']*86400)))
    f=np.asarray(config['positive_channels'])/T
    scale=residual_power_spectrum(f,-14.7,13/3)+2*np.median(sigma)**2*dt
    H=angular_estimators(p,sigma,cross_bins=4,auto_bins=2)
    return dict(points=p,distance_ly=d,sigma=sigma,red=red,T=T,dt=dt,f=f,scale=scale,H=H.matrices,labels=H.labels,weights=np.asarray(config['frequency_weights']))


@lru_cache(maxsize=12)
def nodes(n):
    x,w=roots_legendre(n);x.flags.writeable=False;w.flags.writeable=False
    return x,w


def shared_matrix(beta,y,points,*,lmax,nmu):
    """Shared 1D multipole integrals; checked externally at every requested mass."""
    x,w=nodes(nmu)
    weight=(w*(1-x*x))[None,:]*np.stack([transfer(float(yy),1+beta*x) for yy in y])
    coeff=np.empty((len(y),lmax-1),complex)
    prev=np.zeros_like(x);p=3*(1-x*x)
    for ell in range(2,lmax+1):
        coeff[:,ell-2]=weight@p
        prev,p=p,((2*ell+1)*x*p-(ell+2)*prev)/(ell-1)
    delta=np.clip(points@points.T,-1,1)
    prev=np.ones_like(delta);p=delta.copy();g=np.zeros(delta.shape,complex)
    for ell in range(2,lmax+1):
        new=((2*ell-1)*delta*p-(ell-1)*prev)/ell
        norm=3/32*(2*ell+1)/((ell-1)*ell*(ell+1)*(ell+2))
        c=coeff[:,ell-2]
        g+=norm*(c[:,None]*c[None,:].conj())*new
        prev,p=p,new
    return (g+g.conj().T)/2


class ExactNodeORF:
    """No interpolation. Audit common coarse/fine orders plus predefined direct pairs.

    Agreement of two harmonic resolutions is an internal convergence check, not
    independent certification of every matrix entry by direct sky quadrature.
    """
    def __init__(self,exp,config,path):
        self.e=exp;self.cfg=config;self.path=Path(path);self.path.mkdir(parents=True,exist_ok=True)
        self.y=2*np.pi*exp['f'][:,None]*exp['distance_ly'][None,:]*YEAR
        if self.y.max()>config['maximum_phase']:raise ValueError('Phase exceeds declared domain.')
        self.l=(self.y.max(axis=1)+config['lmax_margin']).astype(int)
        self.n=(2*self.y.max(axis=1)+config['nmu_margin']).astype(int)
        self.lf=self.l+config['fine_lmax_addition'];self.nf=self.n+config['fine_nmu_addition']
        self.work=0;self.records=[]
        self.signature=hashlib.sha256(json.dumps(config,sort_keys=True).encode()+exp['points'].tobytes()+self.y.tobytes()).hexdigest()

    def evaluate(self,u):
        if not np.ndim(u)==0 or not np.isfinite(u) or not 0<=u<=1:raise ValueError('u must be real in [0,1].')
        token=hashlib.sha256(self.signature.encode()+float(u).hex().encode()).hexdigest()
        dest=self.path/(token+'.npz')
        if dest.exists():
            with np.load(dest,allow_pickle=False) as saved:
                self.records.append(json.loads(str(saved['record'])))
                return saved['Gamma']
        cost=int(len(self.e['points'])*np.sum(self.l*self.n+self.lf*self.nf))
        memory=int(32*len(self.e['points'])*max(self.nf)+48*max(self.nf)+16*len(self.e['points'])*max(self.lf))
        if self.work+cost>self.cfg['maximum_total_work_units']:raise RuntimeError('Aggregate ORF work budget exhausted before computation.')
        if memory>self.cfg['maximum_estimated_memory_bytes']:raise RuntimeError('ORF memory estimate exceeds budget.')
        self.work+=cost;t=perf_counter();rows=[];errors=[]
        for k,(y,l,n,lf,nf) in enumerate(zip(self.y,self.l,self.n,self.lf,self.nf)):
            beta=np.sqrt((1-u/(k+1))*(1+u/(k+1)))
            a=shared_matrix(beta,y,self.e['points'],lmax=int(l),nmu=int(n))
            b=shared_matrix(beta,y,self.e['points'],lmax=int(lf),nmu=int(nf))
            error=float(np.max(abs(a-b)))
            if error>self.cfg['maximum_matrix_abs_difference']:raise RuntimeError(f'ORF unresolved at u={u}, channel={k+1}: {error}')
            if np.linalg.eigvalsh(b).min()<-1e-12:raise RuntimeError('Negative ORF eigenvalue; no clipping allowed.')
            rows.append(b);errors.append(error)
        g=np.array(rows)
        record=dict(u=float(u),seconds=perf_counter()-t,maximum_coarse_fine_difference=max(errors),channel_errors=errors,minimum_eigenvalue=float(np.linalg.eigvalsh(g).min()),work_units=cost,estimated_memory_bytes=memory,signature=self.signature)
        np.savez_compressed(dest,Gamma=g,record=json.dumps(record))
        self.records.append(record)
        return g

    def direct_checks(self):
        result=[]
        direct_work=6*2*int(self.nf[0])**2+2*int(self.nf[-1])**2
        direct_memory=24*16*int(self.nf[-1])*128+544*int(self.nf[-1])
        # Separate explicit budget: the direct routine uses 128 azimuthal columns.
        # Original sparse checks preceded this guard; reports record that fact.
        if direct_work>1_000_000_000 or direct_memory>700_000_000:
            raise RuntimeError('Sparse independent direct checks exceed their explicit work/memory budget.')
        # Two pairs, three masses, lowest channel; an extra highest-frequency pair.
        for u in self.cfg['direct_mass_points']:
            g=self.evaluate(u)
            for a,b in self.cfg['direct_pairs']:
                k=0;beta=np.sqrt((1-u)*(1+u));cos=float(self.e['points'][a]@self.e['points'][b]);y=self.y[k]
                t=perf_counter()
                direct=raw_direct_orf(beta,cos,y[a],y[b],nmu=int(self.nf[k]),nphi=int(2*self.nf[k]))
                error=float(abs(direct-g[k,a,b]))
                if error>1e-7:raise RuntimeError(f'Independent direct pair disagrees: {error}')
                result.append(dict(u=u,channel=k+1,pair=[a,b],absolute_difference=error,seconds=perf_counter()-t))
        u=.5;g=self.evaluate(u);k=3;a,b=3,8;y=self.y[k];beta=np.sqrt(1-(u/(k+1))**2)
        t=perf_counter();direct=raw_direct_orf(beta,float(self.e['points'][a]@self.e['points'][b]),y[a],y[b],nmu=int(self.nf[k]),nphi=int(2*self.nf[k]))
        error=float(abs(direct-g[k,a,b]))
        if error>1e-7:raise RuntimeError('Highest channel direct check failed.')
        result.append(dict(u=u,channel=k+1,pair=[a,b],absolute_difference=error,seconds=perf_counter()-t))
        for record in result:
            record['all_direct_checks_work_proxy']=direct_work
            record['maximum_direct_memory_estimate_bytes']=direct_memory
            record['direct_budget']={'work_proxy':1_000_000_000,'estimated_memory_bytes':700_000_000}
        return result


def covariance_batch(eta,gamma,e):
    eta=np.atleast_2d(eta);ag,slope,ar,efac=eta.T
    sg=10**(2*ag[:,None])*YEAR**3/(12*np.pi*np.pi)*(e['f'][None,:]*YEAR)**(-slope[:,None])/e['scale']
    sr=10**(2*ar[:,None])*YEAR**3/(12*np.pi*np.pi)*(e['f'][None,:]*YEAR)**(-4)/e['scale']
    sw=10**(2*efac[:,None])*2*e['dt']/e['scale']
    weights=np.stack((sg,sr,sw),axis=-1)
    c=sg[:,:,None,None]*gamma[None]
    ii=np.arange(c.shape[-1])
    c[:,:,ii,ii]+=sr[:,:,None]*e['red'][None,None,:]**2+sw[:,:,None]*e['sigma'][None,None,:]**2
    return c,weights


def moment_basis(gamma,e):
    k,p,_=gamma.shape
    components=np.stack((gamma,np.broadcast_to(np.diag(e['red']**2),(k,p,p)),np.broadcast_to(np.diag(e['sigma']**2),(k,p,p))),axis=1)
    hc=np.einsum('dab,ksbc->ksdac',e['H'],components,optimize=True)
    mu=np.einsum('ksdaa->ksd',hc).real
    sigma=np.einsum('ksiab,ktjba->kstij',hc,hc,optimize=True).real
    return mu,sigma


def cn_logpdf(c,q):
    """Batch C (N,K,P,P), data (R,K,P), one proper CN coefficient/channel."""
    chol=np.linalg.cholesky(c)
    rhs=np.broadcast_to(q.transpose(1,2,0),(len(c),*q.transpose(1,2,0).shape))
    solved=np.linalg.solve(chol,rhs)
    ld=2*np.log(np.diagonal(chol,axis1=-2,axis2=-1).real).sum(axis=(-2,-1))
    return -np.sum(abs(solved)**2,axis=(1,2))-ld[:,None]-q.shape[1]*q.shape[2]*np.log(np.pi)


def normal_logpdf(mu,cov,y):
    """Batch independent frequency blocks; y=(R,K,d)."""
    chol=np.linalg.cholesky(cov)
    residual=y.transpose(1,2,0)[None]-mu[:,:,:,None]
    solved=np.linalg.solve(chol,residual)
    ld=2*np.log(np.diagonal(chol,axis1=-2,axis2=-1)).sum(axis=(-2,-1))
    return -.5*(np.sum(solved*solved,axis=(1,2))+ld[:,None]+y.shape[1]*y.shape[2]*np.log(2*np.pi))


class Likelihood:
    def __init__(self,e,q,xphysical,xgaussian):
        self.e=e;self.q=q;self.n=len(q)
        self.x=np.concatenate((xphysical,xgaussian),axis=0)
        self.z=compress_frequencies(self.x,e['weights'])[:,None,:]
        self.names=['A0_CN','A_CN','B_CN','A_G','B_G']
    def prepare(self,gamma):
        return moment_basis(gamma,self.e)
    def __call__(self,eta,gamma,basis=None):
        c,w=covariance_batch(eta,gamma,self.e)
        a0=cn_logpdf(c,self.q)
        bm,bs=moment_basis(gamma,self.e) if basis is None else basis
        mu=np.einsum('nks,ksd->nkd',w,bm,optimize=True)
        cov=np.einsum('nks,nkt,kstij->nkij',w,w,bs,optimize=True)
        a=normal_logpdf(mu,cov,self.x)
        mb,cb=compress_independent_moments(mu,cov,self.e['weights'])
        b=normal_logpdf(mb[:,None,:],cb[:,None,:,:],self.z)
        # Result flattened as model-major R. This ordering is frozen in metadata.
        return np.concatenate((a0,a[:,:self.n],b[:,:self.n],a[:,self.n:],b[:,self.n:]),axis=-1)


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
