from pathlib import Path
import json,unittest
import numpy as np
from inference.campaign_sbc import synthesize, resolved_by_function
from inference.diagnostics import diagnose_sbc

ROOT=Path(__file__).resolve().parents[1]


class CampaignSBCTests(unittest.TestCase):
    def test_nominal_report_matches_existing_analytic_toy(self):
        cfg=json.loads((ROOT/'configs/calibration/sbc_synthesis_v1.json').read_text())
        cfg['n_realizations']=64
        with np.load(ROOT/'results/C07/toy/toy_inputs.npz',allow_pickle=False) as f:
            order=[0,1,1,0,0]
            u=f['pit'][order,:64];ll=f['loglikelihood_pit'][order,:64]
            q=f['quantiles'][order,:64];theta=f['truth'][:64]
            parameters=f['parameters'].tolist()
        groups={k:cfg['families'][k]['models'] for k in ['correct','approximate']}
        old=diagnose_sbc(u,q,theta,ll,methods=cfg['models'],parameters=parameters,
            probabilities=cfg['probabilities'],groups=groups,replicate_ids=list(range(64)),
            expected_n=64,numerical_complete=True)
        # Analytic TOY values, not an actual importance MCSE or a PTA result.
        pit=np.concatenate((u,ll[:,:,None]),axis=2)
        new,bounds=synthesize(pit,np.full(pit.shape,1e-8),np.ones(pit.shape,bool),q,cfg,parameters)
        self.assertEqual(len(new['tests']),155)
        self.assertEqual(len(new['paired_central90']),15)
        self.assertEqual(bounds['pit_lower'].shape,pit.shape)
        for a,b in zip(old['tests'],new['tests']):
            self.assertEqual((a['method'],a['target'],a['diagnostic']),(b['method'],b['target'],b['diagnostic']))
            self.assertAlmostEqual(a['pvalue'],b['nominal']['pvalue'],places=14)
            self.assertAlmostEqual(a['holm_pvalue'],b['nominal_holm_pvalue'],places=14)
            self.assertEqual(a['reject'],b['nominal_reject'])

    def fixture(self):
        import itertools
        specs=[]
        for level,indices in [(0,[0,5,10,15,20,25,26]),(1,list(range(27)))]:
            specs.extend([level,j,a,b] for j in indices for a,b in itertools.combinations(range(4),2))
        return dict(replication_specification=np.array(specs),replication_pass=np.ones(204,bool),
            refinement_pass=np.ones(7,bool),weight_deletion_guard_by_level=np.ones(2,bool),
            saturated_weight=np.zeros((2,4)),pit_precision_pass=np.ones(6,bool),pit_resolved=np.ones(6,bool))

    def test_per_function_gate_separates_unrelated_failure(self):
        arrays=self.fixture()
        np.testing.assert_array_equal(resolved_by_function(arrays),np.ones(6,bool))
        # Failure of the mass PIT does not invent failures in other parameters.
        arrays['refinement_pass'][0]=False
        np.testing.assert_array_equal(resolved_by_function(arrays),[False,True,True,True,True,True])
        # A low-level log evidence failure is common to the normalized ratios.
        arrays['replication_pass'][np.where(arrays['replication_specification'][:,1]==26)[0][0]]=False
        self.assertFalse(resolved_by_function(arrays).any())

    def test_quantile_cut_failure_is_retained_outside_pit_gate(self):
        arrays=self.fixture()
        arrays['replication_pass'][np.where(arrays['replication_specification'][:,1]==1)[0][0]]=False
        self.assertTrue(resolved_by_function(arrays).all())
        arrays['saturated_weight'][1,0]=2e-12
        self.assertFalse(resolved_by_function(arrays).any())


if __name__=='__main__':unittest.main()
