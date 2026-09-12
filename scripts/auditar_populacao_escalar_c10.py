"""Independent seed, trace and covariance reconstruction of production draws."""
from pathlib import Path
import json,sys
import numpy as np
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'src'),str(R/'tmp/c10_exact_lifecycle_v1')]
from physical import sha,load_geometry,NodalCovariances
O=R/'tmp/c10_population_v1'
def read(p):
    d=json.loads(p.read_text());return d.get('payload',d)
def main():
    plan=read(O/'plan.json');done=read(O/'complete.json')
    for n,h in plan['sources'].items():assert sha(R/n)==h,n
    for name,key in (('generation.npz','generation_sha256'),('nodal_component.npz','nodal_component_sha256'),('truth.npy','truth_sha256')):assert sha(O/name)==done[key]
    spec=read(R/'tmp/c10_exact_lifecycle_v1/execution_spec.json');geo=load_geometry(R,spec);H=geo['estimator_matrices']
    with np.load(O/'nodal_component.npz') as f:provider=NodalCovariances(f['masses'],f['gamma'],geo,read(R/'configs/scalar/c10_production_v1.json'),read(R/'configs/experiments/c06_moments.json'))
    with np.load(O/'generation.npz') as f:data={k:f[k] for k in f.files}
    maximum=0.;counts={}
    for row in plan['inventory']:
        i=row['global_id'];counts[row['ensemble']]=counts.get(row['ensemble'],0)+1
        if 'fixed_truth' in row:truth=row['fixed_truth']
        else:
            rng=np.random.default_rng(np.random.SeedSequence(row['truth_seed']))
            truth=[rng.uniform(.001,1.),0.] if row['ensemble']=='null' else rng.uniform([.001,0.],[1.,1.])
        np.testing.assert_array_equal(truth,data['truth'][i])
        rng=np.random.default_rng(np.random.SeedSequence(row['data_seed']))
        re=rng.standard_normal((1,3,10))[0];im=rng.standard_normal((1,3,10))[0];z=(re+1j*im)/np.sqrt(2)
        a,b=provider(float(truth[0]),'D',2);c=a+truth[1]*b
        q=np.stack([np.linalg.cholesky(ck)@zk for ck,zk in zip(c,z)])
        x=np.array([[np.vdot(qk,h@qk).real for h in H] for qk in q])
        g=[]
        for k,ck in enumerate(c):
            mu=np.array([np.trace(h@ck).real for h in H])
            sigma=np.array([[np.trace(h@ck@j@ck).real for j in H] for h in H])
            g.append(mu+np.linalg.cholesky(sigma)@(np.sqrt(2)*z[k].real))
        for name,reference in (('q',q),('x',x),('g',np.array(g))):
            maximum=max(maximum,float(np.max(abs(reference-data[name][i]))/max(1,float(np.max(abs(reference))))))
    assert counts=={'null':500,'prior2D':500,'recovery':192} and maximum<1e-12
    out=R/'results/C10/population_generation_audit';out.mkdir(exist_ok=False)
    result=dict(status='PRODUCTION_GENERATION_INDEPENDENT_AUDIT_PASS',counts=counts,maximum_scaled_array_difference=maximum,
                truth_seed_reconstruction_exact=True,new_likelihood_values=0,source_sha256=sha(Path(__file__)),
                generation_sha256=done['generation_sha256'],scope='Generation and identities; not posterior calibration')
    (out/'audit.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
if __name__=='__main__':main()
