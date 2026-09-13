"""Paired mass-quantile sensitivity with fixed nuisance parameters."""
from pathlib import Path
import argparse, hashlib, importlib.util, json
import numpy as np
ROOT=Path(__file__).resolve().parents[1]

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--clean-root',type=Path,required=True)
    args=parser.parse_args(); clean=args.clean_root
    config_path=ROOT/'configs/experiments/c13_conditional_contrasts.json'
    cfg=json.loads(config_path.read_text());out=ROOT/'results/C13/conditional_contrasts'
    module_path=out/'density_reference.py'
    spec=importlib.util.spec_from_file_location('density_reference',module_path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    plan_path=clean/'tmp/c11_pilot16_candidate_v2/preflight.json'
    plan=json.loads(plan_path.read_text());index_path=clean/'tmp/c13_population_reproduced_third/likelihood_index.json'
    records=json.loads(index_path.read_text())['records']
    inputs={str(config_path.relative_to(ROOT)):sha(config_path),str(module_path.relative_to(ROOT)):sha(module_path),'preflight':sha(plan_path)}
    values={}; details=[];p=cfg['probability'];eps=cfg['cdf_sensitivity']
    edges=np.array([0.,.0001,.001,.01,.05,.25,.5,.75,.9,.99,1.])
    for model in cfg['models']:
        record=next(r for r in records if r['population']==cfg['population'] and r['model']==model)
        path=Path(record['path']);assert sha(path)==record['sha256'];inputs[model]=record['sha256']
        report_path=clean/'tmp/c13_synthesis_reproduced'/f"{cfg['population']}_{model}.json"
        previous=json.loads(report_path.read_text())['rows'];inputs[model+'_synthesis']=sha(report_path)
        with np.load(path) as data:
            u=data['u'];ell=data['logL'];lookup={float(x).hex():i for i,x in enumerate(u)}
            rows=[]
            for datum in range(cfg['ids']['start'],cfg['ids']['stop_exclusive']):
                densities=[]
                for rule in ('alpha32','alpha64'):
                    nodes=np.unique(np.r_[edges,plan['rules'][rule]['u']])
                    ix=[lookup[float(x).hex()] for x in nodes]
                    densities.append(module.Density(nodes,ell[1,ix,datum]))
                a,b=densities;ref=previous[datum]
                assert ref['id']==datum and ref['SBC'] and ref['finite_mass_controls_passed']
                q=b.quantile(p)
                assert abs(q-ref['quantiles'][str(p)][1])<1e-12
                lo=min(d.quantile(p-eps) for d in densities)
                hi=max(d.quantile(p+eps) for d in densities)
                residual=max(abs(float(b.cdf(b.quantile(v)))-v) for v in (p-eps,p,p+eps))
                assert residual<1e-10 and lo<=q<=hi
                rows.append([q,lo,hi])
                details.append(dict(model=model,id=datum,quantile=q,interval=[lo,hi],inverse_cdf_residual=residual,
                    refinement_difference=abs(a.quantile(p)-q)))
            values[model]=np.array(rows)
    contrasts=[]
    for left,right in cfg['contrasts']:
        a,b=values[left],values[right]
        nominal=a[:,0]-b[:,0];lo=a[:,1]-b[:,2];hi=a[:,2]-b[:,1]
        radius=np.maximum(nominal-lo,hi-nominal);tol=cfg['horizontal_tolerance']
        contrasts.append(dict(left=left,right=right,n=len(nominal),mean=float(nominal.mean()),
            mean_numerical_interval=[float(lo.mean()),float(hi.mean())],
            maximum_numerical_radius=float(radius.max()),maximum_interval_width=float((hi-lo).max()),
            numerically_resolved_at_tolerance=int(np.sum(radius<tol)),
            individual_intervals_inside_equivalence_window=int(np.sum((lo>=-tol)&(hi<=tol))),
            nominal_values=nominal.tolist(),numerical_intervals=np.column_stack((lo,hi)).tolist()))
    report=dict(config=cfg,input_sha256=inputs,quantile_details=details,contrasts=contrasts,
        interval_interpretation='Inverse envelopes of two finite CDF representations enlarged by 0.002 vertically. Conditional on the established finite discretization checks; not frequentist confidence intervals.',
        population_inference='Means describe the selected 50 paired realizations. No population equivalence claim.')
    (out/'results.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps([{k:v for k,v in row.items() if k not in ('nominal_values','numerical_intervals')} for row in contrasts],indent=2))
if __name__=='__main__':main()
