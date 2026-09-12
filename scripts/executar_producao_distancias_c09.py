"""All500 registered distance data, three models, global mixture and nominal analyses."""
from pathlib import Path
import json,time,traceback,sys
import executar_lote_nominal_c09 as w
import numpy as np
from scipy.special import logsumexp
from backend_checks import scipy_loglike

R=w.ROOT;H=R/'tmp/c09_distance_production_v1'


def main():
    bindings={}
    def read(p):bindings[str(p.relative_to(R))]=w.sha(p);return json.loads(p.read_text())
    plan=read(H/'prepared/plan.json')
    assert w.sha(H/'prepared/response_atlas.npz')==plan['atlas_sha256']
    for rel,digest in plan['inputs_sha256'].items():assert w.sha(R/rel)==digest,rel
    index=read(R/'tmp/c09_production_v1/generation/inference_index.json')
    registered=[r for r in index if r['stage_id']==6]
    assert len(registered)==500 and [r['datum_id'] for r in registered]==list(range(500))
    assert all(not {'truth_u','distance_scale','latent_seed'} & r.keys() for r in registered)
    models=['A0_CN','B_CN_full_variable','B_G_full_variable'];rows=[]
    for r in registered:
        for model in models:
            assert model+'__correct_mixture' in r['models'] and model+'__nominal_scale_only' in r['models']
            rows.append(dict(curve_id=r['id']+'__'+model,data_id=r['row'],datum_id=r['datum_id'],observation_id=r['id'],
                analysis=model,eta_physical_coordinates=r['eta'],analysis_contaminant_ratio=0.,
                observation_field='q' if model=='A0_CN' else ('x_physical' if model.startswith('B_CN') else 'x_gaussian'),
                additional_likelihood_cap=3*(plan['fine_nodes']+plan['control_nodes'])+9))
    cap=sum(r['additional_likelihood_cap'] for r in rows);assert cap==12145500 and cap+54871597<120000000
    estimate=8*3*(plan['fine_nodes']+plan['control_nodes'])*1500+2*(plan['fine_nodes']+plan['control_nodes'])*4*12*12*16+350*1024**2
    assert estimate<1024**3
    out=H/'execution';out.mkdir(exist_ok=False);start=time.process_time();wall=time.monotonic()
    class Guard:
        config={'estimated_numeric_bytes':1024**3}
        def check(self):
            rss=w.resource.getrusage(w.resource.RUSAGE_SELF).ru_maxrss
            if sys.platform!='darwin':rss*=1024
            if time.process_time()-start>600 or time.monotonic()-wall>900:raise RuntimeError('Production time cap')
            if rss>1536*1024**2:raise MemoryError('Production RSS cap')
    guard=Guard();budget=w.Budget(rows,additional_cap=cap,historical_values=54871597,checkpoint=guard.check)
    modules={str(Path(m.__file__).resolve().relative_to(R)):w.sha(Path(m.__file__).resolve())
        for m in list(sys.modules.values()) if getattr(m,'__file__',None) and Path(m.__file__).resolve().is_relative_to(R)
        and Path(m.__file__).suffix=='.py'}
    w.write(out/'activation.json',dict(rows=rows,LL_cap=cap,CPU_cap=600,wall_cap=900,array_estimate_bytes=estimate,
        process_RSS_cap=1536*1024**2,inputs_sha256=bindings,source_sha256=modules,
        source_file_sha256=w.sha(Path(__file__)),mixture_weights=[.25,.5,.25],all500_retained=True,
        scope='Known nuisance conditional analyses. All frequencies combined before mixing global distance scale. No latent generating scale read.'))
    (out/'source.py').write_bytes(Path(__file__).read_bytes())
    status='FAILED';error=None;reports=[]
    try:
        with np.load(H/'prepared/response_atlas.npz') as f:atlas={k:f[k] for k in f.files}
        u=atlas['fine_u'];control_u=atlas['control_u'];ci=atlas['coarse_indices']
        config=read(R/'tmp/c09_nominal14_v4/config.json');e=w.experiment(read(R/config['experiment_config']))
        table=w.load_table(R/config['table_file'],config['table_sha256'],guard,expected_shape=(8336,4,12,12));anchor=table(np.array([.5]))[0]
        datafile=R/'tmp/c09_production_v1/generation/stage_6.npz';bindings[str(datafile.relative_to(R))]=w.sha(datafile)
        with np.load(datafile) as f:
            assert f['ids'].tolist()==[r['id'] for r in registered]
            data={k:f[k] for k in ('q','x_physical','x_gaussian')}
        group=w.KernelGroup(rows,data,covariance=w.ScenarioCovariance(e,rows[0]['eta_physical_coordinates'],ratio=0.),
            moments=lambda c:w.quadratic_moments(c,e['H']),weights=e['weights'],anchor_gamma=anchor,budget=budget)
        names=[r['curve_id'] for r in rows]
        components=np.empty((3,len(u),len(rows)));controls=np.empty((3,len(control_u),len(rows)));checks=[]
        for scale_index,scale in enumerate((.9,1.,1.1)):
            for kind,points,destination in [('fine',u,components),('controls',control_u,controls)]:
                for first in range(0,len(points),32):
                    batch=points[first:first+32]
                    gamma=table(batch) if scale==1. else atlas['Gamma_'+kind][0 if scale==.9 else 1,first:first+len(batch)]
                    values=group.evaluate_gamma(gamma,names,reason='grid' if kind=='fine' else 'backend_check')
                    destination[scale_index,first:first+len(batch)]=np.column_stack([values[n] for n in names])
            for j,row in enumerate(rows):
                for i in (0,len(control_u)//2,len(control_u)-1):
                    gamma=table(control_u[i:i+1])[0] if scale==1. else atlas['Gamma_controls'][0 if scale==.9 else 1,i]
                    reservation=budget.reserve([row['curve_id']],1,reason='scipy_reference');success=False
                    try:value=scipy_loglike(group,row,gamma,e['H'],anchor);success=True
                    finally:budget.complete(reservation,success=success)
                    checks.append(dict(curve=row['curve_id'],scale=scale,u=float(control_u[i]),delta=float(abs(value-controls[scale_index,i,j]))))
            np.savez_compressed(out/f'component_{scale_index}.npz',u=u,log_likelihood=components[scale_index],control_u=control_u,
                control_log_likelihood=controls[scale_index],curves=np.array(names))
            assert (out/f'component_{scale_index}.npz').stat().st_size<90*1024**2
            print(json.dumps(dict(component=scale,CPU=time.process_time()-start,LL=budget.charged)),flush=True)
        w.write(out/'scipy_checks.json',checks)
        scipy_by_curve={n:0. for n in names}
        for check in checks:scipy_by_curve[check['curve']]=max(scipy_by_curve[check['curve']],check['delta'])
        mixture=logsumexp(components+np.log([.25,.5,.25])[:,None,None],axis=0)
        mixture_controls=logsumexp(controls+np.log([.25,.5,.25])[:,None,None],axis=0)
        for mode,values,oracle in [('correct_mixture',mixture,mixture_controls),('nominal_scale_only',components[1],controls[1])]:
            for model in models:
                selected=[i for i,r in enumerate(rows) if r['analysis']==model];assert len(selected)==500
                fine=w.MassPosteriorBatch(u,values[:,selected]);coarse=w.MassPosteriorBatch(u[ci],values[ci][:,selected])
                q,qc=fine.quantile_brackets(),coarse.quantile_brackets();wf,wc=fine.wasserstein_bounds(),coarse.wasserstein_bounds()
                cuts=np.unique(np.r_[np.linspace(0,1,101),control_u])
                cdf_delta=np.max(abs(fine.cdf(cuts)-coarse.cdf(cuts)),axis=0)
                heldout=np.max(abs(fine.interpolator(np.arcsin(control_u))+fine.shift-oracle[:,selected]),axis=0)
                for j,index in enumerate(selected):
                    row=rows[index];delta={k:float(abs(fine.summary[k][j]-coarse.summary[k][j])) for k in fine.summary}
                    delta['CDF']=float(cdf_delta[j]);delta['W1']=float(max(abs(wf['upper'][j]-wc['lower'][j]),abs(wc['upper'][j]-wf['lower'][j])))
                    qlo=np.minimum(q['lower'][:,j],qc['lower'][:,j]);qhi=np.maximum(q['upper'][:,j],qc['upper'][:,j])
                    mesh=all(v <= (.002 if k=='CDF' else .001) for k,v in delta.items()) and np.max(qhi-qlo)<=.001
                    reports.append(dict(curve_id=row['curve_id']+'__'+mode,datum_id=row['datum_id'],analysis=model,mode=mode,
                        summary={k:float(v[j]) for k,v in fine.summary.items()},delta=delta,
                        quantile_probabilities=q['probabilities'].tolist(),quantile_lower=qlo.tolist(),quantile_upper=qhi.tolist(),
                        W1=[float(wf['lower'][j]),float(wf['upper'][j])],heldout_logL_delta=float(heldout[j]),
                        scipy_delta=scipy_by_curve[row['curve_id']],mesh_passed=bool(mesh),
                        heldout_passed=bool(heldout[j]<=.001),scipy_passed=scipy_by_curve[row['curve_id']]<=1e-8,
                        mass_PIT=None,logL_event=None,calibration_complete=False))
                guard.check();w.write(out/'posteriors.json',reports)
                print(json.dumps(dict(mode=mode,model=model,recorded=len(reports),CPU=time.process_time()-start)),flush=True)
        assert len(reports)==3000
        status='COMPLETED_WITH_PER_CASE_GATES'
    except Exception:error=traceback.format_exc();print(error,flush=True)
    finally:
        rss=w.resource.getrusage(w.resource.RUSAGE_SELF).ru_maxrss
        if sys.platform!='darwin':rss*=1024
        w.write(out/'receipt.json',dict(status=status,error=error,budget=budget.report(),CPU=time.process_time()-start,
            wall=time.monotonic()-wall,peak_RSS_bytes=rss,recorded_posteriors=len(reports),
            mesh_passed=sum(r['mesh_passed'] for r in reports),heldout_passed=sum(r['heldout_passed'] for r in reports),
            all_gates_passed=sum(r['mesh_passed'] and r['heldout_passed'] and r['scipy_passed'] for r in reports),
            inputs_sha256=bindings,calibration_complete=False,C09_complete=False))
    if error:raise SystemExit(1)
if __name__=='__main__':main()
