"""Same moment algebra as CubicPointLikelihood, with bounded construction copies."""
import numpy as np
from .orf_cubic_reference import CubicPointLikelihood

class PreallocatedCubicPointLikelihood(CubicPointLikelihood):
    def __init__(self,e,data,table,*,maximum_estimated_numeric_bytes=2*1024**3):
        self.e=e;self.data=data;self.table=table;self.n=len(data['q']);self.pairs=[(i,j) for i in range(6) for j in range(i,6)]
        intervals=len(table.coeff);_,K,P,_=table.coeff[0].shape;D=len(e['H'])
        bank_bytes=int(8*intervals*K*(6*D+21*D*D))
        # Includes retained ORF arrays and 128MiB allowance for evaluation batches.
        estimate=bank_bytes+table.coeff.nbytes+table.matrices.nbytes+128*1024**2
        if estimate>maximum_estimated_numeric_bytes:raise RuntimeError('Explicit preallocated likelihood numeric-array budget exceeded.')
        self.construction_budget=dict(estimated_retained_bank_bytes=bank_bytes,estimated_numeric_bytes=estimate,maximum_estimated_numeric_bytes=maximum_estimated_numeric_bytes,scope='Numeric arrays; not an imposed process RSS ceiling. ORF spline construction is separately budgeted.')
        self.meanbank=np.empty((intervals,K,6,D));self.covbank=np.empty((intervals,K,21,D,D))
        red=np.broadcast_to(np.diag(e['red']**2),(K,1,P,P));white=np.broadcast_to(np.diag(e['sigma']**2),(K,1,P,P))
        for index,coeff in enumerate(table.coeff):
            components=np.concatenate((np.moveaxis(coeff,0,1),red,white),axis=1)
            hc=np.einsum('iab,ksbc->ksiac',e['H'],components,optimize=True)
            self.meanbank[index]=np.einsum('ksiaa->ksi',hc).real
            row=np.stack([np.einsum('kiab,kjba->kij',hc[:,i],hc[:,j]).real*(1 if i==j else 2) for i,j in self.pairs],axis=1)
            self.covbank[index]=(row+row.swapaxes(-1,-2))/2
        self.y=np.stack((data['x_physical'],data['x_gaussian']));self.z=np.einsum('gmkd,k->gmd',self.y,e['weights'])
