"""Measure original partition inconsistencies and test explicit roundoff accounting."""
from pathlib import Path
import copy
import hashlib
import json
import math
import numpy as np
from c10_mass_roundoff import with_roundoff
R=Path(__file__).resolve().parents[1]


def main():
    rows=[];inputs={};resolved=0;largest=0.
    for path in sorted((R/'tmp/c10_physical_pilot_v1/event_slices').glob('*.json')):
        row=json.loads(path.read_text())['payload']
        if row.get('failure_preserved')!='ArithmeticError: Reference partition incompatible with total':continue
        inputs[str(path.relative_to(R))]=hashlib.sha256(path.read_bytes()).hexdigest()
        d=row['denominator'];n=row['numerator_references']['inside'];a=row['numerator_references']['ambiguous']
        outside=[c for c in row['partition'] if c['classification']=='outside']
        low=n['lower']+a['lower']+math.fsum(c['mass_lower'] for c in outside)-d['upper']
        high=d['lower']-n['upper']-a['upper']-math.fsum(c['mass_upper'] for c in outside)
        gap=max(low,high)/d['value'];largest=max(largest,gap)
        repaired=with_roundoff(row,relative_allowance=1e-10)
        assert repaired['quadrature_roundoff_compatibility']
        assert row.get('failure_preserved') # original input not mutated
        resolved+=repaired['status'].startswith('SLICE_OPERATIONAL')
        rows.append(dict(path=str(path.relative_to(R)),scaled_gap=gap,recomputed_status=repaired['status']))
    assert len(rows)==363
    # Adversarial negative control: a materially inconsistent total must remain
    # unresolved. This operates on a copied report, without scoring new data.
    bad=copy.deepcopy(row) if rows else None
    original=json.loads((R/rows[0]['path']).read_text())['payload'];bad=copy.deepcopy(original)
    bad['numerator_references']['inside'].update(lower=2*bad['denominator']['upper'],upper=3*bad['denominator']['upper'])
    rejected=with_roundoff(bad,relative_allowance=1e-10)
    assert rejected['status']=='UNRESOLVED' and rejected['quadrature_roundoff_compatibility'] is False
    for p in (Path(__file__),R/'scripts/c10_mass_roundoff.py'):inputs[str(p.relative_to(R))]=hashlib.sha256(p.read_bytes()).hexdigest()
    out=R/'results/C10/roundoff_diagnostic';out.mkdir(exist_ok=False)
    result=dict(status='ROUNDING_SCALE_DIAGNOSTIC_PASS_NOT_GLOBAL_CERTIFICATE',cases=len(rows),maximum_scaled_gap=largest,
                compatible_with_explicit_allowance=len(rows),operationally_resolved_after_model=resolved,
                relative_mass_allowance=1e-10,material_incompatibility_rejected=True,
                new_likelihood_values=0,new_ORFs=0,rows=rows,inputs=inputs,
                scope='Diagnostic only. Original failure reports are preserved; full recombination pending.')
    (out/'audit.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ('inputs','rows')}))


if __name__=='__main__':main()
