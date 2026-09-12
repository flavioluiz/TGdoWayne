"""C10 production: all frozen observations, positive grids and direct SBC events."""
import os
for _n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','VECLIB_MAXIMUM_THREADS'):os.environ[_n]='1'
from pathlib import Path
import argparse,json,math,resource,sys,time
import numpy as np
R=Path(__file__).resolve().parents[1];S=R/'tmp/c10_exact_lifecycle_v1';G=R/'tmp/c10_population_v1'
sys.path[:0]=[str(R/'src'),str(R/'scripts'),str(S),str(R/'tmp/c10_nested_quadrature_v1')]
from physical import sha,load_geometry,NodalCovariances,ROUTES,LABELS
from ledger import GlobalLedger,ScalarCache
from references import summary,compare_summaries
from bilinear_reference import BilinearPosterior
from report_io import json_report
from c10_memoized_kernel import MemoizedLikelihood
from c10_batched_taylor_adapter import BatchedTaylorEvent
from pta.moment_cache import MomentCache
from pta.prepared_density import PreparedDensity
from pta.nested_quadrature import clenshaw_curtis_prior_weights
from harmonic_margin import polynomial_pair,uniform_loglike_difference,event_level
from nested_event import reference_slice
from aggregate import aggregate_slices,compare_u_rules
O=R/'tmp/c10_production_v1';C=R/'configs/scalar/c10_production_v1.json'


def read(p):
    d=json.loads(p.read_text());return d.get('payload',d)


def save(path,value):
    payload=json.dumps(json_report(value),allow_nan=False,separators=(',',':'))+'\n'
    with path.open('x') as out:out.write(payload)


def freeze():
    protocol=read(C);gen=read(G/'complete.json');audit=read(R/'results/C10/population_generation_audit/audit.json')
    assert gen['observations']==1192 and audit['status']=='PRODUCTION_GENERATION_INDEPENDENT_AUDIT_PASS'
    inputs=dict(read(G/'plan.json')['sources'])
    for n,h in inputs.items():assert sha(R/n)==h,n
    for path in (Path(__file__),C,G/'generation.npz',G/'nodal_component.npz',G/'plan.json',G/'complete.json',
                 R/'results/C10/population_generation_audit/audit.json',R/'results/C10/prepared_event_audit/audit.json',
                 R/'scripts/c10_memoized_kernel.py',R/'scripts/c10_batched_taylor_adapter.py',R/'src/pta/moment_cache.py',
                 R/'src/pta/epsilon_taylor_batched.py',R/'src/pta/epsilon_taylor.py',R/'src/pta/prepared_density.py',
                 R/'src/pta/nested_quadrature.py',R/'tmp/c10_nested_quadrature_v1/nested_event.py'):
        inputs[str(path.relative_to(R))]=sha(path)
    inventory=read(G/'plan.json')['inventory'];batches=[]
    for route in ROUTES:
        ids=[r['global_id'] for r in inventory if route=='D' or LABELS[route][0] in r['analyses']]
        for start in range(0,len(ids),64):batches.append(dict(route=route,ids=ids[start:start+64]))
    grid_values=sum(len(b['ids'])*len(ROUTES[b['route']][0])*257*129 for b in batches)
    truth_values=3*sum(len(r['analyses']) for r in inventory)
    assert grid_values==210322632 and truth_values==19032
    plan=dict(schema='C10_POSTERIOR_PRODUCTION_EXECUTION_v1',execution_enabled=True,inputs=inputs,batches=batches,
              grid_values=grid_values,truth_values=truth_values,event_value_cap=300000000-grid_values-truth_values,
              maximum_values=300000000,CPU_cap=protocol['resources']['maximum_estimated_main_seconds'],
              RSS_cap=4*1024**3,output_cap=16*1024**3,curve_reserve=16*1024**2,
              event_splits=128,event_depth=24,additional_values_per_slice=256,
              decision='No new statistical hypotheses, no discarded targets, no population-selected mesh changes; retain unresolved intervals',
              direct_logL_CDF='D analyses on all 500 prior2D observations',scientific_protocol_sha256=sha(C),threads=1)
    O.mkdir(exist_ok=False);(O/'plan.json').write_text(json.dumps(plan,indent=2)+'\n')
    print(json.dumps({k:v for k,v in plan.items() if k not in ('inputs','batches')}))


def execute():
    started=time.process_time();wall=time.monotonic();plan=read(O/'plan.json')
    for n,h in plan['inputs'].items():assert sha(R/n)==h,n
    if (O/'ledger.json').exists():raise FileExistsError('Previous production is preserved; no implicit restart')
    resource.setrlimit(resource.RLIMIT_CPU,(math.ceil(started)+plan['CPU_cap'],math.ceil(started)+plan['CPU_cap']+1))
    ledger=GlobalLedger(O/'ledger.json',identity=sha(O/'plan.json'),allocations={'grid':plan['grid_values'],'truth':plan['truth_values'],'events':plan['event_value_cap']},maximum_values=plan['maximum_values'],maximum_cpu_seconds=plan['CPU_cap'])
    def guard():
        if time.process_time()-started>plan['CPU_cap']-30:raise RuntimeError('CPU remainder reserved for terminal output')
        if resource.getrusage(resource.RUSAGE_SELF).ru_maxrss>plan['RSS_cap']:raise RuntimeError('RSS cap')
    disk=sum(p.stat().st_size for p in O.iterdir() if p.is_file());completed_targets=0
    for name in ('grids','targets','events'):(O/name).mkdir(exist_ok=False)
    spec=read(S/'execution_spec.json');axes=read(S/'axes.json');protocol=read(C);inventory=read(G/'plan.json')['inventory'];geometry=load_geometry(R,spec)
    with np.load(G/'generation.npz') as f:data=tuple(f[k] for k in ('q','x','g'));truth=f['truth']
    with np.load(G/'nodal_component.npz') as f:provider=NodalCovariances(f['masses'],f['gamma'],geometry,protocol,read(R/'configs/experiments/c06_moments.json'))
    mass=np.array(axes['master_mass_nodes'])[::2];eps=np.array(axes['master_epsilon_nodes'])[::2]
    epsilon_keys={float(x).hex() for x in eps};protocol_hash=sha(C)
    label_order=sum((list(LABELS[r]) for r in ROUTES),[]);columns={x:i for i,x in enumerate(label_order)}
    moments=MomentCache()
    def engine(ids):return MemoizedLikelihood(*(a[ids] for a in data),geometry['estimator_matrices'],geometry['frequency_weights'],moment_cache=moments,maximum_logl_values=15000000,maximum_workspace_bytes=256*1024**2)
    truthLL=np.lib.format.open_memmap(O/'truth_logL.npy',mode='w+',dtype=float,shape=(3,1192,9));truthLL[:]=np.nan
    for record in inventory:
        guard();i=record['global_id'];e=engine([i])
        for route,(models,_) in ROUTES.items():
            if LABELS[route][0] not in record['analyses']:continue
            for level in range(3):
                a,b=provider(float(truth[i,0]),route,level)
                values=ledger.evaluate('truth',len(models),lambda:e.evaluate(a,b,[truth[i,1]],models=models)[0][0,:,0])
                truthLL[level,i,[columns[x] for x in LABELS[route]]]=values
    truthLL.flush();disk+=(O/'truth_logL.npy').stat().st_size
    print(json.dumps(dict(stage='truth_densities_complete',charged=ledger.state['charged'],CPU=time.process_time()-started)),flush=True)
    # Exact nodal covariances shared by every observation; no ORF interpolation.
    covariances={route:[[provider(float(u),route,level) for level in range(3)] for u in mass] for route in ROUTES}
    for batch_index,batch in enumerate(plan['batches']):
        guard();ids=batch['ids'];route=batch['route'];models=ROUTES[route][0];labels=LABELS[route];e=engine(ids)
        grid_path=O/'grids'/f'batch_{batch_index}.npy';shape=(257,129,len(models),len(ids))
        if disk+math.prod(shape)*8+plan['curve_reserve']>plan['output_cap']:raise RuntimeError('Grid disk reservation')
        grid=np.lib.format.open_memmap(grid_path,mode='w+',dtype=float,shape=shape);grid[:]=np.nan
        for j,u in enumerate(mass):
            guard();a,b=covariances[route][j][2]
            grid[j]=ledger.evaluate('grid',129*len(models)*len(ids),lambda:e.evaluate(a,b,eps,models=models)[0])
        grid.flush();disk+=grid_path.stat().st_size
        save(grid_path.with_suffix('.json'),dict(status='COMPLETE',ids=ids,models=list(models),labels=list(labels),route=route,sha256=sha(grid_path)))
        disk+=grid_path.with_suffix('.json').stat().st_size
        for r,i in enumerate(ids):
            one=engine([i]);record=inventory[i]
            for m,(model,label) in enumerate(zip(models,labels)):
                guard()
                if disk+plan['curve_reserve']>plan['output_cap']:raise RuntimeError('Curve disk reservation')
                name=f'{label}_d{i}';col=columns[label];dt=float(np.max(abs(truthLL[:2,i,col]-truthLL[2,i,col])))+1e-10
                logs=grid[:,:,m,r];fine=summary(mass,eps,logs,truth[i],truthLL[2,i,col]);coarse=summary(mass[::2],eps[::2],logs[::2,::2],truth[i],truthLL[2,i,col]);checks=compare_summaries(fine,coarse)
                direct=record['ensemble']=='prior2D' and route=='D';rows=[];extra=[];deltas=[];failure=None
                try:
                    for j,u in enumerate(mass):
                        guard();cov=covariances[route][j];a,b=cov[2];polynomial=polynomial_pair(one,a,b,model)
                        bounds=[uniform_loglike_difference(polynomial,polynomial_pair(one,x,y,model),normal=model!='A0_CN',roundoff_allowance=1e-10) for x,y in cov[:2]]
                        delta=max(x['delta_loglike'] for x in bounds) if all(x['delta_loglike'] is not None for x in bounds) else math.inf
                        deltas.append(delta)
                        if not direct:continue
                        if not math.isfinite(delta):
                            rows.append(dict(status='UNRESOLVED',interval=[0.,1.],candidate_interval=[0.,1.],delta_logL_node=delta));continue
                        prepared=PreparedDensity(*polynomial,maximum_values=256)
                        cache=ScalarCache(prepared,ledger,'events',identity=f'{protocol_hash}:{label}:{i}:{float(u).hex()}',maximum_values=256)
                        cache.cache={float(x).hex():float(y) for x,y in zip(eps,logs[j])}
                        row=reference_slice(BatchedTaylorEvent(one,a,b,model,roundoff_allowance=1e-10),cache,event_level(float(truthLL[2,i,col]),delta,dt),maximum_splits=128,maximum_depth=24,controls={'roundoff_allowance_validated':True,'same_node_covariance_reference_validated':True})
                        for key,value in cache.cache.items():
                            if key not in epsilon_keys:extra.append((j,float.fromhex(key),value))
                        if row.get('partition'):
                            points=np.array([float.fromhex(k) for k in cache.cache]);values=np.array(list(cache.cache.values()));cells=row['partition'];idx=np.searchsorted([c['right'] for c in cells],points,side='left')
                            if not np.all((values>=np.array([c['logL_lower'] for c in cells])[idx])&(values<=np.array([c['logL_upper'] for c in cells])[idx])):raise ArithmeticError('Cached density outside final cell')
                        row.update(delta_logL_node=delta,new_values=cache.charged);rows.append(row)
                except Exception as exc:failure=type(exc).__name__+': '+str(exc)
                if direct:
                    np.savez_compressed(O/'events'/f'{name}.npz',additional=np.array(extra).reshape(-1,3))
                    save(O/'events'/f'{name}.json',dict(rows=rows,failure=failure,base_grid=str(grid_path.relative_to(R)),model_index=m,data_index=r))
                    disk+=(O/'events'/f'{name}.npz').stat().st_size+(O/'events'/f'{name}.json').stat().st_size
                if failure is not None:
                    save(O/'targets'/f'{name}_FAILED.json',dict(reason=failure,rows_completed=len(deltas),charged=ledger.state['charged']))
                    raise RuntimeError(failure)
                maximum_delta=max(deltas);weight_error=min(1.,math.expm1(2*maximum_delta)) if maximum_delta<.3 else 1.
                underflow=fine['log_upper_bound_omitted_scaled_nodal_probability']<=math.log(1e-8)
                norm_ok=checks['logZ_H0'] and checks['logZ_H1'] and maximum_delta<=.001 and underflow
                errors=[abs(x-y)+weight_error for x,y in zip(fine['parameter_CDF'],coarse['parameter_CDF'])]
                pit_bounds=[[max(0.,p-err),min(1.,p+err)] if norm_ok and err<=.002 else [0.,1.] for p,err in zip(fine['parameter_CDF'],errors)]
                bf_error=abs(fine['logBF']-coarse['logBF'])+2*maximum_delta
                bf_bounds=[fine['logBF']-bf_error,fine['logBF']+bf_error] if norm_ok and checks['logBF'] and bf_error<=.002 else [-math.inf,math.inf]
                posterior=BilinearPosterior(mass,eps,logs);quantile_bounds=[]
                for k,marginal in enumerate((posterior.marginal_x,posterior.marginal_y)):
                    q=[]
                    for n,prob in enumerate((.05,.5,.9,.95)):
                        h=abs(fine['quantiles'][k][n]-coarse['quantiles'][k][n]);lo=marginal.quantile(max(0.,prob-weight_error));hi=marginal.quantile(min(1.,prob+weight_error))
                        q.append([max(float(marginal.axis[0]),lo-h),min(float(marginal.axis[-1]),hi+h)] if norm_ok and checks['quantiles'] else [float(marginal.axis[0]),float(marginal.axis[-1])])
                    quantile_bounds.append(q)
                event=dict(status='NOT_DIRECTLY_VALIDATED_DESCRIPTIVE_ONLY',interval=[0.,1.])
                if direct:
                    ag=[]
                    for step in (2,1):
                        ag.append(aggregate_slices(rows[::step],clenshaw_curtis_prior_weights(mass[::step]),deltas[::step],controls={'same_node_reference':True,'roundoff':True,'harmonic_level_enclosure':math.isfinite(maximum_delta)}))
                    interval=ag[1]['candidate_interval'];compatible=max(abs(fine['logL_CDF']-v) for v in interval)<=.002
                    compatible=compatible and ('log_masses' in ag[1]) and abs(ag[1]['log_masses']['Zpoint']-fine['logZ_H1'])<=.001
                    event=compare_u_rules(*ag,original_gates={'bilinear_comparison':compatible,'underflow':underflow,'threshold_reference':math.isfinite(dt),'parameter_CDF_quantiles':checks['parameter_CDF'] and checks['quantiles'],'warning_free':all('failure_preserved' not in x for x in rows)})
                result=dict(status='PRODUCTION_TARGET_COMPLETE_WITH_EXPLICIT_NUMERICAL_STATUS',global_id=i,ensemble=record['ensemble'],local_id=record['id'],label=label,route=route,truth=truth[i].tolist(),
                            grid_batch=batch_index,model_index=m,data_index=r,fine=fine,coarse=coarse,comparison=checks,
                            maximum_harmonic_logL_bound=maximum_delta,parameter_PIT_intervals=pit_bounds,quantile_intervals=quantile_bounds,
                            logBF_interval=bf_bounds,logL_event=event,deterministic_sensitivity_not_MCSE=True)
                save(O/'targets'/f'{name}.json',result);disk+=(O/'targets'/f'{name}.json').stat().st_size
                if disk>plan['output_cap']:raise RuntimeError('Final curve disk cap')
                completed_targets+=1
                if completed_targets%25==0:print(json.dumps(dict(stage='posteriors',targets=completed_targets,expected=6344,charged=ledger.state['charged'],CPU=time.process_time()-started)),flush=True)
        del grid
    assert completed_targets==6344 and ledger.state['charged']==ledger.state['completed']
    result=dict(status='PRODUCTION_POSTERIORS_COMPLETE_NOT_SCIENTIFIC_SYNTHESIS',targets=completed_targets,
                charged=ledger.state['charged'],completed=ledger.state['completed'],CPU=time.process_time()-started,wall=time.monotonic()-wall,
                output_bytes_tracked=disk,new_ORFs=0,new_observations=0,plan_sha256=sha(O/'plan.json'))
    save(O/'complete.json',result);print(json.dumps(result))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--execute',action='store_true');execute() if p.parse_args().execute else freeze()
