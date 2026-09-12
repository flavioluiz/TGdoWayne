"""Independent scalar Simpson sums, exact cache reuse, CC sums and GL comparison."""
from pathlib import Path
import hashlib
import json
import math
import collections
import numpy as np
from scipy.special import logsumexp
R=Path(__file__).resolve().parents[1]


def main():
    inputs={}
    def bind(p):inputs[str(p.relative_to(R))]=hashlib.sha256(p.read_bytes()).hexdigest();return p
    def read(p):
        raw=json.loads(bind(p).read_text());return raw['payload'] if raw.get('schema')=='C10_OPERATIONAL_REPORT_JSON_v1' else raw
    base=R/'tmp/c10_nested_integral_validation_v1';physical=R/'tmp/c10_physical_pilot_v1'
    plan=read(base/'plan.json');done=read(base/'complete.json');ledger=read(base/'ledger.json');axes=read(R/'tmp/c10_exact_lifecycle_v1/axes.json')
    for name,digest in plan['inputs'].items():assert hashlib.sha256((R/name).read_bytes()).hexdigest()==digest,name
    assert done['stop']=='ALL_SLICES_VISITED' and done['visited']==18468 and not (base/'FAILED_PRESERVED.json').exists()
    assert ledger['charged']==ledger['completed'];high={route:np.load(bind(physical/f'{route}_high.npy'),mmap_mode='r') for route in ('D','C_beta','C_full')}
    states={route:read(physical/f'{route}_high.state.json') for route in high};eps=np.array(axes['master_epsilon_nodes'])[::2]
    scalar_error=0.;cached=0;new=0;count=0;groups={}
    def regions(cells,kind):
        out=[]
        for c in cells:
            if c['classification']!=kind:continue
            if out and out[-1][1]==c['left']:out[-1]=(out[-1][0],c['right'])
            else:out.append((c['left'],c['right']))
        return out
    def integrate(cache,intervals,panels,shift):
        terms=[]
        for a,b in intervals:
            boundaries=[a]+[j/panels for j in range(math.floor(a*panels)+1,math.ceil(b*panels))]+[b]
            for left,right in zip(boundaries,boundaries[1:]):
                mid=left+(right-left)/2
                va,vm,vb=[math.exp(cache[float(x).hex()]-shift) for x in (left,mid,right)]
                terms.append((right-left)*(va+4*vm+vb)/6)
        return math.fsum(terms)
    for path in sorted((base/'slices').glob('*.json')):
        row=read(path);item=row['selection'];route=item['route'];i=item['id'];j=item['mass_index']
        with np.load(bind(path.with_suffix('.npz'))) as f:points,values=f['epsilon'],f['log_likelihood']
        assert len(set(points))==len(points) and np.isfinite(values).all()
        cache={float(x).hex():float(v) for x,v in zip(points,values)}
        state=states[route];m=state['models'].index(item['model']);ri=state['data_ids'].index(i)
        restored=np.array([cache[float(x).hex()] for x in eps])
        assert restored.tobytes()==np.asarray(high[route][j,::2,m,ri]).tobytes()
        assert len(points)-129==row['charged_values']
        new+=row['charged_values'];cached+=len(points);count+=1
        cells=row['partition'];assert cells[0]['left']==0 and cells[-1]['right']==1
        assert all(a['right']==b['left'] for a,b in zip(cells,cells[1:]))
        index=np.searchsorted([c['right'] for c in cells],points,side='left')
        lo=np.array([-np.inf if c['logL_lower'] is None else c['logL_lower'] for c in cells])[index]
        hi=np.array([np.inf if c['logL_upper'] is None else c['logL_upper'] for c in cells])[index]
        assert np.all((lo<=values)&(values<=hi))
        references=[(row['denominator'],[(0.,1.)])]+[(row['numerator_references'][k],regions(cells,k)) for k in ('inside','ambiguous')]
        for reference,intervals in references:
            for n,field in ((32,'coarse'),(64,'fine')):
                value=integrate(cache,intervals,n,row['log_shift']);delta=abs(value-reference[field])/max(1.,abs(reference[field]))
                assert delta<1e-12;scalar_error=max(scalar_error,delta)
        assert row['status'].startswith('SLICE_OPERATIONAL') and all(row['slice_gates'].values())
        groups.setdefault(f'{item["label"]}:{i}',{})[j]=row
    assert count==18468 and new==ledger['charged']['epsilon'] and ledger['charged']['bridges']==108
    assert new+108==done['charged_new_values']==80564
    mass_error=0.;rules={}
    for key,rows in groups.items():
        assert set(rows)==set(range(513));label,i=key.split(':')
        for n,step in ((129,4),(257,2),(513,1)):
            nl=[];nh=[];zl=[];zh=[];zp=[]
            for j,weight in zip(range(0,513,step),plan['weights'][str(n)]):
                row=rows[j];d=row['denominator'];refs=row['numerator_references'];delta=row['delta_logL_node'];b=math.log(weight)+row['log_shift']
                low=refs['inside']['lower'];upper=min(d['upper'],refs['inside']['upper']+refs['ambiguous']['upper'])
                nl.append(-np.inf if low==0 else b-delta+math.log(low));nh.append(-np.inf if upper==0 else b+delta+math.log(upper))
                zl.append(b-delta+math.log(d['lower']));zh.append(b+delta+math.log(d['upper']));zp.append(b+math.log(d['value']))
            expected=np.array([np.exp(logsumexp(nl)-logsumexp(zh)),min(1.,np.exp(logsumexp(nh)-logsumexp(zl)))])
            saved=read(base/f'{label}_d{i}_cc{n}.json');error=max(float(np.max(abs(expected-saved['candidate_interval']))),abs(float(logsumexp(zp))-saved['log_masses']['Zpoint']))
            assert error<1e-10;mass_error=max(mass_error,error);rules[key,n]=saved
    gold=read(R/'results/C10/taylor_event_final_gate/audit.json')['events'];old=read(physical/'nodal_posterior_summaries.json');comparisons={}
    for key,event in gold.items():
        selected=[rules[key,n] for n in (129,257,513)];low=min(r['candidate_interval'][0] for r in selected);high=max(r['candidate_interval'][1] for r in selected)
        dz=max(r['log_masses']['Zpoint'] for r in selected)-min(r['log_masses']['Zpoint'] for r in selected)
        low=min(low,event['interval'][0]);high=max(high,event['interval'][1])
        gates=dict(all_rule_controls=all(r.get('finite_controls_pass') is True for r in selected),CDF_hull_width=high-low<=.002,logZ_change=dz<=.001,
                   bilinear_event_comparison=all(max(abs(old[key][name]['logL_CDF']-low),abs(old[key][name]['logL_CDF']-high))<=.002 for name in ('fine','high','independent_grid')))
        comparisons[key]=dict(passed=all(gates.values()),gates=gates,CDF_hull=[low,high],observed_logZ_change=dz)
    size=sum(p.stat().st_size for p in base.rglob('*') if p.is_file());assert size<=plan['output_cap_bytes']
    bind(Path(__file__));out=R/'results/C10/nested_integral_audit';out.mkdir(exist_ok=False)
    result=dict(status='NESTED_INTEGRATION_AUDIT_COMPLETE',slices=count,cache_memberships=cached,new_values=80564,cumulative_values=14622522,
                independent_Simpson_max_scaled_difference=scalar_error,independent_CC_max_difference=mass_error,
                complete_comparisons_pass=sum(r['passed'] for r in comparisons.values()),complete_comparisons=len(comparisons),comparisons=comparisons,
                output_bytes=size,new_audit_likelihood_values=0,new_ORFs=0,production_authorized=False,inputs=inputs,
                scope='Finite pilot validation against completed GL references; no population or global physical certificate.')
    (out/'audit.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k not in ('inputs','comparisons')}))


if __name__=='__main__':main()
