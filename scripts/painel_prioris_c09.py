"""Frozen paired prior panel: first32 core-U observations, ten models, five measures.

Uses cached likelihoods only. Reweighted priors are sensitivity analyses, not SBC.
"""
from pathlib import Path
import hashlib
import json
import resource
import sys
import time

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
import numpy as np
from inference.mass_batch import MassPosteriorBatch


def prior_cdf(u,kind,lower):
    if kind=='uniform_u':return u
    if kind=='uniform_u_squared':return u*u
    return np.log(u/lower)/np.log(1/lower)


def main():
    start=time.process_time();bindings={}

    def bind(path):
        bindings[str(path.relative_to(ROOT))]=hashlib.sha256(path.read_bytes()).hexdigest()
        return path

    def read(path):
        return json.loads(bind(path).read_text())

    bind(Path(__file__));bind(ROOT/'src/inference/mass_batch.py')
    config=read(ROOT/'configs/robustness/c09_production_v1.json')
    ids=config['paired_prior_sensitivity']['datum_ids']
    assert ids==list(range(32))
    kinds=[('uniform_u',0.),('uniform_u_squared',0.),('log_uniform_u',.001)]
    kinds += [('log_uniform_u',cut) for cut in config['paired_prior_sensitivity']['extra_log_cutoffs']]
    base=ROOT/'tmp/c09_nominal_production_v1'
    plan=read(base/'plan.json')
    job=next(j for j in plan['jobs'] if j['job_id']=='nominal_00')
    execution=base/'execution/nominal_00'
    receipt=read(execution/'receipt.json')
    assert receipt['recorded_posteriors']==5000 and receipt['finite_backend_passed']==5000
    with np.load(bind(base/'grids.npz')) as grid:
        coarse=grid['coarse_u']
    with np.load(bind(execution/'likelihoods.npz')) as cache:
        u=cache['u'];ell=cache['log_likelihood'];names=cache['curve_ids'].tolist()
    assert names==[r['curve_id'] for r in job['curves']]
    records=[];contrasts=[]
    for model in config['core_models']:
        indices=[i for i,r in enumerate(job['curves']) if r['analysis']==model and r['datum_id'] in ids]
        assert [job['curves'][i]['datum_id'] for i in indices]==ids
        for i in indices:
            evidence=read(execution/'backend_checks'/(names[i]+'.json'))
            assert evidence['accepted_finite_domain']
        baseline=None
        for kind,lower in kinds:
            keep=u>=lower;v=u[keep];values=ell[keep][:,indices]
            cv=coarse[coarse>=lower];ci=np.searchsorted(v,cv)
            assert v[0]==lower and np.array_equal(v[ci],cv)
            fine=MassPosteriorBatch(v,values,prior=kind,lower=lower)
            rough=MassPosteriorBatch(cv,values[ci],prior=kind,lower=lower)
            q,qr=fine.quantile_brackets(),rough.quantile_brackets()
            w,wr=fine.wasserstein_bounds(),rough.wasserstein_bounds()
            cuts=np.unique(np.r_[np.linspace(lower,1,2049),fine.prior_ppf(np.linspace(0,1,2049)),.2])
            cuts=np.clip(cuts,lower,1)
            F,Fr=fine.cdf(cuts),rough.cdf(cuts)
            prior=prior_cdf(cuts,kind,lower)
            sup_lo=np.max(abs(F-prior[:,None]),axis=0)
            sup_hi=np.max(np.maximum(abs(F[1:]-prior[:-1,None]),abs(F[:-1]-prior[1:,None])),axis=0)
            mass=fine.cdf(np.array([.2]))[0]
            pm=float(prior_cdf(np.array([.2]),kind,lower)[0])
            assert 0<pm<1 and np.all((mass>0)&(mass<1))
            odds=(mass/(1-mass))/(pm/(1-pm))
            qlo=np.minimum(q['lower'],qr['lower']);qhi=np.maximum(q['upper'],qr['upper'])
            label=kind if kind!='log_uniform_u' else f'log_uniform_u_{lower:g}'
            for j,datum in enumerate(ids):
                delta={k:float(abs(fine.summary[k][j]-rough.summary[k][j])) for k in fine.summary}
                delta['CDF']=float(np.max(abs(F[:,j]-Fr[:,j])))
                delta['W1']=float(max(abs(w['upper'][j]-wr['lower'][j]),abs(wr['upper'][j]-w['lower'][j])))
                passed=all(value<=(.002 if k=='CDF' else .001) for k,value in delta.items()) and np.max(qhi[:,j]-qlo[:,j])<=.001
                records.append(dict(model=model,datum_id=datum,prior=label,lower=lower,
                    summary={k:float(value[j]) for k,value in fine.summary.items()},
                    variance=float(fine.summary['second'][j]-fine.summary['mean'][j]**2),
                    quantile_probabilities=q['probabilities'].tolist(),quantile_lower=qlo[:,j].tolist(),quantile_upper=qhi[:,j].tolist(),
                    W1=[float(w['lower'][j]),float(w['upper'][j])],sup_CDF_difference=[float(sup_lo[j]),float(sup_hi[j])],
                    prior_probability_u_le_02=pm,posterior_probability_u_le_02=float(mass[j]),posterior_to_prior_odds=float(odds[j]),
                    mesh_deltas=delta,mesh_passed=bool(passed),SBC=False))
            if baseline is None:
                baseline=dict(lower=qlo.copy(),upper=qhi.copy(),mean=fine.summary['mean'].copy(),KL=fine.summary['KL'].copy())
            else:
                for j,datum in enumerate(ids):
                    contrasts.append(dict(model=model,datum_id=datum,prior=label,reference='uniform_u',
                        quantile_delta_lower=(qlo[:,j]-baseline['upper'][:,j]).tolist(),
                        quantile_delta_upper=(qhi[:,j]-baseline['lower'][:,j]).tolist(),
                        mean_delta=float(fine.summary['mean'][j]-baseline['mean'][j]),
                        KL_delta=float(fine.summary['KL'][j]-baseline['KL'][j]),SBC=False))
        print(model,flush=True)
    assert len(records)==1600 and len(contrasts)==1280
    rss=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    if sys.platform!='darwin':rss*=1024
    out=ROOT/'results/C09/paired_prior_panel'
    out.mkdir(parents=True,exist_ok=False)
    for name,value in [('posteriors',records),('contrasts',contrasts)]:
        (out/(name+'.json')).write_text(json.dumps(value,indent=2,allow_nan=False)+'\n')
    audit=dict(schema='C09_PAIRED_PRIOR_PANEL_v1',posteriors=1600,contrasts=1280,
        mesh_passed=sum(r['mesh_passed'] for r in records),new_observations=0,new_likelihood_values=0,new_ORFs=0,
        CPU=time.process_time()-start,peak_RSS_bytes=rss,resource_passed=rss<=1536*1024**2,
        inputs_sha256=bindings,output_sha256={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in out.glob('*.json')},
        scope='Paired sensitivity only. Includes320 existing uniform-prior posteriors recomputed from cache, not1600 new independent analyses. CDF envelopes concern normalized positive tables and exclude physical backend error. No independent adaptive validation of extra logarithmic cutoffs claimed.',
        SBC=False,C09_complete=False)
    (out/'audit.json').write_text(json.dumps(audit,indent=2,allow_nan=False)+'\n')
    print(json.dumps({k:v for k,v in audit.items() if k not in ('inputs_sha256','output_sha256')}))


if __name__=='__main__':main()
