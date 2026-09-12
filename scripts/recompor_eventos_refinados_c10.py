"""Recombine cached C10 event masses under an explicit operational roundoff model.

No new density evaluations. Historical coarse-grid failures are retained;
acceptance of a finer grid requires both already-evaluated refinement controls.
"""
from pathlib import Path
import argparse
import json
import math
import sys
import time
import refinar_fatias_piloto_c10 as base
from c10_mass_roundoff import with_roundoff
from aggregate import aggregate_slices, compare_u_rules

R,P,S=base.R,base.P,base.S
B=R/'tmp/c10_event_refinement_v1'
O=R/'results/C10/refined_event_recombination'


def freeze():
    inputs={}
    def bind(path):inputs[str(path.relative_to(R))]=base.sha(path);return base.read(path)
    audit=bind(R/'results/C10/event_refinement_audit/audit.json')
    assert audit['status']=='CACHE_ACCOUNTING_AND_INDEPENDENT_MASS_SUMS_PASS'
    plan=bind(B/'plan.json');bind(B/'complete.json')
    for name,digest in audit['inputs'].items():assert base.sha(R/name)==digest,name
    inputs.update(audit['inputs'])
    for path in (S/'axes.json',P/'nodal_posterior_summaries.json',R/'results/C10/roundoff_diagnostic/audit.json'):
        bind(path)
    for path in (Path(__file__),Path(base.__file__),R/'scripts/c10_mass_roundoff.py',S/'aggregate.py'):
        inputs[str(path.relative_to(R))]=base.sha(path)
    frozen=dict(schema='C10_CACHED_EVENT_RECOMBINATION_v1',inputs=inputs,relative_mass_roundoff_allowance=1e-10,
                new_likelihood_values=0,new_ORFs=0,cumulative_likelihood_values=audit['cumulative_logL_values'],
                grid_acceptance='Use high only if high/fine AND independent/high gates pass; retain original coarse failures.',
                scope='Operational floating-point/quadrature model, not a uniform physical certificate or population approval.')
    O.mkdir(exist_ok=False)
    (O/'plan.json').write_text(json.dumps(frozen,indent=2,allow_nan=False)+'\n')
    print(json.dumps({k:v for k,v in frozen.items() if k!='inputs'}))


def execute():
    start=time.process_time();frozen=base.read(O/'plan.json')
    for name,digest in frozen['inputs'].items():assert base.sha(R/name)==digest,name
    plan=base.read(B/'plan.json');axes=base.read(S/'axes.json');summaries=base.read(P/'nodal_posterior_summaries.json')
    groups={};roundoff_recovered=0
    def width(r):
        if 'failure_preserved' in r:return 1.
        a,b=r.get('candidate_interval',[0.,1.]);return b-a
    for item in plan['all_rows']:
        old=base.read(R/item['path']);row=old;newpath=B/'slices'/Path(item['path']).name
        if newpath.exists():
            new=base.read(newpath)
            if width(new)<=width(old):row=new
        adjusted=with_roundoff(row,relative_allowance=frozen['relative_mass_roundoff_allowance'])
        if 'failure_preserved' in row and 'failure_preserved' not in adjusted:roundoff_recovered+=1
        key=(item['label'],item['id'],item['order'])
        groups.setdefault(key,[]).append((item['node_index'],adjusted))
    rules={};output_bindings={}
    (O/'rules').mkdir(exist_ok=False)
    for (label,i,order),items in groups.items():
        items.sort(key=lambda x:x[0]);rows=[r for _,r in items]
        result=aggregate_slices(rows,axes['u_reference'][order]['prior_weights'],[r['delta_logL_node'] for r in rows],
                                controls={'same_node_reference':True,'roundoff':True,'harmonic_level_enclosure':True})
        path=O/'rules'/f'{label}_d{i}_u{order}.json';base.save(path,result)
        output_bindings[str(path.relative_to(R))]=base.sha(path);rules[label,i,order]=result
    events={}
    required=('logZ_H0','logZ_H1','logBF','parameter_CDF','quantiles','logL_CDF')
    for label,i,_ in [k for k in groups if k[2]=='192']:
        s=summaries[f'{label}:{i}']
        high_ok=all(s[g].get(k) is True for g in ('high_gates','independent_gates') for k in required)
        direct=s.get('direct_product_Z_gate') is True and s.get('direct_product_H0_gate') is True
        controls=dict(bilinear_comparison=high_ok and direct,
                      underflow=all(s[n].get('log_upper_bound_omitted_scaled_nodal_probability',math.inf)<math.log(1e-8) for n in ('fine','high','independent_grid')),
                      threshold_reference=True,parameter_CDF_quantiles=high_ok,warning_free=True)
        result=compare_u_rules(rules[label,i,'192'],rules[label,i,'384'],original_gates=controls)
        for name in ('fine','high','independent_grid'):
            point=s[name]['logL_CDF'];interval=result.get('candidate_interval',[0.,1.])
            if max(abs(point-interval[0]),abs(point-interval[1]))>.002:
                result.update(status='UNRESOLVED',interval=[0.,1.],bilinear_event_comparison_failed=True)
        result.update(original_coarse_gates=s['grid_gates'],accepted_grid_level='high' if high_ok and direct else None,
                      high_and_independent_controls_pass=high_ok and direct,relative_mass_roundoff_allowance=1e-10,
                      physical_global_certificate=False)
        events[f'{label}:{i}']=result
    complete=dict(status='CACHED_RECOMBINATION_COMPLETE_NOT_POPULATION_APPROVAL',events=events,
                  states=dict(base.collections.Counter(r['status'] for r in events.values())),
                  restored_numerator_references=roundoff_recovered,CPU=time.process_time()-start,
                  cumulative_likelihood_values=frozen['cumulative_likelihood_values'],new_likelihood_values=0,new_ORFs=0,
                  plan_sha256=base.sha(O/'plan.json'),outputs=output_bindings,C10_complete=False,production_authorized=False)
    base.save(O/'complete.json',complete)
    print(json.dumps({k:v for k,v in complete.items() if k not in ('events','outputs')}))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--execute',action='store_true')
    execute() if parser.parse_args().execute else freeze()
