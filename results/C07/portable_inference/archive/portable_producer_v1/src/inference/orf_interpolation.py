"""Threshold derivative fixed by the exact evenness of isotropic TT ORFs."""
import numpy as np
from scipy.interpolate import CubicSpline
from .pointwise import ConvexORF
from .orf_cubic_reference import CertifiedCubicORF,CubicPointLikelihood
class EvenThresholdCubicORF(CertifiedCubicORF):
    def __init__(self,nodes,matrices,*,coordinate='beta'):
        ConvexORF.__init__(self,nodes,matrices)
        if coordinate not in ('alpha','beta'):raise ValueError('Unsupported interpolation coordinate.')
        self.coordinate_name=coordinate
        self.coordinate=np.arcsin if coordinate=='alpha' else lambda u:-np.sqrt((1-u)*(1+u))
        self.alpha=self.coordinate(self.nodes);width=np.diff(self.alpha)
        c=CubicSpline(self.alpha,self.matrices,bc_type=('not-a-knot',(1,np.zeros(self.matrices.shape[1:])))).c
        self.coeff=np.stack([c[3-j]*width[:,None,None,None]**j for j in range(4)],axis=1)
        a0,a1,a2,a3=np.moveaxis(self.coeff,1,0)
        bernstein=np.stack([a0,a0+a1/3,a0+2*a1/3+a2/3,a0+a1+a2+a3],axis=1)
        mineig=np.linalg.eigvalsh(bernstein).min(axis=(1,2,3));self.fallback=np.where(mineig< -1e-12)[0]
        for j in self.fallback:
            self.coeff[j,0]=self.matrices[j];self.coeff[j,1]=self.matrices[j+1]-self.matrices[j];self.coeff[j,2:]=0
        self.bernstein_minimum_eigenvalue=mineig
        self.threshold_derivative_condition='zero from exact beta parity of isotropic unpolarized TT integral'
