"""Batched reversible logit MH; adaptation ends before retained draws."""
import numpy as np
from scipy.special import logit,expit,logsumexp
class BatchedMH:
    solve=staticmethod(np.linalg.solve)
    def __init__(self,target,targets,*,seed,chains=4,dimension=5,mass_probability=.15,independence_probability=.65,nuisance_probability=0.,student_df=5.,student_scales=(1.,),student_weights=(1.,),adaptation_window=1000):
        self.target=target;self.targets=np.asarray(targets,int);self.n=len(targets);self.chains=chains;self.d=dimension
        if mass_probability<0 or nuisance_probability<0 or independence_probability<0 or mass_probability+nuisance_probability+independence_probability>1 or student_df<=2 or (nuisance_probability>0 and dimension<2):raise ValueError('Invalid mixture.')
        self.mass_p=mass_probability;self.nuis_p=nuisance_probability;self.ind_p=independence_probability;self.df=student_df
        self.student_scales=np.asarray(student_scales,float);self.student_weights=np.asarray(student_weights,float);self.adaptation_window=int(adaptation_window)
        if self.student_scales.ndim!=1 or self.student_weights.shape!=self.student_scales.shape or np.any(self.student_scales<=0) or np.any(self.student_weights<=0) or not np.isclose(self.student_weights.sum(),1) or self.adaptation_window<1000:raise ValueError("Invalid defensive mixture.")
        ss=np.random.SeedSequence(seed);self.rngs=[np.random.default_rng(s) for s in ss.spawn(chains)];self.seed=seed
        self.ids=np.repeat(self.targets,chains);self.z=logit(self.rand(dimension));self.lp,self.ll=target(self.z,self.ids)
        self.chol=np.broadcast_to(np.eye(dimension)*1.7,(self.n,dimension,dimension)).copy();self.mean=np.zeros((self.n,dimension));self.logscale=np.full(self.n,np.log(2.38/np.sqrt(dimension)))
        self.history=[];self.accwindow=np.zeros(self.n);self.trywindow=np.zeros(self.n);self.steps=0;self.frozen=False
        self.accept=np.zeros((4,self.n));self.attempt=np.zeros((4,self.n))
    def rand(self,size=None,normal=False):
        shape=(self.n,) if size is None else (self.n,size)
        values=[(r.normal(size=shape) if normal else r.random(shape)) for r in self.rngs]
        return np.stack(values,axis=1).reshape((-1,) if size is None else (-1,size))
    def t_logq(self,z):
        center=z.reshape(self.n,self.chains,self.d)-self.mean[:,None,:]
        w=self.solve(self.chol,center.transpose(0,2,1)).transpose(0,2,1)/np.sqrt((self.df-2)/self.df)
        mahal=np.sum(w*w,axis=-1).ravel()/self.df
        components=np.log(self.student_weights)[None,:]-self.d*np.log(self.student_scales)[None,:]-.5*(self.df+self.d)*np.log1p(mahal[:,None]/self.student_scales[None,:]**2)
        return logsumexp(components,axis=-1)
    def step(self,*,adapt=False):
        if adapt and self.frozen:raise RuntimeError('Production proposal cannot adapt.')
        if not adapt:self.frozen=True
        choice=self.rand();mass=choice<self.mass_p;nuis=(choice>=self.mass_p)&(choice<self.mass_p+self.nuis_p);ind=(choice>=self.mass_p+self.nuis_p)&(choice<self.mass_p+self.nuis_p+self.ind_p)&(self.steps>=1000)
        refresh=mass|nuis
        kind=np.where(mass,0,np.where(nuis,1,np.where(ind,2,3)));noise=self.rand(self.d,normal=True).reshape(self.n,self.chains,self.d)
        jump=np.einsum('nij,ncj->nci',self.chol,noise)
        prop=self.z+(jump*np.exp(self.logscale[:,None,None])).reshape(-1,self.d)
        if np.any(ind):
            chi=np.stack([r.chisquare(self.df,size=self.n) for r in self.rngs],axis=1)
            component=np.searchsorted(np.cumsum(self.student_weights),self.rand()).reshape(self.n,self.chains)
            scale=self.student_scales[component]
            independent=self.mean[:,None,:]+jump*np.sqrt((self.df-2)/chi[:,:,None])*scale[:,:,None]
            prop[ind]=independent.reshape(-1,self.d)[ind]
        prop[refresh]=self.z[refresh];prop[mass,0]=logit(self.rand()[mass])
        if np.any(nuis):
            coordinate=1+np.floor(self.rand()*(self.d-1)).astype(int)
            prop[np.where(nuis)[0],coordinate[nuis]]=logit(self.rand()[nuis])
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
        self.frozen=True;self.history=[];self.accept[:]=0;self.attempt[:]=0
    def metadata(self):
        return dict(seed=self.seed,chains=self.chains,targets=self.targets.tolist(),independence_probability=self.ind_p,mass_probability=self.mass_p,nuisance_probability=self.nuis_p,move_names=["mass_prior","nuisance_prior","student_independent","random_walk"],student_df=self.df,student_scales=self.student_scales.tolist(),student_weights=self.student_weights.tolist(),adaptation_window=self.adaptation_window,production_adaptation=False,mean=self.mean.tolist(),cholesky=self.chol.tolist(),logscale=self.logscale.tolist(),acceptance=np.divide(self.accept,self.attempt,out=np.zeros_like(self.accept),where=self.attempt>0).tolist())
