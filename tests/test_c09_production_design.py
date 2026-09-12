"""Prospective IDs and latent construction, independent of physical backend."""
import importlib.util,json,unittest
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('prepare_c09',R/'scripts/preparar_producao_c09.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
class ProductionDesignTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.design=json.loads((R/'configs/robustness/c09_prospective_original_v1.json').read_text());cls.rows,cls.pairs,cls.truths=module.build(cls.design)
 def test_full_prospective_counts_and_unique_data_streams(self):
  expected={1:(1500,15000),2:(1500,1500),3:(1000,3000),4:(256,768),5:(256,1536),6:(500,3000),7:(384,1152)}
  for stage,(n,m) in expected.items():
   rows=[r for r in self.rows if r['stage_id']==stage];self.assertEqual(len(rows),n);self.assertEqual(sum(len(r['models']) for r in rows),m)
  self.assertEqual(len({tuple(r['data_seed']) for r in self.rows}),len(self.rows))
 def test_seeded_truths_reuse_and_global_latents(self):
  for p in range(3):
   for i in (0,27,499):
    v=np.random.Generator(np.random.PCG64(np.random.SeedSequence([909110101,1,p,0,i]))).random();u=(v,np.sqrt(v),np.exp(np.log(.001)*(1-v)))[p]
    self.assertAlmostEqual(self.truths[p,i],u,places=15)
  for r in self.rows:
   np.testing.assert_array_equal(self.pairs[r['truth_response_index']],[r['truth_u'],r['distance_scale']])
   if r['stage_id'] in (2,3,6):self.assertEqual(r['truth_u'],self.truths[0,r['datum_id']])
   if r['stage_id']==6:self.assertNotEqual(r['latent_seed'],r['data_seed']);self.assertTrue(r['latent_not_supplied_to_inference'])
if __name__=='__main__':unittest.main(verbosity=2)
