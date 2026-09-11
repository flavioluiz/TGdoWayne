"""Analytic normal-conjugate TOY64 and archive-schema guards, not PTA results."""
from pathlib import Path
import importlib.util,itertools,json,tempfile,unittest
import numpy as np
from scipy.stats import norm,ncx2,kstest,binomtest
from inference.campaign_io import write_json_new,write_npz_new,sha256,read_json
from inference.campaign_sbc import synthesize

BASE=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('delivery',BASE/'scripts/sintetizar_calibracao.py');delivery=importlib.util.module_from_spec(spec);spec.loader.exec_module(delivery)
ROOT=Path.cwd()


def make_fixture(root):
    rng=np.random.default_rng(907140301);n=64;theta=rng.normal(size=(n,5));y=theta+rng.normal(scale=.7,size=(n,5));truth=norm.cdf(theta);probs=delivery.PROBS
    models=list(delivery.MODELS);bounds=np.tile([0.,1.],(5,1));pit=[];quantiles=[];truth_logl=[]
    for noise in [.7,.35,.45,.7,.7]:
        variance=1/(1+1/noise**2);mean=variance*y/noise**2;sd=np.sqrt(variance)
        p=norm.cdf((theta-mean)/sd);q=norm.cdf(mean[:,:,None]+sd*norm.ppf(probs)[None,None,:])
        distance=np.sum((theta-y)**2,axis=1);noncentral=np.sum((mean-y)**2,axis=1)/variance
        logl_pit=ncx2.sf(distance/variance,df=5,nc=noncentral)
        pit.append(np.c_[p,logl_pit]);quantiles.append(q);truth_logl.append(-2.5*np.log(2*np.pi*noise**2)-distance/(2*noise**2))
    pit=np.asarray(pit);quantiles=np.asarray(quantiles)
    data=root/'data.npz';write_npz_new(data,truth=truth,latent_truth=theta,observations=y,label=np.asarray('Analytic TOY64; no PTA or ORF calculation.'))
    exp=root/'experiment.json';write_json_new(exp,dict(n_realizations=n,models=models,prior={'bounds':bounds.tolist()},parameters=['u','log10_Agw','gamma_gw','log10_Ar','log10_EFAC'],scope='TOY_SCHEMA_ONLY'))
    protocol=root/'numerical.json';write_json_new(protocol,dict(population_targets=320,levels=[16384,65536],independent_replications=4,cdf_mcse_target=.00335,alpha_replicate_family=.05,alpha_refinement_family=.05,maximum_saturated_target_weight=1e-12))
    direct=root/'truth_logl.json';write_json_new(direct,dict(status='DIRECT_ORF_TRUTH_LOGL_DIAGNOSTIC_ONLY',scope='SCHEMA_FIXTURE_ONLY: analytic conjugate logL, no actual ORF',data_sha256=sha256(data),config_sha256=sha256(exp),models=models,shape=[5,n],log_likelihood=np.asarray(truth_logl).tolist()))
    cfg=read_json(ROOT/'configs/calibration/sbc_synthesis_v1.json');cfg.update(n_realizations=n,data_sha256=sha256(data),scope='ANALYTIC_TOY64_NOT_PTA');config=root/'synthesis.json';write_json_new(config,cfg)
    evidence_doc=root/'analytic_evidence.txt';evidence_doc.write_text('TOY metadata guard only. Conjugate normal posterior and noncentral chi-square logL CDF. No ORF approval.\n')
    evidence=root/'evidence.json';write_json_new(evidence,dict(entries=[dict(role=role,path=evidence_doc.name,sha256=sha256(evidence_doc)) for role in ['orf_interpolation','likelihood_kernel','external_posterior_reference']],limitations=['Synthetic evidence roles solely test schema; they are not PTA numerical validation.']))
    for m in range(5):
        for d in range(n):
            t=m*n+d;est=np.zeros((2,26))
            for j in range(5):est[:,j*5]=pit[m,d,j];est[:,j*5+1:j*5+5]=probs
            est[:,25]=pit[m,d,5];se=np.full((2,26),1e-8)
            a=dict(target=np.asarray(t),datum=np.asarray(d),model_index=np.asarray(m),probabilities=probs,
                truth_physical=truth[d],truth_unit=truth[d],truth_log_likelihood=np.asarray(truth_logl[m][d]),
                quantiles_unit=quantiles[m,d],quantiles_physical=quantiles[m,d],pit=pit[m,d],pit_mcse=se[1,delivery.PIT],
                cdf_estimates_by_level=est,cdf_mcse_by_level=se,cdf_resolved_by_level=np.ones((2,26),bool),cdf_precision_by_level=np.ones((2,26),bool),pit_resolved=np.ones(6,bool),pit_precision_pass=np.ones(6,bool),
                replication_specification=delivery.SPECS,replication_difference=np.zeros(204),replication_mcse=np.full(204,1e-8),replication_resolved=np.ones(204,bool),replication_pass=np.ones(204,bool),
                refinement_difference=np.zeros(7),refinement_mcse=np.full(7,1e-8),refinement_resolved=np.ones(7,bool),refinement_pass=np.ones(7,bool),weight_deletion_guard_by_level=np.ones(2,bool),saturated_weight=np.zeros((2,4)),cut_precision_pass=np.ones((5,4),bool),weight_ess=np.asarray(262144.),maximum_weight=np.asarray(1/262144),log_evidence=np.asarray(0.))
            numeric=root/'diagnostics'/f'diagnostic_target_{t:06d}.npz';write_npz_new(numeric,**a)
            reps=[dict(level=level,replicate=r,raw_file=f'target_{t:06d}_N{level}_rep_{r:02d}.npz',raw_sha256='schema_fixture_no_raw') for level in [16384,65536] for r in range(4)]
            pp=root/'production'/f'target_{t:06d}.json';producer=dict(identity='ANALYTIC_TOY64_SCHEMA',target=t,datum=d,model=models[m],input_sha256={'data':sha256(data),'experiment':sha256(exp)},proposal_sha256='schema_fixture_no_proposal',levels=[16384,65536],replicates=reps);write_json_new(pp,producer)
            meta=dict(status='NUMERICAL_DIAGNOSTICS_COMPLETE',schema='C07_TARGET_IID_DIAGNOSTICS_v1',identity='ANALYTIC_TOY64_SCHEMA',target=t,datum=d,model=models[m],numeric_file=numeric.name,numeric_sha256=sha256(numeric),diagnostic_inputs={'producer_report_sha256':sha256(pp),'truth_data_sha256':sha256(data),'truth_loglikelihood_sha256':sha256(direct),'protocol_sha256':sha256(protocol)},proposal_sha256=producer['proposal_sha256'],levels=[16384,65536],raw_sha256={r['raw_file']:r['raw_sha256'] for r in reps},toy_precision_flags='Synthetic positive MCSE1e-8 solely tests schema; no PTA precision claim.');write_json_new(root/'diagnostics'/f'diagnostic_target_{t:06d}.json',meta)
    return dict(diagnostics=root/'diagnostics',production=root/'production',experiment=exp,data=data,truth_logl=direct,config=config,numerical_protocol=protocol,evidence=evidence),pit,quantiles


class DeliveryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory();cls.root=Path(cls.temp.name);cls.inputs,cls.pit,cls.quantiles=make_fixture(cls.root)
    @classmethod
    def tearDownClass(cls):cls.temp.cleanup()
    def load(self):return delivery.load_campaign(**self.inputs,toy64=True)
    def test_analytic_toy64_against_independent_scipy_tests(self):
        arrays,cfg,parameters,provenance=self.load();np.testing.assert_array_equal(arrays['pit'],self.pit)
        report,_=synthesize(arrays['pit'],arrays['mcse'],arrays['resolved'],arrays['quantiles_unit'],cfg,parameters)
        self.assertEqual(len(report['tests']),155);self.assertEqual(len(report['paired_central90']),15)
        for row in report['tests']:
            m=cfg['models'].index(row['method']);j=(parameters+['logL_at_truth']).index(row['target']);values=self.pit[m,:,j]
            if row['diagnostic']=='PIT':expected=kstest(values,'uniform',method='exact').pvalue
            elif row['diagnostic']=='central_90':expected=binomtest(int(((values>=.05)&(values<=.95)).sum()),64,.9).pvalue
            else:
                p=float(row['diagnostic'].split('q')[1]);expected=binomtest(int((values<=p).sum()),64,p).pvalue
            self.assertAlmostEqual(row['nominal']['pvalue'],expected,places=13)
        self.assertTrue(provenance['all_ids_retained']);self.assertEqual(len(provenance['inventory']),320)
    def test_incomplete_inventory_is_rejected(self):
        path=self.root/'diagnostics/diagnostic_target_000000.json';saved=path.read_bytes();path.unlink()
        try:
            with self.assertRaisesRegex(ValueError,'Missing or extra'):self.load()
        finally:path.write_bytes(saved)
    def test_identity_and_duplicate_guards(self):
        path=self.root/'diagnostics/diagnostic_target_000001.json';saved=path.read_bytes()
        try:
            for field,value,message in [('identity','different','Mixed runtime'),('target',0,'Duplicate'),('datum',2,'mismatch')]:
                altered=json.loads(saved);altered[field]=value;path.write_text(json.dumps(altered))
                with self.assertRaisesRegex((ValueError,RuntimeError),message):self.load()
        finally:path.write_bytes(saved)
    def test_numeric_hash_truth_and_specification_guards(self):
        meta=self.root/'diagnostics/diagnostic_target_000000.json';numeric=self.root/'diagnostics/diagnostic_target_000000.npz';saved_meta=meta.read_bytes();saved_numeric=numeric.read_bytes()
        try:
            numeric.write_bytes(saved_numeric+b'changed')
            with self.assertRaisesRegex(RuntimeError,'hash changed'):self.load()
            for field in ['truth_physical','replication_specification']:
                numeric.write_bytes(saved_numeric)
                with np.load(numeric) as f:a={k:f[k] for k in f.files}
                if field=='truth_physical':a[field]=a[field].copy();a[field][0]+=.001
                else:a[field]=a[field].copy();a[field][1]=a[field][0]
                np.savez_compressed(numeric,**a);record=json.loads(saved_meta);record['numeric_sha256']=sha256(numeric);meta.write_text(json.dumps(record))
                with self.assertRaises((ValueError,RuntimeError)):self.load()
        finally:meta.write_bytes(saved_meta);numeric.write_bytes(saved_numeric)
    def test_toy_cannot_be_mistaken_for_main500(self):
        with self.assertRaisesRegex(ValueError,'500'):delivery.load_campaign(**self.inputs)

if __name__=='__main__':unittest.main()
