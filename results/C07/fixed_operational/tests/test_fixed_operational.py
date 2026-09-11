"""TOY operations validate archival/resume without training or PTA likelihood calls."""
import ast
import contextlib
import importlib.util
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
import numpy as np

ROOT=Path('.').resolve();PACKAGE=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
spec=importlib.util.spec_from_file_location('fixed_driver',PACKAGE/'scripts/run_fixed_campaign.py')
driver=importlib.util.module_from_spec(spec);spec.loader.exec_module(driver)
driver.initialize(ROOT,PACKAGE/'src/inference/fixed_diagnostics_v2.py')
from inference.campaign_io import read_json,write_json_new,write_npz_new,sha256
from inference.campaign_archive import prepare_archive,verify_archive_receipt
from inference.campaign_iid import release_raw


class ToyRuntime:
    def __init__(self):
        self.identity='fixed_toy_runtime';self.likelihood_evaluations=0;self.paths={}
        self.settings=dict(models=['A0_CN'],training={'steps':2},production={'levels':[4,8]},
            budget={'maximum_training_likelihood_values':1000,'maximum_production_likelihood_values':1000,
                    'maximum_total_likelihood_values':2000,'maximum_active_raw_bytes':100000})
    def snapshot(self,output):pass
    def verify_unchanged(self):pass


class ToyOperations:
    def __init__(self,generation,fail_once=None,bad_schema=False):
        self.generation=generation;self.fail_once=fail_once;self.events=[];self.bad_schema=bad_schema
    def train(self,rt,ids,output,*,resume=False):
        self.events.append(('train',tuple(ids)))
        for t in ids:
            path=output/f'target_{t:06d}.json'
            if not path.exists():
                rt.likelihood_evaluations+=12
                write_json_new(path,dict(target=t,label='TOY_PROPOSAL_NO_POSTERIOR_TRAINING'))
    def produce(self,rt,target,proposals,output,raw,*,resume=False):
        self.events.append(('produce',target))
        if self.fail_once==target:
            self.fail_once=None;rt.likelihood_evaluations+=24;raise RuntimeError('TOY injected computational failure')
        path=output/f'target_{target:06d}.json'
        if path.exists():return read_json(path)
        rows=[];proposal=sha256(proposals/f'target_{target:06d}.json')
        for level in [4,8]:
            for r in range(4):
                name=f'target_{target:06d}_N{level}_rep_{r:02d}.npz'
                write_npz_new(raw/name,toy=np.arange(level),label=np.asarray('TOY_RAW_NO_PTA_POSTERIOR'))
                row=dict(status='IID_REPLICATE_COMPLETE',identity=rt.identity,target=target,level=level,replicate=r,
                    raw_file=name,raw_sha256=sha256(raw/name),rng_recipe='TOY deterministic arange',rng_state_before={},rng_state_after={},seed=7,proposal_sha256=proposal)
                write_json_new(output/f'target_{target:06d}_N{level}_rep_{r:02d}.json',row);rows.append(row)
        rt.likelihood_evaluations+=48
        record=dict(status='IID_COMPLETE_AWAITING_DIAGNOSTICS',identity=rt.identity,target=target,datum=target,model='A0_CN',
            replicates=rows,proposal_sha256=proposal,input_sha256={'toy':'source'},levels=[4,8])
        write_json_new(path,record);return record
    def diagnose(self,rt,report,raw,truth,generation,protocol,output,*,resume=False):
        production=read_json(report);t=production['target'];self.events.append(('diagnose',t))
        numeric=output/f'diagnostic_target_{t:06d}.npz'
        mask=np.ones(6,bool);structural=np.zeros(6,bool);pit=np.full(6,.5);mcse=np.full(6,.001)
        if t==0:structural[0]=True;pit[0]=0;mcse[0]=0
        if t==64:mask[[0,1,2,5]]=False;pit[~mask]=np.nan;mcse[~mask]=np.nan
        write_npz_new(numeric,pit=pit,pit_mcse=mcse,pit_applicable=mask,pit_structural_exact=structural,label=np.asarray('TOY_COMPACT_FLAGS_NO_PTA_INFERENCE'))
        summary=dict(cdf_precision_pass=t!=32,pooled_weight_guard_pass=True,saturation_guard_pass=True,replication_pass=True,refinement_pass=True)
        record=dict(status='NUMERICAL_DIAGNOSTICS_COMPLETE',schema='WRONG' if self.bad_schema else 'C07_FIXED_MASKED_IID_DIAGNOSTICS_v2_OPERATIONAL',
            scope='FIXED_TRUTH96_NOT_SBC',identity=rt.identity,target=t,numeric_file=numeric.name,numeric_sha256=sha256(numeric),
            raw_sha256={r['raw_file']:r['raw_sha256'] for r in production['replicates']},raw_release_authorized=False,summary=summary,
            diagnostic_inputs={'generation_sha256':sha256(generation)})
        write_json_new(output/f'diagnostic_target_{t:06d}.json',record);return record
    def archive(self,*args,**kwargs):self.events.append(('archive',args[1]));return prepare_archive(*args,**kwargs)
    def release(self,*args,**kwargs):self.events.append(('release',args[1]));return release_raw(*args,**kwargs)
    def mapping(self):return {k:getattr(self,k) for k in ['train','produce','diagnose','archive','release']}


def toy_setup(root):
    protocol=root/'protocol.json';generation=root/'generation.json';truth=root/'truth.npz'
    write_json_new(protocol,{'label':'TOY_DRIVER_TEST_ONLY'});write_json_new(generation,{'label':'TOY_GENERATION_METADATA_ONLY'})
    truth.write_bytes(b'never deserialized by mocked TOY operations')
    plan=dict(identity='fixed_toy_runtime',driver_identity='fixed_toy_driver',scope='FIXED_TRUTH96_NOT_SBC',
        execution_ready=True,all_target_ids=[0,32,64],training_blocks=[[0,32],[64]],
        driver_source_sha256={k:sha256(p) for k,p in driver.extra_sources().items()},
        extra_input_sha256={'protocol':sha256(protocol),'generation':sha256(generation),'truth_data':sha256(truth)},
        explicit_test_label='TOY_THREE_OPS_TARGETS_BYPASS_PRODUCTION_PREFLIGHT_NOT96_POSTERIOR')
    return protocol,generation,truth,plan


class FixedOperationalTests(unittest.TestCase):
    def execute(self,rt,plan,protocol,generation,truth,output,ops,resume=False):
        with contextlib.redirect_stdout(io.StringIO()):
            return driver.run_fixed_campaign(rt,plan,protocol,truth,generation,output,operations=ops.mapping(),resume=resume)
    def test_v2_preserves_v1_numerical_function_bodies(self):
        def functions(name):
            return {n.name:ast.dump(n,include_attributes=False) for n in ast.parse((PACKAGE/'src/inference'/name).read_text()).body if isinstance(n,ast.FunctionDef)}
        a=functions('fixed_diagnostics.py');b=functions('fixed_diagnostics_v2.py')
        for name in ['_truth_contract','_placeholder','_contrasts','fixed_numerical_statistics','load_fixed_truth']:
            self.assertEqual(a[name],b[name],name)
    def test_generic_archive_retains_masks_and_unresolved_target(self):
        with tempfile.TemporaryDirectory() as name:
            root=Path(name);protocol,generation,truth,plan=toy_setup(root);ops=ToyOperations(generation)
            result=self.execute(ToyRuntime(),plan,protocol,generation,truth,root/'out',ops)
            self.assertEqual(result['targets'],[0,32,64]);self.assertEqual(result['numerically_unresolved_targets'],[32])
            self.assertEqual(result['ledger']['total'],180);self.assertFalse(list((root/'out/raw').glob('*.npz')))
            for t in [0,32,64]:
                prod=read_json(root/f'out/production/target_{t:06d}.json')
                receipt=verify_archive_receipt(root/f'out/production/archive_receipt_target_{t:06d}.json',root/'out/production','fixed_toy_runtime',t,{r['raw_file']:r['raw_sha256'] for r in prod['replicates']})
                self.assertTrue(receipt['no_scientific_calibration_claim'])
                with np.load(root/f'out/production/archive_target_{t:06d}/numeric.npz',allow_pickle=False) as p:
                    if t==0:self.assertTrue(p['pit_structural_exact'][0]);self.assertEqual(p['pit_mcse'][0],0.)
                    if t==64:self.assertTrue(np.isnan(p['pit'][[0,1,2,5]]).all())
            before=len(ops.events)
            again=self.execute(ToyRuntime(),plan,protocol,generation,truth,root/'out',ops,resume=True)
            self.assertEqual(result,again);self.assertEqual(before,len(ops.events))
    def test_failure_resume_reuses_retired_target_and_charges_ledger(self):
        with tempfile.TemporaryDirectory() as name:
            root=Path(name);protocol,generation,truth,plan=toy_setup(root);ops=ToyOperations(generation,fail_once=32)
            with self.assertRaisesRegex(RuntimeError,'TOY injected'):
                self.execute(ToyRuntime(),plan,protocol,generation,truth,root/'out',ops)
            result=self.execute(ToyRuntime(),plan,protocol,generation,truth,root/'out',ops,resume=True)
            self.assertEqual(result['ledger']['total'],204);self.assertEqual(ops.events.count(('produce',0)),1)
            self.assertEqual(result['numerically_unresolved_targets'],[32])
    def test_wrong_masked_schema_prevents_archive_or_deletion(self):
        with tempfile.TemporaryDirectory() as name:
            root=Path(name);protocol,generation,truth,plan=toy_setup(root);ops=ToyOperations(generation,bad_schema=True)
            with self.assertRaisesRegex(RuntimeError,'Wrong diagnostic'):
                self.execute(ToyRuntime(),plan,protocol,generation,truth,root/'out',ops)
            self.assertFalse(any(s=='archive' for s,t in ops.events));self.assertEqual(len(list((root/'out/raw').glob('*.npz'))),8)
    def test_changed_generation_or_driver_snapshot_blocks_resume(self):
        with tempfile.TemporaryDirectory() as name:
            root=Path(name);protocol,generation,truth,plan=toy_setup(root);ops=ToyOperations(generation)
            self.execute(ToyRuntime(),plan,protocol,generation,truth,root/'out',ops)
            snapshot=root/'out/driver_provenance/fixed_toy_driver/fixed_driver.py';snapshot.write_text('changed')
            with self.assertRaisesRegex(RuntimeError,'snapshot collision'):
                self.execute(ToyRuntime(),plan,protocol,generation,truth,root/'out',ops,resume=True)
    def test_generation_changed_after_plan_blocks_before_training(self):
        with tempfile.TemporaryDirectory() as name:
            root=Path(name);protocol,generation,truth,plan=toy_setup(root);ops=ToyOperations(generation)
            generation.write_text('{"changed":true}')
            with self.assertRaisesRegex(RuntimeError,'input changed'):
                self.execute(ToyRuntime(),plan,protocol,generation,truth,root/'out',ops)
            self.assertEqual(ops.events,[]);self.assertFalse((root/'out').exists())
    def test_preflight_requires_all96_a0_targets(self):
        rt=ToyRuntime();rt.n=96;rt.targets=np.array([0,32,64]);rt.preflight=lambda:{'levels':[4,8]}
        with self.assertRaisesRegex(ValueError,'all96'):
            driver.fixed_plan(rt,'unused','unused','unused','unused')


if __name__=='__main__':unittest.main()
