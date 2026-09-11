"""Axis adapter only: retain the frozen mixture sampler and normalized density."""
import numpy as np
from mixture_proposal_v2 import GaussianDefensiveProposal

class GaussianIIDAdapter:
    def __init__(self,training):
        rows=training['records']
        self.q=GaussianDefensiveProposal(*[np.array([r[key] for r in rows]) for key in ['weights','means','covariances','global_mean','global_cholesky']],defensive_fraction=training['defensive_student_fraction'],student_df=training['student_df'],student_scale=training['student_scale'])
        self.targets,self.d=self.q.n,self.q.d
    def sample(self,rng,count):
        # Each returned column is one IID draw for every target, not a MH chain.
        entropy=rng.integers(0,2**32,size=4,dtype=np.uint32)
        rngs=[np.random.default_rng(child) for child in np.random.SeedSequence(entropy).spawn(count)]
        z=self.q.sample(rngs).reshape(self.targets,count,self.d).transpose(1,0,2)
        # Frozen sampler does not expose selected components. 255 explicitly means unknown.
        return z,np.full((count,self.targets),255,dtype=np.uint8)
    def logpdf(self,z):
        z=np.asarray(z,float)
        if z.ndim!=3 or z.shape[1:]!=(self.targets,self.d):raise ValueError('Expected sample,target,coordinate axes.')
        return self.q.logpdf(z.transpose(1,0,2).reshape(-1,self.d)).reshape(self.targets,len(z)).T
