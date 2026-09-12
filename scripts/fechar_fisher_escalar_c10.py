"""Physical six-coordinate Fisher diagnostics at the eight prospective points."""
import os
for _n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','VECLIB_MAXIMUM_THREADS'):os.environ[_n]='1'
from pathlib import Path
import argparse,json,math,resource,sys,time
import numpy as np
R=Path(__file__).resolve().parents[1];S=R/'tmp/c10_exact_lifecycle_v1';G=R/'tmp/c10_population_v1'
sys.path[:0]=[str(R/'src'),str(S),str(R/'tmp/c10_scalar_blas/src/inference')]
from physical import load_geometry,sha
from pta.simulation import residual_power_spectrum,JULIAN_YEAR_SECONDS
from pta.fisher_information import proper_cn_features,real_gaussian_features,local_diagnostics,derivative_stencil
O=R/'results/C10/fisher_v4';C=R/'configs/scalar/c10_production_v1.json'
def read(p):
    d=json.loads(p.read_text());return d.get('payload',d)

def freeze():
    protocol=read(C);spec=read(S/'execution_spec.json');fisher=dict(protocol['fisher']);fisher['relative_steps']=[.001/(2**j) for j in range(10)];sources=dict(spec['source_sha256'])
    for n,h in sources.items():assert sha(R/n)==h,n
    for path in (Path(__file__),C,S/'execution_spec.json',G/'nodal_component.npz',G/'complete.json',R/'src/pta/fisher_information.py',R/'tests/test_c10_fisher_information.py',R/'tmp/c10_fisher_tests.txt',R/'results/C10/fisher_v1/FAILED_PRESERVED.json',R/'results/C10/fisher_v2/FAILED_PRESERVED.json',R/'scripts/calcular_fisher_escalar_c10.py',R/'scripts/concluir_fisher_escalar_c10.py',R/'results/C10/fisher_v3/new_orf.npz',R/'results/C10/fisher_v3/FAILED_PRESERVED.json',R/'scripts/refinar_fisher_escalar_c10.py'):
        sources[str(path.relative_to(R))]=sha(path)
    masses=set()
    for point in fisher['points']:
        masses.add(point['u'])
        for h in fisher['relative_steps']:
            nodes,_=derivative_stencil(point['u'],h*fisher['coordinate_scales'][0],.001,1.)
            masses.update(map(float,nodes))
    plan=dict(sources=sources,fisher=fisher,mass_nodes=sorted(masses),harmonic_resolutions=spec['harmonic_resolutions'],
              historical_ORF_CPU=read(G/'complete.json')['cumulative_ORF_CPU']+120,combined_ORF_CPU_cap=600,
              CPU_cap=60,output_cap=32*1024**2,RSS_cap=4*1024**3,models=['A0_CN','A_G','B_G'],
              new_likelihood_values=0,new_observations=0,scope='Local correctly specified CN and G experiments; no misspecified-normal physical Fisher or global identifiability claim')
    O.mkdir(exist_ok=False);(O/'plan.json').write_text(json.dumps(plan,indent=2)+'\n')
    print(json.dumps({k:v for k,v in plan.items() if k not in ('sources','fisher','mass_nodes')}))

def execute():
    start=time.process_time();plan=read(O/'plan.json')
    if (O/'STARTED.json').exists():raise FileExistsError('Previous Fisher attempt preserved')
    for n,h in plan['sources'].items():assert sha(R/n)==h,n
    (O/'STARTED.json').write_text(json.dumps(dict(plan_sha256=sha(O/'plan.json')))+'\n')
    resource.setrlimit(resource.RLIMIT_CPU,(math.ceil(start)+60,math.ceil(start)+61))
    protocol=read(C);spec=read(S/'execution_spec.json');geo=load_geometry(R,spec);config=read(R/'configs/experiments/c06_moments.json');fisher=plan['fisher']
    with np.load(G/'nodal_component.npz') as f:old_mass=f['masses'];old_gamma=f['gamma']
    old_index={float(u).hex():i for i,u in enumerate(old_mass)}
    masses=np.array([u for u in plan['mass_nodes'] if float(u).hex() not in old_index]);new_index={float(u).hex():i for i,u in enumerate(masses)}
    with np.load(R/'results/C10/fisher_v3/new_orf.npz') as f:
        np.testing.assert_array_equal(f['masses'],masses);new=f['gamma']
    orf_CPU=0.
    def gamma(u,level):
        key=float(u).hex()
        return old_gamma[level,old_index[key],:3] if key in old_index else new[level,new_index[key],:3]
    f=geo['frequencies_hz'];scale=geo['fixed_scale_psd_seconds_cubed'];H=geo['estimator_matrices'];w=geo['frequency_weights'];n=protocol['nuisance'];cg=config['geometry']
    sigma=np.array(cg['nominal_toa_sigma_nanoseconds'])*1e-9;pattern=np.array(cg['red_amplitude_pattern']);cadence=15*JULIAN_YEAR_SECONDS/392
    maximum_covariance_antisymmetry=0.;maximum_moment_antisymmetry=0.;maximum_derivative_projection_relative=0.
    def covariance(theta,level):
        nonlocal maximum_covariance_antisymmetry
        u,e,at,g,ar,ef=theta;gam=gamma(u,level)
        signal=residual_power_spectrum(f,at,g)/scale
        red=residual_power_spectrum(f,ar,n['red_gamma'])/scale
        noise=red[:,None]*pattern[None]**2+2*(10**ef*sigma[None])**2*cadence/scale[:,None]
        c=signal[:,None,None]*(gam[:,0]+e*gam[:,1]);c[:,np.arange(10),np.arange(10)]+=noise
        asym=float(np.linalg.norm(c-c.conj().swapaxes(-1,-2))/max(np.linalg.norm(c),np.finfo(float).tiny))
        maximum_covariance_antisymmetry=max(maximum_covariance_antisymmetry,asym)
        assert asym<=64*np.finfo(float).eps
        c=(c+c.conj().swapaxes(-1,-2))/2
        np.linalg.cholesky(c)
        return c
    def moments(c):
        nonlocal maximum_moment_antisymmetry
        hc=np.einsum('dab,kbc->kdac',H,c,optimize=True)
        mu=np.einsum('kdaa->kd',hc).real
        s=np.einsum('kiab,kjba->kij',hc,hc,optimize=True).real
        asym=float(np.linalg.norm(s-s.swapaxes(-1,-2))/max(np.linalg.norm(s),np.finfo(float).tiny))
        maximum_moment_antisymmetry=max(maximum_moment_antisymmetry,asym)
        assert asym<=64*np.finfo(float).eps
        return mu,(s+s.swapaxes(-1,-2))/2
    scales=np.array(fisher['coordinate_scales']);all_results=[];raw={}
    for point_index,point in enumerate(fisher['points']):
        theta=np.array([point['u'],point['epsilon'],n['log10_AT'],n['gamma'],n['log10_Ar'],math.log10(n['EFAC'])]);levels=[]
        for level in range(3):
            c=covariance(theta,level);mu,s=moments(c);steps=[]
            for relative_step in fisher['relative_steps']:
                dc=[];dmu=[];ds=[]
                for j in range(6):
                    lower,upper=(.001,1.) if j==0 else ((0.,1.) if j==1 else (-math.inf,math.inf))
                    nodes,weights=derivative_stencil(theta[j],relative_step*scales[j],lower,upper)
                    cc=[];mm=[];ss=[]
                    for value in nodes:
                        t=theta.copy();t[j]=value;cv=covariance(t,level);mv,sv=moments(cv);cc.append(cv);mm.append(mv);ss.append(sv)
                    dc.append(np.tensordot(weights,np.array(cc),axes=(0,0)));dmu.append(np.tensordot(weights,np.array(mm),axes=(0,0)));ds.append(np.tensordot(weights,np.array(ss),axes=(0,0)))
                dc=np.array(dc);dmu=np.array(dmu);ds=np.array(ds)
                # A real linear combination of Hermitian matrices is Hermitian.
                # Bound floating-point antisymmetry at the finite-difference scale,
                # rather than at the often much smaller derivative scale.
                for j in range(6):
                    bound=256*np.finfo(float).eps*max(np.linalg.norm(c),np.linalg.norm(s))/(relative_step*scales[j])
                    anti=max(np.linalg.norm(dc[j]-dc[j].conj().T.swapaxes(0,2)) if False else np.linalg.norm(dc[j]-dc[j].conj().swapaxes(-1,-2)),np.linalg.norm(ds[j]-ds[j].swapaxes(-1,-2)))
                    assert anti<=bound
                    maximum_derivative_projection_relative=max(maximum_derivative_projection_relative,float(anti/max(np.linalg.norm(dc[j]),np.linalg.norm(ds[j]),np.finfo(float).tiny)))
                dc=(dc+dc.conj().swapaxes(-1,-2))/2;ds=(ds+ds.swapaxes(-1,-2))/2
                features={'A0_CN':proper_cn_features(c,dc),'A_G':real_gaussian_features(s,ds,dmu),
                          'B_G':real_gaussian_features(np.einsum('kij,k->ij',s,w*w)[None],np.einsum('pkij,k->pij',ds,w*w)[:,None],np.einsum('pkd,k->pd',dmu,w)[:,None])}
                diagnostics={model:local_diagnostics(value,scales,rank_relative=fisher['rank_relative_threshold']) for model,value in features.items()}
                # Independent analytic covariance derivatives for all non-mass coordinates.
                gam=gamma(theta[0],level);sig=residual_power_spectrum(f,theta[2],theta[3])/scale
                signal=sig[:,None,None]*(gam[:,0]+theta[1]*gam[:,1]);red=residual_power_spectrum(f,theta[4],n['red_gamma'])/scale
                redmat=np.zeros_like(c);redmat[:,np.arange(10),np.arange(10)]=red[:,None]*pattern[None]**2
                white=np.zeros_like(c);white[:,np.arange(10),np.arange(10)]=2*(10**theta[5]*sigma[None])**2*cadence/scale[:,None]
                analytic=[sig[:,None,None]*gam[:,1],2*np.log(10)*signal,-np.log(f*JULIAN_YEAR_SECONDS)[:,None,None]*signal,2*np.log(10)*redmat,2*np.log(10)*white]
                errors=[float(np.linalg.norm(dc[j+1]-a)/max(np.linalg.norm(a),np.finfo(float).tiny)) for j,a in enumerate(analytic)]
                steps.append(dict(relative_step=relative_step,diagnostics=diagnostics,analytic_covariance_derivative_relative_errors=errors))
                if level==2 and relative_step==fisher['relative_steps'][-1]:raw[f'point_{point_index}_covariance']=c;raw[f'point_{point_index}_derivatives']=dc
            levels.append(steps)
        gates={}
        for model in plan['models']:
            f0=np.array(levels[2][-2]['diagnostics'][model]['information']);f1=np.array(levels[2][-1]['diagnostics'][model]['information'])
            step_error=float(np.linalg.norm(f1-f0)/max(np.linalg.norm(f1),np.finfo(float).tiny))
            harmonic_error=max(float(np.linalg.norm(np.array(levels[k][-1]['diagnostics'][model]['information'])-f1)/max(np.linalg.norm(f1),np.finfo(float).tiny)) for k in (0,1))
            ranks=[levels[2][k]['diagnostics'][model]['rank'] for k in (-2,-1)]
            gates[model]=dict(step_relative_matrix_change=step_error,harmonic_relative_matrix_change=harmonic_error,rank_stable=ranks[0]==ranks[1],
                              passed=step_error<=.001 and harmonic_error<=.001 and ranks[0]==ranks[1] and max(levels[2][-1]['analytic_covariance_derivative_relative_errors'])<=.001)
        all_results.append(dict(point=point,levels=levels,gates=gates))
        print(json.dumps(dict(point=point,gates=gates)),flush=True)
    np.savez_compressed(O/'derivatives.npz',**raw)
    result=dict(status='PHYSICAL_FISHER_COMPLETE_WITH_EXPLICIT_CONVERGENCE_GATES',results=all_results,new_mass_nodes=0,new_ORF_matrices=0,reused_mass_nodes=len(masses),maximum_derivative_projection_relative=maximum_derivative_projection_relative,
                ORF_CPU=orf_CPU,cumulative_ORF_CPU=plan['historical_ORF_CPU']+orf_CPU,CPU=time.process_time()-start,maximum_covariance_antisymmetry=maximum_covariance_antisymmetry,maximum_moment_antisymmetry=maximum_moment_antisymmetry,
                new_likelihood_values=0,new_observations=0,plan_sha256=sha(O/'plan.json'),scope=plan['scope'])
    assert result['CPU']<=60
    (O/'complete.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    assert sum(p.stat().st_size for p in O.iterdir() if p.is_file())<=plan['output_cap']
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--execute',action='store_true');execute() if p.parse_args().execute else freeze()
