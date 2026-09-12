"""Independent cache-accounting and mass-sum audit of C10 refinement runs."""
from pathlib import Path
import json
import hashlib
import math
import numpy as np
from scipy.special import logsumexp

R=Path(__file__).resolve().parents[1]


def main():
    bindings={}
    def bind(p):
        bindings[str(p.relative_to(R))]=hashlib.sha256(p.read_bytes()).hexdigest()
        return p
    def read(p):
        raw=json.loads(bind(p).read_text())
        return raw['payload'] if raw.get('schema')=='C10_OPERATIONAL_REPORT_JSON_v1' else raw
    directories=[R/'results/C10/slice_refinement_probe_v2',R/'results/C10/slice_refinement_hard_probe',R/'tmp/c10_event_refinement_v1']
    audits=[];cumulative=11930676
    for directory in directories:
        plan=read(directory/'plan.json');done=read(directory/'complete.json');ledger=read(directory/'ledger.json')
        assert not (directory/'FAILED_PRESERVED.json').exists()
        assert plan['historical_charged']==cumulative
        assert ledger['charged']==ledger['completed']
        for name,digest in plan['inputs'].items():assert hashlib.sha256((R/name).read_bytes()).hexdigest()==digest,name
        new_values=0;reused=0;rows=[]
        for path in sorted((directory/'slices').glob('*.json')):
            row=read(path);oldpath=R/row['selection']['path'];old=read(oldpath)
            with np.load(bind(oldpath.with_suffix('.npz'))) as f:
                old_cache={float(x).hex():float(y) for x,y in zip(f['epsilon'],f['log_likelihood'])}
            with np.load(bind(path.with_suffix('.npz'))) as f:
                eps,vals=f['epsilon'],f['log_likelihood']
                assert len(eps)==len(set(eps)) and np.isfinite(vals).all()
                cache={float(x).hex():float(y) for x,y in zip(eps,vals)}
            assert all(k in cache and cache[k]==v for k,v in old_cache.items()),path
            assert len(cache)-len(old_cache)==row['charged_values'],path
            assert row['reused_values']==len(old_cache) and row['bridge_max_delta']<=1e-10
            new_values+=row['charged_values']+3;reused+=len(old_cache)
            cells=row['partition']
            assert cells[0]['left']==0 and cells[-1]['right']==1
            assert all(a['right']==b['left'] for a,b in zip(cells,cells[1:]))
            if row['status'].startswith('SLICE_OPERATIONAL'):
                assert all(row['slice_gates'].values()) and 'failure_preserved' not in row
            rows.append(row)
        assert new_values==sum(ledger['charged'].values())==done['charged_new_values']
        cumulative+=new_values;assert cumulative==done['cumulative_values']<=15000000
        audits.append(dict(directory=str(directory.relative_to(R)),slices=len(rows),charged=new_values,reused=reused,
                           states=dict(__import__('collections').Counter(r['status'] for r in rows))))
    # Reconstruct all 72 weighted N/A/Z rules directly in log space, using the
    # explicitly declared old/new selection. No likelihood or ORF is evaluated.
    directory=directories[-1];plan=read(directory/'plan.json');axes=read(R/'tmp/c10_exact_lifecycle_v1/axes.json')
    groups={}
    def width(r):
        if 'failure_preserved' in r:return 1.
        a,b=r.get('candidate_interval',[0.,1.]);return b-a
    for item in plan['all_rows']:
        old=read(R/item['path']);newpath=directory/'slices'/Path(item['path']).name;row=old
        if newpath.exists():
            new=read(newpath)
            if width(new)<=width(old):row=new
        key=f'{item["label"]}_d{item["id"]}_u{item["order"]}'
        groups.setdefault(key,[]).append((item,row))
    maximum_error=0.;intervals={}
    for key,items in groups.items():
        nlo=[];nhi=[];zlo=[];zhi=[];zp=[]
        for item,row in items:
            w=axes['u_reference'][item['order']]['prior_weights'][item['node_index']]
            den=row['denominator'];refs=row['numerator_references'];delta=row['delta_logL_node']
            lo=refs['inside']['lower'] if 'inside' in refs and 'failure_preserved' not in row else 0.
            hi=min(den['upper'],refs['inside']['upper']+refs['ambiguous']['upper']) if all(k in refs for k in ('inside','ambiguous')) and 'failure_preserved' not in row else den['upper']
            b=math.log(w)+row['log_shift']
            nlo.append(-np.inf if lo==0 else b-delta+math.log(lo));nhi.append(-np.inf if hi==0 else b+delta+math.log(hi))
            zlo.append(b-delta+math.log(den['lower']));zhi.append(b+delta+math.log(den['upper']));zp.append(b+math.log(den['value']))
        expected=[float(np.exp(logsumexp(nlo)-logsumexp(zhi))),float(min(1.,np.exp(logsumexp(nhi)-logsumexp(zlo))))]
        stored=read(directory/f'{key}_mass_reference.json')
        error=max(abs(np.array(expected)-stored['candidate_interval']))
        error=max(error,abs(float(logsumexp(zp))-stored['log_masses']['Zpoint']))
        assert error<1e-10,key
        maximum_error=max(maximum_error,error)
        intervals[key]=dict(interval=expected,width=expected[1]-expected[0],status=stored['status'])
    out=R/'results/C10/event_refinement_audit';out.mkdir(exist_ok=False)
    bind(Path(__file__))
    result=dict(status='CACHE_ACCOUNTING_AND_INDEPENDENT_MASS_SUMS_PASS',runs=audits,cumulative_logL_values=cumulative,
                mass_rules=len(groups),maximum_aggregation_difference=maximum_error,intervals=intervals,inputs=bindings,
                new_likelihood_values=0,new_ORFs=0,C10_complete=False,production_authorized=False,
                scope='Numerical audit only; adaptive selection and observed quadrature differences are not uniform physical error certificates.')
    (out/'audit.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ('inputs','intervals')}))


if __name__=='__main__':main()
