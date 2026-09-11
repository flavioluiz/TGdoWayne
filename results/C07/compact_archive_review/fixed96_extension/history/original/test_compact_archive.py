"""Integrity and transport tests only; no fake posterior/calibration claims."""
from pathlib import Path
import fcntl
import importlib.util
import json
import sys
import tempfile
import unittest
import zipfile

SCRIPT = Path(__file__).resolve().parents[1]/'scripts'/'compactar_calibracao.py'
if not SCRIPT.exists():
    SCRIPT = Path(__file__).resolve().parents[1]/'scripts'/'compactar_calibracao.py'
spec = importlib.util.spec_from_file_location('compact_archive_under_test', SCRIPT)
c = importlib.util.module_from_spec(spec); spec.loader.exec_module(c)


def fixture(root):
    root.mkdir(); (root/'.campaign.lock').touch()
    def put(name, value):
        p=root/name; p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(value, sort_keys=True)); return p
    def binary(name, value):
        p=root/name; p.parent.mkdir(parents=True, exist_ok=True); p.write_bytes(value); return p
    runtime='runtime-test'; driver='driver-test'; fake_hash='0'*64
    source=b'\n# Frozen fixture source, not a posterior calculation.\n'
    binary(f'provenance/{runtime}/fixture.py', source)
    source_hash=c.digest(root/f'provenance/{runtime}/fixture.py')
    put(f'provenance/{runtime}/manifest.json',dict(identity=runtime,input_sha256={'data':fake_hash},source_sha256={'fixture':source_hash}))
    binary(f'driver_provenance/{driver}/driver.py',source)
    protocol=put(f'driver_provenance/{driver}/protocol.json',{'toy':True})
    truth=put(f'driver_provenance/{driver}/truth_logl.json',{'not_a_posterior':True})
    plan=dict(identity=runtime,driver_identity=driver,scope='ENGINEERING_ONLY',datasets=2,all_target_ids=[0,1],levels=[16,64],input_sha256={'data':fake_hash},driver_source_sha256={'driver':source_hash},extra_input_sha256={'protocol':c.digest(protocol),'truth_logl':c.digest(truth)})
    put('campaign_plan.json',plan)
    for t in range(2):
        p=f'{t:06d}'; flags={name:t==0 for name in ('cdf_precision_pass','pooled_weight_guard_pass','saturation_guard_pass','replication_pass','refinement_pass')}
        numerical='RECORDED_NUMERICAL_CHECKS_PASSED' if t==0 else 'NUMERICALLY_UNRESOLVED'
        proposal=put(f'proposals/target_{p}.json',{'frozen':True,'target':t,'rng_recipe':'toy only'})
        reps=[]; raw={}
        for n in [16,64]:
            for r in range(4):
                rawname=f'target_{p}_N{n}_rep_{r:02d}.npz'; raw[rawname]=fake_hash
                cp=dict(identity=runtime,target=t,level=n,replicate=r,proposal_sha256=c.digest(proposal),rng_recipe='fixture',rng_state_before={},rng_state_after={},seed=123,raw_file=rawname,raw_sha256=fake_hash)
                put(f'production/target_{p}_N{n}_rep_{r:02d}.json',cp); reps.append(cp)
                binary(f'production/descriptive_target_{p}_N{n}_rep_{r:02d}.npz',b'NON-POSTERIOR fixture descriptive bytes\0')
        producer=put(f'production/target_{p}.json',dict(status='IID_COMPLETE_AWAITING_DIAGNOSTICS',identity=runtime,target=t,model='A0_CN',datum=t,input_sha256=plan['input_sha256'],levels=[16,64],replicates=reps,proposal_sha256=c.digest(proposal)))
        numeric=binary(f'diagnostics/diagnostic_target_{p}.npz',b'Binary fixture. No inferential content.\0'+bytes([t]))
        diag=put(f'diagnostics/diagnostic_target_{p}.json',dict(status='NUMERICAL_DIAGNOSTICS_COMPLETE',identity=runtime,target=t,model='A0_CN',datum=t,numeric_file=numeric.name,numeric_sha256=c.digest(numeric),raw_sha256=raw,summary=flags))
        sources=[('producer',producer),('diagnostic',diag),('numeric',numeric),('proposal',proposal)]
        sources += [(f'checkpoint_N{cp["level"]}_rep{cp["replicate"]}',root/f'production/target_{p}_N{cp["level"]}_rep_{cp["replicate"]:02d}.json') for cp in reps]
        artifacts=[]
        for role, sourcefile in sources:
            saved=binary(f'production/archive_target_{p}/{role}{sourcefile.suffix}',sourcefile.read_bytes())
            artifacts.append(dict(role=role,file=saved.relative_to(root/'production').as_posix(),sha256=c.digest(saved),bytes=saved.stat().st_size))
        receipt=put(f'production/archive_receipt_target_{p}.json',dict(status='RAW_ARCHIVE_VERIFIED',archive_scope='reproducible_target_summary',identity=runtime,target=t,raw_sha256=raw,all_indicators_and_failures_retained=True,no_scientific_calibration_claim=True,numerical_status=numerical,numerical_flags=flags,artifacts=artifacts))
        release=put(f'production/released_target_{p}.json',dict(status='RAW_RELEASED',identity=runtime,target=t,raw_sha256=raw,archive_receipt_sha256=c.digest(receipt),numerical_status=numerical))
        artifacts=[dict(file=file.relative_to(root).as_posix(),sha256=c.digest(file)) for file in (producer,diag,numeric,receipt,release)]
        put(f'state/target_{p}.json',dict(status='TARGET_ARCHIVED',driver_identity=driver,target=t,model='A0_CN',datum=t,numerical_status=numerical,numerical_flags=flags,artifacts=artifacts,no_scientific_calibration_claim=True))
    # Include a failed attempt: budget must retain its actual spent work.
    intent=put('ledger/event_000000.intent.json',dict(driver_identity=driver,kind='training',reserved_likelihood_values=10))
    put('ledger/event_000000.end.json',dict(intent_sha256=c.digest(intent),status='COMPUTATIONAL_OR_INTEGRITY_FAILURE',likelihood_evaluations=7))
    put('campaign_complete.json',dict(status='ALL_TARGET_PRODUCTS_ARCHIVED',driver_identity=driver,targets=[0,1],numerically_unresolved_targets=[1],no_SBC_uniformity_claim=True,ledger=dict(training=7,production=0,other=0,unclosed_reservations=0,total=7)))
    put('state/attempt_0000.end.json',dict(status='COMPLETED',fixture=True))
    return root


class CompactArchiveTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name); self.campaign=fixture(self.root/'campaign')
    def pack(self, name='bundle', **kwargs):
        return c.pack(self.campaign,self.root/name,engineering=True,block_size=1,**kwargs)
    def test_roundtrip_all_bytes_and_failures_deterministic(self):
        log=self.root/'progress.log'; log.write_text('fixture log\n')
        original={p.relative_to(self.campaign).as_posix():c.digest(p) for p in c.scan(self.campaign) if p.name!='.campaign.lock'}
        one=self.pack(supplements={'log':log}); two=self.pack('bundle2',supplements={'log':log})
        self.assertEqual(one,two)
        self.assertEqual(one['unresolved_count'],1)
        self.assertEqual([d['sha256'] for d in one['archives']],[d['sha256'] for d in two['archives']])
        verified, inv=c.verify(self.root/'bundle'); self.assertEqual(len(inv['retired_raw_sha256']),16)
        self.assertEqual({x['target'] for x in inv['targets']},{0,1})
        c.extract(self.root/'bundle',self.root/'restored')
        recovered={p.relative_to(self.root/'restored'/'campaign').as_posix():c.digest(p) for p in c.scan(self.root/'restored'/'campaign')}
        self.assertEqual(original,recovered)
        self.assertEqual(original,{p.relative_to(self.campaign).as_posix():c.digest(p) for p in c.scan(self.campaign) if p.name!='.campaign.lock'})
        self.assertEqual((self.root/'restored'/'supplements'/'log'/'progress.log').read_bytes(),log.read_bytes())
        self.assertFalse(any('/raw/' in x['member'] for x in inv['files']))
        with self.assertRaisesRegex(ValueError,'new destination'):c.extract(self.root/'bundle',self.root/'restored')
    def test_default_inventory_lock_and_raw_guards(self):
        with self.assertRaisesRegex(ValueError,'all2500'):c.pack(self.campaign,self.root/'bundle')
        with (self.campaign/'.campaign.lock').open('rb') as lock:
            fcntl.flock(lock.fileno(),fcntl.LOCK_EX|fcntl.LOCK_NB)
            with self.assertRaisesRegex(RuntimeError,'driver is active'):self.pack()
        raw=self.campaign/'raw'/'orphan.npz'; raw.parent.mkdir(); raw.write_bytes(b'never remove this')
        with self.assertRaisesRegex(ValueError,'still has raw'):self.pack()
        self.assertEqual(raw.read_bytes(),b'never remove this')
        self.assertFalse((self.root/'bundle').exists())
    def test_missing_state_hash_and_symlink_guards(self):
        path=self.campaign/'state'/'target_000001.json'; original=path.read_bytes(); path.unlink()
        with self.assertRaisesRegex(ValueError,'state count'):self.pack()
        path.write_bytes(original)
        numeric=self.campaign/'diagnostics'/'diagnostic_target_000001.npz'; original=numeric.read_bytes(); numeric.write_bytes(b'corrupt')
        with self.assertRaisesRegex(ValueError,'hash mismatch'):self.pack()
        numeric.write_bytes(original)
        (self.campaign/'link').symlink_to(numeric)
        with self.assertRaisesRegex(ValueError,'Symlinks'):self.pack()
    def test_corrupted_bundle_and_unsafe_member_rejected(self):
        summary=self.pack(); archive=self.root/'bundle'/summary['archives'][0]['file']
        with archive.open('ab') as f:f.write(b'tamper')
        with self.assertRaisesRegex(ValueError,'SHA256/size'):c.verify(self.root/'bundle')
        self.assertFalse((self.root/'restored').exists())
        for name in ('../escape','/absolute','a/../b','a\\b','a//b','C:/x',''):
            with self.subTest(name=name),self.assertRaises(ValueError):c.relative_name(name)
    def test_partition_budget_and_ledger_integrity(self):
        # Small cap forces bounded parts without changing any member bytes.
        summary=self.pack(maximum_archive_bytes=12_000)
        self.assertTrue(all(r['bytes']<=12_000 for r in summary['archives']))
        self.assertGreater(len(summary['archives']),3)
        with self.assertRaisesRegex(ValueError,'Restoration budget'):c.extract(self.root/'bundle',self.root/'tiny',maximum_restored_bytes=1)
        with self.assertRaisesRegex(ValueError,'One member'):self.pack('impossible',maximum_archive_bytes=1100)
        self.assertFalse((self.root/'impossible').exists())
        end=self.campaign/'ledger'/'event_000000.end.json'; value=json.loads(end.read_text()); value['likelihood_evaluations']=11; end.write_text(json.dumps(value))
        with self.assertRaisesRegex(ValueError,'Ledger hash/count'):self.pack('bad-ledger')


if __name__=='__main__':unittest.main()
