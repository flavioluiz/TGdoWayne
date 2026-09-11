"""Geometry and a deliberately expensive, audited small-fixture ORF adapter.

This adapter validates every pair with C05. It is for fixtures, not likelihood
loops. A shared harmonic-table implementation needs its own convergence audit.
"""
from dataclasses import asdict
import hashlib
import time
import numpy as np
from .validation import checked_orf,Resolution,ResourceBudget,MAX_VALIDATED_PHASE


def fibonacci_directions(count):
    """Fixed idealized spherical directions; these are not an observed PTA."""
    if isinstance(count,bool) or not isinstance(count,(int,np.integer)) or count<2:
        raise ValueError('At least two synthetic pulsars are required.')
    j=np.arange(count);z=1-2*(j+.5)/count
    phi=np.pi*(3-np.sqrt(5))*j;r=np.sqrt(1-z*z)
    return np.column_stack((r*np.cos(phi),r*np.sin(phi),z))


class CheckedPairMatrixBuilder:
    """Common cutoffs for a whole matrix; retain pair and matrix audit records.

    Aggregate preflight sums conservative per-pair *budgets*, not hidden runtime
    estimates. Sequential execution uses one pair memory budget. Matrix caching
    only reuses exactly identical inputs; it never interpolates a mass grid.
    Directions must have unit norm within 1e-12; their scalar products are
    saturated to [-1,1] solely for the resulting floating-point roundoff.
    """
    def __init__(self,*,coarse:Resolution,fine:Resolution,pair_budget:ResourceBudget,
                 aggregate_work_budget:int,atol:float,rtol:float):
        if isinstance(aggregate_work_budget,bool) or not isinstance(aggregate_work_budget,int) or aggregate_work_budget<=0:
            raise ValueError('An explicit positive aggregate work budget is required.')
        if not isinstance(pair_budget,ResourceBudget):raise TypeError('An explicit ResourceBudget is required.')
        self.coarse=coarse;self.fine=fine;self.pair_budget=pair_budget
        self.aggregate_work_budget=aggregate_work_budget;self.atol=atol;self.rtol=rtol
        self.reserved_work_units=0;self.cache_hits=0;self.records=[];self._cache={}

    def __call__(self,beta,phases,directions):
        p=np.asarray(directions,dtype=float);y=np.asarray(phases,dtype=float)
        if p.ndim!=2 or p.shape[1]!=3 or y.shape!=(len(p),) or not np.isfinite(p).all() or not np.isfinite(y).all():
            raise ValueError('Finite matching phases and unit directions are required.')
        if not np.allclose(np.linalg.norm(p,axis=1),1,atol=1e-12,rtol=0):raise ValueError('Unit directions required.')
        if not np.isscalar(beta) or not np.isreal(beta) or not np.isfinite(beta) or not 0<=beta<=1:raise ValueError('Require beta in [0,1].')
        if np.any(y<0) or np.any(y>MAX_VALIDATED_PHASE):raise ValueError('Phase outside the C05 audited envelope.')
        key=hashlib.sha256(np.asarray([beta],dtype='<f8').tobytes()+y.astype('<f8').tobytes()+p.astype('<f8').tobytes()).hexdigest()
        if key in self._cache:
            self.cache_hits+=1
            return self._cache[key].copy()
        pairs=len(p)*(len(p)+1)//2
        reservation=pairs*self.pair_budget.max_work_units
        if self.reserved_work_units+reservation>self.aggregate_work_budget:
            raise ValueError('Aggregate ORF work budget exceeded before matrix quadrature.')
        self.reserved_work_units+=reservation
        gamma=np.empty((len(p),len(p)),complex);reports=[];t0=time.perf_counter()
        for a in range(len(p)):
            for b in range(a,len(p)):
                value,report=checked_orf(float(beta),float(np.clip(p[a]@p[b],-1,1)),float(y[a]),float(y[b]),
                    coarse=self.coarse,fine=self.fine,budget=self.pair_budget,atol=self.atol,rtol=self.rtol)
                gamma[a,b]=value;gamma[b,a]=value.conjugate()
                reports.append({'a':a,'b':b,**report})
        diagonal_imag=float(np.max(abs(np.diag(gamma).imag)))
        if diagonal_imag>1e-11*max(float(np.max(abs(gamma))),np.finfo(float).tiny):
            raise ValueError('Non-real ORF auto response beyond roundoff.')
        gamma=(gamma+gamma.conj().T)/2
        eigenvalues=np.linalg.eigvalsh(gamma)
        if eigenvalues.min() < -1e-10*max(float(np.max(abs(eigenvalues))),np.finfo(float).tiny):
            raise ValueError('Pairwise acceptance did not yield a positive-semidefinite ORF matrix.')
        record={'input_sha256':key,'beta':float(beta),'phases':y.tolist(),'pairs':pairs,
                'seconds':time.perf_counter()-t0,'reserved_work_units':reservation,
                'summed_pair_estimated_work_units':sum(r['resources']['work_units_proxy'] for r in reports),
                'sequential_estimated_peak_memory_bytes':max(r['resources']['estimated_memory_bytes'] for r in reports),
                'minimum_eigenvalue':float(eigenvalues.min()),
                'condition_number':float(np.linalg.cond(gamma)),
                'maximum_abs_imaginary_cross':float(np.max(abs(gamma.imag))),
                'maximum_diagonal_imaginary_roundoff':diagonal_imag,'pair_reports':reports}
        self.records.append(record);self._cache[key]=gamma.copy()
        return gamma

    def summary(self):
        return {'coarse':asdict(self.coarse),'fine':asdict(self.fine),
            'pair_budget':asdict(self.pair_budget),'aggregate_work_budget':self.aggregate_work_budget,
            'reserved_work_units':self.reserved_work_units,'cache_hits':self.cache_hits,
            'unique_matrices':len(self.records),'unique_pairs':sum(r['pairs'] for r in self.records),
            'wall_seconds':sum(r['seconds'] for r in self.records),
            'warning':'Every pair checked; common harmonic cutoffs; no eigenvalue clipping or interpolation. Dot products of validated unit directions are saturated to [-1,1] for roundoff only. Resource numbers are conservative proxies, not measured RSS or runtime guarantees.'}
