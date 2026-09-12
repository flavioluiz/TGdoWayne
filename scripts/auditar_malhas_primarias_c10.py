"""Independent normalization, complete fine-grid reuse and ledger audit."""
from pathlib import Path
import hashlib
import json
import numpy as np
from scipy.special import logsumexp
R=Path(__file__).resolve().parents[1]


def main():
    inputs={}
    def bind(p):inputs[str(p.relative_to(R))]=hashlib.sha256(p.read_bytes()).hexdigest();return p
    def read(p):
        raw=json.loads(bind(p).read_text());return raw['payload'] if raw.get('schema')=='C10_OPERATIONAL_REPORT_JSON_v1' else raw
    base=R/'tmp/c10_primary_grid_refinement_v1';old=R/'tmp/c10_physical_pilot_v1'
    plan=read(base/'plan.json');done=read(base/'complete.json');ledger=read(base/'ledger.json');axes=read(R/'tmp/c10_exact_lifecycle_v1/axes.json')
    for name,digest in plan['inputs'].items():assert hashlib.sha256((R/name).read_bytes()).hexdigest()==digest,name
    assert not (base/'FAILED_PRESERVED.json').exists() and ledger['charged']==ledger['completed']
    assert sum(ledger['charged'].values())==done['charged_new_values']==273038
    size=sum(p.stat().st_size for p in base.rglob('*') if p.is_file());assert size<=plan['maximum_output_bytes']
    checks=[]
    def weights(x):
        d=np.diff(x);return np.r_[d[0]/2,(d[:-1]+d[1:])/2,d[-1]/2]/(x[-1]-x[0])
    for item in plan['targets']:
        route=item['route'];i=item['id'];label=item['label'];name=f'{label}_d{i}'
        state=read(old/f'{route}_fine.state.json');m=state['models'].index(item['model']);j=state['data_ids'].index(i)
        fine=np.load(bind(old/f'{route}_fine.npy'),mmap_mode='r')[:,:,m,j]
        report=read(base/f'{name}_summary.json');assert report['finite_grid_controls_pass']
        for kind,field in [('high','high'),('product','independent')]:
            logs=np.load(bind(base/f'{name}_{kind}.npy'))[:,:,0,0];assert np.isfinite(logs).all()
            if kind=='high':
                assert np.array_equal(logs[::2,::2],fine)
                u=np.array(axes['master_mass_nodes']);e=np.array(axes['master_epsilon_nodes'])
            else:
                u=np.r_[.001,axes['u_reference']['384']['nodes'],1.];e=np.r_[0.,axes['epsilon_product_reference']['nodes'],1.]
            wu,we=weights(u),weights(e)
            z=float(logsumexp(logs+np.log(wu)[:,None]+np.log(we)[None]));h=float(logsumexp(logs[:,0]+np.log(wu)))
            reference=report[field];delta=max(abs(z-reference['logZ_H1']),abs(h-reference['logZ_H0']),abs(z-h-reference['logBF']))
            assert delta<1e-10
            checks.append(dict(target=name,grid=kind,normalization_difference=delta))
    bind(Path(__file__));out=R/'results/C10/primary_grid_refinement_audit';out.mkdir(exist_ok=False)
    result=dict(status='NORMALIZATION_EXACT_REUSE_AND_RESOURCE_AUDIT_PASS',checks=checks,inputs=inputs,
                reused_values=2*257*129,charged_values=273038,cumulative_values=13880746,output_bytes=size,
                maximum_normalization_difference=max(x['normalization_difference'] for x in checks),new_likelihood_values=0,new_ORFs=0,
                scope='Finite grids for A_CN/d9 and C_full_G/d14. Continuous events and population validation remain separate.')
    (out/'audit.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k!='inputs'}))


if __name__=='__main__':main()
