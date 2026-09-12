"""Freeze a new64-mass validation set; never fit its physical likelihood values."""
from pathlib import Path
import json,hashlib,shutil,re
import numpy as np
R=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    previous=R/'tmp/c09_distance_interpolation_refinement_v3'
    out=R/'tmp/c09_distance_broad_validation_v1';(out/'prepared').mkdir(parents=True,exist_ok=False)
    plan=json.loads((previous/'prepared/plan.json').read_text())
    fit=previous/'pilot_validation/training_0.npz'
    diagnostic=R/'results/C09/distance_interpolation_diagnostics/diagnostic.json'
    oldfit=R/'tmp/c09_distance_interpolation_refinement_v1/pilot_validation/training_64.npz'
    with np.load(oldfit) as f:old_u=f['u']
    mid=np.array(json.loads(diagnostic.read_text())['proposed_training_u'])
    cell=np.searchsorted(old_u,mid)-1
    a,b=np.arcsin(old_u[cell]),np.arcsin(old_u[cell+1])
    local=np.sin(a[:,None]+(b-a)[:,None]*np.array([.37,.73])).ravel()
    x,_=np.polynomial.legendre.leggauss(32)
    global_u=np.sin((x+1)*np.pi/4)
    u=np.unique(np.r_[local,global_u]);assert len(u)==64
    with np.load(fit) as f:assert not np.isin(u,f['u']).any()
    np.savez_compressed(out/'prepared/rules.npz',u=u,training_u=np.array([]),heldout_u=u)
    for job in plan['jobs']:
        l,n=job['level']['lmax'],job['level']['nmu']
        job['products']=4*n*(l-1)+6*144*(l-1)+128*(24*n*(l-1)+6*144*(l-1)+16*12*n)
    cost=sum(j['products'] for j in plan['jobs']);history=plan['cumulative_D3_products'];nodes=plan['cumulative_D3_nodes']
    plan.update(rules_file=str((out/'prepared/rules.npz').relative_to(R)),rules_sha256=sha(out/'prepared/rules.npz'),
        real_products=cost,u_nodes_per_scale=64,new_full_four_channel_nodes=128,
        historical_D3_products=history,cumulative_D3_products=history+cost,historical_D3_nodes=nodes,cumulative_D3_nodes=nodes+128,
        historical_C09_likelihood_values=54869635,expected_new_pilot_likelihood_values=1206,
        training_u=[],heldout_control_u=u.tolist(),previous_fit_file=str(fit.relative_to(R)),previous_density_file=str(fit.relative_to(R)),
        broad_validation_only=True,
        scope='Fixed previous final posterior fit. All64 new masses held out:32 global Gauss-alpha locations and32 local .37/.73-cell probes. No new fit or new mesh-convergence claim; identical fit passed through generic evaluator.')
    assert plan['cumulative_D3_nodes']<8000 and plan['cumulative_D3_products']<90000000000000
    plan['bindings'].update({str(p.relative_to(R)):sha(p) for p in (Path(__file__),fit,oldfit,diagnostic)})
    (out/'prepared/plan.json').write_text(json.dumps(plan,indent=2)+'\n')
    shutil.copyfile(previous/'worker.py',out/'worker.py')
    driver=re.sub(r'\d+ direct additional refinement/control nodes','128 direct broad validation nodes',(previous/'run_backend.py').read_text())
    (out/'run_backend.py').write_text(driver)
    print(json.dumps(dict(new_nodes=128,cumulative_nodes=nodes+128,new_products=cost,remaining_nodes=8000-nodes-128)))
if __name__=='__main__':main()
