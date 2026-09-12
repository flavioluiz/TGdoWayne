"""Preliminary registered126-test SBC family; uncomputed logL events remain unresolved."""
from pathlib import Path
import json,hashlib,sys,collections
import numpy as np
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tmp/c09_sbc_synthesis_v1'))
from synthesis import synthesize

def main():
    path=R/'results/C09/production_mass_PIT/records.json'
    rows=json.loads(path.read_text());lookup={r['curve_id']:r for r in rows}
    binding=hashlib.sha256(path.read_bytes()).hexdigest()
    generation=hashlib.sha256((R/'tmp/c09_production_v1/generation/audit.json').read_bytes()).hexdigest()
    registry=[];groups=[]
    def add(group_id,stratum,stage,prior_id,scenario,model,suffix=''):
        names=[f's{stage}_p{prior_id}_c{scenario}_d{i}__{model}{suffix}' for i in range(500)]
        selected=[lookup[n] for n in names]
        assert [r['datum_id'] for r in selected]==list(range(500)) and all(r['SBC_eligible'] for r in selected)
        priors={r['prior'] for r in selected};assert len(priors)==1
        registry.append(dict(group_id=group_id,stratum=stratum,prior_id=next(iter(priors)),
            generative_model=model,analysis_model=model+suffix,generation_binding=generation,
            truth_design='continuous_prior_predictive',fixed_nuisance_known=True))
        groups.append(dict(group_id=group_id,datum_ids=np.arange(500),
            pit_intervals=np.array([[r['mass_PIT_interval'],r['logL_PIT_interval']] for r in selected],dtype=float),
            resolved=np.array([[r['mass_resolved'],r['logL_resolved']] for r in selected],dtype=bool),
            interval_evidence_binding=binding,logL_null_definition='not_evaluated'))
    for prior in range(3):
        for model in ('A0_CN','A_G','B_G_full_variable'):
            add(f'core_p{prior}_{model}','core',1,prior,0,model)
    for scenario,variant in enumerate(('diagonal_variable','full_fixed','diagonal_fixed')):
        add('self_'+variant,'covariance_self',2,0,scenario,'B_G_'+variant)
    for scenario,label in enumerate(('strong_red','strong_white')):
        for model in ('A0_CN','B_G_full_variable'):
            add(label+'_'+model,'noise',3,0,scenario,model)
    for model in ('A0_CN','B_G_full_variable'):
        add('distance_'+model,'distance_mixture',6,0,1,model,'__correct_mixture')
    result=synthesize(groups,registry)
    # Report the physical generative mixture explicitly rather than the component label.
    for item in registry:
        if item['stratum']=='distance_mixture':item['generative_model']+='__global_distance_mixture'
    result.update(status='PRELIMINARY_MASS_SBC_LOG_LIKELIHOOD_EVENTS_PENDING',
        C09_complete=False,new_likelihood_values=0,new_ORFs=0,
        source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        statistical_source_sha256=hashlib.sha256((R/'tmp/c09_sbc_synthesis_v1/synthesis.py').read_bytes()).hexdigest(),
        pit_evidence_sha256=binding,
        interpretation='Holm decisions are conditional on observed-discretization PIT envelopes. Missing logL tests retain[0,1] and remain in the126-test family. Not a complete calibration claim.')
    out=R/'results/C09/SBC_mass_preliminary';out.mkdir(parents=True,exist_ok=False)
    (out/'registry.json').write_text(json.dumps(registry,indent=2)+'\n')
    (out/'results.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    print(json.dumps(dict(groups=len(registry),tests=len(result['tests']),
        mass_resolved=sum(g['resolved_mass'] for g in result['group_summary']),
        logL_resolved=sum(g['resolved_logL'] for g in result['group_summary']),
        decisions=dict(collections.Counter(r['decision'] for r in result['tests'])))))
if __name__=='__main__':main()
