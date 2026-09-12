"""Read-only audit of the bounded full-flow benchmark and its cost projection."""
from pathlib import Path
import hashlib
import json
import numpy as np
R=Path(__file__).resolve().parents[1]
O=R/'results/C10/full_flow_benchmark_v1'


def read(p):
    d=json.loads(p.read_text());return d.get('payload',d)


def main():
    plan=read(O/'plan.json');done=read(O/'complete.json');ledger=read(O/'ledger.json')
    for n,h in plan['inputs'].items():assert hashlib.sha256((R/n).read_bytes()).hexdigest()==h,n
    assert done['status']=='COMPLETE' and done['events']==2570
    assert done['charged']==done['completed']==ledger['charged']==ledger['completed']
    assert done['CPU']<=plan['CPU_cap'] and done['output_bytes_before_terminal']<=plan['disk_cap']
    grid=np.load(O/'grid.npy',mmap_mode='r');assert np.isfinite(grid).all()
    axes=read(R/'tmp/c10_exact_lifecycle_v1/axes.json');eps=np.array(axes['master_epsilon_nodes'])[::2]
    additional=0;reused=0
    for j in range(257):
        for r in range(2):
            for m in range(5):
                with np.load(O/f'cache_{j}_{r}_{m}.npz') as f:
                    cache={float(x).hex():float(y) for x,y in zip(f['epsilon'],f['log_likelihood'])}
                    assert len(cache)==len(f['epsilon']) and np.isfinite(f['log_likelihood']).all()
                np.testing.assert_array_equal([cache[float(x).hex()] for x in eps],grid[j,:,m,r])
                additional+=len(cache)-129;reused+=129
    assert additional==done['charged']['events'] and reused==done['charged']['grid']
    summaries=read(O/'summaries.json');comparison_keys=('logZ_H0','logZ_H1','logBF','parameter_CDF','quantiles','logL_CDF')
    assert all(all(x['comparison'][k] for k in comparison_keys) for x in summaries['summaries'])
    max_delta=0.;labels=('A0_CN','A_CN','B_CN','A_G','B_G')
    for item in summaries['aggregates']:
        r,m=item['key'];a=item['result'];i=plan['ids'][r]
        b=read(R/f'tmp/c10_nested_integral_validation_v1/{labels[m]}_d{i}_cc{item["nodes"]}.json')
        assert a['slice_controls_pass'] and a['finite_controls_pass']
        delta=float(np.max(abs(np.array(a['candidate_interval'])-b['candidate_interval'])))
        assert delta<=1e-10;max_delta=max(max_delta,delta)
    t=done['timings']
    projection=dict(events=t['events']/2570*(2500*257),
                    grid=t['grid']/331530*210322632,
                    summaries=t['summaries']/10*6344)
    projection['sum']=sum(projection.values())
    result=dict(status='FULL_FLOW_READ_ONLY_AUDIT_PASS',events=2570,cache_grid_values=reused,new_event_values=additional,
                primary_comparisons_pass=10,aggregate_comparisons_pass=20,maximum_CDF_endpoint_change=max_delta,
                cumulative_values=done['cumulative_values'],pilot_remaining_values=15000000-done['cumulative_values'],
                cumulative_CPU_upper=plan['prior_CPU_upper']+done['CPU'],projection_seconds=projection,
                projection_is_upper_bound=False,projection_limitations='D-model batch of two only; C complexity and production batching differ; ORF construction excluded',
                estimated_main_target_seconds=3600,estimated_target_met=projection['sum']<=3600,
                production_enabled=False,source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    (O/'audit.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n');print(json.dumps(result,indent=2))


if __name__=='__main__':main()
