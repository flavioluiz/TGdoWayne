#!/usr/bin/env python3
"""Read-only independent audit of a CLOSED 500x5 synthesis. No ROOT helpers."""
from pathlib import Path
import argparse,csv,hashlib,json,os,resource,time
# Thread environment must be set before NumPy/SciPy import.
for key in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','VECLIB_MAXIMUM_THREADS'):
    if key in os.environ and os.environ[key]!='1':raise RuntimeError('Audit requires one numerical-library thread.')
    os.environ[key]='1'
import numpy as np
from scipy import stats

MODELS=['A0_CN','A_CN','B_CN','A_G','B_G']
PARAMETERS=['u','log10_Agw','gamma_gw','log10_Ar','log10_EFAC']
PROBABILITIES=[.05,.5,.9,.95]
DATA_SHA='63679c96852f3c0aa1e25c8a3f087c0646ceb22cd7701758491cabdd42ac0103'


def digest(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda:stream.read(1024**2),b''):h.update(block)
    return h.hexdigest()


def read(path):
    with Path(path).open() as stream:return json.load(stream)


class Checks:
    def __init__(self):self.count=0;self.maximum={};self.failures=[]
    def same(self,name,actual,expected):
        self.count+=1
        if isinstance(expected,(bool,str,int)) or expected is None:
            ok=actual==expected and (not isinstance(expected,bool) or type(actual) is bool)
        else:
            a,b=np.asarray(actual),np.asarray(expected)
            numeric=a.dtype.kind in 'fiub' and b.dtype.kind in 'fiub'
            ok=a.shape==b.shape and (np.allclose(a,b,rtol=2e-11,atol=5e-12,equal_nan=False) if numeric else np.array_equal(a,b))
            if numeric and a.shape==b.shape and a.size:
                error=float(np.max(np.abs(a.astype(float)-b.astype(float))))
                self.maximum[name]=error
        if not ok:self.failures.append(dict(check=name,actual=np.asarray(actual).tolist(),expected=np.asarray(expected).tolist()))


def cp(k,n,alpha):
    # Survival-tail form for the upper bound independently of ROOT beta.ppf(1-a/2).
    return [0. if k==0 else float(stats.beta.ppf(alpha/2,k,n-k+1)),
            1. if k==n else float(stats.beta.isf(alpha/2,k+1,n-k))]


def holm_independent(p):
    p=np.asarray(p,float);order=sorted(range(len(p)),key=lambda i:(p[i],i));out=np.empty(len(p));previous=0.
    for rank,i in enumerate(order):
        previous=max(previous,(len(p)-rank)*p[i]);out[i]=min(1.,previous)
    return out


def interval_ks(a,b):
    # Dmax is the larger KS of the two endpoint samples; monotonic order
    # statistics give Dmin as a valid lower bound, without claiming attainability.
    sa=np.sort(a);sb=np.sort(b);n=len(a)
    lower=max([0.]+[(i+1)/n-sb[i] for i in range(n)]+[sa[i]-i/n for i in range(n)])
    upper=max(stats.kstest(a,'uniform',method='exact').statistic,
              stats.kstest(b,'uniform',method='exact').statistic)
    return float(lower),float(upper)


def paired_rectangular_pvalue(cx,px,cy,py):
    # Enumerate feasible total discordances of the rectangular SUPERSET.
    # For a fixed total, binomial two-sided p is smallest at an endpoint and
    # largest at the feasible integer closest to half. No n-by-n grid needed.
    n=len(cx);amin=int(np.sum(cx&~py));amax=int(np.sum(px&~cy));bmin=int(np.sum(cy&~px));bmax=int(np.sum(py&~cx))
    d=np.arange(amin+bmin,min(n,amax+bmax)+1)
    left=np.maximum(amin,d-bmax);right=np.minimum(amax,d-bmin);valid=left<=right
    d,left,right=d[valid],left[valid],right[valid]
    middle=np.clip(d//2,left,right)
    def pv(a):return np.minimum(1.,2*stats.binom.cdf(np.minimum(a,d-a),d,.5))
    low=float(np.minimum(pv(left),pv(right)).min());high=float(pv(middle).max())
    return dict(n=n,mean_difference_bounds=[float(cx.mean()-py.mean()),float(px.mean()-cy.mean())],
                discordant_x_only_bounds=[amin,amax],discordant_y_only_bounds=[bmin,bmax],
                pvalue_lower=low,pvalue_upper=high)


def check_pair(checks,name,row,x,y):
    delta=x-y;n=len(delta);mean=float(delta.mean());se=float(np.sqrt(np.sum((delta-mean)**2)/(n*(n-1))))
    half=float(stats.t.isf(.025,n-1)*se)
    for key,value in dict(n=n,difference_direction='x_minus_y',mean_difference=mean,paired_mc_se=se,
                          approximate_t_interval=[mean-half,mean+half],interval_is_asymptotic_not_exact=True).items():
        checks.same(name+'.'+key,row[key],value)
    if np.isin(x,[0,1]).all() and np.isin(y,[0,1]).all():
        n10=int(np.sum((x==1)&(y==0)));n01=int(np.sum((x==0)&(y==1)));disc=n10+n01
        pv=1. if disc==0 else float(min(1.,2*stats.binom.cdf(min(n10,n01),disc,.5)))
        for key,value in dict(discordant_x_only=n10,discordant_y_only=n01,mcnemar_exact_pvalue=pv,
            finite_sample_hoeffding_interval=[max(-1.,mean-np.sqrt(2*np.log(40)/n)),min(1.,mean+np.sqrt(2*np.log(40)/n))]).items():
            checks.same(name+'.'+key,row[key],value)
    return row.get('mcnemar_exact_pvalue')


def audit(args):
    start=time.process_time();wall=time.perf_counter();checks=Checks()
    paths={k:Path(getattr(args,k)).resolve() for k in ('summary','arrays','tests','paired','config','complete','plan')}
    if digest(paths['summary'])!=args.expected_summary_sha or digest(paths['complete'])!=args.expected_complete_sha:
        raise RuntimeError('Explicit CLOSED summary/completion hashes differ; never audit a running prefix.')
    report=read(paths['summary']);cfg=read(paths['config']);complete=read(paths['complete']);plan=read(paths['plan'])
    if (complete.get('status')!='ALL_TARGET_PRODUCTS_ARCHIVED' or complete.get('targets')!=list(range(2500))
            or complete.get('driver_identity')!=plan.get('driver_identity')
            or plan.get('identity')!=report['provenance']['runtime_identity']):
        raise RuntimeError('Full closed2500 products and runtime/driver closure required.')
    if (cfg['n_realizations']!=500 or cfg['models']!=MODELS or cfg['data_sha256']!=DATA_SHA
            or cfg['families']['correct']!={'models':['A0_CN','A_G','B_G'],'hypotheses':93}
            or cfg['families']['approximate']!={'models':['A_CN','B_CN'],'hypotheses':62}
            or cfg['families']['paired_central90']!={'pairs':[['A_CN','B_CN'],['A_G','B_G'],['A0_CN','A_CN']],'hypotheses':15}
            or cfg['probabilities']!=PROBABILITIES or cfg['discard_realizations'] is not False):
        raise RuntimeError('Original93/62/15 scientific protocol changed.')
    sensitivity=cfg['numerical_sensitivity']
    if any(sensitivity[k]!=v for k,v in dict(family_size=15000,alpha_mc=.01,deterministic_component=.002,cdf_mcse_target=.00335).items()):
        raise RuntimeError('Original15000 numerical envelope specification changed.')
    if digest(paths['arrays'])!=report['arrays_sha256']:raise RuntimeError('Summary/NPZ digest mismatch.')
    if report['config']!=cfg or report['provenance']['synthesis_config_sha256']!=digest(paths['config']):raise RuntimeError('External config differs from executed synthesis.')
    checks.same('scope',report['scope'],'CONTINUOUS_PRIOR_PREDICTIVE_SBC_WITH_NUMERICAL_SENSITIVITY')
    checks.same('simulations',report['simulations_per_model'],500)
    checks.same('retained',report['all_simulations_retained'],True)
    checks.same('models',report['models'],MODELS)
    checks.same('parameters',report['parameters'],PARAMETERS)
    checks.same('provenance.data',report['provenance']['data_sha256'],DATA_SHA)
    checks.same('provenance.all_ids',report['provenance']['all_ids_retained'],True)
    inventory=report['provenance']['inventory']
    if len(inventory)!=2500 or len({r['target'] for r in inventory})!=2500 or {r['target'] for r in inventory}!=set(range(2500)):
        raise RuntimeError('Inventory must retain every datum/model once.')
    for row in inventory:
        if type(row['target']) is not int or type(row['datum']) is not int or row['model']!=MODELS[row['target']//500] or row['datum']!=row['target']%500:raise RuntimeError('Inventory model/datum mapping differs.')
        for key in ('diagnostic_sha256','numeric_sha256','producer_sha256'):
            if len(row[key])!=64 or any(c not in '0123456789abcdef' for c in row[key]):raise RuntimeError('Malformed inventory SHA.')
    source_checks=[]
    for path,expected in report['executed_source_sha256'].items():
        if digest(path)!=expected:raise RuntimeError('Executed synthesis source changed.')
        source_checks.append(dict(path=path,sha256=expected))
    with np.load(paths['arrays'],allow_pickle=False) as npz:arrays={k:npz[k] for k in npz.files}
    if sum(a.nbytes for a in arrays.values())>64*1024**2:raise RuntimeError('Bounded compact-array budget exceeded.')
    p=arrays['pit'];s=arrays['mcse'];r=arrays['resolved'];q=arrays['quantiles_unit'];lo=arrays['pit_lower'];hi=arrays['pit_upper']
    if p.shape!=(5,500,6) or s.shape!=p.shape or r.shape!=p.shape or r.dtype.kind!='b' or q.shape!=(5,500,5,4):raise RuntimeError('Complete compact shapes/types required.')
    if not np.isfinite(p).all() or np.any((p<0)|(p>1)) or np.any(np.isnan(s)) or np.any(s<=0):raise RuntimeError('Invalid unmodified PIT/MCSE.')
    if not np.isfinite(q).all() or np.any((q<0)|(q>1)) or np.any(np.diff(q,axis=-1)<0):raise RuntimeError('Invalid compact quantiles.')
    z=float(stats.norm.ppf(1-.01/(2*15000)))
    # Root uses norm.isf; ppf versus isf difference is separately reported.
    z_stable=float(-stats.norm.ppf(.01/(2*15000)))
    delta=.002+z_stable*s[r];expected_lo=np.zeros_like(p);expected_hi=np.ones_like(p)
    expected_lo[r]=np.maximum(0.,p[r]-delta);expected_hi[r]=np.minimum(1.,p[r]+delta)
    checks.same('numerical.lower',lo,expected_lo);checks.same('numerical.upper',hi,expected_hi)
    checks.same('numerical.z',report['sensitivity_intervals']['z'],z_stable)
    checks.same('numerical.unresolved_count',report['sensitivity_intervals']['unresolved_count'],int((~r).sum()))
    if not np.array_equal(lo[~r],np.zeros((~r).sum())) or not np.array_equal(hi[~r],np.ones((~r).sum())):raise RuntimeError('Unresolved cases were not retained as[0,1].')
    checks.same('units.quantiles',arrays['quantiles_physical'],arrays['bounds'][:,0][None,None,:,None]+np.diff(arrays['bounds'],axis=1)[:,0][None,None,:,None]*q)
    rows=report['tests']
    if len(rows)!=155:raise RuntimeError('Exactly155 scientific test rows required.')
    rowkeys=[(x['group'],x['method'],x['target'],x['diagnostic']) for x in rows]
    expectedkeys=[]
    for group in ('correct','approximate'):
        for model in cfg['families'][group]['models']:
            expectedkeys.extend((group,model,parameter,'PIT') for parameter in PARAMETERS+['logL_at_truth'])
            expectedkeys.extend((group,model,parameter,diagnostic) for parameter in PARAMETERS for diagnostic in [*[f'below_q{v:.2f}' for v in PROBABILITIES],'central_90'])
    if rowkeys!=expectedkeys:raise RuntimeError('Missing, duplicate or reordered scientific hypotheses.')
    cache={};events={};histograms={}
    for i,row in enumerate(rows):
        name=f'test{i}';m=MODELS.index(row['method']);j=(PARAMETERS+['logL_at_truth']).index(row['target']);x=p[m,:,j];a=lo[m,:,j];b=hi[m,:,j];nom=row['nominal'];sen=row['sensitivity'];family=93 if row['group']=='correct' else 62
        checks.same(name+'.family',row['family_size'],family);checks.same(name+'.resolved',row['numerical_resolved'],int(r[m,:,j].sum()))
        if row['diagnostic']=='PIT':
            ks=stats.kstest(x,'uniform',method='exact');sx=np.sort(x);dplus=max((k+1)/500-v for k,v in enumerate(sx));dminus=max(v-k/500 for k,v in enumerate(sx));d=float(ks.statistic)
            expected=dict(n=500,statistic=d,dplus=dplus,dminus=dminus,pvalue=float(ks.pvalue),mean=float(np.sum(x)/500),minimum=float(x.min()),maximum=float(x.max()),unique_count=len(set(x.tolist())),exact_zero_count=int(np.sum(x==0)),exact_one_count=int(np.sum(x==1)),dkw_simultaneous_half_width=float(np.sqrt(np.log(2*family/.05)/1000)),log10_dkw_tail_upper_bound=float(min(0.,np.log10(2)-1000*d*d/np.log(10))),pvalue_numerical_underflow=bool(ks.pvalue==0))
            for key,value in expected.items():checks.same(name+'.nominal.'+key,nom[key],value)
            lower,upper=interval_ks(a,b)
            for key,value in dict(statistic_lower_bound=lower,statistic_upper_bound=upper,pvalue_lower=float(stats.kstwo.sf(upper,500)),pvalue_upper=float(stats.kstwo.sf(lower,500))).items():checks.same(name+'.sensitivity.'+key,sen[key],value)
            bins=np.histogram(x,np.linspace(0,1,21))[0];histograms[row['method']+'/'+row['target']]=bins.tolist()
            if bins.sum()!=500:raise RuntimeError('A PIT histogram dropped cases.')
        else:
            central=row['diagnostic']=='central_90';cut=.95 if central else float(row['diagnostic'].removeprefix('below_q'));nominal=.9 if central else cut
            hit=((x>=.05)&(x<=.95)) if central else x<=cut
            certain=((a>=.05)&(b<=.95)) if central else b<=cut
            possible=((b>=.05)&(a<=.95)) if central else a<=cut
            k=int(hit.sum());low=int(certain.sum());high=int(possible.sum());phat=k/500
            expected=dict(n=500,covered=k,fraction=phat,plugin_mc_se=np.sqrt(phat*(1-phat)/500),pvalue=float(stats.binomtest(k,500,nominal).pvalue),nominal=nominal,null_mc_se=np.sqrt(nominal*(1-nominal)/500),exact_interval=cp(k,500,.05),simultaneous_bonferroni_interval=cp(k,500,.05/family),central_null_count_interval=stats.binom.ppf([.025,.975],500,nominal).astype(int).tolist())
            for key,value in expected.items():checks.same(name+'.nominal.'+key,nom[key],value)
            ns=.95-.05 if central else cut
            if ns not in cache:cache[ns]=np.array([stats.binomtest(k,500,ns).pvalue for k in range(501)])
            pv=cache[ns][low:high+1]
            expected=dict(n=500,certainly_covered=low,possibly_covered=high,ambiguous_count=high-low,fraction_bounds=[low/500,high/500],pvalue_lower=float(pv.min()),pvalue_upper=float(pv.max()),binomial_interval_union=[cp(low,500,.05)[0],cp(high,500,.05)[1]],simultaneous_binomial_interval_union=[cp(low,500,.05/family)[0],cp(high,500,.05/family)[1]])
            for key,value in expected.items():checks.same(name+'.sensitivity.'+key,sen[key],value)
            if central:events[row['method'],j]=(hit,certain,possible)
    for group,size in [('correct',93),('approximate',62)]:
        group_rows=[x for x in rows if x['group']==group]
        if len(group_rows)!=size:raise RuntimeError('Scientific family size differs.')
        adjusted=holm_independent([x['nominal']['pvalue'] for x in group_rows]);lower=holm_independent([x['sensitivity']['pvalue_lower'] for x in group_rows]);upper=holm_independent([x['sensitivity']['pvalue_upper'] for x in group_rows])
        for j,row in enumerate(group_rows):
            for key,value in dict(nominal_holm_pvalue=float(adjusted[j]),nominal_reject=bool(adjusted[j]<=.05),sensitivity_holm_pvalue_bounds=[lower[j],upper[j]],rejection_robust_to_sensitivity=bool(upper[j]<=.05),rejection_not_excluded_by_sensitivity=bool(lower[j]<=.05)).items():checks.same(group+str(j)+'.'+key,row[key],value)
    pairs=report['paired_central90']
    if len(pairs)!=15:raise RuntimeError('Exactly15 paired hypotheses required.')
    pairkeys=[(row['method_a'],row['method_b'],row['parameter']) for row in pairs]
    expectedpairs=[(a,b,parameter) for a,b in cfg['families']['paired_central90']['pairs'] for parameter in PARAMETERS]
    if pairkeys!=expectedpairs:raise RuntimeError('Paired hypotheses differ from frozen15.')
    for i,row in enumerate(pairs):
        j=PARAMETERS.index(row['parameter']);x,cx,px=events[row['method_a'],j];y,cy,py=events[row['method_b'],j]
        check_pair(checks,'paired'+str(i),row['nominal'],x.astype(float),y.astype(float))
        expected=paired_rectangular_pvalue(cx,px,cy,py)
        for key,value in expected.items():checks.same('paired'+str(i)+'.sensitivity.'+key,row['sensitivity'][key],value)
    adjusted=holm_independent([row['nominal']['mcnemar_exact_pvalue'] for row in pairs]);lower=holm_independent([row['sensitivity']['pvalue_lower'] for row in pairs]);upper=holm_independent([row['sensitivity']['pvalue_upper'] for row in pairs])
    for i,row in enumerate(pairs):
        checks.same('paired.holm'+str(i),row['nominal_holm_pvalue'],float(adjusted[i]));checks.same('paired.reject'+str(i),row['nominal_reject'],bool(adjusted[i]<=.05));checks.same('paired.robust'+str(i),row['rejection_robust_to_sensitivity'],bool(upper[i]<=.05));checks.same('paired.holm_bounds'+str(i),row['sensitivity_holm_pvalue_bounds'],[lower[i],upper[i]])
    descriptive=report['descriptive_paired_quantiles']
    if len(descriptive)!=60:raise RuntimeError('Exactly60 descriptive paired quantile rows required.')
    if [(row['method_a'],row['method_b'],row['parameter'],row['quantile_probability']) for row in descriptive] != [(a,b,parameter,probability) for a,b,parameter in expectedpairs for probability in PROBABILITIES]:raise RuntimeError('Descriptive paired-quantile inventory differs.')
    for i,row in enumerate(descriptive):
        a=MODELS.index(row['method_a']);b=MODELS.index(row['method_b']);j=PARAMETERS.index(row['parameter']);k=PROBABILITIES.index(row['quantile_probability'])
        check_pair(checks,'quantile_pair'+str(i),row,q[a,:,j,k],q[b,:,j,k])
    if len(report['model_summary'])!=5:raise RuntimeError('All five model summaries required.')
    for m,row in enumerate(report['model_summary']):
        selected=[x for x in rows if x['method']==MODELS[m]];distance=np.max(np.abs(q[m]-np.asarray(PROBABILITIES)[None,None,:]),axis=(1,2))
        for key,value in dict(model=MODELS[m],simulations=500,functions_resolved_by_parameter=r[m].sum(axis=0).tolist(),simulations_with_all_six_resolved=int(r[m].all(axis=1).sum()),nominal_rejections=sum(x['nominal_reject'] for x in selected),robust_rejections=sum(x['rejection_robust_to_sensitivity'] for x in selected)).items():checks.same('model'+str(m)+'.'+key,row[key],value)
        for key,value in dict(maximum_scaled_quantile_distance=float(distance.max()),median_scaled_quantile_distance=float(np.median(distance)),identical_quantiles_every_replication=bool(np.all(q[m]==np.asarray(PROBABILITIES)[None,None,:]))).items():checks.same('model'+str(m)+'.prior.'+key,row['quantile_distance_from_prior'][key],value)
    for kind,expected in [('tests',rows),('paired',pairs)]:
        with paths[kind].open(newline='') as stream:table=list(csv.DictReader(stream))
        if len(table)!=len(expected):raise RuntimeError('CSV row count differs: '+kind)
        for i,(csvrow,row) in enumerate(zip(table,expected)):
            for key,value in csvrow.items():
                original=row[key]
                parsed=(value=='True') if isinstance(original,bool) and value in ('True','False') else int(value) if isinstance(original,int) else float(value) if isinstance(original,float) else value
                checks.same('csv.'+kind+str(i)+'.'+key,parsed,original)
    result=dict(status='PASS' if not checks.failures else 'FAIL',scope='CLOSED500_SYNTHESIS_ARITHMETIC_AND_LOGICAL_INVENTORY_ONLY',checks=checks.count,failures=checks.failures,maximum_absolute_difference=max(checks.maximum.values(),default=0.),largest_differences=sorted(checks.maximum.items(),key=lambda x:x[1],reverse=True)[:20],retained_targets=2500,retained_pits=15000,unresolved_pits=int((~r).sum()),groups={group:sum(row['nominal_reject'] for row in rows if row['group']==group) for group in ('correct','approximate')},robust_groups={group:sum(row['rejection_robust_to_sensitivity'] for row in rows if row['group']==group) for group in ('correct','approximate')},paired_rejections=sum(row['nominal_reject'] for row in pairs),model_summary=report['model_summary'],histogram20_counts=histograms,input_sha256={str(path):digest(path) for path in paths.values()},executed_synthesis_sources_verified=source_checks,audit_source_sha256=digest(__file__),process_cpu_seconds=time.process_time()-start,wall_seconds=time.perf_counter()-wall,maximum_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,root_helpers_imported=False,ORF_evaluations=0,likelihood_evaluations=0,posterior_raw_reads=0,array_bytes=sum(a.nbytes for a in arrays.values()),pvalue_comparison_tolerance=dict(atol=5e-12,rtol=2e-11,justification='Independent SciPy tail/inversion routes; all decision flags compared exactly'),normal_ppf_complement_roundoff=z-z_stable,limitations=['Original per-target raw/NPZ evidence was not re-integrated; logical inventory checked from the closed synthesis provenance.','Purpose-specific resolution mask is retained from synthesis arrays; algebraic envelope recomputed independently.','CLT numerical envelopes are approximate sensitivity bands, not global integration confidence bounds.','KS finite-n reference is conditional on computed PITs; numerical approximation/autocorrelation never silently becomes an ideal uniform sample.','No posterior scientific approval follows from an arithmetic PASS.'])
    if result['process_cpu_seconds']>30 or result['maximum_rss_bytes']>256*1024**2:result['resource_limit_exceeded']=True;result['status']='FAIL_RESOURCE'
    output=Path(args.output)
    if output.exists():raise FileExistsError('Independent audit output must be new; preserve prior review.')
    output.mkdir(parents=True);(output/'review.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    print(json.dumps({k:result[k] for k in ('status','checks','maximum_absolute_difference','retained_targets','unresolved_pits','process_cpu_seconds','maximum_rss_bytes')}))
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('summary','arrays','tests','paired','config','complete','plan','output'):parser.add_argument('--'+name,type=Path,required=True)
    parser.add_argument('--expected-summary-sha',required=True);parser.add_argument('--expected-complete-sha',required=True)
    args=parser.parse_args();result=audit(args);raise SystemExit(result['status']!='PASS')
