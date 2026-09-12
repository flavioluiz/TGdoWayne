"""Freeze the prospective C10 inventory without drawing truths or observations."""
from pathlib import Path
import hashlib
import json
import sys
R=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(R/'src'))
from pta.scalar_campaign import inventory,hypotheses,budget


def main():
    path=R/'tmp/c10_execution_design/c10_protocol_candidate_v1.json'
    protocol=json.loads(path.read_text())
    rows=inventory(protocol); families=hypotheses(protocol); counts=budget(protocol,rows)
    audit_path=R/'results/C10/nested_integral_audit/audit.json'
    audit=json.loads(audit_path.read_text())
    assert audit['complete_comparisons_pass']==audit['complete_comparisons']==36
    benchmark_path=R/'results/C10/moment_cache_benchmark/complete.json'
    benchmark=json.loads(benchmark_path.read_text())['payload']
    assert benchmark['status']=='PAIRED_ANALYTIC_REPLAY_EXACT_MATCH'
    pilot_CPU_upper=1716.625313+benchmark['CPU']
    inputs=[path,audit_path,benchmark_path,Path(__file__),R/'src/pta/scalar_campaign.py',
            R/'tests/test_c10_scalar_campaign.py',R/'tmp/c10_campaign_tests_pass.txt',
            R/'src/pta/fisher_information.py',R/'tests/test_c10_fisher_information.py',R/'tmp/c10_fisher_tests.txt']
    result=dict(status='PROSPECTIVE_INVENTORY_FROZEN_NOT_EXECUTION_APPROVAL',
                source_sha256={str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs},
                inventory=rows,hypotheses=families,budget=counts,
                reconciliation=dict(original_C_data=96,original_C_analyses=384,
                                    erroneous_prior_summary_C_data=94,omitted_from_summary_only_recovery_ids=[133,165],
                                    action='Preserve original JSON IDs and revised design; correct narrative arithmetic. No observations removed.'),
                numerical_method=dict(mass='CC129/257 on exact pilot Chebyshev-Lobatto axis',
                                      epsilon='positive Simpson32/64; boundary panels charged separately',
                                      physical_logL_events='2500 D analyses of prior2D; C comparisons descriptive',
                                      unresolved='Retain all targets and use [0,1] for unresolved PIT; BF certain/possible bounds',
                                      validation='Finite pilot reference comparison, not rigorous quadrature certification'),
                resources=dict(pilot_likelihood_values=14622522,pilot_remaining_values=377478,
                               pilot_CPU_upper_seconds=pilot_CPU_upper,pilot_remaining_CPU_seconds=1800-pilot_CPU_upper,
                               analytic_event_replay_extrapolation_seconds=benchmark['memo_CPU']/benchmark['cases']*2500*257,
                               extrapolation_is_upper_bound=False,
                               extrapolation_excludes='Density scoring, truth ORFs, data generation, grids, posterior summaries, I/O and refinement failures',
                               production_data_batch_candidate=64,
                               maximum_values_per_D_grid_batch=64*5*257*129),
                pending=['Full executor benchmark including summaries and direct event references',
                         'Final source/resource manifest and thread settings',
                         'Population truth ORFs and generation',
                         '6344 posterior analyses and statistical synthesis',
                         'Physical Fisher derivatives and convergence'],
                new_likelihood_values=0,new_ORFs=0,new_observations=0,production_enabled=False)
    out=R/'results/C10/production_preflight_v1';out.mkdir(exist_ok=False)
    (out/'plan.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    print(json.dumps({k:result[k] for k in ('status','budget','resources','pending')},indent=2))


if __name__=='__main__':main()
