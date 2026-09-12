"""Explicit complete-event gates following audited Taylor mass integration."""
from pathlib import Path
import hashlib
import json
import math
import collections
R=Path(__file__).resolve().parents[1]


def main():
    inputs={}
    def read(p):
        inputs[str(p.relative_to(R))]=hashlib.sha256(p.read_bytes()).hexdigest();raw=json.loads(p.read_text())
        return raw['payload'] if raw.get('schema')=='C10_OPERATIONAL_REPORT_JSON_v1' else raw
    audit=read(R/'results/C10/taylor_tail_completion_audit/audit.json')
    assert audit['status']=='EXACT_CACHE_REUSE_CELL_MEMBERSHIP_AND_ACCOUNTING_PASS' and audit['mass_rules']==72
    base=R/'tmp/c10_taylor_completion_tail_v1';done=read(base/'complete.json');axes=read(R/'tmp/c10_exact_lifecycle_v1/axes.json')
    assert done['stop']=='ALL_SELECTED_VISITED' and done['failures']=={}
    old=read(R/'tmp/c10_physical_pilot_v1/nodal_posterior_summaries.json')
    labels=['A0_CN','A_CN','B_CN','A_G','B_G','C_beta_CN','C_beta_G','C_full_CN','C_full_G']
    required=('logZ_H0','logZ_H1','logBF','parameter_CDF','quantiles','logL_CDF');events={}
    for i in axes['independent_reference_ids']:
        for label in labels:
            rules=[read(base/f'{label}_d{i}_u{order}_mass_reference.json') for order in ('192','384')]
            lower=min(r['candidate_interval'][0] for r in rules);upper=max(r['candidate_interval'][1] for r in rules)
            dz=abs(rules[0]['log_masses']['Zpoint']-rules[1]['log_masses']['Zpoint']);s=old[f'{label}:{i}']
            point_differences={name:max(abs(s[name]['logL_CDF']-lower),abs(s[name]['logL_CDF']-upper)) for name in ('fine','high','independent_grid')}
            gates=dict(positive_rule_controls=all(r.get('finite_controls_pass') is True for r in rules),
                       CDF_hull_width=upper-lower<=.002,logZ_change=dz<=.001,
                       high_and_independent_refinements=all(s[g].get(k) is True for g in ('high_gates','independent_gates') for k in required),
                       product_H0=s['direct_product_H0_gate'] is True,product_H1=s['direct_product_Z_gate'] is True,
                       underflow=all(s[n]['log_upper_bound_omitted_scaled_nodal_probability']<math.log(1e-8) for n in ('fine','high','independent_grid')),
                       bilinear_event_comparison=all(d<=.002 for d in point_differences.values()))
            passed=all(gates.values())
            events[f'{label}:{i}']=dict(status='RESOLVED_OPERATIONAL_FINITE_REFERENCE_ONLY' if passed else 'UNRESOLVED',
                 interval=[lower,upper] if passed else [0.,1.],candidate_interval=[lower,upper],gates=gates,
                 original_coarse_gates=s['grid_gates'],accepted_grid_level='high',observed_logZ_difference=dz,
                 bilinear_endpoint_differences=point_differences,physical_global_certificate=False)
    out=R/'results/C10/taylor_event_final_gate';out.mkdir(exist_ok=False)
    inputs[str(Path(__file__).relative_to(R))]=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    result=dict(status='COMPLETE_EVENT_GATES_EVALUATED',events=events,states=dict(collections.Counter(r['status'] for r in events.values())),
                cumulative_likelihood_values=audit['cumulative_values'],new_likelihood_values=0,new_ORFs=0,inputs=inputs,
                scope='Operational numerical controls on four fixed engineering data sets. Not population calibration or a uniform physical error certificate.',
                C10_complete=False,production_authorized=False)
    (out/'audit.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ('events','inputs')}))
    for key,row in events.items():
        if row['status']=='UNRESOLVED':print(json.dumps(dict(key=key,interval=row['candidate_interval'],failed=[k for k,v in row['gates'].items() if not v])))


if __name__=='__main__':main()
