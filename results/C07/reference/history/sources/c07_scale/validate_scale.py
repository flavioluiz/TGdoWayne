"""Independent controls for scale integral, induced joint prior and frozen C07 likelihood."""
import hashlib,json,time
from pathlib import Path
import numpy as np
from scipy.integrate import quad
from scipy.stats import qmc
from scale_marginalization import (LN10,LogAmplitudeBox,cn_log_scale_integral,cn_conditional_scale_cdf)

HERE=Path(__file__).resolve().parent


def direct_log_integral(chi,ld,M,lo,hi):
    """Independent scaled adaptive quadrature in original log10 scale t."""
    mode=float(np.clip(np.log(chi/M)/(2*LN10),lo,hi)) if chi else lo
    def logf(t):return -ld-M*np.log(np.pi)-2*M*LN10*t-chi*np.exp(-2*LN10*t)
    peak=logf(mode);vv=chi*np.exp(-2*LN10*mode)
    derivative=abs(2*LN10*(vv-M));curvature=(2*LN10)**2*vv
    width=1/max(derivative,np.sqrt(curvature),1/(hi-lo))
    splits=sorted(set(float(x) for x in [lo,hi,mode,*[mode+sign*width*j for sign in [-1,1] for j in [1,2,4,8,16,32,64]] ] if lo<=x<=hi))
    value=0;error=0
    for a,b in zip(splits[:-1],splits[1:]):
        part,err=quad(lambda t:np.exp(logf(t)-peak),a,b,epsabs=1e-13*(hi-lo),epsrel=3e-12,limit=100)
        value+=part;error+=err
    return peak+np.log(value),error/value


def check_blocks(values,target):
    values=np.asarray(values);target=np.asarray(target);mean=values.mean(axis=0);se=values.std(axis=0,ddof=1)/np.sqrt(len(values))
    error=abs(mean-target);z=np.divide(error,se,out=np.zeros_like(error),where=se>1e-14)
    if np.any((se<=1e-14)&(error>1e-12)):raise AssertionError('A deterministic prior moment is inconsistent.')
    if np.max(z)>6:raise AssertionError(('Prior joint distribution failed',float(np.max(z))))
    return {'maximum_standard_errors':float(np.max(z)),'maximum_absolute_error':float(error.max()),'estimate':mean.tolist(),'expected':target.tolist()}


def main():
    start=time.perf_counter();checks=[]
    for M in [1,12,48]:
        for chi in [0.,1e-240,1e-20,.1,1.,12.,48.,100.,1000.,10000.]:
            for lo,hi in [(-.3010299956639812,.3010299956639812),(.12,.121),(-.03,-.0299999)]:
                predicted=float(cn_log_scale_integral(chi,3.7,M,lo,hi,conditional_average=False))
                reference,err=direct_log_integral(chi,3.7,M,lo,hi)
                difference=abs(predicted-reference)
                if difference>2e-7:raise AssertionError((M,chi,lo,hi,predicted,reference,difference))
                checks.append({'M':M,'chi':chi,'low':lo,'high':hi,'absolute_log_integral_difference':difference,'quadrature_relative_error_estimate':err})
    cdfs=[]
    for chi in [0.,1e-20,.1,1.,48.,100.,1000.]:
        lo,hi=-.3,.3;whole,_=direct_log_integral(chi,0.,48,lo,hi)
        for t in [-.3,-.25,-.05,.05,.25,.3]:
            predicted=float(cn_conditional_scale_cdf(t,chi,48,lo,hi))
            ref=0. if t<=lo else (1. if t>=hi else np.exp(direct_log_integral(chi,0.,48,lo,t)[0]-whole))
            error=abs(predicted-ref)
            if error>2e-9:raise AssertionError(('CDF',chi,t,predicted,ref))
            cdfs.append({'chi':chi,'threshold':t,'absolute_CDF_difference':error})
    box=LogAmplitudeBox();mean_e=np.mean(box.efac);var_e=np.diff(box.efac)[0]**2/12
    target_mean=np.array([np.mean(box.gw)-mean_e,np.mean(box.red)-mean_e])
    target_cov=np.array([[np.diff(box.gw)[0]**2/12+var_e,var_e],[var_e,np.diff(box.red)[0]**2/12+var_e]])
    means=[];covs=[];rectangle=[];joint=[]
    events=[(-15.1,-15.9),(-14.6,-16.8),(-15.8,-15.3)]
    joint_exact=[]
    for ga,rb in events:
        breakpoints=sorted(set([*box.efac,*[x for x in [box.gw[0]-ga,box.gw[1]-ga,box.red[0]-rb,box.red[1]-rb] if box.efac[0]<x<box.efac[1]]]))
        value=sum(quad(lambda t:np.clip((ga+t-box.gw[0])/np.diff(box.gw)[0],0,1)*np.clip((rb+t-box.red[0])/np.diff(box.red)[0],0,1),a,b,epsabs=1e-13)[0] for a,b in zip(breakpoints[:-1],breakpoints[1:]))/np.diff(box.efac)[0]
        joint_exact.append(value)
    rect_threshold=np.array([-15.2,-16.,.05])
    rect_exact=np.prod((rect_threshold-np.array([box.gw[0],box.red[0],box.efac[0]]))/np.array([np.diff(box.gw)[0],np.diff(box.red)[0],np.diff(box.efac)[0]]))
    for seed in range(7101000,7101008):
        x=qmc.Sobol(4,scramble=True,seed=seed).random_base2(17);r=box.sample_ratio_prior(x[:,:3])
        a,b,slope,lo,hi=r.T;t=lo+x[:,3]*(hi-lo);g=a+t;red=b+t
        for val,limits in [(g,box.gw),(red,box.red),(t,box.efac)]:
            if val.min()<limits[0] or val.max()>limits[1]:raise AssertionError('Original rectangular prior support changed.')
        z=np.column_stack((a,b));means.append(z.mean(axis=0));center=z-target_mean
        covs.append(center.T@center/len(z))
        rectangle.append(np.mean(np.all(np.column_stack((g,red,t))<=rect_threshold,axis=1)))
        joint.append([np.mean((a<=aa)&(b<=bb)) for aa,bb in events])
    prior={'ratio_mean':check_blocks(means,target_mean),'ratio_covariance':check_blocks(covs,target_cov),
           'original_joint_rectangle':check_blocks(rectangle,rect_exact),'ratio_joint_CDF':check_blocks(joint,joint_exact),
           'replicates':8,'points_per_replicate':2**17,'seeds':list(range(7101000,7101008)),
           'independent_joint_reference':'1D integration over the ORIGINAL common t with independent rectangular g/r priors; not product of ratio marginals.'}
    # Verify covariance scaling and absolute likelihood normalization against C07.
    from compare_pilot import PILOT,FrozenMassTable
    from inference_pilot import experiment,covariance_batch,cn_logpdf
    cfg=json.loads((PILOT/'config.json').read_text());e=experiment(cfg);data=np.load(PILOT/'results/data.npz');q=data['q'][[0,9,14]]
    gamma=FrozenMassTable(e,cfg['orf']).get(.5)
    coords=box.sample_ratio_prior(qmc.Sobol(3,scramble=True,seed=7103000).random_base2(4))
    a,b,slope,lo,hi=coords.T;eta0=np.column_stack((a,slope,b,np.zeros(len(a))))
    C0,_=covariance_batch(eta0,gamma,e);chol=np.linalg.cholesky(C0)
    rhs=np.broadcast_to(q.transpose(1,2,0),(len(C0),*q.transpose(1,2,0).shape))
    solved=np.linalg.solve(chol,rhs);chi=np.sum(abs(solved)**2,axis=(1,2))
    ld=2*np.log(np.diagonal(chol,axis1=-2,axis2=-1).real).sum(axis=(-2,-1));M=q.shape[1]*q.shape[2]
    scalar_errors=[];covariance_errors=[]
    for frac in [.03,.5,.97]:
        t=lo+frac*(hi-lo);eta=eta0.copy();eta[:,0]+=t;eta[:,2]+=t;eta[:,3]=t
        C,_=covariance_batch(eta,gamma,e)
        covariance_errors.append(float(np.max(abs(C-10**(2*t[:,None,None,None])*C0)/np.maximum(abs(C),1e-300))))
        reference=cn_logpdf(C,q);closed=-ld[:,None]-M*np.log(np.pi)-2*M*LN10*t[:,None]-chi*np.exp(-2*LN10*t[:,None])
        scalar_errors.append(float(np.max(abs(reference-closed))))
    if max(covariance_errors)>1e-12 or max(scalar_errors)>1e-7:raise AssertionError('Physical normalization/scaling failed.')
    physical_integrals=[]
    for j in [0,5,10,15]:
        for r in range(len(q)):
            pred=float(cn_log_scale_integral(chi[j,r],ld[j],M,lo[j],hi[j],conditional_average=True))
            ref,err=direct_log_integral(chi[j,r],ld[j],M,lo[j],hi[j]);ref-=np.log(hi[j]-lo[j])
            physical_integrals.append({'ratio_sample':j,'data_index':[0,9,14][r],'absolute_log_difference':abs(pred-ref)})
    report={'status':'PASS','scope':'Exact scale reduction only; no posterior campaign or outer-mass convergence claimed.',
            'analytic_integral_cases':len(checks),'maximum_absolute_log_integral_difference':max(x['absolute_log_integral_difference'] for x in checks),
            'integral_checks':checks,'maximum_CDF_absolute_difference':max(x['absolute_CDF_difference'] for x in cdfs),'cdf_checks':cdfs,
            'joint_prior':prior,'physical_C07':{'mass_u':.5,'ratio_points':16,'data_indices':[0,9,14],
                'maximum_covariance_relative_difference':max(covariance_errors),
                'maximum_abs_loglikelihood_difference':max(scalar_errors),'scale_integral_checks':physical_integrals},
            'source_sha256':hashlib.sha256((HERE/'scale_marginalization.py').read_bytes()).hexdigest(),
            'seconds':time.perf_counter()-start}
    (HERE/'results/validation.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:report[k] for k in ['status','analytic_integral_cases','maximum_absolute_log_integral_difference','maximum_CDF_absolute_difference','seconds']},indent=2))

if __name__=='__main__':main()
