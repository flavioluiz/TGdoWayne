"""Fixed-proposal MH for independent validation of a learned joint mixture."""
import numpy as np
from scipy.special import logit,expit
class FrozenMixtureMH:
    def __init__(self,target,targets,proposal,rw_cholesky,rw_logscale,*,seed,chains=4):
        self.target=target;self.targets=np.asarray(targets,int);self.n=len(targets);self.c=chains;self.d=5;self.proposal=proposal
        if proposal.n!=self.n or proposal.d!=self.d:raise ValueError('Proposal and target dimensions disagree.')
        self.rw_chol=np.asarray(rw_cholesky);self.rw_scale=np.exp(rw_logscale);self.ids=np.repeat(self.targets,chains);self.seed=seed
        self.rngs=[np.random.default_rng(x) for x in np.random.SeedSequence(seed).spawn(chains)];self.z=logit(self.rand(self.d));self.lp,self.ll=target(self.z,self.ids)
        self.accept=np.zeros((4,self.n));self.attempt=np.zeros((4,self.n))
    def rand(self,d=None,normal=False):
        shape=(self.n,) if d is None else (self.n,d);v=[r.normal(size=shape) if normal else r.random(shape) for r in self.rngs]
        return np.stack(v,axis=1).reshape((-1,) if d is None else (-1,d))
    def step(self):
        move=self.rand();mass=move<.15;nuis=(move>=.15)&(move<.35);ind=(move>=.35)&(move<.80);refresh=mass|nuis
        kind=np.where(mass,0,np.where(nuis,1,np.where(ind,2,3)))
        noise=self.rand(self.d,normal=True).reshape(self.n,self.c,self.d);jump=np.einsum('nij,ncj->nci',self.rw_chol,noise)*self.rw_scale[:,None,None];znew=self.z+jump.reshape(-1,self.d)
        if np.any(ind):znew[ind]=self.proposal.sample(self.rngs)[ind]
        znew[refresh]=self.z[refresh];znew[mass,0]=logit(self.rand()[mass])
        if np.any(nuis):
            coordinate=1+np.floor(4*self.rand()).astype(int);znew[np.where(nuis)[0],coordinate[nuis]]=logit(self.rand()[nuis])
        lpnew,llnew=self.target(znew,self.ids);delta=lpnew-self.lp;delta[refresh]=llnew[refresh]-self.ll[refresh]
        if np.any(ind):delta[ind]+=(self.proposal.logpdf(self.z)-self.proposal.logpdf(znew))[ind]
        accepted=np.log(self.rand())<delta;self.z[accepted]=znew[accepted];self.lp[accepted]=lpnew[accepted];self.ll[accepted]=llnew[accepted]
        for k in range(4):
            mask=(kind==k).reshape(self.n,self.c);self.attempt[k]+=mask.sum(axis=1);self.accept[k]+=(mask&accepted.reshape(self.n,self.c)).sum(axis=1)
        return expit(self.z).reshape(self.n,self.c,self.d),self.ll.reshape(self.n,self.c)
