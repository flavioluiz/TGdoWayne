"""Batched individual-parameter likelihoods; exact moments of a convex ORF table."""
import numpy as np
from scipy.special import expit
from .model import YEAR

class ConvexORF:
    def __init__(self,nodes,matrices):
        self.nodes=np.asarray(nodes,float);self.matrices=np.asarray(matrices)
        if self.nodes.ndim!=1 or len(self.nodes)<2 or self.nodes[0]!=0 or self.nodes[-1]!=1 or np.any(np.diff(self.nodes)<=0):raise ValueError('Ordered full [0,1] table required.')
        if not np.all(np.isfinite(self.matrices)) or self.matrices.shape[0]!=len(self.nodes):raise ValueError('Invalid matrices.')
        if np.max(abs(self.matrices-self.matrices.swapaxes(-1,-2).conj()))>1e-12:raise ValueError('Not Hermitian.')
        if np.linalg.eigvalsh(self.matrices).min()<-1e-12:raise ValueError('Not PSD; no clipping.')
    def location(self,u):
        u=np.asarray(u,float)
        if not np.all(np.isfinite(u)) or np.any((u<0)|(u>1)):raise ValueError('Mass outside [0,1].')
        j=np.clip(np.searchsorted(self.nodes,u,side='right')-1,0,len(self.nodes)-2)
        f=(u-self.nodes[j])/(self.nodes[j+1]-self.nodes[j])
        return j,f
    def __call__(self,u):
        j,f=self.location(u)
        return (1-f[:,None,None,None])*self.matrices[j]+f[:,None,None,None]*self.matrices[j+1]

class PointLikelihood:
    solve=staticmethod(np.linalg.solve)
    def __init__(self,e,data,table):
        self.e=e;self.data=data;self.table=table;self.n=len(data['q'])
        self.pairs=[(i,j) for i in range(4) for j in range(i,4)]
        means=[];covs=[]
        for lo,hi in zip(table.matrices[:-1],table.matrices[1:]):
            k,p,_=lo.shape
            components=np.stack((lo,hi-lo,np.broadcast_to(np.diag(e['red']**2),(k,p,p)),np.broadcast_to(np.diag(e['sigma']**2),(k,p,p))),axis=1)
            hc=np.einsum('iab,ksbc->ksiac',e['H'],components,optimize=True)
            means.append(np.einsum('ksiaa->ksi',hc).real)
            covs.append(np.stack([np.einsum('kiab,kjba->kij',hc[:,i],hc[:,j]).real*(1 if i==j else 2) for i,j in self.pairs],axis=1))
        self.meanbank=np.asarray(means);self.covbank=np.asarray(covs)
        # Off-diagonal component symmetrization: traces reverse the estimator order.
        self.covbank=(self.covbank+self.covbank.swapaxes(-1,-2))/2
        self.y=np.stack((data['x_physical'],data['x_gaussian']))
        self.z=np.einsum('gmkd,k->gmd',self.y,e['weights'])
    def weights(self,theta):
        u,g,gamma,r,efac=np.asarray(theta).T;e=self.e
        pg=10**(2*g[:,None])*YEAR**3/(12*np.pi*np.pi)*(e['f'][None,:]*YEAR)**(-gamma[:,None])/e['scale']
        pr=10**(2*r[:,None])*YEAR**3/(12*np.pi*np.pi)*(e['f'][None,:]*YEAR)**(-4)/e['scale']
        pw=10**(2*efac[:,None])*2*e['dt']/e['scale']
        return pg,pr,pw
    def moments(self,theta):
        j,f=self.table.location(theta[:,0]);pg,pr,pw=self.weights(theta)
        w=np.stack((pg,pg*f[:,None],pr,pw),axis=-1)
        mu=np.einsum('nks,nksd->nkd',w,self.meanbank[j])
        ww=np.stack([w[:,:,i]*w[:,:,j] for i,j in self.pairs],axis=-1)
        cov=np.einsum('nks,nksij->nkij',ww,self.covbank[j])
        return mu,cov
    def __call__(self,theta,targets):
        theta=np.asarray(theta,float);targets=np.asarray(targets,int)
        if theta.ndim!=2 or theta.shape[1]!=5 or targets.shape!=(len(theta),) or not np.all(np.isfinite(theta)):raise ValueError('Invalid batched point contract.')
        if np.any((targets<0)|(targets>=5*self.n)):raise ValueError('Target ID invalid.')
        ans=np.empty(len(theta));models=targets//self.n;ids=targets%self.n
        select=np.where(models==0)[0]
        if len(select):
            t=theta[select];pg,pr,pw=self.weights(t);c=pg[:,:,None,None]*self.table(t[:,0]);ii=np.arange(c.shape[-1]);e=self.e
            c[:,:,ii,ii]+=pr[:,:,None]*e['red']**2+pw[:,:,None]*e['sigma']**2
            L=np.linalg.cholesky(c);s=self.solve(L,self.data['q'][ids[select],:,:,None])[...,0]
            ans[select]=-np.sum(abs(s)**2,axis=(1,2))-2*np.log(np.diagonal(L,axis1=-2,axis2=-1).real).sum(axis=(1,2))-c.shape[1]*c.shape[2]*np.log(np.pi)
        select=np.where(models!=0)[0]
        if len(select):
            mu,cov=self.moments(theta[select]);m=models[select];r=ids[select]
            for compressed in (False,True):
                ix=np.where(np.isin(m,[2,4])==compressed)[0]
                if not len(ix):continue
                kind=(m[ix]>=3).astype(int)
                if compressed:
                    mean=np.einsum('nkd,k->nd',mu[ix],self.e['weights'])[:,None,:]
                    cv=np.einsum('nkij,k->nij',cov[ix],self.e['weights']**2)[:,None,:,:]
                    y=self.z[kind,r[ix]][:,None,:]
                else:mean=mu[ix];cv=cov[ix];y=self.y[kind,r[ix]]
                L=np.linalg.cholesky(cv);s=self.solve(L,(y-mean)[...,None])[...,0]
                ans[select[ix]]=-.5*(np.sum(s*s,axis=(1,2))+2*np.log(np.diagonal(L,axis1=-2,axis2=-1)).sum(axis=(1,2))+mean.shape[1]*mean.shape[2]*np.log(2*np.pi))
        return ans

class UnitPosterior:
    def __init__(self,likelihood,bounds):self.likelihood=likelihood;self.bounds=np.array(bounds);self.width=np.diff(self.bounds,axis=1)[:,0]
    def physical(self,x):return self.bounds[:,0]+x*self.width
    def __call__(self,z,targets):
        x=expit(z);ll=self.likelihood(self.physical(x),targets)
        jac=(-np.logaddexp(0,-z)-np.logaddexp(0,z)).sum(axis=-1)
        return ll+jac,ll
