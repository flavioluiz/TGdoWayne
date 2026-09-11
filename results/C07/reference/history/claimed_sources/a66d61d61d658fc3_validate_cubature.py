"""Independent prior-polynomial and Cholesky checks for panel/spectral algebra."""
import json,time
from pathlib import Path
import numpy as np
from cubature import (HERE,PILOT,LogAmplitudeBox,experiment,FrozenMassTable,
                      b_nodes,a_nodes,slope_nodes,SpectralCN,digest)
from inference_pilot import covariance_batch,cn_logpdf

def validate():
    start=time.perf_counter();box=LogAmplitudeBox();cfg=json.loads((PILOT/'config.json').read_text());e=experiment(cfg)
    q=np.load(PILOT/'results/data.npz')['q'][14];table=FrozenMassTable(e,cfg['orf'])
    volume=np.prod([hi-lo for lo,hi in [box.gw,box.red,box.efac]])
    results=[]
    for order in [2,3,5,12]:
        values=np.zeros(9)
        for b,wb in zip(*b_nodes(box,order)):
            a,wa=a_nodes(box,b,order);lo,hi=box.conditional_bounds(a,b)
            I0=hi-lo;I1=.5*(hi**2-lo**2);I2=(hi**3-lo**3)/3
            # 1,g,r,t,g²,r²,t²,g*r,a*b integrated over original scale.
            terms=np.array([I0,a*I0+I1,b*I0+I1,I1,
                            a*a*I0+2*a*I1+I2,b*b*I0+2*b*I1+I2,I2,
                            a*b*I0+(a+b)*I1+I2,a*b*I0])
            values+=wb*(terms@wa)/volume
        mg=np.mean(box.gw);mr=np.mean(box.red);mt=np.mean(box.efac)
        vg=np.ptp(box.gw)**2/12;vr=np.ptp(box.red)**2/12;vt=np.ptp(box.efac)**2/12
        expected=np.array([1,mg,mr,mt,mg*mg+vg,mr*mr+vr,mt*mt+vt,mg*mr,(mg-mt)*(mr-mt)+vt])
        error=float(np.max(abs(values-expected)))
        results.append(dict(order=order,values=values.tolist(),expected=expected.tolist(),max_abs_error=error,
                            ratio_covariance=float(values[-1]-(mg-mt)*(mr-mt))))
    # GL3 already integrates all displayed polynomials exactly in these panels.
    if max(r['max_abs_error'] for r in results if r['order']>=3)>5e-12:raise AssertionError('Panel prior or joint covariance changed.')
    spectral=[]
    masses=[0.,.5,float(np.sqrt(1-.001**2)),1.]
    for u in masses:
        gamma=table.get(u)
        # Both support edges and interior; ratios chosen from positive-volume panels.
        bs,_=b_nodes(box,3)
        for b in bs:
            aa,_=a_nodes(box,b,3)
            slopes=np.array([box.slope[0],4.3,box.slope[1]])
            a,s=np.broadcast_arrays(aa[:,None],slopes[None,:]);a=a.ravel();s=s.ravel()
            eta=np.column_stack([a,s,np.full(len(a),b),np.zeros(len(a))])
            C,_=covariance_batch(eta,gamma,e);chol=np.linalg.cholesky(C)
            rhs=np.broadcast_to(q[None,:,:,None],(len(a),*q.shape,1))
            v=np.linalg.solve(chol,rhs);chi=np.sum(abs(v)**2,axis=(1,2,3))
            ld=2*np.log(np.diagonal(chol,axis1=-2,axis2=-1).real).sum(axis=(1,2))
            engine=SpectralCN(e,q,gamma,float(b));cs,ds=engine.coefficients(a,s)
            error_ll=float(np.max(abs((-cs-ds)-(-chi-ld))))
            relative_chi=float(np.max(abs(cs-chi)/np.maximum(1,chi)))
            error_ld=float(np.max(abs(ds-ld)))
            if error_ll>2e-8 or relative_chi>5e-11 or error_ld>2e-9:raise AssertionError((u,b,error_ll,relative_chi,error_ld))
            spectral.append(dict(u=u,b=float(b),cases=len(a),max_abs_logL_error=error_ll,
                                 max_relative_chi_error=relative_chi,max_abs_logdet_error=error_ld,
                                 minimum_denominator=engine.minimum_denominator,
                                 minimum_whitened_orf_eigenvalue=engine.minimum_eigenvalue))
    return dict(status='PASS',prior_checks=results,spectral_case_count=sum(r['cases'] for r in spectral),
                max_abs_logL_error=max(r['max_abs_logL_error'] for r in spectral),
                max_relative_chi_error=max(r['max_relative_chi_error'] for r in spectral),
                max_abs_logdet_error=max(r['max_abs_logdet_error'] for r in spectral),
                minimum_denominator=min(r['minimum_denominator'] for r in spectral),
                minimum_whitened_orf_eigenvalue=min(r['minimum_whitened_orf_eigenvalue'] for r in spectral),
                no_eigenvalue_clipping=True,seconds=time.perf_counter()-start,
                source_hashes={str(p):digest(p) for p in [Path(__file__),HERE/'cubature.py']})

if __name__=='__main__':
    out=validate();(HERE/'results').mkdir(exist_ok=True)
    (HERE/'results/validation.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
