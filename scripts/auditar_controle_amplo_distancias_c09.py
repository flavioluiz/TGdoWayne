"""Audit all retained broad/local holdouts against the final fit, with charged history."""
from pathlib import Path
import json,hashlib,sys,zipfile
import numpy as np
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'src'))
from inference.mass_batch import MassPosteriorBatch
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    roots=[R/'tmp/c09_distance_broad_validation_v1']+[R/f'tmp/c09_distance_broad_correction_v{i}' for i in (1,2,3)]
    fitpath=roots[-1]/'pilot_validation/training_0.npz'
    with np.load(fitpath) as f:fit=MassPosteriorBatch(f['u'],f['mixture_logL'])
    reports=[];total_nodes=total_LL=total_products=0;maximum=np.zeros(6);archives=[]
    out=R/'results/C09/distance_broad_validation';out.mkdir(parents=True,exist_ok=True)
    heldout_nodes=[];heldout_values=[]
    for index,root in enumerate(roots):
        plan=json.loads((root/'prepared/plan.json').read_text());pilot=root/'pilot_validation'
        receipt=json.loads((pilot/'receipt.json').read_text());response=json.loads((pilot/'response_audit.json').read_text())
        assert receipt['status']=='COMPLETED_PILOT_INTERPOLATION_CHECKS' and response['passed']
        n=plan['u_nodes_per_scale'];stages=np.empty((3,2,n,4,12,12),complex);cost=0
        for job in plan['jobs']:
            base=root/'backend_execution'/job['name'];r=json.loads((base/'receipt.json').read_text())
            assert r['status']=='COMPLETED' and sha(base/'matrices.npz')==r['matrix_sha256'] and r['products']==job['products']
            with np.load(base/'matrices.npz') as f:stages[job['level_index'],:,:,job['channel']]=f['Gamma']
            cost+=r['products']
        assert np.max(abs(stages[1]-stages[0]))<=1e-8 and np.max(abs(stages[2]-stages[1]))<=1e-8
        assert np.linalg.eigvalsh(stages).min()>=-1e-12 and cost==plan['real_products']
        checks=json.loads((pilot/'scipy_checks.json').read_text());assert len(checks)==54 and max(c['delta'] for c in checks)<=1e-8
        with np.load(pilot/'likelihoods.npz') as f:
            mask=~np.isin(f['u'],fit.u);u=f['u'][mask];values=f['mixture_logL'][mask]
        assert len(u)>0
        errors=abs(fit.interpolator(np.arcsin(u))+fit.shift-values)
        maximum=np.maximum(maximum,errors.max(axis=0));heldout_nodes.extend(u);heldout_values.extend(values)
        LL=18*n+54;assert receipt['budget']['additional_charged_values']==LL and receipt['budget']['failed_reserved_values']==0
        total_LL+=LL;total_nodes+=2*n;total_products+=cost
        reports.append(dict(stage=root.name,retained_holdout_masses=len(u),maximum_error_by_curve=errors.max(axis=0).tolist(),
            original_new_holdout_passed=receipt['heldout_passed'],LL=LL,new_full_nodes=2*n,products=cost))
        archive=out/f'stage_{index}.zip';members={}
        with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
            for path in sorted(root.rglob('*')):
                if path.is_file():
                    name=str(path.relative_to(R));members[name]=sha(path);z.write(path,name)
        assert archive.stat().st_size<90*1024**2
        with zipfile.ZipFile(archive) as z:
            for name,digest in members.items():assert hashlib.sha256(z.read(name)).hexdigest()==digest
        archives.append(dict(file=archive.name,sha256=sha(archive),bytes=archive.stat().st_size,members_sha256=members))
    assert len(np.unique(heldout_nodes))==len(heldout_nodes) and not np.isin(heldout_nodes,fit.u).any()
    names=[r['curve'] for r in json.loads((roots[-1]/'pilot_validation/comparisons.json').read_text())]
    np.savez_compressed(out/'retained_controls.npz',u=np.array(heldout_nodes),mixture_logL=np.array(heldout_values),curves=np.array(names))
    audit=dict(schema='C09_DISTANCE_RETAINED_HOLDOUT_AUDIT_v1',passed=bool(np.max(maximum)<=.001),
        final_training_sha256=sha(fitpath),source_sha256=sha(Path(__file__)),posterior_component_sha256=sha(R/'src/inference/mass_batch.py'),
        retained_controls_sha256=sha(out/'retained_controls.npz'),retained_masses=len(heldout_nodes),
        curve_maximum_errors=dict(zip(names,maximum.tolist())),reports=reports,archives=archives,
        new_full_nodes=total_nodes,new_likelihood_values=total_LL,new_products=total_products,
        cumulative_C09_likelihood_values=54869635+total_LL,cumulative_D3_nodes=6991+total_nodes,
        cumulative_D3_products=75643182776784+total_products,
        scope='Finite retained controls in six pilot curves, including60 broadly distributed probes. Training selected adaptively from failed probes, which were explicitly excluded from retained controls. No uniform error theorem, production validation, or independent functional-reference claim.',
        C09_complete=False)
    (out/'audit.json').write_text(json.dumps(audit,indent=2,allow_nan=False)+'\n')
    print(json.dumps({k:v for k,v in audit.items() if k not in ('archives','reports')}))
if __name__=='__main__':main()
