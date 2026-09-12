"""Check all registered distance analyses and preserve failed interpolation gates."""
from pathlib import Path
import json,hashlib
import numpy as np
R=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    base=R/'tmp/c09_distance_production_v1';source=base/'execution';recovery=base/'posterior_recovery'
    read=lambda p:json.loads(p.read_text())
    initial=read(source/'receipt.json');final=read(recovery/'receipt.json');activation=read(source/'activation.json')
    assert initial['status']=='FAILED' and 'Production RSS cap' in initial['error']
    assert initial['budget']['additional_charged_values']==12145500 and initial['budget']['failed_reserved_values']==0
    assert final['status']=='COMPLETED_FROM_CACHED_COMPONENTS' and final['new_likelihood_values']==0
    names=[r['curve_id'] for r in activation['rows']];assert len(set(names))==1500
    for i in range(3):
        with np.load(source/f'component_{i}.npz') as cache:
            assert cache['curves'].tolist()==names
            assert cache['log_likelihood'].shape==(2621,1500) and cache['control_log_likelihood'].shape==(75,1500)
            assert np.isfinite(cache['log_likelihood']).all() and np.isfinite(cache['control_log_likelihood']).all()
    checks=read(source/'scipy_checks.json');assert len(checks)==13500
    assert max(r['delta'] for r in checks)<=1e-8
    records=read(recovery/'posteriors.json');assert len(records)==3000 and len({r['curve_id'] for r in records})==3000
    registered=[r for r in read(R/'tmp/c09_production_v1/generation/inference_index.json') if r['stage_id']==6]
    expected={r['id']+'__'+m for r in registered for m in r['models']}
    assert expected=={r['curve_id'] for r in records}
    failures=[]
    for r in records:
        assert int(r['curve_id'].split('__')[0].rsplit('_d',1)[1])==r['datum_id']
        lo,hi=np.array(r['quantile_lower']),np.array(r['quantile_upper'])
        passed=all(v<=(.002 if k=='CDF' else .001) for k,v in r['delta'].items()) and np.max(hi-lo)<=.001
        assert bool(passed)==r['mesh_passed'] and (r['heldout_logL_delta']<=.001)==r['heldout_passed']
        assert r['calibration_complete'] is False and r['mass_PIT'] is None and r['logL_event'] is None
        if not r['heldout_passed']:failures.append(dict(curve_id=r['curve_id'],delta=r['heldout_logL_delta']))
    assert len(failures)==834 and all('A0_CN' in r['curve_id'] for r in failures)
    groups=[]
    for model in ('A0_CN','B_CN_full_variable','B_G_full_variable'):
        for mode in ('correct_mixture','nominal_scale_only'):
            rows=[r for r in records if r['analysis']==model and r['mode']==mode]
            assert sorted(r['datum_id'] for r in rows)==list(range(500))
            groups.append(dict(model=model,mode=mode,n=500,mesh_passed=sum(r['mesh_passed'] for r in rows),
                heldout_passed=sum(r['heldout_passed'] for r in rows),max_heldout_delta=max(r['heldout_logL_delta'] for r in rows)))
    files=[source/'activation.json',source/'receipt.json',source/'source.py',source/'scipy_checks.json',
        recovery/'activation.json',recovery/'receipt.json',recovery/'posteriors.json']+[source/f'component_{i}.npz' for i in range(3)]
    audit=dict(schema='C09_DISTANCE_PRODUCTION_INVENTORY_v1',inventory_and_accounting_passed=True,posteriors=3000,
        groups=groups,unresolved_pointwise_interpolation=failures,new_likelihood_values=12145500,cumulative_C09=67017097,
        original_attempt_CPU=initial['CPU'],recovery_CPU=final['CPU'],original_peak_RSS=initial['peak_RSS_bytes'],recovery_peak_RSS=final['peak_RSS_bytes'],
        inputs_sha256={str(p.relative_to(R)):sha(p) for p in files},all500_IDs_per_group_retained=True,
        scope='No additional numerical integration in this audit. Mesh/SciPy gates and pointwise interpolation gates remain separate. No SBC calibration or uniform physical error claim.',C09_complete=False)
    out=R/'results/C09/distance_production';out.mkdir(parents=True,exist_ok=True)
    (out/'audit.json').write_text(json.dumps(audit,indent=2)+'\n')
    print(json.dumps({k:v for k,v in audit.items() if k not in ('inputs_sha256','unresolved_pointwise_interpolation')}))
if __name__=='__main__':main()
