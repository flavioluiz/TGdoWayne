"""Assemble existing direct response banks at final training and retained-control masses."""
from pathlib import Path
import json,hashlib
import numpy as np
R=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    bindings={}
    def bind(p):bindings[str(p.relative_to(R))]=sha(p);return p
    audit=json.loads(bind(R/'results/C09/distance_broad_validation/audit.json').read_text())
    assert audit['passed'] and audit['retained_masses']==75
    final=R/'tmp/c09_distance_broad_correction_v3/pilot_validation/training_0.npz'
    assert sha(final)==audit['final_training_sha256']
    with np.load(bind(final)) as f:fine=f['u']
    with np.load(bind(R/'tmp/c09_distance_interpolation_refinement_v1/pilot_validation/training_64.npz')) as f:coarse=f['u']
    with np.load(bind(R/'results/C09/distance_broad_validation/retained_controls.npz')) as f:controls=np.sort(f['u'])
    assert np.isin(coarse,fine).all() and not np.isin(controls,fine).any()
    roots=[R/'tmp/c09_D3_distances_v1']+[R/f'tmp/c09_D3_distance_reference_v{i}' for i in range(1,10)]
    roots += [R/'tmp/c09_distance_endpoints_v1']+[R/f'tmp/c09_distance_interpolation_refinement_v{i}' for i in (1,2,3)]
    roots += [R/'tmp/c09_distance_broad_validation_v1']+[R/f'tmp/c09_distance_broad_correction_v{i}' for i in (1,2,3)]
    needed=np.unique(np.r_[fine,controls]);lookup={float(u).hex():i for i,u in enumerate(needed)}
    gamma=np.empty((2,len(needed),4,12,12),complex);coverage=np.zeros(len(needed),int);duplicate_delta=0.
    origins=[[] for _ in needed]
    for root in roots:
        directory=root/('initial_execution' if 'c09_D3_' in root.name else 'pilot_validation')
        response=json.loads(bind(directory/'response_audit.json').read_text());assert response['passed']
        with np.load(bind(root/'prepared/rules.npz')) as f:u=f['u']
        with np.load(bind(directory/'responses.npz')) as f:g=f['Gamma']
        assert g.shape==(2,len(u),4,12,12)
        for j,value in enumerate(u):
            key=float(value).hex()
            if key not in lookup:continue
            i=lookup[key]
            if coverage[i]:duplicate_delta=max(duplicate_delta,float(np.max(abs(gamma[:,i]-g[:,j]))))
            else:gamma[:,i]=g[:,j]
            coverage[i]+=1;origins[i].append(dict(source=str(directory.relative_to(R)),row=j))
    assert np.all(coverage>0) and duplicate_delta<=1e-10
    out=R/'tmp/c09_distance_production_v1/prepared';out.mkdir(parents=True,exist_ok=False)
    fidx=np.searchsorted(needed,fine);hidx=np.searchsorted(needed,controls)
    np.savez_compressed(out/'response_atlas.npz',fine_u=fine,coarse_indices=np.searchsorted(fine,coarse),
        Gamma_fine=gamma[:,fidx],control_u=controls,Gamma_controls=gamma[:,hidx])
    plan=dict(schema='C09_DISTANCE_PRODUCTION_RESPONSE_ATLAS_v1',execution_enabled=False,
        fine_nodes=len(fine),coarse_nodes=len(coarse),control_nodes=len(controls),distance_scales=[.9,1.1],
        nominal_response='reuse C07 table',mixture_weights=[.25,.5,.25],
        source_sha256=sha(Path(__file__)),inputs_sha256=bindings,atlas_sha256=sha(out/'response_atlas.npz'),
        duplicate_response_delta=duplicate_delta,coverage_min=int(coverage.min()),origins=dict(zip([float(u).hex() for u in needed],origins)),
        new_ORFs=0,new_likelihood_values=0,new_observations=0,production_data='existing stage_6.npz, all500 IDs retained',
        scope='Direct physical responses copied at exact float64 masses. No interpolation of ORFs. Production likelihoods, per-case checks, integration and calibration still required.')
    (out/'plan.json').write_text(json.dumps(plan,indent=2)+'\n')
    print(json.dumps({k:v for k,v in plan.items() if k not in ('inputs_sha256','origins')}))
if __name__=='__main__':main()
