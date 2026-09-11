"""Kernel workload on16 frozen data vectors, not16 posterior integrations/SBC.

Share a covariance eigendecomposition and logdet at fixed mass/b across data.
Conditional PIT numerators are benchmarked only; their ratio-space kinks still
require the independent panel convergence discussed in the cubature report.
"""
import json,time
import numpy as np
from cubature import SpectralCN,LogAmplitudeBox,experiment,PILOT,FrozenMassTable,a_nodes,slope_nodes
from inference_pilot import YEAR
from scale_marginalization import cn_log_scale_integral,cn_conditional_scale_cdf
from bounded import HERE

def batched_coefficients(e,qs,Gamma,b,a,slope):
    red=10.**(2*b)*YEAR**3/(12*np.pi*np.pi)*(e['f']*YEAR)**-4/e['scale'];white=2*e['dt']/e['scale']
    noise=red[:,None]*e['red'][None,:]**2+white[:,None]*e['sigma'][None,:]**2;inv=1/np.sqrt(noise)
    eigen,U=np.linalg.eigh(Gamma*inv[:,:,None]*inv[:,None,:])
    projected=np.einsum('kji,rkj->rki',U.conj(),qs*inv)
    power=abs(projected)**2
    sg=10.**(2*a[:,None])*YEAR**3/(12*np.pi*np.pi)*(e['f'][None,:]*YEAR)**(-slope[:,None])/e['scale']
    den=1+sg[:,:,None]*eigen[None]
    if np.any(den<=0):raise ArithmeticError('Nonpositive denominator; no clipping.')
    chi=power.reshape(len(qs),-1)@(1/den).reshape(len(a),-1).T
    ld=np.log(noise).sum()+np.log(den).sum(axis=(1,2))
    return chi,ld

def compare():
    cfg=json.loads((PILOT/'config.json').read_text());e=experiment(cfg);table=FrozenMassTable(e,cfg['orf']);data=np.load(PILOT/'results/data.npz')
    qs=data['q'];truth=data['truth'];box=LogAmplitudeBox();rows=[]
    for u,b in [(0.,-16.),(.5,-15.2),(1.,-14.5)]:
        Gamma=table.get(u);a,_=a_nodes(box,b,20);s,_=slope_nodes(box,20);a,s=np.broadcast_arrays(a[:,None],s[None,:]);a=a.ravel();s=s.ravel();lo,hi=box.conditional_bounds(a,b)
        before=time.perf_counter();scalar=[];scalar_cdf=[]
        for q,t in zip(qs,truth):
            chi,ld=SpectralCN(e,q,Gamma,b).coefficients(a,s)
            scalar.append(cn_log_scale_integral(chi,ld,q.size,lo,hi,conditional_average=False))
            scalar_cdf.append(cn_conditional_scale_cdf(t[4],chi,q.size,lo,hi))
        scalar_time=time.perf_counter()-before
        before=time.perf_counter();chi,ld=batched_coefficients(e,qs,Gamma,b,a,s)
        logs=cn_log_scale_integral(chi,ld[None],qs.shape[1]*qs.shape[2],lo[None],hi[None],conditional_average=False)
        cdfs=cn_conditional_scale_cdf(truth[:,4,None],chi,qs.shape[1]*qs.shape[2],lo[None],hi[None])
        batch_time=time.perf_counter()-before
        logerr=float(np.max(abs(logs-np.array(scalar))));cdferr=float(np.max(abs(cdfs-np.array(scalar_cdf))))
        if logerr>5e-9 or cdferr>2e-9:raise AssertionError((u,b,logerr,cdferr))
        rows.append(dict(u=u,b=b,parameter_nodes=len(a),data_vectors=len(qs),log_scale_integral_max_abs_error=logerr,conditional_scale_CDF_max_abs_error=cdferr,
                         scalar_seconds=scalar_time,batched_seconds=batch_time,speedup=scalar_time/batch_time))
    out=dict(scope='Workload only:16 data vectors at three fixed mass/ratio combinations; not posterior normalization, global PIT or SBC',
             normalization_approach='Spectral projection and logdet shared; gamma scale integral vectorized over16 data vectors.',
             PIT_limitation='Conditional EFAC CDF numerator shares coefficients, but ratio-space kinks were NOT certified at these orders; use aligned boxes or new convergence checks.',
             status='PASS_LOCAL_KERNEL_EQUIVALENCE',rows=rows)
    (HERE/'results/data_batch_benchmark.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))

if __name__=='__main__':compare()
