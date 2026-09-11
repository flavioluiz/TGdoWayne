"""Twenty quantile brackets: forty simultaneous one-sided CDF checks.

No midpoint CDF is assumed. Extra endpoint differences versus quadrature are
descriptive, without adding another family of accept/reject decisions.
"""
from pathlib import Path
import argparse,hashlib,json,sys,math
import numpy as np
from scipy import stats
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT.parent/'c07_mcmc_diagnostics/src'))
from mcmc_diagnostics import cdf_summary


def json_safe(value):
    if isinstance(value,dict):return{k:json_safe(v)for k,v in value.items()}
    if isinstance(value,(list,tuple)):return[json_safe(v)for v in value]
    if isinstance(value,(np.bool_,)):return bool(value)
    if isinstance(value,(float,np.floating)):return float(value)if math.isfinite(value)else None
    return value


def compare_brackets(draws, brackets, probabilities, reference_cdf,
                     resolution_spread, omission_bound, *, alpha=.05,
                     deterministic_cdf_tolerance=.002, mcse_target=.00335):
    x=np.asarray(draws,float);br=np.asarray(brackets,float);p=np.asarray(probabilities,float)
    cf=np.asarray(reference_cdf,float);spread=np.asarray(resolution_spread,float);omission=np.asarray(omission_bound,float)
    if x.ndim!=3 or x.shape[1:]!=(4,5) or br.shape!=(5,4,2) or cf.shape!=br.shape or spread.shape!=br.shape or omission.shape!=br.shape or p.shape!=(4,):
        raise ValueError('Expected(draw,4,5)and(5,4,2)reference arrays')
    if not all(np.isfinite(a).all()for a in [x,br,p,cf,spread,omission]) or np.any(x<0) or np.any(x>1) or np.any(br<0) or np.any(br>1) or np.any(br[:,:,0]>br[:,:,1]) or np.any(spread<0) or np.any(omission<0):
        raise ValueError('Invalid normalized inputs')
    if not 0<alpha<1 or not 0<deterministic_cdf_tolerance<1 or not 0<mcse_target<1 or np.any(p<=0) or np.any(p>=1):
        raise ValueError('Invalid probabilities/tolerances')
    z=float(stats.norm.isf(alpha/40));rows=[]
    for j in range(5):
        for k,prob in enumerate(p):
            ends=[]
            for side in range(2):
                c=cdf_summary(x[:,:,j],float(br[j,k,side]),alpha=alpha,family_size=20,
                              deterministic_error=deterministic_cdf_tolerance,mcse_target=mcse_target)
                radius=deterministic_cdf_tolerance+z*c['mcse']
                # F(lo)<=p and F(hi)>=p. Bounds use one tail of each error interval.
                violation=c['estimate']-prob if side==0 else prob-c['estimate']
                consistent=bool(np.isfinite(radius)and violation<=radius)
                delta=float(c['estimate']-cf[j,k,side])
                ends.append({'side':'lower'if side==0 else'upper','x_unit':float(br[j,k,side]),
                    'cdf_mc':c,'reference_cdf':float(cf[j,k,side]),
                    'reference_resolution_spread':float(spread[j,k,side]),
                    'reference_omission_bound':float(omission[j,k,side]),
                    'reference_refinement_within_tolerance':bool(spread[j,k,side]+omission[j,k,side]<=deterministic_cdf_tolerance),
                    'signed_inequality_violation':float(violation),'allowed_error':radius,
                    'inequality_consistent':consistent,
                    'difference_MC_minus_quadrature_descriptive':delta,
                    'difference_divided_by_MCSE_descriptive':delta/c['mcse']if np.isfinite(c['mcse'])and c['mcse']>0 else None})
            horizontal=bool(br[j,k,1]-br[j,k,0]<=.001+1e-14)
            rows.append({'parameter_index':j,'probability':float(prob),'ends':ends,
                'horizontal_bracket_width':float(br[j,k,1]-br[j,k,0]),
                'horizontal_refinement_pass':horizontal,
                'bracket_consistent':all(e['inequality_consistent']for e in ends),
                'mc_precision_pass':all(e['cdf_mc']['precision_pass']for e in ends),
                'reference_refinement_pass':all(e['reference_refinement_within_tolerance']for e in ends)})
    return {'quantile_brackets':20,'one_sided_inequalities':40,'alpha_per_pilot_family':alpha,'z':z,
            'rows':rows,'consistent_brackets':sum(r['bracket_consistent']for r in rows),
            'brackets_passing_mc_precision':sum(r['mc_precision_pass']for r in rows),
            'reference_refinement_pass':all(r['horizontal_refinement_pass']and r['reference_refinement_pass']for r in rows),
            'all_bracket_diagnostic_checks_pass':all(r['bracket_consistent']and r['mc_precision_pass']and r['reference_refinement_pass']and r['horizontal_refinement_pass']for r in rows),
            'no_automatic_ORF_or_global_Rhat_approval':True,
            'endpoint_differences_are_descriptive_not_second_test_family':True}


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--reference',type=Path,required=True)
    parser.add_argument('--draws',type=Path,required=True);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();ref=json.loads(args.reference.read_text())
    if ref['model']!='A0_CN'or ref['data_index_zero_based']!=14:raise ValueError('Wrong reference target')
    x=np.load(args.draws,mmap_mode='r')[:,14];bounds=np.array(ref['prior_bounds_original']);width=np.diff(bounds,axis=1)[:,0]
    br=(np.array(ref['brackets_original'])-bounds[:,0,None,None])/width[:,None,None]
    result=compare_brackets(x,br,ref['probabilities'],ref['endpoint_CDF_fine139'],ref['endpoint_CDF_resolution_spread'],ref['endpoint_CDF_omission_bound'])
    result['reference_midpoint_CDF_not_evaluated']=not ref['midpoint_CDF_actually_evaluated']
    result['max_reference_midpoint_vertical_envelope']=ref['maximum_midpoint_CDF_deviation_envelope']
    result['source_hashes']={str(p):hashlib.sha256(p.read_bytes()).hexdigest()for p in [Path(__file__),ROOT.parent/'c07_mcmc_diagnostics/src/mcmc_diagnostics.py',args.reference,args.draws]}
    result['label']='A0_D14_BRACKET_CHECKS_ONLY_NOT_SBC_OR_NUMERICAL_APPROVAL'
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(json_safe(result),indent=2,allow_nan=False)+'\n')
    print(json.dumps({k:result[k]for k in ['consistent_brackets','brackets_passing_mc_precision','reference_refinement_pass','all_bracket_diagnostic_checks_pass','z']},indent=2))


if __name__=='__main__':main()
