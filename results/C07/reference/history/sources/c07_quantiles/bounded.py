"""Positive CDF cubature with a recorded analytic bound on omitted gamma calls.

The finite quadrature is enclosed by [computed, computed+omitted_upper_bound].
This enclosure controls ONLY skipped node evaluations, not quadrature error.
"""
from pathlib import Path
import hashlib,json,time
import numpy as np
from scipy.special import logsumexp
from cubature import (PILOT,LogAmplitudeBox,experiment,FrozenMassTable,
                      SpectralCN,b_nodes,a_nodes,slope_nodes,trapezoid_weights,mass_nodes)
from scale_marginalization import cn_log_scale_integral
from truncated_cdf import truncated_box

HERE=Path(__file__).resolve().parent

def bounded_mass_batch(Gamma,e,q,box,orders,*,log_point_cut):
    """The same spectral/gamma calculation, vectorized over a small mass batch."""
    from inference_pilot import YEAR
    Gamma=np.asarray(Gamma);J=len(Gamma);nb,na,ng=orders
    if J>16:raise ValueError('Mass batching is explicitly limited to16 matrices.')
    bs,bw=b_nodes(box,nb);slopes,gw=slope_nodes(box,ng)
    volume=np.prod([hi-lo for lo,hi in [box.gw,box.red,box.efac,box.slope]])
    M=q.size;logtotal=np.full(J,-np.inf);logupper=np.full(J,-np.inf);nall=0;nexact=np.zeros(J,dtype=np.int64)
    min_den=np.inf
    for b,wb in zip(bs,bw):
        aa,aw=a_nodes(box,float(b),na);a,slope=np.broadcast_arrays(aa[:,None],slopes[None,:]);a=a.ravel();slope=slope.ravel()
        lo,hi=box.conditional_bounds(a,b);logweight=np.log((wb*aw[:,None]*gw[None,:]/volume).ravel())
        red=10.**(2*b)*YEAR**3/(12*np.pi*np.pi)*(e['f']*YEAR)**-4/e['scale']
        white=2*e['dt']/e['scale'];noise=red[:,None]*e['red'][None,:]**2+white[:,None]*e['sigma'][None,:]**2
        inv=1/np.sqrt(noise)
        eig,U=np.linalg.eigh(Gamma*inv[None,:,:,None]*inv[None,:,None,:])
        power=abs(np.einsum('mkji,kj->mki',U.conj(),q*inv))**2
        sg=10.**(2*a[:,None])*YEAR**3/(12*np.pi*np.pi)*(e['f'][None,:]*YEAR)**(-slope[:,None])/e['scale']
        den=1+sg[None,:,:,None]*eig[:,None]
        min_den=min(min_den,float(den.min()))
        if not np.isfinite(den).all() or np.any(den<=0):raise ArithmeticError('Nonpositive spectral denominator; no eigenvalue clipping.')
        chi=np.sum(power[:,None]/den,axis=(2,3));ld=np.log(noise).sum()+np.log(den).sum(axis=(2,3))
        lower=np.broadcast_to(lo,chi.shape);higher=np.broadcast_to(hi,chi.shape)
        with np.errstate(divide='ignore'):tpeak=np.minimum(np.maximum(.5*np.log10(chi/M),lower),higher)
        logmax=-M*np.log(np.pi)-ld-2*M*np.log(10)*tpeak-chi*10.**(-2*tpeak)
        upper=np.log(higher-lower)+logmax+logweight[None]
        keep=upper>=np.asarray(log_point_cut)[:,None];nall+=len(a);nexact+=keep.sum(axis=1)
        values=np.full_like(chi,-np.inf)
        if np.any(keep):
            values[keep]=cn_log_scale_integral(chi[keep],ld[keep],M,lower[keep],higher[keep],conditional_average=False)+np.broadcast_to(logweight,chi.shape)[keep]
            if np.max(values[keep]-upper[keep])>1e-8:raise ArithmeticError('Gamma integral exceeded analytic upper bound.')
        logtotal=np.logaddexp(logtotal,logsumexp(values,axis=1))
        logupper=np.logaddexp(logupper,logsumexp(np.where(keep,-np.inf,upper),axis=1))
    return logtotal,logupper,dict(nodes_per_mass=nall,exact_gamma_nodes_per_mass=nexact.tolist(),minimum_denominator=min_den)

def bounded_mass_integral(Gamma,e,q,box,orders,*,log_point_cut=-np.inf):
    nb,na,ng=orders;bs,bw=b_nodes(box,nb);slopes,gw=slope_nodes(box,ng)
    volume=np.prod([hi-lo for lo,hi in [box.gw,box.red,box.efac,box.slope]])
    M=q.size;logtotal=-np.inf;logupper=-np.inf;nall=0;nexact=0;max_gamma_discrepancy=0.
    for b,wb in zip(bs,bw):
        aa,aw=a_nodes(box,float(b),na);a,slope=np.broadcast_arrays(aa[:,None],slopes[None,:]);a=a.ravel();slope=slope.ravel()
        lo,hi=box.conditional_bounds(a,b);logweight=np.log((wb*aw[:,None]*gw[None,:]/volume).ravel())
        chi,ld=SpectralCN(e,q,Gamma,float(b)).coefficients(a,slope)
        with np.errstate(divide='ignore'):tpeak=np.minimum(np.maximum(.5*np.log10(chi/M),lo),hi)
        logmax=-M*np.log(np.pi)-ld-2*M*np.log(10)*tpeak-chi*10.**(-2*tpeak)
        upper=np.log(hi-lo)+logmax+logweight
        keep=upper>=log_point_cut;nall+=len(a);nexact+=int(keep.sum())
        if np.any(keep):
            value=cn_log_scale_integral(chi[keep],ld[keep],M,lo[keep],hi[keep],conditional_average=False)+logweight[keep]
            # The mathematical upper bound can be exceeded by roundoff only;
            # a meaningful discrepancy indicates a broken derivation/kernel.
            discrepancy=np.max(value-upper[keep]);max_gamma_discrepancy=max(max_gamma_discrepancy,float(discrepancy))
            if discrepancy>1e-8:raise ArithmeticError('Computed integral exceeded its likelihood-maximum bound.')
            logtotal=np.logaddexp(logtotal,logsumexp(value))
        if np.any(~keep):logupper=np.logaddexp(logupper,logsumexp(upper[~keep]))
    return float(logtotal),float(logupper),dict(nodes=nall,exact_gamma_nodes=nexact,maximum_log_bound_excess=max_gamma_discrepancy)

class CDFEvaluator:
    def __init__(self,orders,*,mass_count=129,relative_omission_budget=1e-12,batch_size=8):
        self.orders=tuple(orders);self.box=LogAmplitudeBox();self.relative_budget=relative_omission_budget
        if self.orders not in [(20,20,20),(32,20,12)]:raise ValueError('Reference denominators exist only for the two specified rules.')
        self.cfg=json.loads((PILOT/'config.json').read_text());self.e=experiment(self.cfg)
        self.data=np.load(PILOT/'results/data.npz',allow_pickle=False);self.q=self.data['q'][14]
        self.table=FrozenMassTable(self.e,self.cfg['orf'])
        beta=np.array([0,.0002,.0005,.001,.002,.005,.01,.02,.05,.1,.15])
        self.masses=np.unique(np.r_[np.linspace(0,1,mass_count),np.sqrt(1-beta**2)])
        name='A0_d14_GL20_full_truncated_cdf.json' if self.orders==(20,20,20) else 'A0_d14_GL32_20_12_full_truncated_cdf.json'
        self.reference_path=HERE.parent/'c07_cubature/results'/name
        self.reference=json.loads(self.reference_path.read_text());oldmass=np.array(self.reference['masses'])
        indices=np.array([int(np.where(oldmass==u)[0][0]) for u in self.masses])
        self.mw=trapezoid_weights(self.masses)
        self.logZ=float(logsumexp(np.array(self.reference['log_mass_marginal'])[indices]+np.log(self.mw)))
        self.maximum_nodes=int(len(self.masses)*9*np.prod(orders))
        if self.maximum_nodes>12_000_000:raise RuntimeError('CDF point budget exceeds12M before execution.')
        self.cache={};self.records=[];self.batch_size=batch_size
        if batch_size not in [1,2,4,8,16]:raise ValueError('Declared mass batch must be1,2,4,8 or16.')
        self.cache_dir=HERE/'results/cdf_cache';self.cache_dir.mkdir(parents=True,exist_ok=True)
        self.signature=hashlib.sha256(Path(__file__).read_bytes()+self.reference_path.read_bytes()+np.asarray(self.orders).tobytes()+self.masses.tobytes()).hexdigest()
    def evaluate(self,parameter,cut):
        key=(int(parameter),float(cut))
        if key in self.cache:return self.cache[key]
        path=self.cache_dir/(hashlib.sha256((self.signature+repr(key)).encode()).hexdigest()+'.json')
        if path.exists():
            out=json.loads(path.read_text());self.cache[key]=out;return out
        start=time.perf_counter();box,lf=truncated_box(self.box,parameter,cut)
        # Each discarded weighted node is below Z*epsilon/Nmax after inclusion
        # of its mass and full-prior volume weights. Hence their total is bounded.
        target=self.logZ+np.log(self.relative_budget)-np.log(self.maximum_nodes)
        values=[];uppers=[];counts=[]
        for first in range(0,len(self.masses),self.batch_size):
            masses=self.masses[first:first+self.batch_size];mw=self.mw[first:first+self.batch_size]
            val,upper,count=bounded_mass_batch(np.stack([self.table.get(float(u)) for u in masses]),self.e,self.q,box,self.orders,
                                              log_point_cut=target-np.log(mw)-lf)
            values.extend(val+lf+np.log(mw));uppers.extend(upper+lf+np.log(mw));counts.append(count)
        cdf=float(np.exp(logsumexp(values)-self.logZ));error=float(np.exp(logsumexp(uppers)-self.logZ))
        if error>self.relative_budget*(1+1e-8):raise ArithmeticError('The explicitly allocated omission error budget was exceeded.')
        out=dict(parameter=int(parameter),cut=float(cut),cdf_lower=cdf,cdf_upper=cdf+error,omission_error_bound=error,
                 orders=self.orders,mass_nodes=len(self.masses),maximum_nodes=self.maximum_nodes,
                 exact_gamma_nodes=sum(sum(c['exact_gamma_nodes_per_mass']) for c in counts),seconds=time.perf_counter()-start,
                 denominator_logZ=self.logZ,reference_denominator_sha256=hashlib.sha256(self.reference_path.read_bytes()).hexdigest(),
                 masses=self.masses.tolist(),log_numerator_mass_marginal=(np.asarray(values)-np.log(self.mw)).tolist(),
                 log_omitted_mass_upper=(np.asarray(uppers)-np.log(self.mw)).tolist(),mass_batch_size=self.batch_size,
                 source_signature=self.signature)
        path.write_text(json.dumps(out,indent=2)+'\n')
        self.cache[key]=out;self.records.append(out);return out
