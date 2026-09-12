"""Independent adaptive references for the refined omission and extra prior cutoffs."""
from pathlib import Path
import argparse, hashlib, json, sys, time, traceback
import executar_lote_nominal_c09 as worker
import numpy as np
from priors import PriorMeasure
from reference_runtime import integrate_reference_bundle, conservative_quantile_gate

ROOT=worker.ROOT
sys.path.insert(0,str(ROOT/'tmp/c09_D3_w1_v1'))
from reference import integrate as integrate_w1


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--target',required=True,choices=['refined']+[f'd{d}_{m}' for d in (0,31) for m in ('A0_CN','B_CN_full_variable','B_G_full_variable')])
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();out=args.output;out.mkdir(parents=True,exist_ok=False)
    start=time.process_time();wall=time.monotonic();bindings={}

    def read(path):
        bindings[str(path.relative_to(ROOT))]=worker.sha(path)
        return json.loads(path.read_text())

    if args.target=='refined':
        base=ROOT/'tmp/c09_nominal_refinement_v1'
        job=read(base/'plan.json')['jobs'][0];row=job['curves'][0]
        execution=base/'execution'/job['job_id']
        records=read(execution/'posteriors.json')
        specs=[('uniform_u',0.)]
    else:
        datum,model=args.target.split('_',1);datum=int(datum[1:])
        base=ROOT/'tmp/c09_nominal_production_v1'
        job=read(base/'plan.json')['jobs'][0]
        row=next(r for r in job['curves'] if r['datum_id']==datum and r['analysis']==model)
        execution=base/'execution'/job['job_id']
        panel=read(ROOT/'results/C09/paired_prior_panel/posteriors.json')
        records=[next(r for r in panel if r['datum_id']==datum and r['model']==model and r['lower']==lower) for lower in (.0001,.01)]
        specs=[('log_uniform_u',.0001),('log_uniform_u',.01)]
    evidence=read(execution/'backend_checks'/(row['curve_id']+'.json'))
    assert evidence['accepted_finite_domain']
    path=execution/'likelihoods.npz';bindings[str(path.relative_to(ROOT))]=worker.sha(path)
    with np.load(path) as saved:
        column=saved['curve_ids'].tolist().index(row['curve_id'])
        u=saved['u'];ell=saved['log_likelihood'][:,column]
    shift=float(ell.max())
    priors=[PriorMeasure(kind,lower,1.) for kind,lower in specs]
    cuts=[np.unique(np.r_[p.lower, p.upper,.2,r['quantile_lower'],r['quantile_upper']]) for p,r in zip(priors,records)]
    worker.write(out/'cuts.json',[c.tolist() for c in cuts])
    row['additional_likelihood_cap']=50000

    class Guard:
        config={'estimated_numeric_bytes':1024**3}
        def check(self):
            rss=worker.resource.getrusage(worker.resource.RUSAGE_SELF).ru_maxrss
            if sys.platform!='darwin':rss*=1024
            if time.process_time()-start>120 or time.monotonic()-wall>180:raise RuntimeError('Reference time cap')
            if rss>1536*1024**2:raise MemoryError('Reference RSS cap')

    guard=Guard();budget=worker.Budget([row],additional_cap=50000,historical_values=54787607,checkpoint=guard.check)
    sources=[Path(__file__),Path(worker.__file__),ROOT/'tmp/c09_D3_w1_v1/reference.py',
             ROOT/'tmp/c09_D2_continuation_v3/reference_runtime.py',ROOT/'tmp/c09_D2_components_v1/priors.py']
    for path in sources:bindings[str(path.relative_to(ROOT))]=worker.sha(path)
    worker.write(out/'activation.json',dict(target=args.target,row=row,priors=specs,CPU_cap=120,wall_cap=180,
        LL_cap=50000,inputs_sha256=bindings,scope='Finite-response adaptive primary and W1 references; no new observation or ORF'))
    (out/'source.py').write_bytes(Path(__file__).read_bytes())
    cache={};reports=[];status='FAILED';error=None
    try:
        config=read(ROOT/'tmp/c09_nominal14_v4/config.json')
        e=worker.experiment(read(ROOT/config['experiment_config']))
        table=worker.load_table(ROOT/config['table_file'],config['table_sha256'],guard,expected_shape=(8336,4,12,12))
        anchor=table(np.array([.5]))[0]
        datapath=ROOT/'tmp/c09_production_v1/generation'/row['file'];bindings[str(datapath.relative_to(ROOT))]=worker.sha(datapath)
        with np.load(datapath) as f:
            assert str(f['ids'][row['data_id']])==row['observation_id']
            data={k:f[k] for k in ('q','x_physical','x_gaussian')}
        group=worker.KernelGroup([row],data,covariance=worker.ScenarioCovariance(e,row['eta_physical_coordinates'],
            kind='monopole_rank1',ratio=row['analysis_contaminant_ratio']),moments=lambda c:worker.quadratic_moments(c,e['H']),
            weights=e['weights'],anchor_gamma=anchor,budget=budget)
        name=row['curve_id']
        def direct(value):
            value=float(value);key=value.hex()
            if key not in cache:
                cache[key]=float(group.evaluate_gamma(table(np.array([value])),[name],reason='functional_reference')[name][0])
            return cache[key]
        bridges=[]
        for i in (0,len(u)//2,len(u)-1):
            delta=abs(direct(u[i])-ell[i]);assert delta<=1e-10
            bridges.append(dict(u=float(u[i]),delta=delta))
        worker.write(out/'cache_identity_bridges.json',bridges)
        primary=integrate_reference_bundle(lambda points:np.array([direct(v) for v in points]),priors,cuts,shift=shift,
            on_panel=lambda p:worker.write(out/'panels'/f"{p['panel_index']}.json",p))
        worker.write(out/'primary.json',primary)
        z=np.array([r['denominator'] for r in primary['results']]);ez=np.array([r['denominator_error_estimate'] for r in primary['results']])
        def likelihood_columns(points):return np.array([[direct(v)]*len(priors) for v in points])
        wrefs=[]
        for i,(rtol,step) in enumerate(((1e-8,.01),(1e-9,.005))):
            wref=integrate_w1(likelihood_columns,priors,z,ez,shift=np.full(len(priors),shift),cuts=cuts,
                rtol=rtol,atol=rtol*.01,max_step=step,checkpoint=guard.check)
            worker.write(out/f'W1_reference_{i}.json',wref);wrefs.append(wref)
        for j,(record,ref,c) in enumerate(zip(records,primary['results'],cuts)):
            deltas={key:abs(record['summary'][key]-ref[old]) for key,old in [('logZ','logZ'),('mean','mean'),('second','second'),('KL','kl_to_prior')]}
            deltas['logZ']+=ref['logZ_error_estimate'];deltas['KL']+=ref['kl_error_estimate']
            deltas['mean']+=ref['normalized_moment_errors'][0];deltas['second']+=ref['normalized_moment_errors'][1]
            intervals=np.array(ref['cdf_intervals']);qpass=[]
            keep=u>=priors[j].lower
            posterior=worker.MassPosteriorBatch(u[keep],ell[keep,None],prior=priors[j].kind,lower=priors[j].lower)
            fc=posterior.cdf(c)[:,0];rc=np.array(ref['cdf'])
            deltas['CDF']=float(np.max(abs(fc-rc)+np.maximum(rc-intervals[:,0],intervals[:,1]-rc)))
            for q,lo,hi in zip(record['quantile_probabilities'],record['quantile_lower'],record['quantile_upper']):
                il,ih=np.searchsorted(c,[lo,hi]);qpass.append(conservative_quantile_gate(q,lo,hi,intervals[il],intervals[ih]))
            w0,w1=[wr['results'][j] for wr in wrefs]
            deltas['W1']=max(abs(v-w1['W1']) for v in record['W1'])+abs(w1['W1']-w0['W1'])+w1['normalizer_uncertainty_sensitivity']
            deltas['CDF_ODE']=float(np.max(abs(np.array(w1['cdf'])-ref['cdf'])))
            passed=all(v<=(.002 if k in ('CDF','CDF_ODE') else .001) for k,v in deltas.items()) and all(qpass) and w1['normalization_relative_discrepancy']<=.001
            reports.append(dict(prior=specs[j],delta=deltas,quantiles_passed=qpass,passed=bool(passed),
                independent_W1=w1['W1'],ODE_normalization_delta=w1['normalization_relative_discrepancy']))
        worker.write(out/'comparisons.json',reports);status='COMPLETED_WITH_GATES'
    except Exception:
        error=traceback.format_exc();print(error,flush=True)
    finally:
        values=sorted((float.fromhex(k),v) for k,v in cache.items())
        np.savez_compressed(out/'reference_cache.npz',u=np.array([v[0] for v in values]),log_likelihood=np.array([v[1] for v in values]))
        worker.write(out/'receipt.json',dict(status=status,error=error,budget=budget.report(),CPU=time.process_time()-start,
            wall=time.monotonic()-wall,passed=sum(r['passed'] for r in reports),results=len(reports),inputs_sha256=bindings,C09_complete=False))
    if error:raise SystemExit(1)
    print(json.dumps(dict(target=args.target,passed=sum(r['passed'] for r in reports),results=len(reports),LL=budget.charged)),flush=True)


if __name__=='__main__':main()
