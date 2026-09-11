"""Deterministic panel cubature for one frozen proper-CN target.

No prior replacement, ORF interpolation, eigenvalue clipping or noisy integrand.
The integration order b -> a is a Fubini rearrangement of the same ratio region.
"""
from pathlib import Path
from functools import lru_cache
import hashlib,json,time,argparse
import numpy as np
from scipy.special import roots_legendre,logsumexp
from scale_marginalization import LogAmplitudeBox,cn_log_scale_integral
from inference_pilot import experiment,ExactNodeORF,YEAR,trapezoid_weights,continuous_cdf,continuous_ppf

HERE=Path(__file__).resolve().parent
PILOT=HERE.parent/'c07_integration'

def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()

class FrozenMassTable:
    def __init__(self,e,cfg):
        self.meta=ExactNodeORF(e,cfg,HERE/'empty_metadata_cache')
        self.source=PILOT/'results/orf_cache';self.values={};self.paths={}
    def get(self,u):
        token=hashlib.sha256(self.meta.signature.encode()+float(u).hex().encode()).hexdigest()
        path=self.source/(token+'.npz')
        if not path.exists():raise RuntimeError(f'Mass {u} absent from cache; no new ORF computation authorized here.')
        if u not in self.values:
            with np.load(path,allow_pickle=False) as p:self.values[u]=p['Gamma'].copy()
            self.paths[u]=str(path)
        return self.values[u]

@lru_cache(maxsize=128)
def legendre(n):
    x,w=roots_legendre(n);return x,w

def panel_nodes(edges,n):
    x,w=legendre(n);edges=np.unique(np.asarray(edges,float))
    return (np.concatenate([.5*(hi+lo)+.5*(hi-lo)*x for lo,hi in zip(edges[:-1],edges[1:])]),
            np.concatenate([.5*(hi-lo)*w for lo,hi in zip(edges[:-1],edges[1:])]))

def b_nodes(box,n):
    R0,R1=box.red;E0,E1=box.efac
    return panel_nodes([R0-E1,R0-E0,R1-E1,R1-E0],n)

def a_nodes(box,b,n):
    G0,G1=box.gw;E0,E1=box.efac;R0,R1=box.red
    tlo=max(E0,R0-b);thi=min(E1,R1-b)
    return panel_nodes([G0-thi,G0-tlo,G1-thi,G1-tlo],n)

def slope_nodes(box,n,cuts=()):
    """Allocate n GL nodes per full-width equivalent plus two nodes per panel.

    With no diagnostic cuts this is exactly n nodes. Diagnostic CDF cuts make
    gamma indicators constant on each open panel, avoiding step quadrature.
    Every order and actual node count is reported.
    """
    lo,hi=box.slope
    edges=np.unique(np.r_[lo,[v for v in cuts if lo<v<hi],hi])
    if len(edges)==2:return panel_nodes(edges,n)
    xs=[];ws=[]
    for lower,upper in zip(edges[:-1],edges[1:]):
        count=max(2,int(np.ceil(n*(upper-lower)/(hi-lo)))+2)
        x,w=panel_nodes([lower,upper],count);xs.append(x);ws.append(w)
    return np.concatenate(xs),np.concatenate(ws)

class SpectralCN:
    """At fixed b, diagonalize whitened ORF once; reuse all a/gamma evaluations."""
    def __init__(self,e,q,gamma,b):
        self.e=e
        red=10.**(2*b)*YEAR**3/(12*np.pi*np.pi)*(e['f']*YEAR)**-4/e['scale']
        white=2*e['dt']/e['scale']
        noise=red[:,None]*e['red'][None,:]**2+white[:,None]*e['sigma'][None,:]**2
        if np.any(noise<=0):raise ArithmeticError('Positive diagonal noise required.')
        inv=1/np.sqrt(noise)
        whitened=gamma*inv[:,:,None]*inv[:,None,:]
        self.values,vectors=np.linalg.eigh(whitened)
        z=np.einsum('kji,kj->ki',vectors.conj(),q*inv)
        self.power=abs(z)**2;self.logdet_noise=np.log(noise).sum()
        self.minimum_eigenvalue=float(self.values.min());self.minimum_denominator=np.inf
    def coefficients(self,a,slope):
        a,slope=np.broadcast_arrays(a,slope)
        shape=a.shape
        sg=10.**(2*a.ravel()[:,None])*YEAR**3/(12*np.pi*np.pi)*(self.e['f'][None,:]*YEAR)**(-slope.ravel()[:,None])/self.e['scale']
        den=1+sg[:,:,None]*self.values[None]
        self.minimum_denominator=min(self.minimum_denominator,float(den.min()))
        if not np.isfinite(den).all() or np.any(den<=0):raise ArithmeticError('Nonpositive spectral denominator; no clipping.')
        chi=np.sum(self.power[None]/den,axis=(1,2))
        ld=self.logdet_noise+np.log(den).sum(axis=(1,2))
        return chi.reshape(shape),ld.reshape(shape)

def mass_nodes():
    beta=np.array([0,.0002,.0005,.001,.002,.005,.01,.02,.05,.1,.15])
    return np.unique(np.r_[np.linspace(0,1,129),np.sqrt(1-beta**2)])

def diagnostic_cuts(cfg,data,index):
    source=PILOT/'results/endpoint_129_13_independent.json'
    ref=json.loads(source.read_text());q=np.array(ref['quantiles'])[0,index]
    cuts=[]
    for param in [1,2,3,4]:
        for p,v in zip(cfg['quantiles'],q[param]):
            cuts.append(dict(parameter=param,kind=f'frozen_prior_RQMC_quantile_{p}',value=float(v)))
        cuts.append(dict(parameter=param,kind='truth_PIT_diagnostic_only',value=float(data['truth'][index,param])))
    return cuts,digest(source)

def mass_integral(gamma,e,q,box,order,cuts=(),*,cdf_logdrop=40.):
    """Return log evidence conditional on mass and CDF numerator log integrals.

    All positive cubature contributions enter evidence. Tiny CDF contributions
    may be omitted; their sum bounds absolute normalized CDF error a posteriori.
    """
    nb,na,ng=order
    bs,bw=b_nodes(box,nb)
    slopes,gw=slope_nodes(box,ng,[v['value'] for v in cuts if v['parameter']==2])
    volume=np.prod([hi-lo for lo,hi in [box.gw,box.red,box.efac,box.slope]])
    M=q.size;logtotal=-np.inf;lognum=np.full(len(cuts),-np.inf)
    logomitted=-np.inf;peak=-np.inf;points=0;cdf_points=0;minimum_denominator=np.inf;minimum_eigenvalue=np.inf
    for b,wb in zip(bs,bw):
        aa,aw=a_nodes(box,float(b),na)
        a,slope=np.broadcast_arrays(aa[:,None],slopes[None,:]);shape=a.shape
        a=a.ravel();slope=slope.ravel()
        lo,hi=box.conditional_bounds(a,b)
        weight=(wb*aw[:,None]*gw[None,:]/volume).ravel()
        engine=SpectralCN(e,q,gamma,float(b));chi,ld=engine.coefficients(a,slope)
        full=cn_log_scale_integral(chi,ld,M,lo,hi,conditional_average=False)
        lw=full+np.log(weight);logtotal=np.logaddexp(logtotal,logsumexp(lw))
        points+=len(a);minimum_denominator=min(minimum_denominator,engine.minimum_denominator)
        minimum_eigenvalue=min(minimum_eigenvalue,engine.minimum_eigenvalue)
        if not len(cuts):continue
        peak=max(peak,float(lw.max()))
        retain=lw>=peak-cdf_logdrop
        if np.any(~retain):logomitted=np.logaddexp(logomitted,logsumexp(lw[~retain]))
        for j,cut in enumerate(cuts):
            param=cut['parameter'];threshold=cut['value']
            if param==2:
                selected=retain&(slope<=threshold)
                if np.any(selected):lognum[j]=np.logaddexp(lognum[j],logsumexp(lw[selected]))
                continue
            upper=np.full_like(a,threshold)
            if param==1:upper-=a
            elif param==3:upper-=b
            elif param!=4:raise ValueError('Unexpected CDF parameter.')
            allincluded=retain&(upper>=hi)
            if np.any(allincluded):lognum[j]=np.logaddexp(lognum[j],logsumexp(lw[allincluded]))
            inside=retain&(upper>lo)&(upper<hi)
            cdf_points+=int(inside.sum())
            if np.any(inside):
                partial=cn_log_scale_integral(chi[inside],ld[inside],M,lo[inside],upper[inside],conditional_average=False)
                lognum[j]=np.logaddexp(lognum[j],logsumexp(partial+np.log(weight[inside])))
    return logtotal,lognum,dict(points=points,cdf_partial_integrals=cdf_points,log_omitted_cdf_bound=float(logomitted),minimum_denominator=minimum_denominator,minimum_whitened_orf_eigenvalue=minimum_eigenvalue,slope_nodes=len(slopes),b_nodes=len(bs))

def run(order,index=14,*,only_mass=None,with_cdf=True,max_points=150_000_000):
    cfg=json.loads((PILOT/'config.json').read_text());e=experiment(cfg)
    with np.load(PILOT/'results/data.npz',allow_pickle=False) as p:data={k:p[k] for k in p.files}
    q=data['q'][index];box=LogAmplitudeBox();table=FrozenMassTable(e,cfg['orf'])
    cuts,cut_hash=diagnostic_cuts(cfg,data,index) if with_cdf else ([],None)
    masses=mass_nodes() if only_mass is None else np.asarray(only_mass,float)
    actual_ng=len(slope_nodes(box,order[2],[c['value'] for c in cuts if c['parameter']==2])[0])
    expected=len(masses)*9*order[0]*order[1]*actual_ng
    if expected>max_points:raise RuntimeError(f'Preflight {expected} points exceeds explicit {max_points} budget.')
    start=time.perf_counter();lm=[];ln=[];records=[]
    for j,u in enumerate(masses):
        a,b,r=mass_integral(table.get(float(u)),e,q,box,order,cuts)
        lm.append(a);ln.append(b);records.append(r)
        if j%20==0:print(json.dumps(dict(progress_mass=j+1,total=len(masses),order=order,elapsed=time.perf_counter()-start)),flush=True)
    lm=np.array(lm);ln=np.array(ln);duration=time.perf_counter()-start
    out=dict(scope='A0_CN frozen datum14 only; deterministic nuisance cubature, no SBC or approval of all targets',data_index_zero_based=index,
             order_b_a_gamma=order,actual_slope_nodes=actual_ng,mass_nodes=len(masses),parameter_points=expected,seconds=duration,
             maximum_points_budget=max_points,log_mass_marginal=lm.tolist(),masses=masses.tolist(),cdf_cuts=cuts,cdf_logdrop=40.,
             cdf_partial_integrals=sum(r['cdf_partial_integrals'] for r in records),
             minimum_spectral_denominator=min(r['minimum_denominator'] for r in records),
             minimum_whitened_orf_eigenvalue=min(r['minimum_whitened_orf_eigenvalue'] for r in records),
             no_eigenvalue_clipping=True,prior_preserved=True,source_hashes={str(p):digest(p) for p in [Path(__file__),HERE.parent/'c07_scale/scale_marginalization.py',PILOT/'config.json',PILOT/'results/data.npz',PILOT/'src/inference_pilot.py']},
             cut_source_hash=cut_hash,orf_signature=table.meta.signature,
             cache_hashes={str(u):digest(path) for u,path in table.paths.items()},
             thresholds=cfg['diagnostic_thresholds'],nuisance_quantile_acceptance_assessed=False)
    if len(masses)>1:
        mw=trapezoid_weights(masses);lweights=np.log(mw)
        logZ=float(logsumexp(lm+lweights));logZ0=float(lm[0])
        density=np.exp(lm-lm.max())
        cdf=np.exp(logsumexp(ln+lweights[:,None],axis=0)-logZ)
        omitted=np.exp(logsumexp(np.array([r['log_omitted_cdf_bound'] for r in records])+lweights)-logZ)
        out.update(log_evidence=logZ,log_evidence_fixed_u0=logZ0,log_bayes_factor_free_vs_fixed_u0=logZ-logZ0,
                   original_nuisance_CDF_at_frozen_cuts=cdf.tolist(),absolute_cdf_omission_bound=float(omitted),
                   mass_quantiles=[continuous_ppf(masses,density,p) for p in cfg['quantiles']],
                   mass_PIT=continuous_cdf(masses,density,data['truth'][index,0]),
                   mass_CDF_grid=np.linspace(0,1,201).tolist(),mass_CDF=[continuous_cdf(masses,density,x) for x in np.linspace(0,1,201)])
    else:
        out.update(log_evidence_conditional_mass=float(lm[0]),original_nuisance_CDF_at_frozen_cuts=np.exp(ln[0]-lm[0]).tolist(),absolute_cdf_omission_bound=float(np.exp(records[0]['log_omitted_cdf_bound']-lm[0])))
    return out

def main():
    p=argparse.ArgumentParser();p.add_argument('--orders',type=int,nargs='+',default=[12,20,32]);p.add_argument('--mass',type=float,nargs='+');p.add_argument('--no-cdf',action='store_true');p.add_argument('--maximum-points',type=int,default=150_000_000);a=p.parse_args()
    dest=HERE/'results';dest.mkdir(exist_ok=True)
    for n in a.orders:
        filename=dest/f'A0_d14_GL{n}_{"mass" if a.mass else "full"}_{"evidence" if a.no_cdf else "cdf"}.json'
        if filename.exists():print('Preserving',filename.name,flush=True);continue
        result=run([n,n,n],only_mass=a.mass,with_cdf=not a.no_cdf,max_points=a.maximum_points)
        filename.write_text(json.dumps(result,indent=2)+'\n')
        print(json.dumps({k:v for k,v in result.items() if k in ['order_b_a_gamma','mass_nodes','parameter_points','seconds','log_evidence','log_evidence_conditional_mass','absolute_cdf_omission_bound','original_nuisance_CDF_at_frozen_cuts','mass_quantiles']}),flush=True)

if __name__=='__main__':main()
