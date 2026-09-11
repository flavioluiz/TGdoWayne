import importlib.util,json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import numpy as np
from inference.campaign_io import write_json_new,read_json,sha256

SOURCE=Path(__file__).resolve().parents[1]/'scripts/run_calibration_campaign.py'
spec=importlib.util.spec_from_file_location('driver',SOURCE);driver=importlib.util.module_from_spec(spec);spec.loader.exec_module(driver)

class FakeRuntime:
 def __init__(self):
  self.identity='fake';self.likelihood_evaluations=0
  self.settings=dict(training={'steps':2},production={'levels':[4,8]},budget={'maximum_training_likelihood_values':1000,'maximum_production_likelihood_values':1000,'maximum_total_likelihood_values':2000,'maximum_active_raw_bytes':100000})
 def verify_unchanged(self):pass

def test_plan():
 return dict(identity='fake',driver_identity='fake_driver',execution_ready=True,all_target_ids=[0,1,2],training_blocks=[[0,1],[2]],driver_source_sha256={k:sha256(p) for k,p in driver.extra_sources().items()},extra_input_sha256={})

class FakeOperations:
 def __init__(self,fail=None):self.events=[];self.fail=fail
 def train(self,rt,ids,output,resume=False):
  self.events.append(('train',tuple(ids)))
  for t in ids:
   p=output/f'target_{t:06d}.json'
   if not p.exists():rt.likelihood_evaluations+=12;write_json_new(p,{'target':t})
 def produce(self,rt,target,proposals,output,raw,resume=False):
  self.events.append(('produce',target));assert (proposals/f'target_{target:06d}.json').exists()
  if self.fail==target:self.fail=None;rt.likelihood_evaluations+=24;raise RuntimeError('backend integrity failure')
  rt.likelihood_evaluations+=48;write_json_new(output/f'target_{target:06d}.json',dict(target=target,replicates=[]))
 def diagnose(self,rt,production,raw,truth,protocol,output,**kwargs):
  t=read_json(production)['target'];self.events.append(('diagnose',t));output.mkdir(parents=True,exist_ok=True)
  numeric=output/f'diagnostic_target_{t:06d}.npz';numeric.write_bytes(b'compact toy results, including unresolved flags')
  result=dict(target=t,numeric_file=numeric.name);write_json_new(output/f'diagnostic_target_{t:06d}.json',result);return result
 def archive(self,rt,t,proposals,output,diagnostic,resume=False):
  self.events.append(('archive',t));assert diagnostic.exists()
  result=dict(target=t,datum=t,model='TOY',numerical_status='NUMERICALLY_UNRESOLVED' if t==1 else 'RECORDED_NUMERICAL_CHECKS_PASSED',numerical_flags={'precision':t!=1})
  write_json_new(output/f'archive_receipt_target_{t:06d}.json',result);return result
 def release(self,rt,t,output,raw,receipt,resume=False):
  self.events.append(('release',t));assert receipt.exists();write_json_new(output/f'released_target_{t:06d}.json',{'target':t})
 def mapping(self):return {k:getattr(self,k) for k in ('train','produce','diagnose','archive','release')}

class DriverTests(unittest.TestCase):
 def run_fake(self,root,rt,ops,resume=False):
  protocol=root/'protocol.json';truthlog=root/'truthlog.json'
  if not protocol.exists():write_json_new(protocol,{});write_json_new(truthlog,{})
  plan=test_plan();plan['extra_input_sha256']={'protocol':sha256(protocol),'truth_logl':sha256(truthlog)}
  with patch.object(driver,'snapshot_driver'),patch.object(driver,'verify_archive_receipt',lambda *a:None):
   return driver.run_campaign(rt,plan,protocol,protocol,truthlog,root/'out',resume=resume,operations=ops.mapping())
 def test_order_counts_and_unresolved_retained(self):
  with tempfile.TemporaryDirectory() as name:
   root=Path(name);rt=FakeRuntime();ops=FakeOperations();result=self.run_fake(root,rt,ops)
   self.assertEqual(result['targets'],[0,1,2]);self.assertEqual(result['numerically_unresolved_targets'],[1]);self.assertEqual(result['ledger']['total'],180)
   expected=[('train',(0,1))]+[(stage,t) for t in [0,1] for stage in ['produce','diagnose','archive','release']]+[('train',(2,))]+[(stage,2) for stage in ['produce','diagnose','archive','release']]
   self.assertEqual(ops.events,expected)
   before=len(ops.events);again=self.run_fake(root,FakeRuntime(),ops,resume=True)
   self.assertEqual(again,result);self.assertEqual(len(ops.events),before)
 def test_failure_stops_and_resume_does_not_repeat_retired_target(self):
  with tempfile.TemporaryDirectory() as name:
   root=Path(name);rt=FakeRuntime();ops=FakeOperations(fail=1)
   with self.assertRaisesRegex(RuntimeError,'backend integrity'):self.run_fake(root,rt,ops)
   self.assertFalse((root/'out/state/target_000001.json').exists());self.assertNotIn(('train',(2,)),ops.events)
   result=self.run_fake(root,FakeRuntime(),ops,resume=True)
   self.assertEqual(ops.events.count(('produce',0)),1);self.assertEqual(result['ledger']['total'],204)
   self.assertEqual(result['numerically_unresolved_targets'],[1])
 def test_unclosed_reservation_is_counted_and_budget_rejected_before_work(self):
  with tempfile.TemporaryDirectory() as name:
   root=Path(name);rt=FakeRuntime();ledger=driver.Ledger(root,'x',rt.settings['budget'])
   write_json_new(root/'event_000000.intent.json',dict(driver_identity='x',kind='production',reserved_likelihood_values=990))
   self.assertEqual(ledger.totals()['production'],990)
   with self.assertRaisesRegex(RuntimeError,'budget'):ledger.call(rt,'production',11,'produce',[0],lambda:None)
   self.assertEqual(len(list(root.glob('*.intent.json'))),1)
 def test_ledger_reads_scale_linearly(self):
  with tempfile.TemporaryDirectory() as name:
   root=Path(name);rt=FakeRuntime();ledger=driver.Ledger(root,'x',rt.settings['budget'])
   original=driver.read_json;reads=[]
   def counted(path):reads.append(str(path));return original(path)
   def evaluation():rt.likelihood_evaluations+=1
   with patch.object(driver,'read_json',counted):
    for i in range(100):ledger.call(rt,'production',1,'produce',[i],evaluation)
    self.assertEqual(len(reads),0)
    self.assertEqual(ledger.totals()['total'],100)
    ledger.totals(audit=True);self.assertEqual(len(reads),200)
    reopened=driver.Ledger(root,'x',rt.settings['budget']);self.assertEqual(reopened.totals()['total'],100)
    self.assertEqual(len(reads),400)
    for i in range(100,200):reopened.call(rt,'production',1,'produce',[i],evaluation)
    self.assertEqual(len(reads),400)
    self.assertEqual(reopened.totals()['total'],200)
 def test_single_writer_lock(self):
  with tempfile.TemporaryDirectory() as name:
   with driver.campaign_lock(Path(name)):
    with self.assertRaisesRegex(RuntimeError,'Another driver'):
     with driver.campaign_lock(Path(name)):pass

if __name__=='__main__':unittest.main()
