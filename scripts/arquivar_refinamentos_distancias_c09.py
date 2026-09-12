"""Archive the endpoint bank and three local refinements, preserving all failures."""
from pathlib import Path
import hashlib,json,zipfile
import numpy as np
R=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    roots=[R/'tmp/c09_distance_endpoints_v1']+[R/f'tmp/c09_distance_interpolation_refinement_v{i}' for i in (1,2,3)]
    out=R/'results/C09/distance_local_refinement';out.mkdir(parents=True,exist_ok=True)
    audits=[];artifacts=[];LL=products=nodes=0
    for number,root in enumerate(roots):
        plan=json.loads((root/'prepared/plan.json').read_text());pilot=root/'pilot_validation'
        response=json.loads((pilot/'response_audit.json').read_text());receipt=json.loads((pilot/'receipt.json').read_text())
        assert response['passed'] and receipt['status']=='COMPLETED_PILOT_INTERPOLATION_CHECKS'
        activation=json.loads((pilot/'activation.json').read_text())
        assert sha(pilot/'source.py')==activation['source_sha256']
        for rel,digest in plan['bindings'].items():assert sha(R/rel)==digest,rel
        n=plan['u_nodes_per_scale'];stages=np.empty((3,2,n,4,12,12),complex);cost=0
        for job in plan['jobs']:
            base=root/'backend_execution'/job['name'];r=json.loads((base/'receipt.json').read_text())
            assert r['status']=='COMPLETED' and r['products']==job['products'] and sha(base/'matrices.npz')==r['matrix_sha256']
            with np.load(base/'matrices.npz') as data:stages[job['level_index'],:,:,job['channel']]=data['Gamma']
            cost+=r['products']
        assert cost==response['products']==plan['real_products']
        dn=float(np.max(abs(stages[1]-stages[0])));dl=float(np.max(abs(stages[2]-stages[1])))
        assert dn==response['angular_delta'] and dl==response['harmonic_delta']
        assert np.linalg.eigvalsh(stages).min()>=-1e-12
        expected=18*n+54
        assert receipt['budget']['additional_charged_values']==expected and receipt['budget']['failed_reserved_values']==0
        records=json.loads((pilot/'comparisons.json').read_text())
        assert len(records)==6
        assert sum(r['mesh_passed'] for r in records)==receipt['mesh_passed']
        assert sum(r['heldout_gate'] for r in records)==receipt['heldout_passed']
        LL+=expected;products+=cost;nodes+=2*n
        audits.append(dict(stage=root.name,new_nodes=2*n,products=cost,LL=expected,
            mesh_passed=receipt['mesh_passed'],heldout_passed=receipt['heldout_passed'],
            response_CPU=response['worker_CPU'],density_CPU=receipt['CPU'],comparisons=records))
        archive=out/f'stage_{number}.zip';members={}
        with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
            for path in sorted(root.rglob('*')):
                if path.is_file():
                    name=str(path.relative_to(R));members[name]=sha(path);z.write(path,name)
        assert archive.stat().st_size<90*1024**2
        with zipfile.ZipFile(archive) as z:
            for name,digest in members.items():assert hashlib.sha256(z.read(name)).hexdigest()==digest
        artifacts.append(dict(file=archive.name,bytes=archive.stat().st_size,sha256=sha(archive),members_sha256=members))
    assert LL==1908 and nodes==188
    audit=dict(schema='C09_DISTANCE_LOCAL_REFINEMENTS_ARCHIVE_v1',archive_and_accounting_passed=True,
        stages=audits,archives=artifacts,new_nodes=nodes,new_products=products,new_likelihood_values=LL,
        cumulative_C09_likelihood_values=54867727+LL,cumulative_D3_nodes=6803+nodes,
        cumulative_D3_products=73603353930960+products,
        scope='Final six local gates pass at two new masses per scale in the last failing interval. Prior held-out controls entered later training. Broader new independent controls and functional references remain required; production not activated.',
        C09_complete=False)
    (out/'audit.json').write_text(json.dumps(audit,indent=2,allow_nan=False)+'\n')
    print(json.dumps({k:v for k,v in audit.items() if k not in ('stages','archives')}))
if __name__=='__main__':main()
