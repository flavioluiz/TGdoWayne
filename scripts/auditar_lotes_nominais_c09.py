"""Check complete production job inventory and accounting, retaining failed gates."""
from pathlib import Path
import argparse
import hashlib
import json
import numpy as np


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('directory',type=Path)
    parser.add_argument('--output',type=Path,default=Path('results/C09/nominal_production/audit.json'))
    args=parser.parse_args()
    root=args.directory
    bindings={}

    def bind(path):
        bindings[str(path)]=hashlib.sha256(path.read_bytes()).hexdigest()
        return path

    def read(path):
        return json.loads(bind(path).read_text())

    plan=read(root/'plan.json')
    total=charged=mesh=backend=0
    failures=[]
    for job in plan['jobs']:
        base=root/'execution'/job['job_id']
        receipt=read(base/'receipt.json')
        activation=read(base/'activation.json')
        assert receipt['status']=='COMPLETED_WITH_PER_CASE_GATES'
        assert hashlib.sha256((base/'worker_source.py').read_bytes()).hexdigest()==activation['source_sha256']['scripts/executar_lote_nominal_c09.py']
        bind(base/'worker_source.py')
        results=read(base/'posteriors.json')
        names=[r['curve_id'] for r in job['curves']]
        assert names==[r['curve_id'] for r in results]
        with np.load(bind(base/'likelihoods.npz')) as cache:
            assert cache['curve_ids'].tolist()==names
            assert cache['log_likelihood'].shape==(job['fine_nodes'],len(names))
            assert np.isfinite(cache['log_likelihood']).all()
            assert np.all(np.diff(cache['u'])>0)
        expected=(job['fine_nodes']+35)*len(names)
        assert receipt['budget']['additional_charged_values']==expected
        assert receipt['budget']['failed_reserved_values']==0
        for result in results:
            evidence=read(base/'backend_checks'/(result['curve_id']+'.json'))
            backend_pass=evidence['maximum_absolute_logL_difference']<=.001 and evidence['scipy_maximum_absolute_difference']<=1e-8
            assert backend_pass==result['finite_backend_gate']
            qlo,qhi=np.array(result['quantile_lower']),np.array(result['quantile_upper'])
            mesh_pass=all(v <= (.002 if k=='CDF' else .001) for k,v in result['delta'].items()) and np.max(qhi-qlo)<=.001
            assert bool(mesh_pass)==result['mesh_gate']
            assert np.all(qhi>=qlo) and np.all(qlo>=job['lower']) and np.all(qhi<=1)
            assert result['W1'][0]<=result['W1'][1]
            assert result['calibration_complete'] is False
            mesh+=bool(mesh_pass); backend+=bool(backend_pass)
            if not (mesh_pass and backend_pass):
                failures.append(dict(curve_id=result['curve_id'],mesh=bool(mesh_pass),backend=bool(backend_pass)))
        total+=len(names); charged+=expected
    assert total==plan['planned_posteriors']
    audit=dict(schema='C09_NOMINAL_PRODUCTION_INVENTORY_AUDIT_v1',inventory_and_accounting_passed=True,
        posteriors=total,mesh_passed=mesh,finite_backend_passed=backend,failed_gates=failures,
        new_likelihood_values=charged,cumulative_likelihood_values=plan['historical_likelihood_values']+charged,
        inputs_sha256=bindings,calibration_complete=False,C09_complete=False,
        scope='Inventory, recorded arithmetic gates and counts; no independent posterior integration or SBC assertion')
    output=args.output
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(audit,indent=2,allow_nan=False)+'\n')
    print(json.dumps({k:v for k,v in audit.items() if k not in ('inputs_sha256','failed_gates')}))


if __name__=='__main__':
    main()
