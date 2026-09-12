"""Operational roundoff model for cached positive GL mass references.

No likelihoods, ORFs or roots are evaluated. Observed GL16/32 differences are
NOT rigorous errors. The additional 1e-10 relative allowance remains an explicit
engineering assumption; it is not an interval-arithmetic certificate.
"""
import copy
import math
import sys


def with_roundoff(row, *, relative_allowance):
    if not math.isfinite(relative_allowance) or relative_allowance<0:
        raise ValueError('Explicit nonnegative relative allowance required')
    failure=row.get('failure_preserved')
    allowed='ArithmeticError: Reference partition incompatible with total'
    if failure is not None and failure!=allowed:
        return copy.deepcopy(row)
    refs=row.get('numerator_references',{})
    cells=row.get('partition',[]);den=row.get('denominator')
    if den is None or not all(k in refs for k in ('inside','ambiguous')) or not cells:
        return copy.deepcopy(row)
    if cells[0]['left']!=0 or cells[-1]['right']!=1 or any(a['right']!=b['left'] for a,b in zip(cells,cells[1:])):
        raise ValueError('Incomplete partition')
    result=copy.deepcopy(row)
    if failure:result['original_failure_preserved']=result.pop('failure_preserved')
    def pad(ref, regions):
        if regions==0:
            if any(ref[k]!=0 for k in ('value','GL16','GL32','observed_difference','lower','upper')):
                raise ValueError('Nonzero mass for empty union')
            return
        # Conservative scalar operation count for a positive weighted dot product.
        # Density/exponential error is a separate, declared operational allowance.
        n=2*32*regions+2;gamma=n*sys.float_info.epsilon/(1-n*sys.float_info.epsilon)
        extra=(relative_allowance+gamma)*den['value']
        ref['lower']=max(0.,ref['lower']-extra);ref['upper']+=extra
        ref['additional_roundoff_allowance']=extra
    pad(result['denominator'],1)
    for kind in ('inside','ambiguous'):
        count=sum(c['classification']==kind and (i==0 or cells[i-1]['classification']!=kind) for i,c in enumerate(cells))
        pad(result['numerator_references'][kind],count)
    d=result['denominator'];n=result['numerator_references']['inside'];a=result['numerator_references']['ambiguous']
    out=[c for c in cells if c['classification']=='outside']
    compatible=(n['lower']+a['lower']+math.fsum(c['mass_lower'] for c in out)<=d['upper'] and
                n['upper']+a['upper']+math.fsum(c['mass_upper'] for c in out)>=d['lower'])
    for kind in ('inside','ambiguous'):
        ref=result['numerator_references'][kind];selected=[c for c in cells if c['classification']==kind]
        compatible=compatible and ref['upper']>=math.fsum(c['mass_lower'] for c in selected) and ref['lower']<=math.fsum(c['mass_upper'] for c in selected)
    result.update(status='UNRESOLVED',interval=[0.,1.],mass_roundoff_model=dict(relative_allowance=relative_allowance,
                  positive_dot_gamma=True,uniform_physical_certificate=False,rigorous_error_bound=False),
                  quadrature_roundoff_compatibility=bool(compatible))
    if not compatible or d['lower']<=0:
        result['failure_preserved']='ArithmeticError: Incompatible even with explicit mass roundoff model'
        return result
    lo=n['lower']/d['upper'];hi=min(1.,(n['upper']+a['upper'])/d['lower'])
    if lo>hi:
        result['failure_preserved']='ArithmeticError: Invalid interval after mass roundoff model'
        return result
    ambiguity=a['upper']/d['lower'];qerror=(n['upper']-n['lower']+a['upper']-a['lower']+d['upper']-d['lower'])/d['lower']
    controls=result.get('controls',{})
    gates=dict(ambiguity=ambiguity<=.001,observed_total_width=hi-lo<=.002,quadrature_difference=qerror<=.00025,
               finite_controls=all(controls.get(k) is True for k in ('roundoff_allowance_validated','same_node_covariance_reference_validated')))
    result.update(candidate_interval=[lo,hi],ambiguous_mass_upper=min(1.,ambiguity),quadrature_operational_error=qerror,slice_gates=gates)
    if all(gates.values()):result.update(status='SLICE_OPERATIONAL_CONTROLS_PASS_NOT_2D_CDF_APPROVAL',interval=[lo,hi])
    return result
