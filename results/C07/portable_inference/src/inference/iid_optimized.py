"""Cached IID diagnostics with unchanged v1 statistical formulas and decisions.

The optimized kernel keeps the original matrix-vector CDF sum. It computes each
influence standard deviation in a contiguous vector, avoiding large N*K float
temporaries. It does not replace the variance by a cancellation-prone prefix
formula. No mutable global cache or patch of the reference module is used.
"""
import copy
import math
import numpy as np
from scipy.special import logsumexp
from inference import iid_diagnostics as reference
from inference.iid_diagnostics import json_safe, simultaneous_differences


class _Weights:
    def __init__(self, log_weights):
        self.lw,self.p,self.logz=reference._weights(log_weights)
        self.n=len(self.p);self.root_n=np.sqrt(self.n)
        self.positive=self.p>0;self.positive_count=int(np.count_nonzero(self.positive))
        self.scaled_p=self.n*self.p
        for a in (self.lw,self.p,self.positive,self.scaled_p):a.setflags(write=False)

    def cdf(self,x,thresholds,mcse_target):
        n=self.n;indicator=x[:,None]<=thresholds[None,:]
        estimate=self.p@indicator;rows=[];errors=[];counts=[]
        for k in range(len(thresholds)):
            influence=self.scaled_p*(indicator[:,k]-estimate[k])
            errors.append(float(np.std(influence,ddof=1)/self.root_n))
            a=int(np.count_nonzero(indicator[:,k]&self.positive));counts.append((a,self.positive_count-a))
        # Restore v1 reduction order near decision/underflow boundaries. This
        # changes computation, never the numerical acceptance threshold.
        borderline=any(abs(se-mcse_target)<=1e-12 or (se<1e-12 and a and b)
            for se,(a,b)in zip(errors,counts))
        if borderline:
            original_influence=self.n*self.p[:,None]*(indicator-estimate)
            errors=np.std(original_influence,axis=0,ddof=1)/self.root_n
        for k,cutoff in enumerate(thresholds):
            se=float(errors[k]);a,b=counts[k]
            resolved=bool(a and b and np.isfinite(se) and se>0)
            rows.append({'threshold':float(cutoff),'estimate':float(estimate[k]),
                'mcse':se if resolved else math.inf,'raw_delta_mcse':se,
                'status':'asymptotic_influence'if resolved else'constant_indicator_unresolved',
                'positive_weight_counts_below_above':[a,b],
                'precision_pass':bool(resolved and se<=mcse_target)})
        return rows

    def quantiles(self,x,probabilities):
        order=np.argsort(x,kind='stable');cumulative=np.cumsum(self.p[order]);cumulative[-1]=1
        return x[order][np.searchsorted(cumulative,probabilities,side='left')]

    def summary(self,deletion_bound_target=.00335):
        # Same arithmetic and sort as v1; only the normalization is reused.
        if not 0<deletion_bound_target<1:raise ValueError('Invalid single-deletion tolerance')
        lw,p,logz=self.lw,self.p,self.logz;n=self.n;sq=float(p@p);pmax=float(p.max())
        order=np.sort(p)[::-1];entropy=float(-np.sum(p[p>0]*np.log(p[p>0])))
        relative_se=float(np.sqrt(max(0.,(n*sq-1)/(n-1))))
        deletion=pmax/(1-pmax)if pmax<1 else math.inf
        return {'n':n,'log_evidence':logz,'log_evidence_delta_mcse':relative_se,
            'evidence_relative_mcse':relative_se,'weight_ess_concentration_only':1/sq,
            'entropy_effective_count':math.exp(entropy),'maximum_normalized_weight':pmax,
            'largest_ten_weight_fraction':float(order[:10].sum()),
            'largest_one_percent_weight_fraction':float(order[:max(1,math.ceil(n*.01))].sum()),
            'log_weight_range_finite':float(np.ptp(lw[np.isfinite(lw)])),
            'exact_zero_target_weights':int(np.isneginf(lw).sum()),
            'floating_point_weight_underflows':int(((p==0)&np.isfinite(lw)).sum()),
            'single_deletion_cdf_bound':deletion,'single_deletion_guard_pass':deletion<=deletion_bound_target,
            'no_unseen_tail_certificate':True}


def _cdf_inputs(values,thresholds,shape,ndim,mcse_target):
    x=reference._real_array(values,ndim,'values');t=reference._real_array(thresholds,1,'thresholds')
    if x.shape!=shape or not np.isfinite(x).all()or not np.isfinite(t).all()or not 0<mcse_target<1:
        raise ValueError('Invalid values/thresholds/precision')
    return x,t


class TargetIIDContext:
    """One target, one level, equal-length independent replications (R,N).

    Owns weight copies; values and thresholds are validated/copied per operation.
    No truth, target identity, raw-release authorization or sampler is stored.
    """
    def __init__(self,log_weights):
        lw=reference._real_array(log_weights,2,'log_weights')
        if lw.shape[0]<2:raise ValueError('Need independent replicated weights')
        self.shape=lw.shape;self.r,self.n=self.shape
        self._each=[_Weights(a)for a in lw];self._pooled=_Weights(lw.ravel())
        self._logz=np.array([a.logz for a in self._each])
        # Preserve v1's distinct normalizer arithmetic for CDF and Z summaries.
        lp=logsumexp(self._logz)-np.log(self.r)
        self._z_ratio=np.exp(self._logz-lp);self._summary=None

    def cdf(self,values,thresholds,*,mcse_target=.00335):
        x,t=_cdf_inputs(values,thresholds,self.shape,2,mcse_target)
        each=[self._each[j].cdf(x[j],t,mcse_target)for j in range(self.r)]
        pooled=self._pooled.cdf(x.ravel(),t,mcse_target)
        for k,row in enumerate(pooled):
            f=np.array([a[k]['estimate']for a in each]);block=self._z_ratio*(f-row['estimate'])
            between=float(np.std(block,ddof=1)/np.sqrt(self.r))
            row['pooled_iid_influence_mcse']=row['mcse'];row['between_replications_influence_mcse']=between
            row['replication_estimates']=f.tolist();row['replication_mcse']=[a[k]['mcse']for a in each]
            row['replication_status']=[a[k]['status']for a in each]
            row['all_replications_resolved']=all(a[k]['precision_pass']or a[k]['status']=='asymptotic_influence'for a in each)
            row['mcse']=max(row['mcse'],between)if row['all_replications_resolved']else math.inf
            row['precision_pass']=bool(np.isfinite(row['mcse'])and row['mcse']<=mcse_target)
        return pooled

    def quantiles(self,values,probabilities):
        x=reference._real_array(values,2,'values');p=reference._real_array(probabilities,1,'probabilities')
        if x.shape!=self.shape or not np.isfinite(x).all()or not np.isfinite(p).all()or np.any((p<=0)|(p>=1)):
            raise ValueError('Invalid quantile inputs')
        return self._pooled.quantiles(x.ravel(),p)

    def weights(self):
        if self._summary is None:
            each=[a.summary()for a in self._each];pooled=self._pooled.summary()
            ratios=np.exp(self._logz-pooled['log_evidence'])
            between=float(np.std(ratios,ddof=1)/np.sqrt(self.r))
            pooled['pooled_iid_evidence_relative_mcse']=pooled['evidence_relative_mcse']
            pooled['between_replications_evidence_relative_mcse']=between
            pooled['evidence_relative_mcse']=max(pooled['evidence_relative_mcse'],between)
            pooled['log_evidence_delta_mcse']=pooled['evidence_relative_mcse'];pooled['replications']=each
            self._summary=pooled
        return copy.deepcopy(self._summary)


def iid_cdf(values,log_weights,thresholds,*,mcse_target=.00335):
    w=_Weights(log_weights);x,t=_cdf_inputs(values,thresholds,(w.n,),1,mcse_target)
    return w.cdf(x,t,mcse_target)

def replicated_cdf(values,log_weights,thresholds,*,mcse_target=.00335):
    return TargetIIDContext(log_weights).cdf(values,thresholds,mcse_target=mcse_target)

def weighted_quantiles(values,log_weights,probabilities):
    w=_Weights(log_weights);x=reference._real_array(values,1,'values');p=reference._real_array(probabilities,1,'probabilities')
    if x.shape!=(w.n,)or not np.isfinite(x).all()or not np.isfinite(p).all()or np.any((p<=0)|(p>=1)):
        raise ValueError('Invalid quantile inputs')
    return w.quantiles(x,p)

def replicated_weights(log_weights):return TargetIIDContext(log_weights).weights()

def weight_summary(log_weights,*,deletion_bound_target=.00335):
    return _Weights(log_weights).summary(deletion_bound_target)


from scipy.stats import norm
def compare_brackets(values, log_weights, brackets, probabilities, reference_cdf,
                     resolution_spread, omission_bound, *, alpha=.05,
                     deterministic_error=.002, quantile_width=.001, mcse_target=.00335, context=None):
    """A0d14: forty one-sided checks, no assumed midpoint CDF."""
    x = reference._real_array(values, 3, 'values'); lw = reference._real_array(log_weights, 2, 'log_weights')
    br = reference._real_array(brackets, 3, 'brackets'); p = reference._real_array(probabilities, 1, 'probabilities')
    ref, spread, omitted = [np.asarray(a, float) for a in (reference_cdf, resolution_spread, omission_bound)]
    if x.shape[:2] != lw.shape or x.shape[2] != 5 or br.shape != (5,4,2) or p.shape != (4,) or any(a.shape != br.shape for a in (ref, spread, omitted)):
        raise ValueError('Invalid 20-bracket reference shapes')
    if not all(np.isfinite(a).all() for a in (x,br,p,ref,spread,omitted)) or np.any(x < 0) or np.any(x > 1) or np.any(br < 0) or np.any(br > 1) or np.any(br[:,:,0] > br[:,:,1]) or np.any(spread < 0) or np.any(omitted < 0) or np.any((p <= 0)|(p >= 1)) or not 0 < alpha < 1:
        raise ValueError('Invalid normalized reference/domain')
    if context is None: context = TargetIIDContext(lw)
    elif context.shape != lw.shape or not np.array_equal(context._pooled.lw, lw.ravel()):
        raise ValueError('Context weights differ from supplied weights')
    z = float(norm.isf(alpha/40)); rows = []
    for j in range(5):
        cdfs = context.cdf(x[:,:,j], br[j].ravel(), mcse_target=mcse_target)
        near_decision = any(np.isfinite(c['mcse']) and
            abs((c['estimate']-p[index//2])*(1 if index%2==0 else -1)
                -(deterministic_error+z*c['mcse'])) <= 1e-12
            for index,c in enumerate(cdfs))
        if near_decision:
            cdfs = reference.replicated_cdf(x[:,:,j], lw, br[j].ravel(), mcse_target=mcse_target)
        for k, prob in enumerate(p):
            ends = []
            for side in (0,1):
                c = cdfs[2*k+side]; violation = (c['estimate']-prob)*(1 if side == 0 else -1)
                radius = deterministic_error+z*c['mcse']
                ends.append({'side': 'lower' if side == 0 else 'upper', 'cdf': c,
                    'signed_inequality_violation': float(violation), 'allowed_error': radius,
                    'inequality_consistent': bool(np.isfinite(radius) and violation <= radius),
                    'reference_cdf': float(ref[j,k,side]),
                    'reference_resolution_spread': float(spread[j,k,side]),
                    'reference_omission_bound': float(omitted[j,k,side]),
                    'reference_refinement_pass': bool(spread[j,k,side]+omitted[j,k,side] <= deterministic_error),
                    'difference_MC_minus_quadrature_descriptive': float(c['estimate']-ref[j,k,side])})
            rows.append({'parameter_index': j, 'probability': float(prob), 'ends': ends,
                'horizontal_width': float(br[j,k,1]-br[j,k,0]),
                'horizontal_refinement_pass': bool(br[j,k,1]-br[j,k,0] <= quantile_width+1e-14),
                'bracket_consistent': all(e['inequality_consistent'] for e in ends),
                'mc_precision_pass': all(e['cdf']['precision_pass'] for e in ends)})
    return {'z': z, 'alpha': alpha, 'one_sided_inequalities': 40, 'rows': rows,
        'consistent_brackets': sum(a['bracket_consistent'] for a in rows),
        'brackets_passing_mc_precision': sum(a['mc_precision_pass'] for a in rows),
        'no_midpoint_CDF_assumption': True, 'no_automatic_inference_approval': True}
