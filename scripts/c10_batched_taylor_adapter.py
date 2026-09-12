"""Batched Taylor bounds intersected with the unchanged perturbation bounds."""
from epsilon_event import PolynomialEvent
from vendor_d1.envelope import LogRange
from pta.epsilon_taylor_batched import cn_taylor,normal_taylor


class BatchedTaylorEvent(PolynomialEvent):
    def envelope(self,left,right,center_logl):
        original=super().envelope(left,right,center_logl)
        if self.model=='A0_CN':
            result=cn_taylor(self.c,self.q,left,right,center_logl,roundoff_allowance=self.roundoff)
        else:
            result=normal_taylor(self.mu,self.sigma,self.y,left,right,center_logl,roundoff_allowance=self.roundoff)
        if not result['available']:return original
        lo=max(original.lower,result['lower']);hi=min(original.upper,result['upper'])
        if lo>hi:raise ArithmeticError('Taylor/perturbation enclosures incompatible')
        return LogRange(lo,hi,'intersection_with_local_Taylor_not_directed_rounding')
