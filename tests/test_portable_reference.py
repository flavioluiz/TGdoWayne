"""Root-import algebra checks; no rerun of the historical 139-mass campaign."""
import ast,json,tempfile,unittest
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
from unittest.mock import patch
from pathlib import Path
import numpy as np
from inference.model import experiment,covariance_batch
from inference.reference_paths import CONFIG,DATA
from inference.reference_cubature import (LogAmplitudeBox,FrozenMassTable,SpectralCN,b_nodes,a_nodes,mass_integral)
from inference.reference_truncated import truncated_box
from inference.reference_bounded import bounded_mass_batch,bounded_mass_integral

class PortableReferenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.e=experiment(json.loads(CONFIG.read_text()));cls.box=LogAmplitudeBox()
        with np.load(DATA,allow_pickle=False) as p:cls.q=p['q'][14]
        cls.table=FrozenMassTable(cls.e,json.loads(CONFIG.read_text())['orf'])
    def test_joint_prior_normalization_and_covariance(self):
        box=self.box;volume=np.ptp(box.gw)*np.ptp(box.red)*np.ptp(box.efac)
        total=ab=amean=bmean=0.
        for b,wb in zip(*b_nodes(box,3)):
            a,wa=a_nodes(box,b,3);lo,hi=box.conditional_bounds(a,b);w=wb*wa*(hi-lo)/volume
            total+=w.sum();ab+=w@(a*b);amean+=w@a;bmean+=w.sum()*b
        self.assertAlmostEqual(total,1.,12)
        self.assertAlmostEqual(ab-amean*bmean,np.ptp(box.efac)**2/12,11)
    def test_truncation_retains_full_prior_measure(self):
        for param in [1,2,3,4]:
            attr={1:'gw',2:'slope',3:'red',4:'efac'}[param];lo,hi=getattr(self.box,attr)
            small,logfraction=truncated_box(self.box,param,lo+.37*(hi-lo))
            self.assertAlmostEqual(np.exp(logfraction),.37,13)
            self.assertAlmostEqual(getattr(small,attr)[1],lo+.37*(hi-lo),13)
    def test_spectral_coefficients_against_cholesky(self):
        for u in [0.,.5,1.]:
            gamma=self.table.get(u);a=np.array([-15.9,-15.,-14.6]);slope=np.array([3.,4.3,5.5]);b=-15.
            eta=np.column_stack([a,slope,np.full(3,b),np.zeros(3)])
            C,_=covariance_batch(eta,gamma,self.e);L=np.linalg.cholesky(C)
            x=np.linalg.solve(L,np.broadcast_to(self.q[None,:,:,None],(3,*self.q.shape,1)))
            chi=np.sum(abs(x)**2,axis=(1,2,3));ld=2*np.log(np.diagonal(L,axis1=-2,axis2=-1).real).sum(axis=(1,2))
            actual_chi,actual_ld=SpectralCN(self.e,self.q,gamma,b).coefficients(a,slope)
            np.testing.assert_allclose(actual_chi,chi,rtol=5e-11,atol=2e-9)
            np.testing.assert_allclose(actual_ld,ld,rtol=0,atol=2e-9)
    def test_batched_integrals_match_unpruned_scalar(self):
        gammas=np.stack([self.table.get(u) for u in [0.,.5,1.]])
        small,_=truncated_box(self.box,4,-.2)
        vals,uppers,_=bounded_mass_batch(gammas,self.e,self.q,small,(4,4,4),log_point_cut=np.full(3,-np.inf))
        scalar=np.array([mass_integral(g,self.e,self.q,small,(4,4,4))[0] for g in gammas])
        np.testing.assert_allclose(vals,scalar,atol=2e-10,rtol=0)
        self.assertTrue(np.isneginf(uppers).all())
    def test_cache_signature_includes_omission_budget(self):
        from inference.reference_bounded import CDFEvaluator
        artifact_root=Path(__file__).resolve().parents[1]/'results/C07/reference/cubature'
        if not artifact_root.exists():
            from inference.reference_paths import FROZEN_CUBATURE_RESULTS
            artifact_root=FROZEN_CUBATURE_RESULTS
        with tempfile.TemporaryDirectory() as scratch,patch('inference.reference_bounded.FROZEN_CUBATURE_RESULTS',artifact_root),patch('inference.reference_bounded.QUANTILE_RESULTS',Path(scratch)):
            first=CDFEvaluator((20,20,20),mass_count=17,relative_omission_budget=1e-12)
            second=CDFEvaluator((20,20,20),mass_count=17,relative_omission_budget=1e-10)
            self.assertNotEqual(first.signature,second.signature)
            self.assertEqual(first.logZ,second.logZ)
    def test_omission_encloses_finite_quadrature(self):
        gamma=self.table.get(.5)
        exact=bounded_mass_integral(gamma,self.e,self.q,self.box,(4,4,4),log_point_cut=-np.inf)[0]
        computed,upper,_=bounded_mass_integral(gamma,self.e,self.q,self.box,(4,4,4),log_point_cut=exact-5)
        self.assertLessEqual(computed,exact+2e-12)
        self.assertGreaterEqual(np.logaddexp(computed,upper),exact-2e-12)

if __name__=='__main__':unittest.main()
