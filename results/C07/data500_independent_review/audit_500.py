"""Independent direct generation/moment stress audit on the actual 500 data.

No inference.model covariance, experiment, simulation, paired generator or
quadratic-moment helpers are imported. Existing checked ORFs are inputs.
"""
import os
os.environ.setdefault('VECLIB_MAXIMUM_THREADS','1')
from pathlib import Path
import hashlib,json,time
import numpy as np
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def direct_statistics(q,pairs,groups,autos):
    products=q[:,pairs[:,0]]*q[:,pairs[:,1]].conj()
    return np.column_stack([products[:,g].real.mean(axis=1) for g in groups]
                           +[products[:,g].imag.mean(axis=1) for g in groups]
                           +[(abs(q[:,g])**2).mean(axis=1) for g in autos])

def main():
    start=time.perf_counter();cfgpath=ROOT/'configs/calibration/prior_predictive_500_v1.json';base=ROOT/'results/C07/prior_predictive'
    cfg=json.loads(cfgpath.read_text());manifest=json.loads((base/'generation.json').read_text())
    assert sha(cfgpath)==manifest['config_sha256'] and sha(base/'data.npz')==manifest['data_sha256']
    assert sha(base/'orf_construction.json')==manifest['orf_construction_sha256']
    with np.load(base/'data.npz',allow_pickle=False) as d:arrays={k:d[k] for k in d.files}
    N=cfg['n_realizations'];P=cfg['n_pulsars'];K=4;D=10
    assert N==500 and P==12 and cfg['positive_channels']==[1,2,3,4] and cfg['fixed_red_slope']==4
    bounds=np.asarray(cfg['prior']['bounds'])
    truth=bounds[:,0]+np.random.default_rng(cfg['truth_seed']).uniform(size=(N,5))*np.diff(bounds,axis=1)[:,0]
    assert np.array_equal(truth,arrays['truth'])
    year=365.25*24*3600;T=cfg['duration_years']*year;f=np.arange(1,5)/T
    dt=T/int(np.ceil(T/(cfg['cadence_days']*86400)))
    sigma=arrays['sigma'];red=arrays['red_pattern'];points=arrays['directions']
    scale=10**(-29.4)/(12*np.pi**2)*(year**3)*(f*year)**(-13/3)+2*np.median(sigma)**2*dt
    assert np.allclose(f,arrays['frequency_hz'],rtol=0,atol=0)
    assert np.allclose(scale,arrays['scale'],rtol=2e-14,atol=0)
    pairs=np.array([(a,b) for a in range(P) for b in range(a+1,P)])
    order=sorted(range(len(pairs)),key=lambda i:float(points[pairs[i,0]]@points[pairs[i,1]]))
    groups=np.array_split(order,4);autos=np.array_split(np.argsort(sigma,kind='stable'),2)
    H=np.zeros((D,P,P),complex)
    for i,g in enumerate(groups):
        for a,b in pairs[g]:
            H[i,a,b]=H[i,b,a]=1/(2*len(g));H[i+4,a,b]=1j/(2*len(g));H[i+4,b,a]=-1j/(2*len(g))
    for i,g in enumerate(autos):H[8+i,g,g]=1/len(g)
    A=np.array([np.block([[h.real,-h.imag],[h.imag,h.real]]) for h in H])
    rng=np.random.default_rng(cfg['data_seed']);rows=[];cache_hashes={};covariances=[];moment_covariances=[]
    for index,(theta,record) in enumerate(zip(truth,manifest['truth_orf_records'])):
        assert theta[0]==record['u'] and record['interpolation_used'] is False
        cache=base/'orf_cache'/record['file'];cache_hashes[cache.name]=sha(cache);assert cache_hashes[cache.name]==record['sha256']
        with np.load(cache,allow_pickle=False) as a:gamma=a['Gamma']
        assert gamma.shape==(K,P,P) and np.isfinite(gamma).all()
        assert np.max(abs(gamma-gamma.swapaxes(-1,-2).conj()))<1e-12
        _,g,slope,r,e=theta
        gw=10**(2*g)*year**3/(12*np.pi**2)*(f*year)**(-slope)
        rn=10**(2*r)*year**3/(12*np.pi**2)*(f*year)**(-4)
        white=2*dt*10**(2*e)*sigma**2
        C=np.array([(gw[k]*gamma[k]+np.diag(rn[k]*red**2+white))/scale[k] for k in range(K)])
        latent=(rng.standard_normal((K,P))+1j*rng.standard_normal((K,P)))/np.sqrt(2)
        L=np.linalg.cholesky(C)
        q=np.array([L[k]@latent[k] for k in range(K)])
        physical=direct_statistics(q,pairs,groups,autos)
        mu=np.empty((K,D));S=np.empty((K,D,D))
        for k in range(K):
            hc=[h@C[k] for h in H]
            mu[k]=[np.trace(b).real for b in hc]
            S[k]=[[np.trace(a@b).real for b in hc] for a in hc]
        # C06 uses the first D real latent components, retaining its actual
        # sqrt(2) rounding after the proper-complex transformation.
        v=np.sqrt(2)*latent.real[:,:D]
        control=np.array([mu[k]+np.linalg.cholesky(S[k])@v[k] for k in range(K)])
        qscale=np.sqrt(np.max(C.diagonal(axis1=-2,axis2=-1).real,axis=1))[:,None]
        statscale=np.sqrt(S.diagonal(axis1=-2,axis2=-1))
        score_q=float(np.max(abs(q-arrays['q'][index])/qscale))
        score_physical=float(np.max(abs(physical-arrays['x_physical'][index])/statscale))
        score_control=float(np.max(abs(control-arrays['x_gaussian'][index])/statscale))
        assert max(score_q,score_physical,score_control)<2e-10
        eig=np.linalg.eigvalsh(C);eigs=np.linalg.eigvalsh(S)
        assert eig.min()>0 and eigs.min()>0
        snr=np.array([gw[k]*np.trace(gamma[k]).real/np.sum(rn[k]*red**2+white) for k in range(K)])
        rows.append(dict(index=index,u=float(theta[0]),C_condition_max=float(np.max(eig[:,-1]/eig[:,0])),Sigma_condition_max=float(np.max(eigs[:,-1]/eigs[:,0])),gw_to_noise_trace_max=float(snr.max()),gw_to_noise_trace_min=float(snr.min()),q_error_in_standard_deviation=score_q,physical_error_in_standard_deviation=score_physical,gaussian_error_in_standard_deviation=score_control,frequency_ORF_variation=float(np.max(abs(gamma-gamma[0])))))
        covariances.append(C);moment_covariances.append(S)
    selected=sorted(set([min(rows,key=lambda r:r['u'])['index'],max(rows,key=lambda r:r['u'])['index'],max(rows,key=lambda r:r['C_condition_max'])['index'],max(rows,key=lambda r:r['Sigma_condition_max'])['index'],max(rows,key=lambda r:r['gw_to_noise_trace_max'])['index'],min(rows,key=lambda r:r['gw_to_noise_trace_min'])['index']]))
    checks=[]
    for index in selected:
        for k,C in enumerate(covariances[index]):
            V=.5*np.block([[C.real,-C.imag],[C.imag,C.real]])
            av=[a@V for a in A]
            S_real=np.array([[2*np.trace(a@b) for b in av] for a in av])
            S=moment_covariances[index][k]
            relative=float(np.max(abs(S_real-S))/np.max(abs(S)))
            assert relative<2e-12
            L=np.linalg.cholesky(C);left=L/np.sqrt(2);right=1j*L/np.sqrt(2)
            cc=left@left.conj().T+right@right.conj().T
            pseudo=left@left.T+right@right.T
            assert np.max(abs(cc-C))/np.max(abs(C))<2e-14 and np.max(abs(pseudo))<1e-14
            checks.append(dict(index=index,channel=k+1,real_Isserlis_relative_error=relative,pseudocovariance_maximum_absolute=float(np.max(abs(pseudo)))))
    result=dict(status='PASS_INDEPENDENT_GENERATION_AND_EXTREME_MOMENTS_NOT_SBC',N=N,question='Do the actual500 draws preserve complex normalization, imaginary cross-statistic signs and paired Gaussian moments at the realized condition/signal extremes?',maximum_q_error_standard_deviation=max(r['q_error_in_standard_deviation'] for r in rows),maximum_physical_error_standard_deviation=max(r['physical_error_in_standard_deviation'] for r in rows),maximum_gaussian_error_standard_deviation=max(r['gaussian_error_in_standard_deviation'] for r in rows),extreme_indices=selected,extreme_rows=[rows[i] for i in selected],independent_real_Isserlis_checks=checks,all_rows=rows,cache_payload_hashes=cache_hashes,source_sha256={str(p.relative_to(ROOT)):sha(p) for p in [Path(__file__),cfgpath,base/'generation.json',base/'data.npz',base/'orf_construction.json']},no_model_covariance_or_pair_helpers_imported=True,orf_quadrature_not_repeated=True,numpy_version=np.__version__,seconds=time.perf_counter()-start,limitations=['Checked ORF cache values are inputs; this review does not independently recompute their quadrature.','No posterior training, IID inference, coverage or SBC run is performed.','The Gaussian controls have declared matched moments but are not the exact quadratic physical distribution.','Numerical reproduction in standardized units tests the generated observations, not empirical moment convergence across different truths.'])
    with (HERE/'review.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ['all_rows','cache_payload_hashes','source_sha256','independent_real_Isserlis_checks']},indent=2))

if __name__=='__main__':main()
