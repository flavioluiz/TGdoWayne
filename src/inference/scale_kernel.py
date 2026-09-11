"""Sufficient coefficients for the existing A/B/G families under common scale."""
from dataclasses import dataclass
import numpy as np
from .model import covariance_batch, moment_basis
from .likelihood import precision_and_logdet
from pta.statistics import compress_frequencies,compress_independent_moments
from .scale_gaussian import gaussian_log_scale_integral,gaussian_scale_loglike


@dataclass(frozen=True)
class ScaleTerms:
    chi:np.ndarray
    linear:np.ndarray
    constant:np.ndarray
    logdet:np.ndarray
    real_dimension:int

    def loglike(self,t):
        return gaussian_scale_loglike(t,self.chi,self.linear,self.constant,self.logdet,self.real_dimension)


def _terms(mu,cov,y,outer):
    precision,ld=precision_and_logdet(cov)
    v=np.einsum('nkab,nkb->nka',precision,mu,optimize=True)
    chi=np.einsum('nkab,rkba->nr',precision,outer,optimize=True)
    linear=np.einsum('nka,rka->nr',v,y,optimize=True)
    constant=np.einsum('nka,nka->n',mu,v,optimize=True)[:,None]
    return ScaleTerms(chi,linear,constant,ld[:,None],y.shape[1]*y.shape[2])


class GaussianScaleKernel:
    """Ratios are (a=logAgw-t,b=logAr-t,gamma); no mass/ORF interpolation."""
    names=['A_CN','B_CN','A_G','B_G']
    def __init__(self,experiment,x_physical,x_gaussian):
        self.e=experiment;self.n=len(x_physical)
        self.x=np.concatenate((x_physical,x_gaussian),axis=0)
        self.z=compress_frequencies(self.x,self.e['weights'])[:,None,:]
        self.xouter=self.x[:,:,:,None]*self.x[:,:,None,:]
        self.zouter=self.z[:,:,:,None]*self.z[:,:,None,:]

    def coefficients(self,ratios,gamma,basis=None):
        ratios=np.atleast_2d(ratios)
        if ratios.shape[1]!=3:raise ValueError('Expected ratio columns(a,b,slope).')
        eta=np.column_stack((ratios[:,0],ratios[:,2],ratios[:,1],np.zeros(len(ratios))))
        _,w=covariance_batch(eta,gamma,self.e)
        bm,bs=moment_basis(gamma,self.e) if basis is None else basis
        mu=np.einsum('nks,ksd->nkd',w,bm,optimize=True)
        cov=np.einsum('nks,nkt,kstij->nkij',w,w,bs,optimize=True)
        a=_terms(mu,cov,self.x,self.xouter)
        mb,cb=compress_independent_moments(mu,cov,self.e['weights'])
        b=_terms(mb[:,None,:],cb[:,None,:,:],self.z,self.zouter)
        return a,b

    def marginalized(self,ratios,gamma,low,high,*,coarse_order,fine_order,**kwargs):
        budget=kwargs.get('maximum_evaluations',20_000_000)
        estimate=2*2*self.n*len(np.atleast_2d(ratios))*(coarse_order+fine_order)
        if estimate>budget:raise ValueError(f'Combined A/B scale-quadrature budget exceeded before coefficient construction: {estimate}>{budget}.')
        a,b=self.coefficients(ratios,gamma)
        lo=np.asarray(low)[:,None];hi=np.asarray(high)[:,None]
        values=[];diagnostics=[]
        for term in (a,b):
            value,diagnostic=gaussian_log_scale_integral(term.chi,term.linear,term.constant,term.logdet,term.real_dimension,lo,hi,coarse_order=coarse_order,fine_order=fine_order,conditional_average=True,return_diagnostics=True,**kwargs)
            values.append(value);diagnostics.append(diagnostic)
        a,b=values
        result=np.concatenate((a[:,:self.n],b[:,:self.n],a[:,self.n:],b[:,self.n:]),axis=-1)
        return result,{'A':diagnostics[0],'B':diagnostics[1],'combined_quadrature_evaluations_upper_bound':int(estimate),'prior_measure':'Exact induced ratio prior, conditional uniform t on[low,high]; divided by interval width.'}
