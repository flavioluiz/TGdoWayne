"""Memory-bounded posterior recovery from completed components; no likelihood evaluation."""
from pathlib import Path
import json,hashlib,sys,time,resource
import numpy as np
from scipy.special import logsumexp
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'src'))
from inference.mass_batch import MassPosteriorBatch


def main():
    base=R/'tmp/c09_distance_production_v1';source=base/'execution';out=base/'posterior_recovery';out.mkdir(exist_ok=False)
    read=lambda p:json.loads(p.read_text())
    receipt=read(source/'receipt.json');assert receipt['budget']['additional_charged_values']==12145500 and receipt['budget']['failed_reserved_values']==0
    assert (source/'scipy_checks.json').exists()
    bindings={str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest() for p in
        [Path(__file__),R/'src/inference/mass_batch.py',source/'receipt.json',source/'activation.json',source/'scipy_checks.json']+
        [source/f'component_{i}.npz' for i in range(3)]}
    checks=read(source/'scipy_checks.json');scipy_error={}
    for r in checks:scipy_error[r['curve']]=max(scipy_error.get(r['curve'],0),r['delta'])
    assert len(checks)==13500 and len(scipy_error)==1500
    with np.load(base/'prepared/response_atlas.npz') as f:ci=f['coarse_indices']
    start=time.process_time();reports=[]
    def guard():
        rss=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*(1 if sys.platform=='darwin' else 1024)
        if rss>1536*1024**2 or time.process_time()-start>180:raise RuntimeError('Recovery resource cap')
    (out/'activation.json').write_text(json.dumps(dict(inputs_sha256=bindings,CPU_cap=180,RSS_cap=1536*1024**2,
        array_estimate_bytes=400*1024**2,new_likelihood_values=0,new_ORFs=0,previous_failure_preserved=True),indent=2)+'\n')
    for model in ('A0_CN','B_CN_full_variable','B_G_full_variable'):
        component=[];controls=[];names=None
        for i in range(3):
            with np.load(source/f'component_{i}.npz') as f:
                allnames=f['curves'].tolist();selected=[j for j,n in enumerate(allnames) if n.endswith('__'+model)]
                assert len(selected)==500
                if names is None:names=[allnames[j] for j in selected]
                else:assert names==[allnames[j] for j in selected]
                u=f['u'];cu=f['control_u'];component.append(f['log_likelihood'][:,selected]);controls.append(f['control_log_likelihood'][:,selected])
        mixture=logsumexp(np.array(component)+np.log([.25,.5,.25])[:,None,None],axis=0)
        mc=logsumexp(np.array(controls)+np.log([.25,.5,.25])[:,None,None],axis=0)
        for mode,values,oracle in [('correct_mixture',mixture,mc),('nominal_scale_only',component[1],controls[1])]:
            guard();fine=MassPosteriorBatch(u,values);coarse=MassPosteriorBatch(u[ci],values[ci])
            q,qc=fine.quantile_brackets(),coarse.quantile_brackets();wf,wc=fine.wasserstein_bounds(),coarse.wasserstein_bounds()
            cuts=np.unique(np.r_[np.linspace(0,1,101),cu]);cd=np.max(abs(fine.cdf(cuts)-coarse.cdf(cuts)),axis=0)
            hd=np.max(abs(fine.interpolator(np.arcsin(cu))+fine.shift-oracle),axis=0)
            for j,name in enumerate(names):
                delta={k:float(abs(fine.summary[k][j]-coarse.summary[k][j])) for k in fine.summary}
                delta['CDF']=float(cd[j]);delta['W1']=float(max(abs(wf['upper'][j]-wc['lower'][j]),abs(wc['upper'][j]-wf['lower'][j])))
                lo=np.minimum(q['lower'][:,j],qc['lower'][:,j]);hi=np.maximum(q['upper'][:,j],qc['upper'][:,j])
                passed=all(v<=(.002 if k=='CDF' else .001) for k,v in delta.items()) and np.max(hi-lo)<=.001
                reports.append(dict(curve_id=name+'__'+mode,datum_id=j,analysis=model,mode=mode,
                    summary={k:float(v[j]) for k,v in fine.summary.items()},delta=delta,
                    quantile_probabilities=q['probabilities'].tolist(),quantile_lower=lo.tolist(),quantile_upper=hi.tolist(),
                    W1=[float(wf['lower'][j]),float(wf['upper'][j])],heldout_logL_delta=float(hd[j]),
                    scipy_delta=scipy_error[name],mesh_passed=bool(passed),heldout_passed=bool(hd[j]<=.001),
                    scipy_passed=scipy_error[name]<=1e-8,mass_PIT=None,logL_event=None,calibration_complete=False))
            (out/'posteriors.json').write_text(json.dumps(reports,indent=2,allow_nan=False)+'\n');guard()
            print(model,mode,len(reports),flush=True)
            del fine,coarse
    assert len(reports)==3000 and len({r['curve_id'] for r in reports})==3000
    rss=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*(1 if sys.platform=='darwin' else 1024)
    summary=dict(status='COMPLETED_FROM_CACHED_COMPONENTS',posteriors=3000,CPU=time.process_time()-start,peak_RSS_bytes=rss,
        new_likelihood_values=0,new_ORFs=0,cumulative_C09=67017097,
        mesh_passed=sum(r['mesh_passed'] for r in reports),heldout_passed=sum(r['heldout_passed'] for r in reports),
        scipy_passed=sum(r['scipy_passed'] for r in reports),
        all_gates_passed=sum(r['mesh_passed'] and r['heldout_passed'] and r['scipy_passed'] for r in reports),
        groups=[dict(model=m,mode=mode,mesh_passed=sum(r['mesh_passed'] for r in reports if r['analysis']==m and r['mode']==mode),
            heldout_passed=sum(r['heldout_passed'] for r in reports if r['analysis']==m and r['mode']==mode))
            for m in ('A0_CN','B_CN_full_variable','B_G_full_variable') for mode in ('correct_mixture','nominal_scale_only')],
        calibration_complete=False,C09_complete=False)
    (out/'receipt.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary),flush=True)
if __name__=='__main__':main()
