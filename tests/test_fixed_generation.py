"""Small independent algebraic/data-contract checks; no posterior calculations."""
import importlib.util
import json
import os
from pathlib import Path
import sys
import unittest
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
PACKAGE=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
spec=importlib.util.spec_from_file_location('inference.fixed_generation',PACKAGE/'src/inference/fixed_generation.py')
fixed=importlib.util.module_from_spec(spec);sys.modules[spec.name]=fixed;spec.loader.exec_module(fixed)
from inference.model import experiment,YEAR
from inference.campaign_io import load_observations,target_ids


class IdentityORF:
    def __init__(self):self.calls=[]
    def evaluate(self,u):
        self.calls.append(u)
        return np.broadcast_to(np.eye(12,dtype=complex),(4,12,12)).copy()


class FixedGenerationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config=json.loads((ROOT/'configs/calibration/fixed_experiment_v1.json').read_text())
        cls.protocol=json.loads((ROOT/'configs/calibration/fixed_scenarios_v1.json').read_text())
        cls.provider=IdentityORF()
        cls.arrays=fixed.generate_fixed_fixture(cls.config,cls.protocol,cls.provider)
        cls.exp=experiment(cls.config)

    def test_only_two_defined_orf_requests(self):
        self.assertEqual(self.provider.calls,[0.,.995])

    def test_no_gw_covariance_is_exact_noise_without_provider(self):
        class ForbiddenORF:
            def evaluate(self,u):raise AssertionError('No GW must not request an ORF.')
        c,g,noise=fixed.fixed_covariance(self.protocol['scenarios'][2],self.exp,ForbiddenORF())
        np.testing.assert_array_equal(g,np.zeros_like(g));np.testing.assert_array_equal(c,noise)
        for k,f in enumerate(self.exp['f']):
            red=10**(-31)*YEAR**3/(12*np.pi**2)*(f*YEAR)**(-4)*self.exp['red']**2
            white=2*self.exp['dt']*self.exp['sigma']**2
            expected=np.diag((red+white)/self.exp['scale'][k])
            np.testing.assert_allclose(c[k],expected,rtol=3e-15,atol=0)

    def test_missing_truth_masks_and_structural_endpoint(self):
        a=self.arrays
        self.assertTrue(np.isnan(a['truth'][64:,:3]).all())
        self.assertTrue(np.isfinite(a['truth'][:64]).all())
        np.testing.assert_array_equal(a['truth_defined'],np.isfinite(a['truth']))
        self.assertTrue(np.isnan(a['log_likelihood_at_truth'][64:]).all())
        self.assertTrue(np.isfinite(a['log_likelihood_at_truth'][:64]).all())
        self.assertEqual(a['structural_lower_boundary_pit'].sum(),32)
        self.assertTrue(a['structural_lower_boundary_pit'][:32,0].all())

    def test_cn_truth_loglikelihood_against_full_solve(self):
        a=self.arrays
        for row in [0,9,31,32,44,63]:
            c=a['covariance_by_scenario'][row//32];q=a['q'][row]
            value=0.
            for ck,qk in zip(c,q):
                sign,logdet=np.linalg.slogdet(ck)
                self.assertAlmostEqual(float(sign.real),1.)
                value-=float((qk.conj()@np.linalg.solve(ck,qk)).real+logdet+len(qk)*np.log(np.pi))
            self.assertAlmostEqual(value,a['log_likelihood_at_truth'][row],places=11)

    def test_reproducible_independent_scenario_streams(self):
        second=fixed.generate_fixed_fixture(self.config,self.protocol,IdentityORF())
        for name,value in self.arrays.items():self.assertTrue(np.array_equal(value,second[name],equal_nan=True),name)
        changed=json.loads(json.dumps(self.protocol));changed['scenarios'][1]['data_seed']+=1000
        third=fixed.generate_fixed_fixture(self.config,changed,IdentityORF())
        for name in ['q','x_physical','x_gaussian']:
            np.testing.assert_array_equal(self.arrays[name][:32],third[name][:32])
            np.testing.assert_array_equal(self.arrays[name][64:],third[name][64:])
            self.assertFalse(np.array_equal(self.arrays[name][32:64],third[name][32:64]))

    def test_row_and_runtime_target_contract(self):
        a=self.arrays
        self.assertEqual(a['q'].shape,(96,4,12));self.assertEqual(a['x_physical'].shape,(96,4,10))
        np.testing.assert_array_equal(np.bincount(a['scenario_index']),[32,32,32])
        np.testing.assert_array_equal(a['target'],target_ids({'models':['A0_CN'],'targets':list(range(96))},96))
        np.testing.assert_array_equal(a['replicate_within_scenario'],np.tile(np.arange(32),3))

    def test_missing_truth_cannot_be_finite_placeholder(self):
        bad=json.loads(json.dumps(self.protocol));bad['scenarios'][2]['truth'][:3]=[0.,-99.,4.]
        with self.assertRaises(ValueError):fixed.validate_design(self.config,bad)

    def test_design_mismatch_is_rejected(self):
        for key,value in [('n_realizations',95),('models',['A0_CN']),('fixed_red_slope',3.9)]:
            bad=dict(self.config);bad[key]=value
            with self.assertRaises(ValueError):fixed.validate_design(bad,self.protocol)

    def test_generated_fixture_runtime_loading(self):
        path=ROOT/'results/C07/fixed_scenarios/data.npz'
        if not path.exists():self.skipTest('Checked exact-ORF observations not generated yet.')
        observed=load_observations(path,self.exp)
        self.assertEqual(observed['q'].shape,(96,4,12))
        with np.load(path,allow_pickle=False) as a:
            self.assertTrue(np.all(a['gw_covariance_by_scenario'][2]==0))
            self.assertTrue(np.isnan(a['truth'][64:,:3]).all())


if __name__=='__main__':unittest.main()
