"""Independent trace/chain-rule reconstruction of local information matrices."""
from pathlib import Path
import json,sys
import numpy as np
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'src'),str(R/'tmp/c10_exact_lifecycle_v1')]
from physical import sha,load_geometry
O=R/'results/C10/fisher_v4'
def read(p):
    d=json.loads(p.read_text());return d.get('payload',d)
def main():
    plan=read(O/'plan.json');done=read(O/'complete.json')
    for n,h in plan['sources'].items():assert sha(R/n)==h,n
    geo=load_geometry(R,read(R/'tmp/c10_exact_lifecycle_v1/execution_spec.json'));H=geo['estimator_matrices'];w=geo['frequency_weights'];scales=np.array(plan['fisher']['coordinate_scales'])
    raw=np.load(O/'derivatives.npz');results=[];maximum=0.
    for index,row in enumerate(done['results']):
        c=raw[f'point_{index}_covariance'];dc=raw[f'point_{index}_derivatives'];p=len(dc)
        solved=np.array([[np.linalg.solve(ck,dck) for ck,dck in zip(c,d)] for d in dc])
        cn=np.array([[sum(np.trace(a@b).real for a,b in zip(solved[i],solved[j])) for j in range(p)] for i in range(p)])
        sigma=np.array([[[np.trace(h@ck@j@ck).real for j in H] for h in H] for ck in c])
        dm=np.array([[[np.trace(h@dck).real for h in H] for dck in d] for d in dc])
        ds=np.array([[[[np.trace(h@dck@j@ck+h@ck@j@dck).real for j in H] for h in H] for ck,dck in zip(c,d)] for d in dc])
        def normal(s,m,d):
            out=np.zeros((p,p))
            for k,sk in enumerate(s):
                mean=[np.linalg.solve(sk,v[k]) for v in m];cov=[np.linalg.solve(sk,v[k]) for v in d]
                for i in range(p):
                    for j in range(p):out[i,j]+=m[i,k]@mean[j]+.5*np.trace(cov[i]@cov[j])
            return out
        ag=normal(sigma,dm,ds);bg=normal(np.einsum('kij,k->ij',sigma,w*w)[None],np.einsum('pkd,k->pd',dm,w)[:,None],np.einsum('pkij,k->pij',ds,w*w)[:,None])
        errors={}
        for model,matrix in (('A0_CN',cn),('A_G',ag),('B_G',bg)):
            matrix=matrix*scales[:,None]*scales[None]
            original=np.array(row['levels'][2][-1]['diagnostics'][model]['information'])
            error=float(np.linalg.norm(matrix-original)/np.linalg.norm(original));maximum=max(maximum,error);errors[model]=error
            assert error<=.001 and row['gates'][model]['passed']
        a=np.array(row['levels'][2][-1]['diagnostics']['A_G']['information']);b=np.array(row['levels'][2][-1]['diagnostics']['B_G']['information'])
        L=np.linalg.cholesky(a);whiten=np.linalg.solve(L,np.linalg.solve(L,b).T).T
        ratios=np.linalg.eigvalsh((whiten+whiten.T)/2)
        # Operational tolerance includes finite-difference error, not exact arithmetic.
        assert ratios.min()>=-.001 and ratios.max()<=1.001
        results.append(dict(point=row['point'],relative_matrix_errors=errors,compression_generalized_eigenvalues=ratios.tolist()))
    output=dict(status='PHYSICAL_FISHER_INDEPENDENT_AUDIT_PASS',matrices=24,maximum_relative_matrix_error=maximum,results=results,
                source_sha256=sha(Path(__file__)),complete_sha256=sha(O/'complete.json'),new_likelihood_values=0,new_ORFs=0,
                interpretation='Finite local Fisher and G-to-compressed-G comparison; rank depends on declared coordinate scales and numerical threshold')
    out=R/'results/C10/fisher_audit';out.mkdir(exist_ok=False);(out/'audit.json').write_text(json.dumps(output,indent=2)+'\n');print(json.dumps({k:v for k,v in output.items() if k!='results'}))
if __name__=='__main__':main()
