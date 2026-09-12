"""Audit Taylor cache extensions, final-cell membership and positive mass sums."""
from pathlib import Path
import argparse
import hashlib
import json
import math
import sys
import numpy as np
from scipy.special import logsumexp
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'scripts'))
from c10_mass_roundoff import with_roundoff


def main(which):
    directory=R/({'probe':'results/C10/taylor_selected_probe','completion':'tmp/c10_taylor_completion_v1'}[which])
    inputs={}
    def bind(p):inputs[str(p.relative_to(R))]=hashlib.sha256(p.read_bytes()).hexdigest();return p
    def read(p):
        raw=json.loads(bind(p).read_text());return raw['payload'] if raw.get('schema')=='C10_OPERATIONAL_REPORT_JSON_v1' else raw
    plan=read(directory/'plan.json');done=read(directory/'complete.json');ledger=read(directory/'ledger.json')
    assert not (directory/'FAILED_PRESERVED.json').exists() and ledger['charged']==ledger['completed']
    for name,digest in plan['inputs'].items():assert hashlib.sha256((R/name).read_bytes()).hexdigest()==digest,name
    values=0;reused=0;memberships=0;count=0
    for path in sorted((directory/'slices').glob('*.json')):
        row=read(path);oldpath=(R/row['selection']['path']).with_suffix('.npz')
        with np.load(bind(oldpath)) as f:old={float(x).hex():float(y) for x,y in zip(f['epsilon'],f['log_likelihood'])}
        with np.load(bind(path.with_suffix('.npz'))) as f:eps,logs=f['epsilon'],f['log_likelihood']
        assert len(eps)==len(set(eps)) and np.isfinite(logs).all()
        new={float(x).hex():float(y) for x,y in zip(eps,logs)}
        assert all(k in new and new[k]==v for k,v in old.items())
        assert len(new)-len(old)==row['charged_values'] and len(old)==row['reused_values']
        values+=row['charged_values']+3;reused+=len(old);count+=1
        cells=row['partition'];assert cells[0]['left']==0 and cells[-1]['right']==1
        assert all(a['right']==b['left'] for a,b in zip(cells,cells[1:]))
        for x,value in zip(eps,logs):
            j=int(np.searchsorted([c['right'] for c in cells],x,side='left'));cell=cells[j]
            assert cell['left']<=x<=cell['right']
            assert cell['logL_lower'] is None or cell['logL_lower']<=value
            assert cell['logL_upper'] is None or value<=cell['logL_upper']
            memberships+=1
        if row['status'].startswith('SLICE_OPERATIONAL'):assert all(row['slice_gates'].values())
    assert values==sum(ledger['charged'].values())==done['charged_new_values']
    assert done['cumulative_values']==plan['historical_values']+values<=15000000
    size=sum(p.stat().st_size for p in directory.rglob('*') if p.is_file());assert size<=plan['output_cap_bytes']
    maximum_error=0.;rules=0
    if which=='completion':
        axes=read(R/'tmp/c10_exact_lifecycle_v1/axes.json');groups={}
        for item in plan['all_rows']:
            path=directory/'slices'/Path(item['path']).name
            row=read(path) if path.exists() else with_roundoff(read(R/item['path']),relative_allowance=1e-10)
            key=f'{item["label"]}_d{item["id"]}_u{item["order"]}';groups.setdefault(key,[]).append((item,row))
        for key,items in groups.items():
            nlo=[];nhi=[];zlo=[];zhi=[];zp=[]
            for item,row in items:
                w=axes['u_reference'][item['order']]['prior_weights'][item['node_index']];d=row['denominator'];refs=row['numerator_references']
                lo=refs['inside']['lower'] if 'inside' in refs and 'failure_preserved' not in row else 0.
                hi=min(d['upper'],refs['inside']['upper']+refs['ambiguous']['upper']) if all(k in refs for k in ('inside','ambiguous')) and 'failure_preserved' not in row else d['upper']
                b=math.log(w)+row['log_shift'];delta=row['delta_logL_node']
                nlo.append(-np.inf if lo==0 else b-delta+math.log(lo));nhi.append(-np.inf if hi==0 else b+delta+math.log(hi))
                zlo.append(b-delta+math.log(d['lower']));zhi.append(b+delta+math.log(d['upper']));zp.append(b+math.log(d['value']))
            expected=np.array([np.exp(logsumexp(nlo)-logsumexp(zhi)),min(1.,np.exp(logsumexp(nhi)-logsumexp(zlo)))])
            reference=read(directory/f'{key}_mass_reference.json')
            error=max(float(np.max(abs(expected-reference['candidate_interval']))),abs(float(logsumexp(zp))-reference['log_masses']['Zpoint']))
            assert error<1e-10;maximum_error=max(maximum_error,error);rules+=1
    bind(Path(__file__));out=R/f'results/C10/taylor_{which}_audit';out.mkdir(exist_ok=False)
    result=dict(status='EXACT_CACHE_REUSE_CELL_MEMBERSHIP_AND_ACCOUNTING_PASS',slices=count,new_values=values,reused_values=reused,
                final_cell_membership_checks=memberships,mass_rules=rules,maximum_mass_aggregation_difference=maximum_error,
                cumulative_values=done['cumulative_values'],output_bytes=size,new_audit_likelihood_values=0,new_ORFs=0,inputs=inputs,
                scope='Finite cache/cell and normalization checks. No directed-rounding or global physical certificate; population pending.')
    (out/'audit.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k!='inputs'}))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('which',choices=['probe','completion']);main(p.parse_args().which)
