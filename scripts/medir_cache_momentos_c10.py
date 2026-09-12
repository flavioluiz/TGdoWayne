"""Paired analytic replay benchmark, requiring zero new likelihood values."""
from pathlib import Path
import argparse
import json
import math
import resource
import sys
import time
import numpy as np
import refinar_fatias_piloto_c10 as base
sys.path.insert(0,str(base.R/'tmp/c10_nested_quadrature_v1'))
from nested_event import reference_slice
from c10_taylor_adapter import TaylorEvent
from c10_memoized_kernel import MemoizedLikelihood
from pta.moment_cache import MomentCache
from harmonic_margin import polynomial_pair,uniform_loglike_difference,event_level
R,P,S=base.R,base.P,base.S
B=R/'tmp/c10_nested_integral_validation_v1'
O=R/'results/C10/moment_cache_benchmark'


def freeze():
    inputs={}
    def bind(p):inputs[str(p.relative_to(R))]=base.sha(p);return base.read(p)
    spec=bind(S/'execution_spec.json');axes=bind(S/'axes.json');done=bind(B/'complete.json')
    assert done['visited']==18468 and done['stop']=='ALL_SLICES_VISITED'
    for name,digest in spec['source_sha256'].items():assert base.sha(R/name)==digest,name;inputs[name]=digest
    for p in (Path(__file__),Path(base.__file__),R/'scripts/c10_memoized_kernel.py',R/'src/pta/moment_cache.py',
              R/'tests/test_c10_moment_cache.py',R/'tmp/c10_moment_cache_test_output.txt',
              R/'src/pta/nested_quadrature.py',R/'src/pta/epsilon_taylor.py',R/'scripts/c10_taylor_adapter.py',R/'tmp/c10_nested_quadrature_v1/nested_event.py',
              P/'nodal_component.npz',P/'generation.npz',P/'truth_logL.npy',R/spec['protocol']['path'],R/'configs/experiments/c06_moments.json'):
        inputs[str(p.relative_to(R))]=base.sha(p)
    selected=[]
    for j in range(0,513,4):
        for i in axes['independent_reference_ids']:
            for label in base.LABELS['D']:
                path=B/'slices'/f'{label}_d{i}_m{j}.json';bind(path)
                inputs[str(path.with_suffix('.npz').relative_to(R))]=base.sha(path.with_suffix('.npz'))
                selected.append(dict(mass_index=j,id=i,label=label,path=str(path.relative_to(R))))
    plan=dict(schema='C10_SHARED_MOMENTS_PAIRED_REPLAY_v1',inputs=inputs,selected=selected,CPU_cap_seconds=70,
              prior_pilot_CPU_upper=1716.625313,cumulative_CPU_upper=1786.625313,
              maximum_cache_numeric_bytes=128*1024**2,maximum_cache_entries=4096,
              cumulative_likelihood_values=14622522,new_likelihood_values=0,new_ORFs=0,new_observations=0,
              scope='Paired D-model analytic replay on 129 mass nodes and four fixed data sets. No production authorization.')
    O.mkdir(exist_ok=False);(O/'plan.json').write_text(json.dumps(plan,indent=2)+'\n')
    print(json.dumps({k:v for k,v in plan.items() if k not in ('inputs','selected')}))


class CompleteReadOnlyCache:
    def __init__(self,path):
        with np.load(path) as f:self.cache={float(x).hex():float(y) for x,y in zip(f['epsilon'],f['log_likelihood'])}
        self.charged=0
    def __call__(self,points):
        return np.array([self.cache[float(x).hex()] for x in points]) # Missing points fail; never score.


def execute():
    start=time.process_time();plan=base.read(O/'plan.json')
    for name,digest in plan['inputs'].items():assert base.sha(R/name)==digest,name
    resource.setrlimit(resource.RLIMIT_CPU,(math.ceil(start)+70,math.ceil(start)+71))
    def guard():
        rss=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*(1 if sys.platform=='darwin' else 1024)
        if rss>4*1024**3 or time.process_time()-start>70:raise RuntimeError('Replay CPU/RSS cap')
    spec=base.read(S/'execution_spec.json');axes=base.read(S/'axes.json');geometry=base.load_geometry(R,spec)
    with np.load(P/'nodal_component.npz') as f:provider=base.NodalCovariances(f['masses'],f['gamma'],geometry,base.read(R/spec['protocol']['path']),base.read(R/'configs/experiments/c06_moments.json'))
    with np.load(P/'generation.npz') as f:data=tuple(f[k] for k in ('q','x','g'))
    moment_cache=MomentCache(maximum_bytes=plan['maximum_cache_numeric_bytes'],maximum_entries=plan['maximum_cache_entries'])
    ordinary={i:base.engine_for(data,geometry,[i]) for i in axes['independent_reference_ids']}
    memo={i:MemoizedLikelihood(*(a[[i]] for a in data),geometry['estimator_matrices'],geometry['frequency_weights'],
                              moment_cache=moment_cache,maximum_logl_values=15000000,maximum_workspace_bytes=256*1024**2) for i in ordinary}
    mass=np.array(axes['master_mass_nodes']);truth=np.load(P/'truth_logL.npy');labels=sum((list(base.LABELS[r]) for r in base.ROUTES),[])
    times={'ordinary':0.,'memo':0.};checks=0;old_j=None;rows=[]
    for index,item in enumerate(plan['selected']):
        guard();j=item['mass_index'];i=item['id'];label=item['label']
        if j!=old_j:cov=[provider(float(mass[j]),'D',level) for level in (0,1,2)];old_j=j
        stored=base.read(R/item['path']);cache=CompleteReadOnlyCache((R/item['path']).with_suffix('.npz'))
        results={}
        for kind in (('ordinary','memo') if index%2==0 else ('memo','ordinary')):
            t=time.process_time();engine=ordinary[i] if kind=='ordinary' else memo[i];c0,c1=cov[2]
            fine=polynomial_pair(engine,c0,c1,label);bounds=[]
            for level in (0,1):
                a,b=cov[level];bounds.append(uniform_loglike_difference(fine,polynomial_pair(engine,a,b,label),normal=label!='A0_CN',roundoff_allowance=1e-10))
            delta=max(b['delta_loglike'] for b in bounds)
            assert delta==stored['delta_logL_node']
            threshold=event_level(float(truth[2,i,labels.index(label)]),delta,stored['delta_logL_truth'])
            event=TaylorEvent(engine,c0,c1,label,roundoff_allowance=1e-10)
            result=reference_slice(event,cache,threshold,maximum_splits=128,maximum_depth=24,controls=stored['controls'])
            times[kind]+=time.process_time()-t;results[kind]=result
            for key in ('status','candidate_interval','denominator','numerator_references','partition'):
                # json_report normalizes legitimate infinite bounds for exact comparison.
                assert base.json_report({key:result[key]})==base.json_report({key:stored[key]}),(item,key)
            assert engine.logl_values==engine.completed_logl_values==0
            checks+=1
        rows.append(dict(selection=item,exact_match=True))
    result=dict(status='PAIRED_ANALYTIC_REPLAY_EXACT_MATCH',cases=len(rows),replay_checks=checks,
                ordinary_CPU=times['ordinary'],memo_CPU=times['memo'],CPU=time.process_time()-start,
                speed_ratio_ordinary_over_memo=times['ordinary']/times['memo'],cache=moment_cache.statistics(),
                cumulative_likelihood_values=14622522,new_likelihood_values=0,new_ORFs=0,new_observations=0,
                production_authorized=False,plan_sha256=base.sha(O/'plan.json'))
    base.save(O/'complete.json',result);print(json.dumps(result))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--execute',action='store_true');execute() if p.parse_args().execute else freeze()
