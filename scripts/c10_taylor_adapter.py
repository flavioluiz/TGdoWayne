"""Intersect the frozen perturbation envelope with a local Taylor enclosure."""
import numpy as np
from epsilon_event import PolynomialEvent
from vendor_d1.envelope import LogRange
from pta.epsilon_taylor import cn_taylor,normal_taylor


class TaylorEvent(PolynomialEvent):
    def __init__(self,*args,validation_cache=None,**kwargs):
        super().__init__(*args,**kwargs)
        self.validation_cache=validation_cache
        self.checked_cached_points=0;self.taylor_available_cells=0;self.total_cells=0

    def envelope(self,left,right,center_logl):
        original=super().envelope(left,right,center_logl)
        if self.model=='A0_CN':
            result=cn_taylor(self.c,self.q,left,right,center_logl,roundoff_allowance=self.roundoff)
        else:
            result=normal_taylor(self.mu,self.sigma,self.y,left,right,center_logl,roundoff_allowance=self.roundoff)
        self.total_cells+=1
        if not result['available']:return original
        self.taylor_available_cells+=1
        lo=max(original.lower,result['lower']);hi=min(original.upper,result['upper'])
        if lo>hi:raise ArithmeticError('Taylor/perturbation enclosures incompatible')
        if self.validation_cache is not None:
            for key,value in self.validation_cache.cache.items():
                if left<=float.fromhex(key)<=right:
                    self.checked_cached_points+=1
                    if not lo<=value<=hi:raise ArithmeticError('Taylor enclosure excludes a cached likelihood')
        return LogRange(lo,hi,'intersection_with_local_Taylor_not_directed_rounding')
