"""Freeze38 direct distance responses for support endpoints and held-out controls."""
from pathlib import Path
import json,hashlib,shutil,sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
import numpy as np
from inference.orf_blas import estimate


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    out=ROOT/'tmp/c09_distance_endpoints_v1';(out/'prepared').mkdir(parents=True,exist_ok=False)
    source=ROOT/'tmp/c09_D3_distances_v1'
    shutil.copyfile(source/'worker.py',out/'worker.py')
    resolved=json.loads((ROOT/'tmp/c09_D3_components_v1/backend_execution/plan.json').read_text())
    oracle=ROOT/'tmp/c09_nominal14_backend_v4/gates/harmonic_nodes.npz'
    with np.load(oracle) as f:u=np.unique(np.r_[f['u'],.0001,.01,.75])
    assert len(u)==19 and u[0]==0 and u[-1]==1
    np.savez_compressed(out/'prepared/rules.npz',u=u)
    jobs=[]
    for k,resolution in enumerate(resolved['resolutions']):
        for level_index,level in enumerate(resolution['levels']):
            l,n=level['lmax'],level['nmu']
            products=4*n*(l-1)+6*144*(l-1)+2*len(u)*(24*n*(l-1)+6*144*(l-1)+16*12*n)
            memory=estimate(l,n,12,16)
            assert memory['estimated_memory_bytes']<1024**3
            jobs.append(dict(name=f'channel_{k+1}_level_{level_index}',channel=k,level_index=level_index,
                             level=level,products=products,estimate=memory))
    new_products=sum(j['products'] for j in jobs)
    historical_products=73603353930960;historical_nodes=6803
    assert historical_products+new_products<90000000000000 and historical_nodes+2*len(u)<8000
    plan=dict(schema='C09_DISTANCE_ENDPOINTS_v1',execution_enabled_by_default=False,
        scales=[.9,1.1],rules_file=str((out/'prepared/rules.npz').relative_to(ROOT)),
        rules_sha256=sha(out/'prepared/rules.npz'),u_nodes_per_scale=len(u),new_full_four_channel_nodes=2*len(u),
        real_products=new_products,historical_D3_products=historical_products,historical_D3_nodes=historical_nodes,
        cumulative_D3_products=historical_products+new_products,cumulative_D3_nodes=historical_nodes+2*len(u),
        revised_D3_product_cap=90000000000000,D3_node_cap=8000,
        maximum_RSS_bytes=1536*1024**2,combined_worker_CPU_cap=1440,maximum_numeric_array_bytes=1024**3,
        jobs=jobs,training_u=[0.,1.],heldout_control_u=u[1:-1].tolist(),
        scope='Only endpoint responses enter posterior training;17 interior masses per scale remain held-out physical controls. No production posterior, new data, or uniform certificate.',
        bindings={str(p.relative_to(ROOT)):sha(p) for p in [Path(__file__),oracle,source/'worker.py',
            ROOT/'tmp/c09_D3_components_v1/backend_execution/plan.json',ROOT/'configs/calibration/prior_predictive_500_v1.json',
            ROOT/'src/inference/orf_blas.py',ROOT/'results/C09/D3_distancias_continuacao/audit.json',
            ROOT/'results/C09/production_generation/audit.json']})
    (out/'prepared/plan.json').write_text(json.dumps(plan,indent=2)+'\n')
    # Keep original bounded driver mechanics, with an accurate activation scope.
    driver=(source/'run_backend.py').read_text().replace('1920 direct nodes, three refinements, no likelihood/data generation',
        '38 direct endpoint/control nodes, three refinements, no likelihood/data generation')
    (out/'run_backend.py').write_text(driver)
    print(json.dumps({k:plan[k] for k in ('new_full_four_channel_nodes','real_products','cumulative_D3_products','cumulative_D3_nodes')}))


if __name__=='__main__':main()
