"""TOY array/contract tests for the masked adapter; not PTA posterior samples."""
import copy
import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
from types import SimpleNamespace
import numpy as np
from scipy import stats

ROOT=Path(os.environ.get('TG_PROJECT_ROOT','.')).resolve();PACKAGE=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
spec=importlib.util.spec_from_file_location('inference.fixed_diagnostics',PACKAGE/'src/inference/fixed_diagnostics_v2.py')
fixed=importlib.util.module_from_spec(spec);sys.modules[spec.name]=fixed;spec.loader.exec_module(fixed)
from inference.campaign_diagnostics import numerical_statistics
from inference.campaign_io import sha256
from inference.iid_optimized import TargetIIDContext


class FixedDiagnosticsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cfg=json.loads((PACKAGE/'configs/calibration/fixed_experiment_v1.json').read_text());cls.bounds=np.array(cfg['prior']['bounds'])
        rng=np.random.default_rng(707511901);cls.levels=[]
        for n in [64,256]:
            x=rng.uniform(size=(4,n,5))
            ll=-3*np.square(x-.4).sum(axis=-1)
            # Arbitrary finite TOY importance values; never claimed to target a PTA posterior.
            lw=ll+.2*x[:,:,0]-.1*x[:,:,4]
            cls.levels.append(dict(x_unit=x,log_likelihood=ll,log_weights=lw))

    def run_case(self,case,levels=None):
        truth=np.array([.4,.45,.5,.55,.6]);defined=np.ones(5,bool);structural=np.zeros(5,bool)
        logl=-1.;logl_defined=True
        if case=='zero':truth[0]=0.;structural[0]=True
        if case=='absent':truth[:3]=np.nan;defined[:3]=False;logl=np.nan;logl_defined=False
        return fixed.fixed_numerical_statistics(*(levels or self.levels),truth,defined,logl,logl_defined,self.bounds,structural)

    def test_interior_reproduces_unmasked_v1_all_common_fields(self):
        output,summary=self.run_case('interior')
        ref,old=numerical_statistics(*self.levels,np.array([.4,.45,.5,.55,.6]),-1.,self.bounds,population_targets=96)
        for name,value in ref.items():
            np.testing.assert_allclose(output[name],value,rtol=0,atol=1e-12,equal_nan=True,err_msg=name)
        self.assertEqual(summary['replication_family']['executed'],204)
        self.assertEqual(summary['refinement_family']['executed'],7)
        self.assertEqual(summary['replication_family']['z'],old['replication_family']['z'])

    def test_undefined_values_never_enter_cdf(self):
        seen=[]
        class InspectContext(TargetIIDContext):
            def cdf(self,values,thresholds,**kwargs):
                seen.extend(np.asarray(thresholds).tolist())
                if not np.isfinite(thresholds).all():raise AssertionError('Undefined cutoff entered CDF.')
                return super().cdf(values,thresholds,**kwargs)
        with patch.object(fixed,'TargetIIDContext',InspectContext):out,summary=self.run_case('absent')
        np.testing.assert_array_equal(out['pit_applicable'],[False,False,False,True,True,False])
        self.assertTrue(np.isnan(out['pit'][[0,1,2,5]]).all())
        self.assertTrue(np.isnan(out['pit_mcse'][[0,1,2,5]]).all())
        self.assertFalse(out['pit_resolved'][[0,1,2,5]].any())
        self.assertEqual(len(seen),44) # 22 CDF cuts in each level.
        self.assertEqual(summary['replication_family']['executed'],156)
        self.assertEqual(summary['refinement_family']['executed'],3)

    def test_structural_zero_is_exact_and_omitted_from_contrasts(self):
        out,summary=self.run_case('zero')
        self.assertEqual(out['pit'][0],0.);self.assertEqual(out['pit_mcse'][0],0.)
        self.assertTrue(out['pit_structural_exact'][0]);self.assertTrue(out['pit_precision_pass'][0])
        self.assertTrue(out['pit_resolved'][0])
        self.assertFalse(np.any(out['replication_specification'][:,1]==0))
        self.assertFalse(np.any(out['refinement_specification']==0))
        self.assertEqual(summary['replication_family']['executed'],192)
        self.assertEqual(summary['refinement_family']['executed'],6)

    def test_global_families_unchanged_when_functions_omitted(self):
        for case in ['interior','zero','absent']:
            out,summary=self.run_case(case)
            self.assertAlmostEqual(summary['replication_family']['z'],stats.norm.isf(.05/(2*19584)),places=14)
            self.assertAlmostEqual(summary['refinement_family']['z'],stats.norm.isf(.05/(2*672)),places=14)
            self.assertEqual(summary['replication_family']['global_size'],19584)
            self.assertEqual(summary['refinement_family']['global_size'],672)

    def test_twenty_quantile_products_unchanged_without_truth(self):
        a,_=self.run_case('interior');b,_=self.run_case('absent');c,_=self.run_case('zero')
        for name in ['quantiles_unit','quantiles_physical','independent_cuts_unit','cut_cdf','cut_mcse','cut_precision_pass']:
            if name=='cut_precision_pass':
                np.testing.assert_array_equal(a[name],b[name]);np.testing.assert_array_equal(a[name],c[name])
            else:
                # Different mask widths can select different BLAS reductions.
                # Permit only roundoff; all Boolean decisions remain exact.
                np.testing.assert_allclose(a[name],b[name],rtol=0,atol=2e-14,err_msg=name)
                np.testing.assert_allclose(a[name],c[name],rtol=0,atol=2e-14,err_msg=name)

    def test_other_constant_indicators_stay_unresolved(self):
        levels=copy.deepcopy(self.levels)
        for level in levels:level['x_unit'][:,:,3]=.2
        out,_=self.run_case('absent',levels)
        self.assertAlmostEqual(out['pit'][3],1.,places=14)
        self.assertTrue(np.isinf(out['pit_mcse'][3]));self.assertFalse(out['pit_resolved'][3])
        self.assertFalse(out['pit_precision_pass'][3]);self.assertFalse(out['pit_structural_exact'][3])

    def test_structural_forgery_and_finite_missing_truth_rejected(self):
        truth=np.array([0.,.4,.4,.4,.4]);mask=np.ones(5,bool);bad=np.array([True,True,False,False,False])
        with self.assertRaises(ValueError):fixed.fixed_numerical_statistics(*self.levels,truth,mask,-1.,True,self.bounds,bad)
        truth[:3]=.5;mask[:3]=False
        with self.assertRaises(ValueError):fixed.fixed_numerical_statistics(*self.levels,truth,mask,np.nan,False,self.bounds,np.zeros(5,bool))
        truth[:3]=np.nan
        with self.assertRaises(ValueError):fixed.fixed_numerical_statistics(*self.levels,truth,mask,-1.,False,self.bounds,np.zeros(5,bool))

    def test_truth_only_loader_hashes_and_masks(self):
        data=PACKAGE/'results/C07/fixed_scenarios/data.npz';generation=PACKAGE/'results/C07/fixed_scenarios/generation.json'
        report=json.loads(generation.read_text())
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'producer.json'
            for target in [0,32,64]:
                record={'model':'A0_CN','target':target,'datum':target,'input_sha256':{'data':sha256(data),'experiment':report['preflight']['experiment_sha256']}}
                path.write_text(json.dumps(record))
                t=fixed.load_fixed_truth(path,data,generation,self.bounds)
                self.assertEqual(t['scenario'],target//32)
                self.assertEqual(t['defined'].sum(),5 if target<64 else 2)
                self.assertEqual(t['logl_defined'],target<64)
                self.assertEqual(t['structural'].sum(),1 if target==0 else 0)
            record['input_sha256']['data']='0'*64;path.write_text(json.dumps(record))
            with self.assertRaises(RuntimeError):fixed.load_fixed_truth(path,data,generation,self.bounds)

    def test_json_masked_summary_and_no_approval(self):
        out,summary=self.run_case('absent')
        json.dumps(fixed.json_safe(summary),allow_nan=False)
        clean=fixed.json_safe(out['pit'])
        self.assertEqual(clean[:3],[None,None,None]);self.assertIsNone(clean[5])
        self.assertTrue(summary['no_automatic_approval'])
        self.assertEqual(summary['scope'],'FIXED_TRUTH_NUMERICAL_DIAGNOSTICS_NOT_SBC')

    def test_toy_file_adapter_writes_resumes_and_rejects_changed_identity(self):
        # Complete raw-reader/serialization path with toy64/256 levels and a
        # fabricated96-row truth catalog. No real PTA posterior cloud is read.
        with tempfile.TemporaryDirectory() as directory:
            base=Path(directory);raw=base/'raw';raw.mkdir();out=base/'diagnostics'
            truth=np.tile(self.bounds.mean(axis=1),(96,1));truth[:32,0]=0.;truth[32:64,0]=.995;truth[64:,:3]=np.nan
            defined=np.isfinite(truth);structural=np.zeros((96,5),bool);structural[:32,0]=True
            logl=np.full(96,-1.);logl[64:]=np.nan
            data=base/'toy_truth.npz'
            np.savez(data,truth=truth,truth_defined=defined,structural_lower_boundary_pit=structural,
                log_likelihood_at_truth=logl,log_likelihood_at_truth_defined=np.isfinite(logl),
                scenario_index=np.repeat(np.arange(3),32),replicate_within_scenario=np.tile(np.arange(32),3),target=np.arange(96))
            generation=base/'toy_generation.json';generation.write_text(json.dumps({'status':'FIXED_DATA_GENERATED_NOT_POSTERIOR_INFERENCE',
                'data_sha256':sha256(data),'preflight':{'experiment_sha256':'toy_experiment'}}))
            record={'status':'IID_COMPLETE_AWAITING_DIAGNOSTICS','identity':'toy_identity','target':64,'datum':64,'model':'A0_CN',
                'levels':[64,256],'proposal_sha256':'toy_proposal','input_sha256':{'data':sha256(data),'experiment':'toy_experiment'},'replicates':[]}
            for level,source in zip(record['levels'],self.levels):
                for r in range(4):
                    x=source['x_unit'][r];ll=source['log_likelihood'][r];name=f'toy_N{level}_rep{r}.npz';path=raw/name
                    np.savez(path,x_unit=x,z=np.log(x/(1-x)),log_likelihood=ll,log_weights=ll,
                        log_prior_logit=np.zeros(level),log_proposal=np.zeros(level),target=64,replicate=r)
                    record['replicates'].append({'level':level,'replicate':r,'raw_file':name,'raw_sha256':sha256(path),
                        'saturated_rows':0,'saturated_normalized_target_weight':0.})
            report=base/'toy_target.json';report.write_text(json.dumps(record))
            protocol=json.loads((PACKAGE/'configs/calibration/fixed_diagnostics_v1.json').read_text())
            protocol['levels']=[64,256];protocol['protocol']='TOY_FILE_ADAPTER_ONLY_NOT_PRODUCTION'
            config=base/'toy_protocol.json';config.write_text(json.dumps(protocol))
            calls=[]
            runtime=SimpleNamespace(identity='toy_identity',n=96,targets=np.arange(96),bounds=self.bounds,
                cfg={'prior':{'kind':'independent uniform in these coordinates'}},verify_unchanged=lambda:calls.append('checked'))
            meta=fixed.diagnose_fixed_target(runtime,report,raw,data,generation,config,out)
            self.assertFalse(meta['raw_release_authorized']);self.assertEqual(meta['truth_likelihood_evaluations_this_reader'],0)
            self.assertEqual(meta['summary']['high_pit_applicable'],2);self.assertEqual(calls,['checked'])
            with np.load(out/meta['numeric_file'],allow_pickle=False) as values:
                self.assertTrue(np.isnan(values['pit'][[0,1,2,5]]).all())
                self.assertTrue(np.isfinite(values['quantiles_unit']).all())
            resumed=fixed.diagnose_fixed_target(runtime,report,raw,data,generation,config,out,resume=True)
            self.assertEqual(meta['numeric_sha256'],resumed['numeric_sha256'])
            protocol['unexpected_change']=True;config.write_text(json.dumps(protocol))
            with self.assertRaises(RuntimeError):fixed.diagnose_fixed_target(runtime,report,raw,data,generation,config,out,resume=True)


if __name__=='__main__':unittest.main()
