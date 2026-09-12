"""Activate the96-node refinement proposed by held-out interpolation diagnostics."""
from pathlib import Path
import hashlib,json,shutil
import numpy as np

ROOT=Path(__file__).resolve().parents[1]


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    source=ROOT/'tmp/c09_distance_endpoints_v1'
    out=ROOT/'tmp/c09_distance_interpolation_refinement_v1'
    (out/'prepared').mkdir(parents=True,exist_ok=False)
    diagnostic_path=ROOT/'results/C09/distance_interpolation_diagnostics/diagnostic.json'
    diagnostic=json.loads(diagnostic_path.read_text())
    train=np.array(diagnostic['proposed_training_u']);hold=np.array(diagnostic['proposed_heldout_u'])
    assert len(train)==16 and len(hold)==32 and not np.isin(train,hold).any()
    u=np.unique(np.r_[train,hold]);assert len(u)==48
    np.savez_compressed(out/'prepared/rules.npz',u=u,training_u=train,heldout_u=hold)
    plan=json.loads((source/'prepared/plan.json').read_text())
    jobs=plan['jobs']
    for job in jobs:
        l,n=job['level']['lmax'],job['level']['nmu']
        job['products']=4*n*(l-1)+6*144*(l-1)+2*len(u)*(24*n*(l-1)+6*144*(l-1)+16*12*n)
    products=sum(j['products'] for j in jobs)
    plan.update(schema='C09_DISTANCE_LOCAL_REFINEMENT_v1',rules_file=str((out/'prepared/rules.npz').relative_to(ROOT)),
        rules_sha256=sha(out/'prepared/rules.npz'),u_nodes_per_scale=len(u),new_full_four_channel_nodes=2*len(u),
        real_products=products,historical_D3_products=74016010752528,historical_D3_nodes=6841,
        cumulative_D3_products=74016010752528+products,cumulative_D3_nodes=6937,
        training_u=train.tolist(),heldout_control_u=hold.tolist(),
        scope='All previous pilot controls may enter refined training and lose held-out status. Only32 new quarter-points per scale are held out.',
        historical_C09_likelihood_values=54868123,expected_new_pilot_likelihood_values=918)
    assert plan['cumulative_D3_products']<90000000000000 and plan['cumulative_D3_nodes']<8000
    plan['bindings'].update({str(p.relative_to(ROOT)):sha(p) for p in (Path(__file__),diagnostic_path,source/'prepared/plan.json',source/'pilot_validation/receipt.json')})
    (out/'prepared/plan.json').write_text(json.dumps(plan,indent=2)+'\n')
    shutil.copyfile(source/'worker.py',out/'worker.py')
    driver=(source/'run_backend.py').read_text().replace('38 direct endpoint/control nodes','96 direct local refinement/control nodes')
    (out/'run_backend.py').write_text(driver)
    print(json.dumps({k:plan[k] for k in ('real_products','cumulative_D3_products','cumulative_D3_nodes')}))


if __name__=='__main__':main()
