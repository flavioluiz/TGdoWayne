import importlib.util
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest import mock

SOURCE=Path(__file__).resolve().parents[1]/'scripts/campanha_compressao.py'
spec=importlib.util.spec_from_file_location('c08_transport',SOURCE)
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)


class Transport(unittest.TestCase):
    def fixture(self,root):
        base=root/'tmp/toy/closed';base.mkdir(parents=True)
        (base/'.campaign.lock').touch()
        def save(name,data):
            p=base/name;p.parent.mkdir(parents=True,exist_ok=True);m.write(p,data);return m.sha(p)
        ids=list(range(8));flags={k:True for k in m.FLAGS}
        for t in ids:
            f=dict(flags)
            if t==7:f['pooled_weight_guard_pass']=False
            names=[f'training/t{t}.json',f'production/p{t}.json',f'production/u{t}.json',f'diagnostics/d{t}.json',f'diagnostics/n{t}.json']
            artifacts=[]
            for name in names:artifacts.append(dict(file=name,sha256=save(name,{'toy':True,'value':t})))
            receipt=f'production/archive_receipt_target_{t:06d}.json'
            raws={f'original_{t}.npz':str(t)*64}
            h=save(receipt,dict(raw_sha256=raws));artifacts.append(dict(file=receipt,sha256=h))
            name=f'production/released_target_{t:06d}.json'
            h=save(name,dict(status='RAW_RELEASED',archive_receipt_sha256=h,raw_sha256=raws));artifacts.append(dict(file=name,sha256=h))
            save(f'state/target_{t:06d}.json',dict(target=t,status='TARGET_ARCHIVED',driver_identity='TOY',model='TOY',datum=t,
                numerical_flags=f,numerical_status='NUMERICALLY_UNRESOLVED' if t==7 else 'RECORDED_NUMERICAL_CHECKS_PASSED',
                no_scientific_calibration_claim=True,artifacts=artifacts))
        save('campaign_plan.json',dict(all_target_ids=ids,driver_identity='TOY',phase='engineering',response_variant='C_beta',scope='SYNTHETIC_TRANSPORT_TOY'))
        ledger=dict(total=0,unclosed_reservations=0)
        h=save('campaign_complete.json',dict(schema='C08_PHASE_VARIANT_COMPLETE_v1',status='ALL_TARGET_PRODUCTS_ARCHIVED',targets=ids,
            driver_identity='TOY',phase='engineering',response_variant='C_beta',population_numerical_family=16,
            no_SBC_uniformity_claim=True,no_publication_or_global_response_approval=True,numerically_unresolved_targets=[7],ledger=ledger))
        review=root/'tmp/toy_review.json';m.write(review,dict(status='BOTH_VARIANTS_LIFECYCLE_NUMERICS_COMPLETE',rows=[dict(variant='C_beta',complete_sha256=h,LL=ledger,artifact_hashes_verified=56)]))
        selected=dict(schema='C08_ARCHIVE_SELECTION_v1',original_repository_prefix=str(root),campaigns=[dict(path='tmp/toy/closed',completion_sha256=h,root_review=dict(path='tmp/toy_review.json',sha256=m.sha(review)))],include=['tmp/toy_review.json'],external_dependencies=[])
        selection=root/'selection.json';m.write(selection,selected)
        inv=root/'inventory.json';m.plan(selection,root,inv)
        return base,selection,inv

    def test_roundtrip_retains_failures_and_exact_paths_no_overwrite(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp).resolve();base,sel,inv=self.fixture(root);bundle=root/'bundle'
            r=m.pack(inv,root,bundle,cap=12000);self.assertGreater(r['parts'],1)
            summary,frozen=m.verify(bundle);self.assertEqual(frozen['audits'][0]['unresolved'],[7])
            dest=root/'restore';m.restore(bundle,dest)
            for row in frozen['files']:self.assertEqual(m.sha(dest/row['path']),row['sha256'])
            self.assertEqual(json.loads((dest/'C08_RELOCATION_MAP.json').read_text())['original_prefix'],str(root))
            with self.assertRaises(ValueError):m.restore(bundle,dest)
            self.assertTrue((base/'campaign_complete.json').exists())

    def test_raw_active_incomplete_and_changed_review_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp).resolve();base,sel,inv=self.fixture(root)
            (base/'raw').mkdir();(base/'raw/a.npz').write_bytes(b'toy')
            with self.assertRaises(ValueError):m.plan(sel,root,root/'raw_inventory.json')
            (base/'raw/a.npz').unlink()
            with m.campaign_locks(root,m.read(sel)['campaigns']):
                with self.assertRaises(RuntimeError):m.plan(sel,root,root/'lock_inventory.json')
            p=base/'campaign_complete.json';p.write_text('{}')
            with self.assertRaises((ValueError,KeyError)):m.plan(sel,root,root/'incomplete_inventory.json')

    def test_corrupt_zip_and_unsafe_inventory_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp).resolve();base,sel,inv=self.fixture(root);bundle=root/'bundle';m.pack(inv,root,bundle)
            part=bundle/m.read(bundle/'bundle.json')['archives'][0]['file']
            old=part.read_bytes();part.write_bytes(old[:-1]+bytes([old[-1]^1]))
            with self.assertRaises(ValueError):m.verify(bundle)
            for unsafe in ['../escape','a/../../b','/absolute','a//b','a/./b','a\\b','a:b']:
                with self.assertRaises(ValueError):m.relative(unsafe)

    def test_changed_source_after_copy_preserves_inputs_and_no_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp).resolve();base,sel,inv=self.fixture(root);bundle=root/'bundle'
            original=m.verify
            def mutate_after_zip(*args,**kwargs):
                result=original(*args,**kwargs)
                (root/'tmp/toy_review.json').write_text('{"changed_after_copy":true}')
                return result
            with mock.patch.object(m,'verify',side_effect=mutate_after_zip):
                with self.assertRaises(ValueError):m.pack(inv,root,bundle)
            self.assertFalse(bundle.exists());self.assertTrue((base/'campaign_complete.json').exists())

    def test_overlap_symlink_restore_budget_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp).resolve();base,sel,inv=self.fixture(root)
            with self.assertRaises(ValueError):m.pack(inv,root,base/'newbundle')
            link=root/'alias';link.symlink_to(base,target_is_directory=True)
            with self.assertRaises(ValueError):m.pack(inv,root,link/'newbundle')
            bundle=root/'bundle';m.pack(inv,root,bundle)
            with self.assertRaises(ValueError):m.restore(bundle,root/'small',max_bytes=1)
            self.assertFalse((root/'small').exists())


if __name__=='__main__':unittest.main()
