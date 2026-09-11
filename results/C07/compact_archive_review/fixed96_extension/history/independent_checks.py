"""Independent fixed96 transport checks; actual masked NPZ fixtures, no inference."""
from pathlib import Path
import hashlib,importlib.util,json,tempfile,time
import numpy as np

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
spec=importlib.util.spec_from_file_location('compact_fixture_helpers',ROOT/'tests/test_compact_archive.py')
helpers=importlib.util.module_from_spec(spec);spec.loader.exec_module(helpers)
c=helpers.c


def save(path,obj):path.write_text(json.dumps(obj,sort_keys=True))


def install_numeric(root,target,arrays):
    p=f'{target:06d}';numeric=root/f'diagnostics/diagnostic_target_{p}.npz'
    np.savez(numeric,**arrays)
    receipt=root/f'production/archive_receipt_target_{p}.json';value=c.read_json(receipt)
    for item in value['artifacts']:
        if item['role']=='numeric':
            copied=root/'production'/item['file'];copied.write_bytes(numeric.read_bytes())
            item.update(sha256=c.digest(copied),bytes=copied.stat().st_size)
    save(receipt,value)
    helpers.change_diagnostic_and_bindings(root,target,lambda d:d.update(numeric_sha256=c.digest(numeric)))
    return numeric


def main():
    start=time.process_time();checks=[];finding=None
    before={name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in ['scripts/compactar_calibracao.py','tests/test_compact_archive.py']}
    with tempfile.TemporaryDirectory(prefix='transport_check_',dir=HERE) as name:
        work=Path(name);campaign=helpers.fixture(work/'campaign',fixed96=True)
        no_gw=dict(pit=np.array([np.nan,np.nan,np.nan,.3,.8,np.nan]),
            pit_applicable=np.array([False,False,False,True,True,False]),
            pit_structural_exact=np.zeros(6,bool),
            truth_unit=np.array([np.nan,np.nan,np.nan,.2,.5]),
            fixture_not_inference=np.array(True))
        zero=dict(pit=np.array([0,.2,.3,.4,.5,.6]),pit_mcse=np.array([0,.01,.01,.01,.01,.01]),
            pit_applicable=np.ones(6,bool),pit_structural_exact=np.array([True,False,False,False,False,False]),
            fixture_not_inference=np.array(True))
        originals={}
        for target,data in [(0,zero),(64,no_gw)]:
            path=install_numeric(campaign,target,data);originals[target]=path.read_bytes()
        summary=c.pack(campaign,work/'bundle',fixed96=True)
        c.verify(work/'bundle');c.extract(work/'bundle',work/'restored')
        for target,expected in originals.items():
            path=work/'restored/campaign/diagnostics'/f'diagnostic_target_{target:06d}.npz'
            checks.append(dict(name=f'masked NPZ exact bytes target{target}',passed=path.read_bytes()==expected))
            with np.load(path,allow_pickle=False) as numeric:
                if target==64:
                    checks.append(dict(name='undefined noGW PIT remains NaN with false mask',passed=bool(np.isnan(numeric['pit'][[0,1,2,5]]).all() and not numeric['pit_applicable'][[0,1,2,5]].any())))
                else:
                    checks.append(dict(name='u0 structural exact zero preserved',passed=bool(numeric['pit'][0]==0 and numeric['pit_mcse'][0]==0 and numeric['pit_structural_exact'][0])))
        checks.append(dict(name='all96 IDs and95 unresolved retained',passed=summary['target_count']==96 and summary['unresolved_count']==95))
        # Keep all artifact hashes internally consistent but contradict the known
        # five Boolean flags with the numerical-status label. This is a transport
        # consistency issue, not a request to recompute numerical diagnostics.
        target=95;p=f'{target:06d}'
        receipt=campaign/f'production/archive_receipt_target_{p}.json'
        value=c.read_json(receipt);value['numerical_status']='RECORDED_NUMERICAL_CHECKS_PASSED';save(receipt,value)
        release=campaign/f'production/released_target_{p}.json'
        value=c.read_json(release);value.update(numerical_status='RECORDED_NUMERICAL_CHECKS_PASSED',archive_receipt_sha256=c.digest(receipt));save(release,value)
        state=campaign/f'state/target_{p}.json';value=c.read_json(state);value['numerical_status']='RECORDED_NUMERICAL_CHECKS_PASSED'
        for artifact in value['artifacts']:artifact['sha256']=c.digest(campaign/artifact['file'])
        save(state,value)
        completion=campaign/'campaign_complete.json';value=c.read_json(completion);value['numerically_unresolved_targets'].remove(target);save(completion,value)
        try:
            audited=c.audit_campaign(campaign,c.scan(campaign),fixed96=True)
            row=[r for r in audited['states'] if r['target']==target][0]
            finding=dict(id='T1',reproduced=True,scope='PREEXISTING_TRANSPORT_CONSISTENCY_GAP_ALSO_REACHABLE_IN_FIXED96',
                target=target,accepted_status=row['numerical_status'],retained_flags=row['numerical_flags'],
                description='Self-consistent receipt/state/completion labels pass although every retained numerical flag is false; declared unresolved count drops94 from95.')
        except ValueError as error:
            finding=dict(id='T1',reproduced=False,rejection=str(error))
    unchanged=all(hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==digest for name,digest in before.items())
    report=dict(status='MASKED_TRANSPORT_PASS_WITH_CONSISTENCY_FINDING' if all(c['passed'] for c in checks) and unchanged else 'FAIL',
        scope='TRANSPORT_FIXTURES_ONLY_NOT_PTA_OR_POSTERIOR_VALIDATION',CPU_seconds=time.process_time()-start,
        checks=checks,source_hashes=before,sources_unchanged=unchanged,finding=finding,
        likelihood_values=0,posterior_targets=0,script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    (HERE/'independent_results.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:report[k] for k in ['status','CPU_seconds','finding']}))
    if report['status']=='FAIL':raise SystemExit(1)


if __name__=='__main__':main()
