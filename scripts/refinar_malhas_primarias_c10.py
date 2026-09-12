"""Two selected high/product controls, with exact reuse and fixed file reservation."""
from pathlib import Path
import argparse
import json
import math
import resource
import time
import numpy as np
import refinar_fatias_piloto_c10 as base
from ledger import GlobalLedger
from nodal_runner import ReuseSource
from persistent_grid import run_grid_preserved
from references import summary,compare_summaries,product_log_evidence

R,P,S=base.R,base.P,base.S
O=R/'tmp/c10_primary_grid_refinement_v1'
TARGETS=[dict(label='A_CN',model='A_CN',route='D',id=9),dict(label='C_full_G',model='B_G',route='C_full',id=14)]


def freeze():
    inputs={}
    def bind(path):inputs[str(path.relative_to(R))]=base.sha(path);return base.read(path)
    spec=bind(S/'execution_spec.json');axes=bind(S/'axes.json')
    for name,digest in spec['source_sha256'].items():
        assert base.sha(R/name)==digest,name
        inputs[name]=digest
    audit=bind(R/'results/C10/event_refinement_audit/audit.json')
    assert audit['cumulative_logL_values']==13607708
    bind(R/'results/C10/event_refinement_resource_review/audit.json')
    for path in (P/'nodal_component.npz',P/'generation.npz',P/'truth_logL.npy',Path(__file__),Path(base.__file__)):
        inputs[str(path.relative_to(R))]=base.sha(path)
    for path in (R/spec['protocol']['path'],R/'configs/experiments/c06_moments.json',P/'nodal_posterior_summaries.json'):
        bind(path)
    for item in TARGETS:
        path=P/f'{item["route"]}_fine.npy';inputs[str(path.relative_to(R))]=base.sha(path)
        state=bind(path.with_suffix('.state.json'));assert state['status']=='COMPLETE' and state['sha256']==base.sha(path)
    cap=2*((513*257-257*129)+386*98)+6
    assert cap==273038
    plan=dict(schema='C10_TWO_PRIMARY_GRID_REFINEMENTS_v1',targets=TARGETS,inputs=inputs,
              historical_values=13607708,additional_values_cap=cap,cumulative_values_cap=13607708+cap,
              CPU_seconds_cap=120,maximum_RSS_bytes=4*1024**3,maximum_output_bytes=16*1024**2,
              reservation='Reserve 8 MiB per target before any new evaluation, including arrays, receipts and final metadata.',
              new_ORFs=0,new_observations=0,scope='Two finite grid controls, not full scalar or population validation.')
    O.mkdir(exist_ok=False);(O/'plan.json').write_text(json.dumps(plan,indent=2,allow_nan=False)+'\n')
    print(json.dumps({k:v for k,v in plan.items() if k!='inputs'}))


def execute():
    started=time.process_time();plan=base.read(O/'plan.json')
    for name,digest in plan['inputs'].items():assert base.sha(R/name)==digest,name
    resource.setrlimit(resource.RLIMIT_CPU,(math.ceil(started)+120,math.ceil(started)+121))
    def disk(reserve=0):
        size=sum(p.stat().st_size for p in O.rglob('*') if p.is_file())
        if size+reserve>plan['maximum_output_bytes']:raise RuntimeError('Disk reservation unavailable')
        return size
    def guard():
        rss=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*(1 if base.sys.platform=='darwin' else 1024)
        if rss>plan['maximum_RSS_bytes'] or time.process_time()-started>120:raise RuntimeError('CPU/RSS allowance exhausted')
    # The entire finite set of arrays is known before scoring: <3 MiB.
    # Reserve 8 MiB for BOTH target arrays and 4 MiB for terminal metadata now.
    disk(reserve=12*1024**2)
    ledger=GlobalLedger(O/'ledger.json',identity=base.sha(O/'plan.json'),
                        allocations={'bridges':6,'high':197376,'product':75656},
                        maximum_values=273038,maximum_cpu_seconds=120)
    spec=base.read(S/'execution_spec.json');axes=base.read(S/'axes.json');geometry=base.load_geometry(R,spec)
    with np.load(P/'nodal_component.npz') as f:
        provider=base.NodalCovariances(f['masses'],f['gamma'],geometry,
                                      base.read(R/spec['protocol']['path']),base.read(R/'configs/experiments/c06_moments.json'))
    with np.load(P/'generation.npz') as f:data=tuple(f[k] for k in ('q','x','g'));truth=f['truth']
    truthLL=np.load(P/'truth_logL.npy');labels=sum((list(base.LABELS[r]) for r in base.ROUTES),[])
    master_u=np.array(axes['master_mass_nodes']);master_e=np.array(axes['master_epsilon_nodes'])
    product_u=np.r_[.001,axes['u_reference']['384']['nodes'],1.]
    product_e=np.r_[0.,axes['epsilon_product_reference']['nodes'],1.]
    old_summaries=base.read(P/'nodal_posterior_summaries.json');results={}
    try:
        for item in plan['targets']:
            guard();disk(reserve=8*1024**2)
            route=item['route'];model=item['model'];i=item['id'];label=item['label'];name=f'{label}_d{i}'
            state=base.read(P/f'{route}_fine.state.json');identity=state['identity']
            assert identity==dict(nodal_component_sha256=base.sha(P/'nodal_component.npz'),kernel_sha256=spec['selected_kernel_sha256'],
                                  generation_sha256=base.sha(P/'generation.npz'),fixed_nuisance_sha256=spec['protocol']['sha256'],response=route,harmonic_level='H11')
            stored=np.load(P/f'{route}_fine.npy',mmap_mode='r');m=state['models'].index(model);column=state['data_ids'].index(i)
            old=stored[:,:,m:m+1,column:column+1]
            engine=base.engine_for(data,geometry,[i])
            for a,b in ((0,0),(128,64),(256,128)):
                c0,c1=provider(master_u[::2][a],route,2)
                checked=ledger.evaluate('bridges',1,lambda:engine.evaluate(c0,c1,[master_e[::2][b]],models=(model,))[0][0,0,0])
                assert abs(checked-old[a,b,0,0])<=1e-10
            reuse=ReuseSource(master_u[::2],master_e[::2],old,identity,(i,),(model,))
            def covariance(u):guard();return provider(u,route,2)
            common=dict(models=(model,),data_ids=(i,),identity=identity,ledger=ledger,
                        maximum_workspace_bytes=512*1024**2,additional_resident_bytes=provider.gamma.nbytes)
            high,hr=run_grid_preserved(engine,covariance,master_u,master_e,stage='high',output_path=O/f'{name}_high.npy',reuse=reuse,**common)
            base.save(O/f'{name}_high_receipt.json',hr)
            product,pr=run_grid_preserved(engine,covariance,product_u,product_e,stage='product',output_path=O/f'{name}_product.npy',**common)
            base.save(O/f'{name}_product_receipt.json',pr)
            col=labels.index(label)
            hi=summary(master_u,master_e,high.values[:,:,0,0],truth[i],truthLL[2,i,col])
            independent=summary(product_u,product_e,product.values[:,:,0,0],truth[i],truthLL[2,i,col])
            z,h0=product_log_evidence(product.values[1:-1,1:-1,0,0],product.values[1:-1,0,0,0],
                                      axes['u_reference']['384']['prior_weights'],axes['epsilon_product_reference']['prior_weights'])
            historical=old_summaries[f'{label}:{i}']
            row=dict(original=historical,high=hi,independent=independent,high_gates=compare_summaries(historical['fine'],hi),
                     independent_gates=compare_summaries(hi,independent),direct_product_logZ=z,direct_product_H0=h0,
                     direct_product_Z_gate=abs(z-hi['logZ_H1'])<=.001,direct_product_H0_gate=abs(h0-hi['logZ_H0'])<=.001,
                     cached_values_reused=hr['values_reused_exact_identity'])
            required=('logZ_H0','logZ_H1','logBF','parameter_CDF','quantiles','logL_CDF')
            row['finite_grid_controls_pass']=all(row[g][k] is True for g in ('high_gates','independent_gates') for k in required) and row['direct_product_Z_gate'] and row['direct_product_H0_gate']
            results[f'{label}:{i}']=row;base.save(O/f'{name}_summary.json',row)
            disk(reserve=1024**2)
    except Exception as exc:
        base.save(O/'FAILED_PRESERVED.json',dict(reason=type(exc).__name__+': '+str(exc),charged=ledger.state['charged']))
        raise
    assert ledger.state['charged']==ledger.state['completed']
    charged=sum(ledger.state['charged'].values());assert charged==273038
    result=dict(status='SELECTED_GRID_CONTROLS_COMPLETE',results=results,charged_new_values=charged,
                cumulative_values=plan['historical_values']+charged,CPU=time.process_time()-started,
                output_bytes_before_terminal=disk(reserve=1024**2),new_ORFs=0,new_observations=0,
                C10_complete=False,production_authorized=False,plan_sha256=base.sha(O/'plan.json'))
    base.save(O/'complete.json',result);disk()
    print(json.dumps({k:v for k,v in result.items() if k!='results'}))
    print(json.dumps({k:r['finite_grid_controls_pass'] for k,r in results.items()}))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--execute',action='store_true')
    execute() if p.parse_args().execute else freeze()
