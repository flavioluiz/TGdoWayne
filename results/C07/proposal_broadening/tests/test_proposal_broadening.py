import importlib.util
from pathlib import Path
import unittest,tempfile,sys
from unittest.mock import patch
import numpy as np
from scipy.integrate import quad
from scipy.special import logsumexp
from scipy.stats import multivariate_normal,multivariate_t
from inference.campaign_training import validate_proposal
from inference.gmm_density import MultipleRHSGaussianDefensiveProposal

SOURCE=Path(__file__).resolve().parents[1]/'src/inference/proposal_broadening.py'
spec=importlib.util.spec_from_file_location('broadening',SOURCE);broadening=importlib.util.module_from_spec(spec);spec.loader.exec_module(broadening)
CONFIG=dict(wide_total_probability=.10,variance_multiplier=9)


def fixture(d=5):
    rng=np.random.default_rng(907150101);w=np.array([.15,.25,.20,.40]);means=rng.normal(size=(4,d));a=rng.normal(size=(4,d,d));cov=np.einsum('kij,klj->kil',a,a)/d+np.eye(d)*.3
    return w,means,cov


def proposal(w,m,c):
    d=m.shape[1]
    return MultipleRHSGaussianDefensiveProposal(w[None],m[None],c[None],np.zeros((1,d)),np.eye(d)[None],defensive_fraction=.15,student_df=5,student_scale=3)


class BroadeningTests(unittest.TestCase):
    def test_fit_is_not_mutated_and_fitted_vs_proposal_counts(self):
        w,m,c=fixture();original=[a.copy() for a in (w,m,c)]
        for a in (w,m,c):a.setflags(write=False)
        nw,nm,nc,meta=broadening.broaden_gaussian_fit(w,m,c,CONFIG)
        for a,b in zip((w,m,c),original):np.testing.assert_array_equal(a,b)
        np.testing.assert_array_equal(nm[:4],m);np.testing.assert_array_equal(nm[4:],m)
        np.testing.assert_array_equal(nc[:4],c);np.testing.assert_array_equal(nc[4:],9*c)
        np.testing.assert_array_max_ulp(.85*nw[:4],.75*w,maxulp=2);np.testing.assert_array_max_ulp(.85*nw[4:],.10*w,maxulp=2)
        self.assertEqual(meta['fitted_gaussian_components'],4);self.assertEqual(meta['proposal_gaussian_components'],8)
        self.assertAlmostEqual(meta['pointwise_density_lower_bound_factor'],.75/.85)
        nm[0,0]+=1;self.assertEqual(m[0,0],original[1][0,0])
    def test_eight_components_against_scipy_and_density_bound(self):
        w,m,c=fixture();nw,nm,nc,meta=broadening.broaden_gaussian_fit(w,m,c,CONFIG);old=proposal(w,m,c);new=proposal(nw,nm,nc)
        rng=np.random.default_rng(907150102);z=np.r_[rng.normal(size=(4096,5))*3,rng.standard_t(3,size=(1024,5))*20,m,np.zeros((1,5))]
        reference=logsumexp(np.stack([np.log(.85*nw[k])+multivariate_normal.logpdf(z,nm[k],nc[k]) for k in range(8)]+[np.log(.15)+multivariate_t.logpdf(z,np.zeros(5),np.eye(5)*(3/5)*9,df=5)]),axis=0)
        np.testing.assert_allclose(new.logpdf(z),reference,atol=3e-12,rtol=0)
        bound=new.logpdf(z)-old.logpdf(z)-np.log(meta['pointwise_density_lower_bound_factor'])
        self.assertGreaterEqual(float(bound.min()),-5e-13)
        row=dict(weights=nw.tolist(),means=nm.tolist(),covariances=nc.tolist(),global_mean=[0.]*5,global_cholesky=np.eye(5).tolist(),defensive_fraction=.15,student_df=5.,student_scale=3.)
        self.assertEqual(validate_proposal(row).k,8)
    def test_independent_integral_normalization(self):
        w,m,c=fixture(1);nw,nm,nc,_=broadening.broaden_gaussian_fit(w,m,c,CONFIG);q=proposal(nw,nm,nc)
        result,error=quad(lambda x:float(np.exp(q.logpdf(np.array([[x]])))[0]),-np.inf,np.inf,epsabs=2e-10,epsrel=2e-10,limit=300)
        self.assertLess(abs(result-1),2e-10);self.assertLess(error,2e-9)
    def test_optional_training_credentials_and_producer(self):
        from inference.campaign_training import train_block as original_training
        from inference.campaign_iid import produce_target
        from inference.campaign_io import canonical_hash,write_json_new
        script=SOURCE.parent/'campaign_training.py'
        spec=importlib.util.spec_from_file_location('inference._training_broadening_test',script);staged=importlib.util.module_from_spec(spec);spec.loader.exec_module(staged)
        class Runtime:
            def __init__(self,wide=False):
                self.identity='toy_execution';self.target_identity='toy_data';self.n=1;self.targets=np.array([0]);self.bounds=np.tile([0.,1.],(5,1));self.input_hashes={}
                self.settings=dict(training=dict(steps=1000,chains=4,points_for_em=256,seed=907150103),production=dict(levels=[64,256],replicates=4,seed=907150104,likelihood_batch=64,descriptive_points_per_replicate=8),budget=dict(maximum_active_raw_bytes=2000000))
                if wide:self.settings['training']['gaussian_broadening']=CONFIG
            def require_execution(self):return self
            def set_phase(self,phase):pass
            def snapshot(self,path):pass
            def verify_unchanged(self):pass
            def likelihood(self,theta,targets):return -np.sum(((theta-.4)/.2)**2,axis=1)
        with tempfile.TemporaryDirectory() as directory,patch.dict(sys.modules,{'inference.proposal_broadening':broadening}):
            root=Path(directory)
            old=original_training(Runtime(),[0],root/'old')[0]
            default=staged.train_block(Runtime(),[0],root/'default')[0]
            self.assertEqual(set(default),set(old))
            for key in ('weights','means','covariances','global_mean','global_cholesky'):
                np.testing.assert_array_equal(default[key],old[key])
            wide_runtime=Runtime(True);wide=staged.train_block(wide_runtime,[0],root/'wide')[0]
            self.assertEqual(len(wide['weights']),8);self.assertEqual(wide['unbroadened_gaussian_fit']['weights'],old['weights'])
            self.assertEqual(wide['unbroadened_gaussian_fit_sha256'],canonical_hash(wide['unbroadened_gaussian_fit']))
            self.assertEqual(wide['proposal_content_hash'],canonical_hash({k:v for k,v in wide.items() if k!='proposal_content_hash'}))
            self.assertNotEqual(wide['proposal_content_hash'],old['proposal_content_hash'])
            self.assertNotEqual(wide['training_configuration_sha256'],old['training_configuration_sha256'])
            result=produce_target(wide_runtime,0,root/'wide',root/'products',root/'raw')
            self.assertEqual(len(result['replicates']),8)
            inherited=dict(wide,proposal_content_hash=old['proposal_content_hash']);write_json_new(root/'invalid/target_000000.json',inherited)
            with self.assertRaisesRegex(RuntimeError,'contents changed'):
                produce_target(wide_runtime,0,root/'invalid',root/'bad_products',root/'bad_raw')
    def test_invalid_config_and_covariance_rejected(self):
        w,m,c=fixture()
        for cfg in [None,{},dict(CONFIG,typo=1),dict(CONFIG,wide_total_probability=.85),dict(CONFIG,wide_total_probability=np.nan),dict(CONFIG,variance_multiplier=1),dict(CONFIG,variance_multiplier=True)]:
            with self.assertRaises(ValueError):broadening.broaden_gaussian_fit(w,m,c,cfg)
        with self.assertRaises(ValueError):broadening.broaden_gaussian_fit(w,m,c,CONFIG,defensive_fraction=.2)
        invalid=c.copy();invalid[0]=0
        with self.assertRaises(ValueError):broadening.broaden_gaussian_fit(w,m,invalid,CONFIG)

if __name__=='__main__':unittest.main()
