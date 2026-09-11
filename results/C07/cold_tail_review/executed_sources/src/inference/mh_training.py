"""Batched reversible logit MH; adaptation ends before retained draws."""
import numpy as np
from scipy.special import logit,expit,logsumexp
from .campaign_io import rng_for,positive_int
class TargetSeededMH:
    solve=staticmethod(np.linalg.solve)
    def __init__(self,target,targets,*,seed,chains=4,dimension=5,mass_probability=.15,independence_probability=.65,nuisance_probability=0.,student_df=5.,student_scales=(1.,),student_weights=(1.,),adaptation_window=1000):
        positive_int(seed,'seed',True);positive_int(chains,'chains');positive_int(dimension,'dimension');positive_int(adaptation_window,'adaptation_window')
        if not all(np.isfinite(v) for v in [mass_probability,nuisance_probability,independence_probability,student_df]):raise ValueError('Finite MH settings required.')
        if np.asarray(targets).dtype.kind not in 'iu':raise ValueError('Targets must be integer identities.')
        self.target=target;self.targets=np.asarray(targets,int);self.n=len(targets);self.chains=chains;self.d=dimension
        if mass_probability<0 or nuisance_probability<0 or independence_probability<0 or mass_probability+nuisance_probability+independence_probability>1 or student_df<=2 or (nuisance_probability>0 and dimension<2):raise ValueError('Invalid mixture.')
        self.mass_p=mass_probability;self.nuis_p=nuisance_probability;self.ind_p=independence_probability;self.df=student_df
        self.student_scales=np.asarray(student_scales,float);self.student_weights=np.asarray(student_weights,float);self.adaptation_window=int(adaptation_window)
        if not np.isfinite(self.student_scales).all() or not np.isfinite(self.student_weights).all():raise ValueError('Finite Student mixture required.')
        if self.student_scales.ndim!=1 or self.student_weights.shape!=self.student_scales.shape or np.any(self.student_scales<=0) or np.any(self.student_weights<=0) or not np.isclose(self.student_weights.sum(),1,rtol=0,atol=1e-14) or self.adaptation_window<1000:raise ValueError("Invalid defensive mixture.")
        if self.targets.ndim!=1 or len(self.targets)==0 or len(np.unique(self.targets))!=len(self.targets) or np.any(self.targets<0):raise ValueError('Unique nonnegative global targets required.')
        self.rng_grid=[[rng_for(seed,310,int(t),c) for c in range(chains)] for t in self.targets];self.seed=seed
        self.ids=np.repeat(self.targets,chains);self.z=logit(self.rand(dimension));self.lp,self.ll=target(self.z,self.ids)
        self.chol=np.broadcast_to(np.eye(dimension)*1.7,(self.n,dimension,dimension)).copy();self.mean=np.zeros((self.n,dimension));self.logscale=np.full(self.n,np.log(2.38/np.sqrt(dimension)))
        self.history=[];self.accwindow=np.zeros(self.n);self.trywindow=np.zeros(self.n);self.steps=0;self.frozen=False
        self.accept=np.zeros((4,self.n));self.attempt=np.zeros((4,self.n))
    def rand(self,size=None,normal=False):
        values=np.asarray([[(r.normal(size=size) if normal else r.random(size=size)) for r in row] for row in self.rng_grid])
        if not normal and np.any((values<=0)|(values>=1)):raise FloatingPointError('Uniform RNG reached a transform boundary; no clipping or replacement.')
        return values.reshape((-1,) if size is None else (-1,size))
    def chisquare(self):
        return np.asarray([[r.chisquare(self.df) for r in row] for row in self.rng_grid])
    def t_logq(self,z):
        center=z.reshape(self.n,self.chains,self.d)-self.mean[:,None,:]
        w=self.solve(self.chol,center.transpose(0,2,1)).transpose(0,2,1)/np.sqrt((self.df-2)/self.df)
        mahal=np.sum(w*w,axis=-1).ravel()/self.df
        components=np.log(self.student_weights)[None,:]-self.d*np.log(self.student_scales)[None,:]-.5*(self.df+self.d)*np.log1p(mahal[:,None]/self.student_scales[None,:]**2)
        return logsumexp(components,axis=-1)
    def step(self,*,adapt=False):
        if adapt and self.frozen:raise RuntimeError('Production proposal cannot adapt.')
        if not adapt and self.steps<1000:raise RuntimeError('Freeze only after the fixed Student enable point; no late production changes.')
        if not adapt:self.frozen=True
        choice=self.rand();mass=choice<self.mass_p;nuis=(choice>=self.mass_p)&(choice<self.mass_p+self.nuis_p);ind=(choice>=self.mass_p+self.nuis_p)&(choice<self.mass_p+self.nuis_p+self.ind_p)&(self.steps>=1000)
        refresh=mass|nuis
        kind=np.where(mass,0,np.where(nuis,1,np.where(ind,2,3)));noise=self.rand(self.d,normal=True).reshape(self.n,self.chains,self.d)
        jump=np.einsum('nij,ncj->nci',self.chol,noise)
        prop=self.z+(jump*np.exp(self.logscale[:,None,None])).reshape(-1,self.d)
        # Fixed RNG schedule per target/chain: batching/permutation never changes a stream.
        chi=self.chisquare()
        component=np.searchsorted(np.cumsum(self.student_weights),self.rand()).reshape(self.n,self.chains)
        prior_mass=self.rand();coordinate=1+np.floor(self.rand()*(self.d-1)).astype(int);prior_nuisance=self.rand()
        if np.any(ind):
            scale=self.student_scales[component]
            independent=self.mean[:,None,:]+jump*np.sqrt((self.df-2)/chi[:,:,None])*scale[:,:,None]
            prop[ind]=independent.reshape(-1,self.d)[ind]
        prop[refresh]=self.z[refresh];prop[mass,0]=logit(prior_mass[mass])
        if np.any(nuis):
            prop[np.where(nuis)[0],coordinate[nuis]]=logit(prior_nuisance[nuis])
        plp,pll=self.target(prop,self.ids);delta=plp-self.lp
        delta[refresh]=pll[refresh]-self.ll[refresh]
        if np.any(ind):delta[ind]+=(self.t_logq(self.z)-self.t_logq(prop))[ind]
        accepted=np.log(self.rand())<delta
        self.z[accepted]=prop[accepted];self.lp[accepted]=plp[accepted];self.ll[accepted]=pll[accepted]
        for k in range(4):
            proposed=(kind==k).reshape(self.n,self.chains);self.attempt[k]+=proposed.sum(axis=1);self.accept[k]+=(proposed&accepted.reshape(self.n,self.chains)).sum(axis=1)
        if adapt:
            self.history.append(self.z.reshape(self.n,self.chains,self.d).copy())
            if len(self.history)>self.adaptation_window:self.history.pop(0)
            rw=(kind==3).reshape(self.n,self.chains);self.accwindow+=(accepted.reshape(self.n,self.chains)&rw).sum(axis=1);self.trywindow+=rw.sum(axis=1)
            if (self.steps+1)%100==0:
                rate=self.accwindow/np.maximum(self.trywindow,1);self.logscale=np.clip(self.logscale+.25*(rate-.234),-3,1);self.accwindow[:]=0;self.trywindow[:]=0
            if self.steps>=999 and (self.steps+1)%250==0:
                h=np.array(self.history).transpose(1,0,2,3).reshape(self.n,-1,self.d);self.mean=h.mean(axis=1);center=h-self.mean[:,None,:]
                cov=np.einsum('nsi,nsj->nij',center,center)/(h.shape[1]-1)+np.eye(self.d)[None]*.02
                self.chol=np.linalg.cholesky(cov)
        self.steps+=1
        return expit(self.z).reshape(self.n,self.chains,self.d),self.ll.reshape(self.n,self.chains)
    def freeze(self):
        if self.steps<1000:raise RuntimeError('Cannot freeze before Student enable point.')
        self.frozen=True;self.history=[];self.accept[:]=0;self.attempt[:]=0
    def metadata(self):
        return dict(seed=self.seed,rng_recipe='SeedSequence([master_seed,310,global_target_id,chain]); fixed per-step draw schedule',chains=self.chains,targets=self.targets.tolist(),independence_probability=self.ind_p,mass_probability=self.mass_p,nuisance_probability=self.nuis_p,move_names=["mass_prior","nuisance_prior","student_independent","random_walk"],student_df=self.df,student_scales=self.student_scales.tolist(),student_weights=self.student_weights.tolist(),adaptation_window=self.adaptation_window,production_adaptation=False,mean=self.mean.tolist(),cholesky=self.chol.tolist(),logscale=self.logscale.tolist(),acceptance=np.divide(self.accept,self.attempt,out=np.zeros_like(self.accept),where=self.attempt>0).tolist())
