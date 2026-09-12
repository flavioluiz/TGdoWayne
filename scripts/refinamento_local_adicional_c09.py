"""Prepare one explicitly bounded additional refinement from failed held-out cells."""
from pathlib import Path
import argparse,json,hashlib,shutil
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    p=argparse.ArgumentParser();p.add_argument('--previous',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    args=p.parse_args();previous=args.previous.resolve();out=args.output.resolve()
    plan=json.loads((previous/'prepared/plan.json').read_text());receipt=json.loads((previous/'pilot_validation/receipt.json').read_text())
    assert receipt['status']=='COMPLETED_PILOT_INTERPOLATION_CHECKS'
    fit=previous/'pilot_validation/training_0.npz';errors=previous/'pilot_validation/heldout_errors.npz'
    with np.load(fit) as f:x=f['u']
    with np.load(errors) as f:bad=f['u'][np.max(f['absolute_logL_error'],axis=1)>.001]
    cells=np.unique(np.searchsorted(x,bad)-1);assert 0<len(cells)<=100
    a=np.arcsin(x[cells]);b=np.arcsin(x[cells+1]);train=np.sin((a+b)/2)
    hold=np.sin(a[:,None]+(b-a)[:,None]*np.array([.25,.75])).ravel();u=np.unique(np.r_[train,hold])
    assert len(u)==3*len(cells)
    (out/'prepared').mkdir(parents=True,exist_ok=False)
    np.savez_compressed(out/'prepared/rules.npz',u=u,training_u=train,heldout_u=hold)
    for job in plan['jobs']:
        l,n=job['level']['lmax'],job['level']['nmu']
        job['products']=4*n*(l-1)+6*144*(l-1)+2*len(u)*(24*n*(l-1)+6*144*(l-1)+16*12*n)
    cost=sum(j['products'] for j in plan['jobs'])
    history=plan['cumulative_D3_products'];nodes=plan['cumulative_D3_nodes']
    plan.update(rules_file=str((out/'prepared/rules.npz').relative_to(ROOT)),rules_sha256=sha(out/'prepared/rules.npz'),
        real_products=cost,u_nodes_per_scale=len(u),new_full_four_channel_nodes=2*len(u),
        historical_D3_products=history,cumulative_D3_products=history+cost,historical_D3_nodes=nodes,cumulative_D3_nodes=nodes+2*len(u),
        historical_C09_likelihood_values=receipt['budget']['cumulative_values'],expected_new_pilot_likelihood_values=18*len(u)+54,
        training_u=train.tolist(),heldout_control_u=hold.tolist(),previous_fit_file=str(fit.relative_to(ROOT)),
        previous_density_file=str((previous/'pilot_validation/likelihoods.npz').relative_to(ROOT)),
        scope='Previous held-out probes become training. New quarter-points remain held out. Same PCHIP method and tolerances; no automatic retry.')
    assert plan['cumulative_D3_products']<90000000000000 and plan['cumulative_D3_nodes']<8000
    plan['bindings'].update({str(f.relative_to(ROOT)):sha(f) for f in (Path(__file__),fit,errors,previous/'pilot_validation/receipt.json')})
    (out/'prepared/plan.json').write_text(json.dumps(plan,indent=2)+'\n')
    shutil.copyfile(previous/'worker.py',out/'worker.py')
    driver=(previous/'run_backend.py').read_text().replace('96 direct local refinement/control nodes',f'{len(u)*2} direct additional refinement/control nodes')
    (out/'run_backend.py').write_text(driver)
    print(json.dumps(dict(failed_cells=len(cells),new_full_nodes=len(u)*2,products=cost,cumulative_nodes=plan['cumulative_D3_nodes'])))
if __name__=='__main__':main()
