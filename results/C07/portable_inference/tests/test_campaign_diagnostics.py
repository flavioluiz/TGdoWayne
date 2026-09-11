import unittest
import numpy as np
from scipy.stats import norm
from inference.campaign_diagnostics import numerical_statistics, PIT_INDICES
from inference.iid_diagnostics import replicated_cdf, replicated_weights, weighted_quantiles

class CampaignDiagnosticTests(unittest.TestCase):
    def fixtures(self):
        rng=np.random.default_rng(907121001); result=[]
        for n in [256,1024]:
            x=rng.random((4,n,5));ll=-np.sum((x-.4)**2,axis=-1)*4
            result.append(dict(x_unit=x,log_likelihood=ll,log_weights=ll))
        return result
    def test_against_original_v1(self):
        low,high=self.fixtures();truth=np.array([.15,.3,.5,.7,.9]);truthll=-.8
        arrays,summary=numerical_statistics(low,high,truth,truthll,np.tile([0,1],(5,1)))
        for p in range(5):
            cuts=weighted_quantiles(low['x_unit'][:,:,p].ravel(),low['log_weights'].ravel(),[.05,.5,.9,.95])
            np.testing.assert_array_equal(cuts,arrays['independent_cuts_unit'][p])
            for level,data in enumerate([low,high]):
                reference=replicated_cdf(data['x_unit'][:,:,p],data['log_weights'],np.r_[truth[p],cuts])
                for i,row in enumerate(reference):
                    self.assertAlmostEqual(row['estimate'],arrays['cdf_estimates_by_level'][level,p*5+i],places=14)
                    self.assertAlmostEqual(row['mcse'],arrays['cdf_mcse_by_level'][level,p*5+i],places=14)
                    self.assertEqual(row['precision_pass'],arrays['cdf_precision_by_level'][level,p*5+i])
        reference=replicated_weights(high['log_weights'])
        self.assertAlmostEqual(reference['log_evidence'],float(arrays['log_evidence']),places=14)
        self.assertEqual(summary['replication_family']['global_size'],510000)
        self.assertEqual(summary['refinement_family']['global_size'],17500)
        self.assertAlmostEqual(summary['replication_family']['z'],norm.isf(.05/(2*510000)))
        self.assertAlmostEqual(summary['refinement_family']['z'],norm.isf(.05/(2*17500)))
        self.assertEqual(arrays['replication_specification'].shape,(204,4))
        self.assertEqual(int((arrays['replication_specification'][:,0]==0).sum()),42)
    def test_constant_indicator_is_not_approved(self):
        low,high=self.fixtures()
        arrays,summary=numerical_statistics(low,high,np.zeros(5),-1e100,np.tile([0,1],(5,1)))
        np.testing.assert_array_equal(arrays['pit_resolved'],False)
        np.testing.assert_array_equal(arrays['pit'],0.)
        self.assertTrue(np.isinf(arrays['pit_mcse']).all())
        self.assertFalse(summary['cdf_precision_pass'])
        self.assertFalse(summary['refinement_pass'])
        self.assertTrue(summary['no_automatic_approval'])
    def test_keeps_physical_quantile_units(self):
        low,high=self.fixtures();bounds=np.array([[0,1],[-16,-14],[3,5.5],[-17,-14.5],[-.30103,.30103]])
        arrays,_=numerical_statistics(low,high,np.full(5,.5),-.5,bounds,population_targets=1)
        np.testing.assert_allclose(arrays['quantiles_physical'],bounds[:,0,None]+np.diff(bounds,axis=1)*arrays['quantiles_unit'],rtol=0,atol=0)

if __name__=='__main__':unittest.main()

class DiagnosticIntegrationTests(unittest.TestCase):
    def test_complete_reader_and_direct_truth_identity(self):
        from pathlib import Path
        import tempfile,json
        from inference.campaign_io import write_json_new,write_npz_new,sha256,read_json
        from inference.campaign_diagnostics import diagnose_target
        from inference.campaign_iid import produce_target
        # Existing independent Beta producer fixture; no PTA calibration claim.
        from test_portable_contract import ToyRuntime,put_proposal
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);rt=ToyRuntime();put_proposal(root/'proposals')
            data=root/'data.npz';write_npz_new(data,truth=np.array([[.2,.4,.5,.6,.8],[.5]*5]))
            config=root/'experiment.json';write_json_new(config,{'models':['A0_CN','A_CN','B_CN','A_G','B_G']})
            rt.cfg=read_json(config);rt.input_hashes={'data':sha256(data),'experiment':sha256(config)}
            result=produce_target(rt,0,root/'proposals',root/'production',root/'raw')
            truthlogl=root/'direct_truth.json';write_json_new(truthlogl,dict(status='DIRECT_ORF_TRUTH_LOGL_DIAGNOSTIC_ONLY',data_sha256=sha256(data),config_sha256=sha256(config),models=rt.cfg['models'],shape=[5,2],log_likelihood=[[.4,.1]]*5))
            protocol=root/'protocol.json';write_json_new(protocol,dict(population_targets=2,levels=[64,256],independent_replications=4,cdf_mcse_target=.00335,alpha_replicate_family=.05,alpha_refinement_family=.05,maximum_saturated_target_weight=1e-12))
            # Diagnostic must consume the external value and never call its inference kernel.
            rt.likelihood=lambda *args:(_ for _ in ()).throw(AssertionError('Unexpected interpolated truth likelihood'))
            row=diagnose_target(rt,root/'production/target_000000.json',root/'raw',data,protocol,root/'diagnostic',truth_loglikelihood_path=truthlogl)
            self.assertEqual(row['status'],'NUMERICAL_DIAGNOSTICS_COMPLETE')
            self.assertFalse(row['raw_release_authorized'])
            self.assertLess(row['numeric_bytes'],100000)
            with np.load(root/'diagnostic'/row['numeric_file']) as saved:
                self.assertEqual(saved['pit'].shape,(6,));self.assertEqual(saved['cut_cdf'].shape,(5,4))
                self.assertEqual(float(saved['truth_log_likelihood']),.4)
            resumed=diagnose_target(rt,root/'production/target_000000.json',root/'raw',data,protocol,root/'diagnostic',truth_loglikelihood_path=truthlogl,resume=True)
            self.assertEqual(row,resumed)
            altered=read_json(truthlogl);altered['data_sha256']='bad';bad=root/'bad_truth.json';write_json_new(bad,altered)
            with self.assertRaisesRegex(RuntimeError,'identity mismatch'):
                diagnose_target(rt,root/'production/target_000000.json',root/'raw',data,protocol,root/'bad_diagnostic',truth_loglikelihood_path=bad)
