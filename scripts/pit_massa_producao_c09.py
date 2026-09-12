"""Mass PIT diagnostics for all25956 base posteriors; no new likelihood evaluation.

Intervals are symmetric observed-discretization envelopes, not rigorous physical
error bounds. Failed parent gates remain[0,1]; every registered datum is retained.
"""
from pathlib import Path
import json,hashlib,sys,time,resource
import numpy as np
from scipy.special import logsumexp
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'src'))
from inference.mass_batch import MassPosteriorBatch


def main():
    bindings={};start=time.process_time();results={}
    def bind(p):bindings[str(p.relative_to(R))]=hashlib.sha256(p.read_bytes()).hexdigest();return p
    def read(p):return json.loads(bind(p).read_text())
    truth_rows=read(R/'tmp/c09_production_v1/prepared/rows.json');truth={r['id']:r for r in truth_rows}
    assert len(truth)==5396
    generation=read(R/'tmp/c09_production_v1/generation/audit.json')
    # Bind generation evidence; original audit checks all data and seeds.
    bind(Path(__file__));bind(R/'src/inference/mass_batch.py')
    def process(u,ci,ell,names,parents,prior,lower,replace=False):
        for first in range(0,len(names),500):
            ids=names[first:first+500];values=ell[:,first:first+len(ids)]
            true=np.array([truth[name.split('__')[0]]['truth_u'] for name in ids])
            assert np.all((true>=lower)&(true<=1))
            fine=MassPosteriorBatch(u,values,prior=prior,lower=lower)
            coarse=MassPosteriorBatch(u[ci],values[ci],prior=prior,lower=lower)
            pf=fine.cdf_per_curve(true[None])[0];pc=coarse.cdf_per_curve(true[None])[0]
            del coarse
            quadrature=MassPosteriorBatch(u,values,prior=prior,lower=lower,order=16)
            pq=quadrature.cdf_per_curve(true[None])[0];del quadrature,fine
            error=np.maximum(abs(pf-pc),abs(pf-pq))
            for j,name in enumerate(ids):
                parent=parents[name];datum=truth[name.split('__')[0]]
                base_gate=bool(parent['mesh_passed'] if 'mesh_passed' in parent else parent['mesh_gate'])
                response_gate=bool(parent.get('finite_backend_gate',True) and parent.get('heldout_passed',True) and parent.get('scipy_passed',True))
                passed=base_gate and response_gate and error[j]<=.002
                interval=[max(0.,float(pf[j]-error[j])),min(1.,float(pf[j]+error[j]))] if passed else [0.,1.]
                assert replace == (name in results)
                results[name]=dict(curve_id=name,datum_id=datum['datum_id'],stage_id=datum['stage_id'],
                    prior=prior,truth_u=float(true[j]),CDF_fine=float(pf[j]),CDF_coarse=float(pc[j]),CDF_order16=float(pq[j]),
                    observed_grid_delta=float(abs(pf[j]-pc[j])),observed_quadrature_delta=float(abs(pf[j]-pq[j])),
                    mass_PIT_interval=interval,mass_resolved=bool(passed),parent_mesh_passed=base_gate,parent_response_passed=response_gate,
                    logL_PIT_interval=[0.,1.],logL_resolved=False,logL_status='NOT_EVALUATED',
                    SBC_eligible=datum['stage_id'] in (1,2,3,6),physical_uniform_bound=False)
    for campaign in ('c09_nominal_production_v1','c09_self_production_v1'):
        base=R/'tmp'/campaign;plan=read(base/'plan.json')
        with np.load(bind(base/'grids.npz')) as f:coarse_u=f['coarse_u']
        for job in plan['jobs']:
            directory=base/'execution'/job['job_id'];parents={r['curve_id']:r for r in read(directory/'posteriors.json')}
            with np.load(bind(directory/'likelihoods.npz')) as f:
                u=f['u'];ell=f['log_likelihood'];names=f['curve_ids'].tolist()
            coarse=coarse_u[coarse_u>=job['lower']];ci=np.searchsorted(u,coarse);assert np.array_equal(u[ci],coarse)
            process(u,ci,ell,names,parents,job['curves'][0]['prior'],job['lower'])
            print(campaign,job['job_id'],len(results),flush=True)
    refined=R/'tmp/c09_nominal_refinement_v1';plan=read(refined/'plan.json');directory=refined/'execution/refined_omission_49'
    with np.load(bind(refined/'grids.npz')) as f:coarse=f['coarse_u']
    with np.load(bind(directory/'likelihoods.npz')) as f:u=f['u'];ell=f['log_likelihood'];names=f['curve_ids'].tolist()
    ci=np.searchsorted(u,coarse);assert np.array_equal(u[ci],coarse)
    process(u,ci,ell,names,{r['curve_id']:r for r in read(directory/'posteriors.json')},'uniform_u',0.,replace=True)
    distance=R/'tmp/c09_distance_production_v1';parents={r['curve_id']:r for r in read(distance/'posterior_recovery/posteriors.json')}
    with np.load(bind(distance/'prepared/response_atlas.npz')) as f:ci=f['coarse_indices']
    for model in ('A0_CN','B_CN_full_variable','B_G_full_variable'):
        components=[]
        for k in range(3):
            with np.load(bind(distance/f'execution/component_{k}.npz')) as f:
                allnames=f['curves'].tolist();columns=[i for i,n in enumerate(allnames) if n.endswith('__'+model)]
                names=[allnames[i] for i in columns];u=f['u'];components.append(f['log_likelihood'][:,columns])
        for mode in ('correct_mixture','nominal_scale_only'):
            ell=logsumexp(np.array(components)+np.log([.25,.5,.25])[:,None,None],axis=0) if mode=='correct_mixture' else components[1]
            process(u,ci,ell,[n+'__'+mode for n in names],parents,'uniform_u',0.)
            print('distance',model,mode,len(results),flush=True)
    expected={r['id']+'__'+model for r in truth_rows for model in r['models']}
    assert set(results)==expected and len(results)==25956
    assert all(r['mass_resolved'] or r['mass_PIT_interval']==[0.,1.] for r in results.values())
    rss=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*(1 if sys.platform=='darwin' else 1024)
    out=R/'results/C09/production_mass_PIT';out.mkdir(parents=True,exist_ok=False)
    (out/'records.json').write_text(json.dumps(list(results.values()),indent=2,allow_nan=False)+'\n')
    audit=dict(schema='C09_PRODUCTION_MASS_PIT_v1',records=len(results),mass_resolved=sum(r['mass_resolved'] for r in results.values()),
        logL_resolved=0,new_likelihood_values=0,new_ORFs=0,CPU=time.process_time()-start,peak_RSS_bytes=rss,
        resource_passed=rss<=1536*1024**2,inputs_sha256=bindings,records_sha256=hashlib.sha256((out/'records.json').read_bytes()).hexdigest(),
        scope='Observed-discretization envelopes, conditional on finite response checks; not uniform physical bounds. Truths used only after inference for evaluation. All model groups retained; matched registry and SBC tests still separate.',
        C09_complete=False)
    (out/'audit.json').write_text(json.dumps(audit,indent=2,allow_nan=False)+'\n')
    print(json.dumps({k:v for k,v in audit.items() if k!='inputs_sha256'}))
if __name__=='__main__':main()
