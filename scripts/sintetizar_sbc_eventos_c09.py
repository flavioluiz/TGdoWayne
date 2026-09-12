"""Full registered SBC family, conditional on finite operational PIT envelopes."""
from pathlib import Path
import collections
import hashlib
import json
import sys
import numpy as np
R = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(R/'tmp/c09_sbc_synthesis_v1'))
from synthesis import synthesize


def main():
    bindings = {}
    def read(p): bindings[str(p.relative_to(R))] = hashlib.sha256(p.read_bytes()).hexdigest(); return json.loads(p.read_text())
    registry = read(R/'results/C09/SBC_mass_preliminary/registry.json')
    mass = {r['curve_id']:r for r in read(R/'results/C09/production_mass_PIT/records.json')}
    events = {}
    for folder in ('events_direct_threshold', 'events_distance_direct_threshold'):
        audit = read(R/'results/C09'/folder/'audit.json')
        path = R/'results/C09'/folder/'records.json'; rows = read(path)
        assert bindings[str(path.relative_to(R))] == audit['records_sha256']
        for r in rows: assert r['curve_id'] not in events; events[r['curve_id']] = r
    assert set(events) == set(mass) and len(events) == 25956
    groups = []
    for item in registry:
        stratum = item['stratum']; model = item['analysis_model']; group_id = item['group_id']
        if stratum == 'core': stage, prior, scenario = 1, int(group_id.split('_')[1][1:]), 0
        elif stratum == 'covariance_self':
            stage, prior = 2, 0
            scenario = ('self_diagonal_variable', 'self_full_fixed', 'self_diagonal_fixed').index(group_id)
        elif stratum == 'noise': stage, prior, scenario = 3, 0, int(group_id.startswith('strong_white'))
        elif stratum == 'distance_mixture': stage, prior, scenario = 6, 0, 1
        else: raise ValueError(stratum)
        names = [f's{stage}_p{prior}_c{scenario}_d{i}__{model}' for i in range(500)]
        selected = [mass[n] for n in names]; ev = [events[n] for n in names]
        assert [r['datum_id'] for r in selected] == list(range(500)) and all(r['SBC_eligible'] for r in selected)
        assert all(r['fine_strict'] == r['fine_inclusive'] for r in ev), 'Atom randomization must be explicit'
        groups.append(dict(group_id=group_id, datum_ids=np.arange(500),
            pit_intervals=np.array([[m['mass_PIT_interval'], e['operational_PIT_interval']] for m,e in zip(selected,ev)]),
            resolved=np.array([[m['mass_resolved'], e['finite_operational_gates_passed']] for m,e in zip(selected,ev)], dtype=bool),
            interval_evidence_binding=hashlib.sha256(json.dumps(bindings, sort_keys=True).encode()).hexdigest(),
            logL_null_definition='continuous_statistic'))
    result = synthesize(groups, registry)
    for p in (Path(__file__), R/'tmp/c09_sbc_synthesis_v1/synthesis.py', R/'src/inference/sbc_sensitivity.py'):
        bindings[str(p.relative_to(R))] = hashlib.sha256(p.read_bytes()).hexdigest()
    result.update(status='FULL_FAMILY_CONDITIONAL_OPERATIONAL_SBC', inputs=bindings, C09_complete=False,
        new_likelihood_values=0, new_ORFs=0,
        interpretation='All126 tests retained; unresolved IDs use[0,1]. Decisions depend on observed numerical envelopes, not uniform physical bounds. Continuous nonconstant physical logL assumed; no atoms found in the interpolants. Nonrejection does not establish learning.')
    out = R/'results/C09/SBC_operational_events'; out.mkdir(parents=True, exist_ok=False)
    (out/'results.json').write_text(json.dumps(result, indent=2, allow_nan=False)+'\n')
    (out/'registry.json').write_text(json.dumps(registry, indent=2)+'\n')
    print(json.dumps(dict(groups=len(groups), tests=len(result['tests']),
        mass_resolved=sum(g['resolved_mass'] for g in result['group_summary']),
        logL_resolved=sum(g['resolved_logL'] for g in result['group_summary']),
        decisions=dict(collections.Counter(t['decision'] for t in result['tests'])))))


if __name__ == '__main__': main()
