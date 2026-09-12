"""Frozen production truths, exact truth ORFs and 1192 paired observations."""
import os
for _name in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','VECLIB_MAXIMUM_THREADS'):
    os.environ[_name]='1'
from pathlib import Path
import argparse,hashlib,json,math,resource,sys,time
START=time.process_time()
import numpy as np
R=Path(__file__).resolve().parents[1];S=R/'tmp/c10_exact_lifecycle_v1';P=R/'tmp/c10_physical_pilot_v1'
sys.path[:0]=[str(R/'src'),str(S),str(R/'tmp/c10_scalar_blas/src/inference')]
from physical import load_geometry,NodalCovariances,sha
from pta.scalar_campaign import inventory,hypotheses,budget
from pta.simulation import paired_physical_and_gaussian
O=R/'tmp/c10_population_v1';C=R/'configs/scalar/c10_production_v1.json'


def read(path):
    x=json.loads(path.read_text());return x.get('payload',x)


def freeze():
    protocol=read(C);assert protocol['execution_stages']['truth_orf_generation']
    spec=read(S/'execution_spec.json');sources=dict(spec['source_sha256'])
    for n,h in sources.items():assert sha(R/n)==h,n
    for path in (Path(__file__),C,S/'execution_spec.json',P/'nodal_component.npz',
                 R/'src/pta/scalar_campaign.py',R/'results/C10/prepared_event_audit/audit.json',
                 R/'results/C10/full_flow_benchmark_v1/audit.json',R/'results/C10/production_preflight_v1/plan.json'):
        sources[str(path.relative_to(R))]=sha(path)
    audit=read(R/'results/C10/prepared_event_audit/audit.json');assert audit['status']=='PREPARED_EVENT_AUDIT_PASS'
    rows=inventory(protocol);counts=budget(protocol,rows);hypotheses(protocol)
    assert (counts['observations'],counts['analyses'])==(1192,6344)
    plan=dict(schema='C10_PRODUCTION_GENERATION_STAGE_v1',sources=sources,inventory=rows,counts=counts,
              harmonic_resolutions=spec['harmonic_resolutions'],historical_ORF_CPU=139.347647,
              combined_ORF_CPU_cap=600,stage_CPU_cap=300,RSS_cap=4*1024**3,output_cap=512*1024**2,
              historical_sky_points=50240000,new_sky_points=0,sky_cap=70000000,
              maximum_new_truth_masses=1003,maximum_new_ORF_matrices=30090,
              threads=1,likelihood_values=0,posterior_execution_enabled=False,
              scope='Scientific design frozen before draws; generation does not approve posteriors or assert SBC calibration')
    O.mkdir(exist_ok=False);(O/'plan.json').write_text(json.dumps(plan,indent=2)+'\n')
    print(json.dumps({k:v for k,v in plan.items() if k not in ('sources','inventory','counts')}))


def execute():
    plan=read(O/'plan.json')
    if (O/'STARTED.json').exists():raise FileExistsError('Preserve previous generation attempt; no implicit retry')
    for n,h in plan['sources'].items():assert sha(R/n)==h,n
    (O/'STARTED.json').write_text(json.dumps(dict(plan_sha256=sha(O/'plan.json')))+'\n')
    resource.setrlimit(resource.RLIMIT_CPU,(math.ceil(time.process_time())+300,math.ceil(time.process_time())+301))
    def guard():
        if time.process_time()-START>295:raise RuntimeError('Generation CPU remainder reserved')
        if resource.getrusage(resource.RUSAGE_SELF).ru_maxrss>plan['RSS_cap']:raise RuntimeError('Generation RSS cap')
    protocol=read(C);spec=read(S/'execution_spec.json');geometry=load_geometry(R,spec)
    truth=[]
    for row in plan['inventory']:
        if 'fixed_truth' in row:value=row['fixed_truth']
        else:
            rng=np.random.default_rng(np.random.SeedSequence(row['truth_seed']))
            value=[float(rng.uniform(.001,1.)),0.] if row['ensemble']=='null' else rng.uniform([.001,0.],[1.,1.]).tolist()
        truth.append(value)
    truth=np.array(truth);np.save(O/'truth.npy',truth)
    with np.load(P/'nodal_component.npz') as f:old_mass=f['masses'];old_gamma=f['gamma']
    lookup={float(x).hex() for x in old_mass}
    new_mass=np.array(sorted({float(x) for x in truth[:,0] if float(x).hex() not in lookup}))
    assert len(new_mass)<=plan['maximum_new_truth_masses']
    np.save(O/'new_mass.npy',new_mass)
    from inference.orf_blas import RealHarmonicBasis,TableBudget
    from scalar_blas import RealScalarHarmonicBasis,ScalarTableBudget
    children=[];orf_CPU=0.;proxy=0;shape=(len(new_mass),5,2,10,10)
    for level,resolution in enumerate(plan['harmonic_resolutions']):
        guard();start=time.process_time();B=8;r=resolution
        tt=RealHarmonicBasis(geometry['directions'],lmax=r['lmax'],nmu=r['nmu'],budget=TableBudget(maximum_estimated_memory_bytes=128*1024**2),planned_batch=B)
        fp=RealScalarHarmonicBasis(geometry['directions'],lmax=r['lmax'],nmu=r['nmu'],budget=ScalarTableBudget(maximum_estimated_memory_bytes=128*1024**2),planned_batch=B)
        out=np.lib.format.open_memmap(O/f'gamma_H{level}.npy',mode='w+',dtype=np.complex128,shape=shape);out[:]=complex(float('nan'),float('nan'));out.flush()
        for case,(k,phase) in enumerate(((1,0),(2,1),(3,2),(1,1),(1,2))):
            for a in range(0,len(new_mass),B):
                guard();b=min(a+B,len(new_mass));beta=np.sqrt((1-new_mass[a:b]/k)*(1+new_mass[a:b]/k))
                out[a:b,case,0]=tt.evaluate(beta,geometry['phases'][phase]);out[a:b,case,1]=fp.evaluate(beta,geometry['phases'][phase]);out.flush()
                proxy+=2*(b-a)*10*r['nmu']*2*r['lmax']
        assert np.isfinite(out).all()
        eig=np.linalg.eigvalsh(out);scale=np.maximum(np.max(abs(eig),axis=-1),np.finfo(float).tiny)
        assert np.min(eig[...,0]/scale)>=-1e-10
        elapsed=time.process_time()-start;orf_CPU+=elapsed
        if plan['historical_ORF_CPU']+orf_CPU>600:raise RuntimeError('Inherited ORF CPU cap')
        children.append(dict(level=level,CPU=elapsed,sha256=sha(O/f'gamma_H{level}.npy')))
        print(json.dumps(dict(harmonic_level=level,new_mass_nodes=len(new_mass),CPU=elapsed)),flush=True)
        del tt,fp,out
    new_gamma=np.stack([np.load(O/f'gamma_H{i}.npy') for i in range(3)])
    for a,b in ((0,1),(1,2)):
        if np.any(abs(new_gamma[a]-new_gamma[b])>1e-5+1e-3*abs(new_gamma[b])):raise ArithmeticError('Truth ORF harmonic convergence failed')
    masses=np.r_[old_mass,new_mass];gamma=np.concatenate((old_gamma,new_gamma),axis=1)
    np.savez_compressed(O/'nodal_component.npz',masses=masses,gamma=gamma)
    provider=NodalCovariances(masses,gamma,geometry,protocol,read(R/'configs/experiments/c06_moments.json'))
    data=[]
    for row,(u,eps) in zip(plan['inventory'],truth):
        guard();c0,c1=provider(float(u),'D',2);rng=np.random.default_rng(np.random.SeedSequence(row['data_seed']))
        q,x,g=paired_physical_and_gaussian(c0+eps*c1,geometry['estimator_matrices'],1,rng)
        data.append((q[0],x[0],g[0]))
    q,x,g=(np.stack([row[i] for row in data]) for i in range(3))
    np.savez_compressed(O/'generation.npz',q=q,x=x,g=g,truth=truth,global_ids=np.arange(1192))
    size=sum(p.stat().st_size for p in O.rglob('*') if p.is_file());assert size<plan['output_cap']
    result=dict(status='PRODUCTION_GENERATION_COMPLETE_NOT_POSTERIOR_APPROVAL',observations=1192,
                analyses_planned=6344,new_truth_mass_nodes=len(new_mass),new_ORF_matrices=len(new_mass)*30,
                CPU=time.process_time()-START,ORF_CPU=orf_CPU,cumulative_ORF_CPU=plan['historical_ORF_CPU']+orf_CPU,
                real_BLAS_proxy=proxy,new_sky_points=0,likelihood_values=0,output_bytes_before_terminal=size,
                generation_sha256=sha(O/'generation.npz'),nodal_component_sha256=sha(O/'nodal_component.npz'),
                truth_sha256=sha(O/'truth.npy'),harmonic_reports=children,threads=1,
                posterior_execution_enabled=False,protocol_sha256=sha(C),plan_sha256=sha(O/'plan.json'))
    (O/'complete.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--execute',action='store_true');execute() if parser.parse_args().execute else freeze()
