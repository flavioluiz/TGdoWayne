"""Audit endpoint responses and test pilot posterior interpolation on held-out masses."""
from pathlib import Path
import argparse,json,time,traceback
import executar_lote_nominal_c09 as w
import numpy as np
from scipy.special import logsumexp
from backend_checks import scipy_loglike

R=w.ROOT;H=R/'tmp/c09_distance_endpoints_v1'


def main():
    global H
    parser=argparse.ArgumentParser()
    parser.add_argument('--directory',type=Path,default=H)
    args=parser.parse_args();H=args.directory.resolve()
    out=H/'pilot_validation';out.mkdir(exist_ok=False)
    read=lambda p:json.loads(p.read_text())
    plan=read(H/'prepared/plan.json');backend=read(H/'backend_execution/summary.json')
    assert backend['all_jobs_completed']
    count=plan['u_nodes_per_scale']
    refined=plan['schema']=='C09_DISTANCE_LOCAL_REFINEMENT_v1'
    stages=np.empty((3,2,count,4,12,12),complex)
    products=0
    for job in plan['jobs']:
        base=H/'backend_execution'/job['name'];receipt=read(base/'receipt.json')
        assert receipt['status']=='COMPLETED' and w.sha(base/'matrices.npz')==receipt['matrix_sha256']
        with np.load(base/'matrices.npz') as f:stages[job['level_index'],:,:,job['channel']]=f['Gamma']
        products+=receipt['products']
    assert products==plan['real_products']==backend['products']
    dn=float(np.max(abs(stages[1]-stages[0])));dl=float(np.max(abs(stages[2]-stages[1])))
    eigen=float(np.linalg.eigvalsh(stages).min())
    response_pass=dn<=1e-8 and dl<=1e-8 and eigen>=-1e-12
    w.write(out/'response_audit.json',dict(passed=response_pass,angular_delta=dn,harmonic_delta=dl,minimum_eigenvalue=eigen,
        products=products,worker_CPU=backend['CPU'],new_full_nodes=2*count,scope='Finite response controls only'))
    assert response_pass
    gamma=stages[2].copy();del stages
    np.savez_compressed(out/'responses.npz',Gamma=gamma)
    with np.load(H/'prepared/rules.npz') as f:u=f['u']
    initial=R/'tmp/c09_D3_distances_v1/initial_execution'
    rows=read(initial/'plan.json')['curves']
    for row in rows:row['additional_likelihood_cap']=3*count+9
    names=[r['curve_id'] for r in rows];start=time.process_time();wall=time.monotonic()

    class Guard:
        config={'estimated_numeric_bytes':1024**3}
        def check(self):
            if time.process_time()-start>60 or time.monotonic()-wall>90:raise RuntimeError('Pilot resource cap')
            rss=w.resource.getrusage(w.resource.RUSAGE_SELF).ru_maxrss
            if sys_platform!='darwin':rss*=1024
            if rss>1536*1024**2:raise MemoryError('Pilot RSS cap')
    import sys
    sys_platform=sys.platform;guard=Guard()
    budget=w.Budget(rows,additional_cap=18*count+54,historical_values=plan.get('historical_C09_likelihood_values',54867727),checkpoint=guard.check)
    w.write(out/'activation.json',dict(source_sha256=w.sha(Path(__file__)),plan_sha256=w.sha(H/'prepared/plan.json'),
        LL_cap=18*count+54,CPU_cap=60,training=plan['scope'] if refined else 'GL64 plus reference waves1..8 plus endpoints',
        coarse='previous fine fit' if refined else 'GL32 plus reference waves1..7 plus endpoints',
        heldout=f"{len(plan['heldout_control_u'])} new quarter-points" if refined else '17 interior endpoint-bank masses and all wave9 nodes',
        no_new_observations=True))
    (out/'source.py').write_bytes(Path(__file__).read_bytes())
    status='FAILED';error=None;reports=[]
    try:
        config=read(R/'tmp/c09_nominal14_v4/config.json');e=w.experiment(read(R/config['experiment_config']))
        table=w.load_table(R/config['table_file'],config['table_sha256'],guard,expected_shape=(8336,4,12,12));anchor=table(np.array([.5]))[0]
        with np.load(R/'tmp/c09_D3_components_v1/backend_continuation/data.npz') as f:data={k:f[k] for k in ('q','x_physical','x_gaussian')}
        group=w.KernelGroup(rows,data,covariance=w.ScenarioCovariance(e,rows[0]['eta_physical_coordinates'],ratio=0.),
            moments=lambda c:w.quadratic_moments(c,e['H']),weights=e['weights'],anchor_gamma=anchor,budget=budget)
        components=[];checks=[]
        for s,scale in enumerate((.9,1.,1.1)):
            g=table(u) if scale==1. else gamma[0 if scale==.9 else 1]
            values=group.evaluate_gamma(g,names,reason='grid');components.append(np.column_stack([values[n] for n in names]))
            for j,row in enumerate(rows):
                for i in (0,count//2,count-1):
                    reservation=budget.reserve([row['curve_id']],1,reason='scipy_reference');success=False
                    try:value=scipy_loglike(group,row,g[i],e['H'],anchor);success=True
                    finally:budget.complete(reservation,success=success)
                    checks.append(dict(curve=row['curve_id'],scale=scale,u=float(u[i]),delta=float(abs(value-components[-1][i,j]))))
        assert max(r['delta'] for r in checks)<=1e-8
        components=np.array(components);mixture=logsumexp(components+np.log([.25,.5,.25])[:,None,None],axis=0)
        np.savez_compressed(out/'likelihoods.npz',u=u,component_logL=components,mixture_logL=mixture)
        w.write(out/'scipy_checks.json',checks)
        with np.load(R/'tmp/c09_D3_distances_v1/prepared/rules.npz') as f:rules={k:f[k] for k in f.files}
        with np.load(initial/'likelihoods.npz') as f:original={k:f[k] for k in f.files}
        waves=[]
        for wave in range(1,10):
            with np.load(R/f'tmp/c09_D3_distance_reference_v{wave}/initial_execution/likelihoods.npz') as f:
                waves.append({k:f[k] for k in f.files})
        batches=[]
        endpoints=None
        if refined:
            with np.load(R/'tmp/c09_distance_endpoints_v1/pilot_validation/likelihoods.npz') as f:endpoints={k:f[k] for k in f.files}
        for order,nwaves in (((64,8),(0,9)) if refined else ((32,7),(64,8))):
            bank_u=u if endpoints is None else endpoints['u']
            bank_y=mixture if endpoints is None else endpoints['mixture_logL']
            selected=rules[f'indices{order}'] if order else np.arange(len(original['u']))
            eu=bank_u if order==0 else bank_u[[0,-1]]
            ey=bank_y if order==0 else bank_y[[0,-1]]
            x=np.r_[eu,original['u'][selected],*[v['u'] for v in waves[:nwaves]]]
            y=np.concatenate([ey,original['mixture_logL'][selected],*[v['mixture_logL'] for v in waves[:nwaves]]])
            if order==0:
                training=np.isin(u,plan['training_u']);assert int(training.sum())==len(plan['training_u'])
                x=np.r_[x,u[training]];y=np.concatenate([y,mixture[training]])
            if refined and 'previous_fit_file' in plan:
                with np.load(R/plan['previous_fit_file']) as f:x=f['u'];y=f['mixture_logL']
                if order==0:
                    with np.load(R/plan['previous_density_file']) as f:
                        previous_mask=np.isin(f['u'],plan['previous_density_training_u']) if 'previous_density_training_u' in plan else np.ones(len(f['u']),dtype=bool)
                        x=np.r_[x,f['u'][previous_mask],u[training]];y=np.concatenate([y,f['mixture_logL'][previous_mask],mixture[training]])
            sort=np.argsort(x);x=x[sort];y=y[sort]
            duplicate=np.r_[False,np.diff(x)==0]
            if duplicate.any():assert np.max(abs(y[1:][duplicate[1:]]-y[:-1][duplicate[1:]]))<=1e-10
            x=x[~duplicate];y=y[~duplicate]
            assert np.all(np.diff(x)>0)
            batches.append(w.MassPosteriorBatch(x,y))
            np.savez_compressed(out/f'training_{order}.npz',u=x,mixture_logL=y)
        coarse,fine=batches
        fine_q,coarse_q=fine.quantile_brackets(),coarse.quantile_brackets()
        fine_w,coarse_w=fine.wasserstein_bounds(),coarse.wasserstein_bounds()
        control=np.isin(u,plan['heldout_control_u']) if refined else np.r_[False,np.ones(count-2,dtype=bool),False]
        assert not np.isin(u[control],fine.u).any()
        control_errors=abs(fine.interpolator(np.arcsin(u[control]))+fine.shift-mixture[control])
        control_delta=np.max(control_errors,axis=0)
        heldout=waves[-1];wave_delta=np.max(abs(fine.interpolator(np.arcsin(heldout['u']))+fine.shift-heldout['mixture_logL']),axis=0)
        np.savez_compressed(out/'heldout_errors.npz',u=u[control],absolute_logL_error=control_errors)
        for j,name in enumerate(names):
            delta={k:float(abs(fine.summary[k][j]-coarse.summary[k][j])) for k in fine.summary}
            delta['CDF']=float(np.max(abs(fine.cdf(u)[:,j]-coarse.cdf(u)[:,j])))
            qlo=np.minimum(fine_q['lower'][:,j],coarse_q['lower'][:,j]);qhi=np.maximum(fine_q['upper'][:,j],coarse_q['upper'][:,j])
            delta['W1']=float(max(abs(fine_w['upper'][j]-coarse_w['lower'][j]),abs(coarse_w['upper'][j]-fine_w['lower'][j])))
            mesh=all(v<=(.002 if k=='CDF' else .001) for k,v in delta.items()) and np.max(qhi-qlo)<=.001
            reports.append(dict(curve=name,mesh_passed=bool(mesh),delta=delta,heldout_control_logL_delta=float(control_delta[j]),
                heldout_wave9_logL_delta=None if refined else float(wave_delta[j]),
                heldout_gate=bool((control_delta[j] if refined else max(control_delta[j],wave_delta[j]))<=.001),
                quantile_lower=qlo.tolist(),quantile_upper=qhi.tolist(),W1=[float(fine_w['lower'][j]),float(fine_w['upper'][j])],
                summary={k:float(v[j]) for k,v in fine.summary.items()},independent_full_functional_reference=False))
        w.write(out/'comparisons.json',reports);status='COMPLETED_PILOT_INTERPOLATION_CHECKS'
    except Exception:error=traceback.format_exc();print(error,flush=True)
    finally:
        w.write(out/'receipt.json',dict(status=status,error=error,budget=budget.report(),CPU=time.process_time()-start,
            mesh_passed=sum(r['mesh_passed'] for r in reports),heldout_passed=sum(r['heldout_gate'] for r in reports),
            production_activated=False,C09_complete=False))
    if error:raise SystemExit(1)
    print(json.dumps(reports),flush=True)


if __name__=='__main__':main()
