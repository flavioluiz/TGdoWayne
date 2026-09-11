"""Cost projection from completed engineering runs, not posterior diagnostics."""
from pathlib import Path
import hashlib,json,math
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent

def main():
    source=HERE/'results/benchmark_summary.json';content=json.loads(source.read_text())
    rows=content['reports'];assert len(rows)==6
    groups=[]
    for size in [16,64]:
        group=[r for r in rows if r['targets']==size]
        best=min(group,key=lambda r:r['mh_plus_em_seconds'])
        blocks=math.ceil(2500/size)
        groups.append(dict(targets_per_block=size,best_measured_workers=best['threads'],complete_block_seconds=best['mh_plus_em_seconds'],blocks_for_2500_targets=blocks,projected_training_plus_em_minutes=blocks*best['mh_plus_em_seconds']/60,last_block_counted_full=True,all_thread_selected_point_hashes_identical=len({r['selected_points_sha256'] for r in group})==1,all_thread_fit_hashes_identical=len({r['fit_parameters_sha256'] for r in group})==1))
    report=dict(scope='Local cost projection for 500 datasets times five model families; no statistical approval implied.',groups=groups,read_only_native_parameters=True,thread_rng_invariance=True,total_training_likelihood_points=content['likelihood_points'],extra_native_anchor_points=80*(1+len(rows)),total_em_fits=content['em_fits'],setup_seconds=content['setup_seconds'],maximum_rss_bytes=max(r['darwin_maxrss_bytes'] for r in rows),estimated_array_budget_bytes=content['config']['maximum_estimated_numeric_bytes'],native_reference_anchor_logl_difference=content['native_reference_maximum_logl_difference'],source_sha256={str(source.relative_to(ROOT)):hashlib.sha256(source.read_bytes()).hexdigest(),str(Path(__file__).relative_to(ROOT)):hashlib.sha256(Path(__file__).read_bytes()).hexdigest()},limitations=['Budgets are explicit estimated numeric arrays, not RSS enforcement; observed RSS slightly exceeded 3 GiB and requires headroom.','Group16 contains the selected difficult pilot targets and is not model-balanced; group64 is approximately model-balanced.','Warmup states and fitted proposal densities are engineering artifacts, not posterior inference or SBC500.','1/4/6 thread runs use exactly the same streams and trajectories; they are repeated timing configurations, not independent scientific data.','Single runs per configuration under shared machine load do not establish a precise ranking when times differ only slightly.','Likelihood-only bulk throughput cannot be substituted for measured sequential warmup throughput.'])
    with (HERE/'results/cost_projection.json').open('x') as f:json.dump(report,f,indent=2);f.write('\n')
    print(json.dumps(report,indent=2))

if __name__=='__main__':main()
