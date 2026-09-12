"""C11 basis with the exact unit-vector self-angle identity.

The inherited input validation remains in force. For i=j, P_l(1)=1
analytically; carrying dot-product roundoff through high-order recurrence
would introduce orientation-dependent diagonal errors. No eigenvalue or
covariance repair is performed. Off-diagonal geometry is unchanged.
"""
import numpy as np
from inference.orf_blas import RealHarmonicBasis as OriginalBasis, TableBudget

class RealHarmonicBasis(OriginalBasis):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        ell=np.arange(2,self.lmax+1,dtype=float)
        norm=3/32*(2*ell+1)/((ell-1)*ell*(ell+1)*(ell+2))
        geometry=self.geometry.copy()
        for i in range(len(self.points)):
            geometry[i,i,:]=norm
        geometry.flags.writeable=False
        self.geometry=geometry
