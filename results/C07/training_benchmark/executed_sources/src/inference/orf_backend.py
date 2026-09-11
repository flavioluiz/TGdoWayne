"""Common multipole cuts, explicit resource limits and independently checked ORF pairs."""
from pathlib import Path
from functools import lru_cache
from time import perf_counter
import hashlib
import json
import numpy as np
from scipy.special import roots_legendre
from pta import transfer
from pta.orf import raw_direct_orf
from pta.simulation import JULIAN_YEAR_SECONDS as YEAR

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
