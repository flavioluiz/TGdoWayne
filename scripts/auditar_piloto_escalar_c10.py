"""Terminal C10 pilot inventory and independent event-mass aggregation checks."""
from pathlib import Path
import hashlib
import json
import collections
import numpy as np
from scipy.special import logsumexp
R = Path(__file__).resolve().parents[1]


def main():
    base=R/'tmp/c10_physical_pilot_v1'; bindings={}
    def read(p):
        bindings[str(p.relative_to(R))]=hashlib.sha256(p.read_bytes()).hexdigest()
        raw=json.loads(p.read_text())
        return raw['payload'] if raw.get('schema')=='C10_OPERATIONAL_REPORT_JSON_v1' else raw
    done=read(base/'complete.json'); assert not (base/'FAILED_PRESERVED.json').exists()
    ledger=read(base/'ledger.json'); axes=read(R/'tmp/c10_exact_lifecycle_v1/axes.json')
    spec=read(R/'tmp/c10_exact_lifecycle_v1/execution_spec.json')
    for p,h in spec['source_sha256'].items(): assert hashlib.sha256((R/p).read_bytes()).hexdigest()==h,p
    assert ledger['charged']==ledger['completed']
    charged=sum(ledger['charged'].values()); assert charged==done['global_logL_charged']<=15000000
    controls=read(base/'kernel_controls.json'); assert controls['passed'] and controls['uniform_epsilon_envelope_violations']==0
    summaries=read(base/'nodal_posterior_summaries.json'); assert len(summaries)==144
    failures=[dict(curve=k,gates=[g for g,v in s['grid_gates'].items() if v is False]) for k,s in summaries.items() if any(v is False for v in s['grid_gates'].values())]
    cache_count=0; slice_count=0; max_delta=0.; missing=0
    for path in sorted(base.glob('*_mass_reference.json')):
        saved=read(path); stem=path.stem.removesuffix('_mass_reference'); order=stem.rsplit('_u',1)[1]
        weights=axes['u_reference'][order]['prior_weights']; nodes=axes['u_reference'][order]['nodes']
        numer=[]; upper=[]; zlo=[]; zhi=[]; zpoint=[]; unavailable=False
        for j,(weight,node) in enumerate(zip(weights,nodes)):
            file=base/'event_slices'/f'{stem}_{j}.json'; row=read(file); assert row['node_u']==node
            cache=file.with_suffix('.npz')
            bindings[str(cache.relative_to(R))]=hashlib.sha256(cache.read_bytes()).hexdigest()
            with np.load(cache) as f:
                e,l=f['epsilon'],f['log_likelihood']; assert len(e)==len(set(e)) and np.isfinite(l).all() and np.all((e>=0)&(e<=1))
                cache_count+=len(e)
            slice_count+=1; den=row.get('denominator'); shift=row.get('log_shift'); delta=row.get('delta_logL_node')
            if den is None or shift is None or delta is None:
                unavailable=True; missing+=1; continue
            refs=row.get('numerator_references',{})
            nl=refs['inside']['lower'] if 'inside' in refs and 'failure_preserved' not in row else 0.
            nh=min(den['upper'],refs['inside']['upper']+refs['ambiguous']['upper']) if 'inside' in refs and 'ambiguous' in refs and 'failure_preserved' not in row else den['upper']
            base_log=np.log(weight)+shift
            numer.append(-np.inf if nl==0 else base_log-delta+np.log(nl));upper.append(-np.inf if nh==0 else base_log+delta+np.log(nh))
            zlo.append(base_log-delta+np.log(den['lower']));zhi.append(base_log+delta+np.log(den['upper']));zpoint.append(base_log+np.log(den['value']))
        if unavailable: assert saved['interval']==[0.,1.]; continue
        expected=[float(np.exp(logsumexp(numer)-logsumexp(zhi))),float(min(1.,np.exp(logsumexp(upper)-logsumexp(zlo))))]
        error=max(abs(np.array(expected)-saved['candidate_interval']))
        error=max(error,abs(float(logsumexp(zpoint))-saved['log_masses']['Zpoint']))
        assert error<1e-10;max_delta=max(max_delta,error)
    assert slice_count==20736 and cache_count==ledger['completed']['epsilon_event_references']
    events=done['contour_results']; assert len(events)==36
    event_states=collections.Counter(r['status'] for r in events.values())
    for r in events.values():
        if r['status']=='UNRESOLVED': assert r['interval']==[0.,1.]
    out=R/'results/C10/pilot_terminal_audit';out.mkdir(parents=True,exist_ok=False)
    bindings[str(Path(__file__).relative_to(R))]=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    audit=dict(status='TERMINAL_INVENTORY_AND_EVENT_AGGREGATION_PASS',analyses=144,grid_failures=failures,event_states=dict(event_states),
        reference_slices=slice_count,reference_cached_values=cache_count,missing_reference_denominators=missing,
        independent_aggregation_max_difference=max_delta,new_pilot_logL_values=charged,CPU=done['aggregate_CPU_seconds'],
        inputs=bindings,C10_complete=False,scope='Finite pilot with retained failures; no population false-positive rate, scalar identification or global physical certificate inferred.')
    (out/'audit.json').write_text(json.dumps(audit,indent=2)+'\n')
    print(json.dumps({k:v for k,v in audit.items() if k!='inputs'}))


if __name__=='__main__':main()
