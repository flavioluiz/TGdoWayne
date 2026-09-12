"""Read-only audit of prepared densities and batched cell enclosures."""
from pathlib import Path
import hashlib,json
import numpy as np
R=Path(__file__).resolve().parents[1];O=R/'tmp/c10_prepared_event_benchmark_v1';F=R/'results/C10/full_flow_benchmark_v1'
def read(p):
    d=json.loads(p.read_text());return d.get('payload',d)

def main():
    plan=read(O/'plan.json');done=read(O/'complete.json');ledger=read(O/'ledger.json')
    for n,h in plan['inputs'].items():assert hashlib.sha256((R/n).read_bytes()).hexdigest()==h,n
    assert done['status']=='COMPLETE' and done['events']==2570
    assert done['charged']==done['completed']==ledger['charged']==ledger['completed']
    assert done['CPU']<=plan['CPU_cap']
    count=0;points_checked=0;error=0.;new=0
    for path in (O/'slices').glob('event_*.json'):
        row=read(path);suffix=path.stem[len('event_'):]
        with np.load(path.with_suffix('.npz')) as f:points=f['epsilon'];values=f['log_likelihood']
        with np.load(F/f'cache_{suffix}.npz') as f:old={float(x).hex():float(y) for x,y in zip(f['epsilon'],f['log_likelihood'])}
        for x,y in zip(points,values):error=max(error,abs(float(y)-old[float(x).hex()]))
        cells=row['partition'];indices=np.searchsorted([c['right'] for c in cells],points,side='left')
        assert np.all((values>=np.array([c['logL_lower'] for c in cells])[indices])&(values<=np.array([c['logL_upper'] for c in cells])[indices]))
        assert row['status']=='SLICE_OPERATIONAL_CONTROLS_PASS_NOT_2D_CDF_APPROVAL'
        new+=len(points)-129;points_checked+=len(points);count+=1
    assert count==2570 and new==done['charged']['events'] and error<=1e-10
    output=sum(p.stat().st_size for p in O.rglob('*') if p.is_file());assert output<=plan['output_cap']
    result=dict(status='PREPARED_EVENT_AUDIT_PASS',slices=count,cached_points_checked=points_checked,
                maximum_logL_change=error,additional_event_values=new,bridges=done['charged']['bridges'],
                cumulative_values=done['cumulative_values'],cumulative_CPU_upper=plan['prior_CPU_upper']+done['CPU'],
                output_bytes=output,source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                scope='Finite same-observation comparisons; no population calibration')
    out=R/'results/C10/prepared_event_audit';out.mkdir(exist_ok=False)
    (out/'audit.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))

if __name__=='__main__':main()
