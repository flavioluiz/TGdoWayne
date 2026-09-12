"""Frozen selected likelihood with memoization of observation-independent moments."""
import hashlib
from selected_kernel import ConditionalLikelihood
from pta.moment_cache import array_digest


class MemoizedLikelihood(ConditionalLikelihood):
    def __init__(self,*args,moment_cache,**kwargs):
        super().__init__(*args,**kwargs);self.moment_cache=moment_cache
        self.H.setflags(write=False);self.w.setflags(write=False)
        self.geometry_key=self.geometry_signature()

    def geometry_signature(self):
        h=hashlib.sha256();h.update(str((self.K,self.P,self.D)).encode());h.update(array_digest(self.H));h.update(array_digest(self.w));return h.digest()

    def moments(self,C0,C1):
        if self.geometry_signature()!=self.geometry_key:raise RuntimeError('Moment-cache estimator geometry changed')
        compute=super().moments
        return self.moment_cache.get(self.geometry_key,C0,C1,lambda:compute(C0,C1))
