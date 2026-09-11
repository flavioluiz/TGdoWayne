"""PSD-certified cubic in alpha, with explicitly marked convex-linear fallbacks."""
import numpy as np
from scipy.interpolate import CubicSpline
from .pointwise import ConvexORF,PointLikelihood
class CertifiedCubicORF(ConvexORF):
    def __init__(self,nodes,matrices,*,coordinate="alpha"):
        super().__init__(nodes,matrices)
        self.coordinate_name=coordinate
        if coordinate not in ("alpha","beta"):raise ValueError("Unsupported interpolation coordinate.")
        self.coordinate=(np.arcsin if coordinate=="alpha" else lambda u:-np.sqrt((1-u)*(1+u)))
        self.alpha=self.coordinate(self.nodes);width=np.diff(self.alpha)
        c=CubicSpline(self.alpha,self.matrices).c
        self.coeff=np.stack([c[3-j]*width[:,None,None,None]**j for j in range(4)],axis=1)
        a0,a1,a2,a3=np.moveaxis(self.coeff,1,0)
        bernstein=np.stack([a0,a0+a1/3,a0+2*a1/3+a2/3,a0+a1+a2+a3],axis=1)
        mineig=np.linalg.eigvalsh(bernstein).min(axis=(1,2,3))
        self.fallback=np.where(mineig < -1e-12)[0]
        for j in self.fallback:
            self.coeff[j,0]=self.matrices[j];self.coeff[j,1]=self.matrices[j+1]-self.matrices[j];self.coeff[j,2:]=0
        self.bernstein_minimum_eigenvalue=mineig
    def location(self,u):
        j,_=super().location(u);fraction=(self.coordinate(u)-self.alpha[j])/(self.alpha[j+1]-self.alpha[j])
        return j,fraction
    def __call__(self,u):
        j,f=self.location(u);c=self.coeff[j];f=f[:,None,None,None]
        return c[:,0]+f*(c[:,1]+f*(c[:,2]+f*c[:,3]))

class CubicPointLikelihood(PointLikelihood):
    def __init__(self,e,data,table):
        self.e=e;self.data=data;self.table=table;self.n=len(data['q']);self.pairs=[(i,j) for i in range(6) for j in range(i,6)]
        means=[];covs=[]
        for coeff in table.coeff:
            _,k,p,_=coeff.shape
            components=np.concatenate((np.moveaxis(coeff,0,1),np.broadcast_to(np.diag(e['red']**2),(k,1,p,p)),np.broadcast_to(np.diag(e['sigma']**2),(k,1,p,p))),axis=1)
            hc=np.einsum('iab,ksbc->ksiac',e['H'],components,optimize=True)
            means.append(np.einsum('ksiaa->ksi',hc).real)
            covs.append(np.stack([np.einsum('kiab,kjba->kij',hc[:,i],hc[:,j]).real*(1 if i==j else 2) for i,j in self.pairs],axis=1))
        self.meanbank=np.asarray(means);self.covbank=np.asarray(covs);self.covbank=(self.covbank+self.covbank.swapaxes(-1,-2))/2
        self.y=np.stack((data['x_physical'],data['x_gaussian']));self.z=np.einsum('gmkd,k->gmd',self.y,e['weights'])
    def moments(self,theta):
        j,f=self.table.location(theta[:,0]);pg,pr,pw=self.weights(theta)
        w=np.stack((pg,pg*f[:,None],pg*f[:,None]**2,pg*f[:,None]**3,pr,pw),axis=-1)
        mu=np.einsum('nks,nksd->nkd',w,self.meanbank[j]);ww=np.stack([w[:,:,i]*w[:,:,j] for i,j in self.pairs],axis=-1)
        cov=np.einsum('nks,nksij->nkij',ww,self.covbank[j]);return mu,cov
