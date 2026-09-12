"""Locate held-out pilot failures without evaluating a new likelihood or ORF."""
from pathlib import Path
import json,sys,hashlib
import numpy as np
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from inference.mass_batch import MassPosteriorBatch


def main():
    base=ROOT/'tmp/c09_distance_endpoints_v1/pilot_validation'
    def load(path):
        with np.load(path) as f:return {k:f[k] for k in f.files}
    endpoints=load(base/'likelihoods.npz')
    original=load(ROOT/'tmp/c09_D3_distances_v1/initial_execution/likelihoods.npz')
    rules=load(ROOT/'tmp/c09_D3_distances_v1/prepared/rules.npz')
    waves=[load(ROOT/f'tmp/c09_D3_distance_reference_v{i}/initial_execution/likelihoods.npz') for i in range(1,10)]
    x=np.r_[endpoints['u'][[0,-1]],original['u'][rules['indices64']],*[v['u'] for v in waves[:8]]]
    y=np.concatenate([endpoints['mixture_logL'][[0,-1]],original['mixture_logL'][rules['indices64']],*[v['mixture_logL'] for v in waves[:8]]])
    order=np.argsort(x);x=x[order];y=y[order];table=MassPosteriorBatch(x,y)
    names=[r['curve'] for r in json.loads((base/'comparisons.json').read_text())]
    reports=[];bad_intervals=set();new_training=[];new_validation=[]
    for label,u,truth in [('interior_controls',endpoints['u'][1:-1],endpoints['mixture_logL'][1:-1]),
                          ('wave9',waves[-1]['u'],waves[-1]['mixture_logL'])]:
        error=abs(table.interpolator(np.arcsin(u))+table.shift-truth)
        for j,name in enumerate(names):
            index=int(np.argmax(error[:,j]))
            reports.append(dict(controls=label,curve=name,maximum_delta=float(error[index,j]),u_at_maximum=float(u[index]),
                                failed_nodes=int(np.sum(error[:,j]>.001))))
        for point in u[np.max(error,axis=1)>.001]:
            cell=int(np.searchsorted(x,point)-1)
            assert x[cell]<point<x[cell+1]
            bad_intervals.add(cell)
    for cell in sorted(bad_intervals):
        a,b=np.arcsin(x[[cell,cell+1]])
        new_training.append(float(np.sin((a+b)/2)))
        new_validation.extend(np.sin(a+(b-a)*np.array([.25,.75])).tolist())
    proposed=np.unique(np.r_[new_training,new_validation])
    assert len(proposed)*2<=8000-6841
    out=ROOT/'results/C09/distance_interpolation_diagnostics';out.mkdir(parents=True,exist_ok=True)
    result=dict(schema='C09_DISTANCE_HELDOUT_DIAGNOSTIC_v1',reports=reports,failed_training_intervals=len(bad_intervals),
        proposed_training_u=new_training,proposed_heldout_u=new_validation,proposed_new_full_nodes=2*len(proposed),
        execution_enabled=False,new_likelihood_values=0,new_ORFs=0,
        policy='The observed held-out points may enter a revised fit only if relabeled training; proposed quarter-points must remain held out. Full resource preflight and a new activation are required.',
        source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),C09_complete=False)
    (out/'diagnostic.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(dict(failed_intervals=len(bad_intervals),proposed_new_full_nodes=2*len(proposed),reports=reports)))


if __name__=='__main__':main()
