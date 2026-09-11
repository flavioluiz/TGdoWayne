from pathlib import Path
import sys,unittest
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from inference.iid_diagnostics import *

class IIDTests(unittest.TestCase):
    def test_unweighted_matches_sample_mean_variance(self):
        x=np.arange(100.);r=iid_cdf(x,np.zeros(100),[29.])[0]
        self.assertAlmostEqual(r['estimate'],.3)
        self.assertAlmostEqual(r['mcse'],np.std(x<=29,ddof=1)/10)

    def test_direct_ratio_influence(self):
        x=np.arange(20.);w=np.linspace(.2,3,20);r=iid_cdf(x,np.log(w),[8.])[0]
        f=np.sum(w*(x<=8))/w.sum();psi=w/w.mean()*((x<=8)-f)
        self.assertAlmostEqual(r['mcse'],np.std(psi,ddof=1)/np.sqrt(20))

    def test_shift_changes_evidence_not_cdf(self):
        lw=np.linspace(-20,0,500);x=np.arange(500)
        a=iid_cdf(x,lw,[470])[0];b=iid_cdf(x,lw+1234,[470])[0]
        self.assertAlmostEqual(a['estimate'],b['estimate'],places=13)
        self.assertAlmostEqual(a['mcse'],b['mcse'],places=13)
        self.assertAlmostEqual(weight_summary(lw+1234)['log_evidence']-weight_summary(lw)['log_evidence'],1234)

    def test_constant_is_not_zero_error_approval(self):
        r=iid_cdf(np.ones(100),np.zeros(100),[2])[0]
        self.assertLess(r['raw_delta_mcse'],1e-25);self.assertFalse(r['precision_pass']);self.assertEqual(r['mcse'],math.inf)

    def test_rare_dominant_weight(self):
        lw=np.r_[np.zeros(99),15.]
        self.assertFalse(weight_summary(lw)['single_deletion_guard_pass'])

    def test_replicate_influence_uses_denominator(self):
        x=np.array([[0,0,1,1],[0,1,1,1.]]);lw=np.array([[0,0,0,0],[2,2,2,2.]])
        r=replicated_cdf(x,lw,[.5])[0]
        z=np.exp(lw).mean(axis=1);fr=np.array([.5,.25]);f=np.sum(z*fr)/z.sum()
        expected=np.std(z/z.mean()*(fr-f),ddof=1)/np.sqrt(2)
        self.assertAlmostEqual(r['estimate'],f);self.assertAlmostEqual(r['between_replications_influence_mcse'],expected)

    def test_invalid_inputs(self):
        for lw in ([np.nan,0],[np.inf,0],[-np.inf,-np.inf],['0','1'],[True,False]):
            with self.assertRaises(ValueError):weight_summary(lw)
        with self.assertRaises(ValueError):iid_cdf([np.nan,1],[0,0],[0])
        with self.assertRaises(ValueError):weighted_quantiles([0,1],[0,0],[1])

    def test_underflow_preserved(self):
        r=weight_summary([0,-1000,-np.inf]);self.assertEqual(r['floating_point_weight_underflows'],1)
        self.assertEqual(r['exact_zero_target_weights'],1)

    def test_quantile_inverse_left(self):
        np.testing.assert_array_equal(weighted_quantiles([1,2,3],np.log([1,2,1]),[.25,.5,.75]),[1,2,2])

    def test_bonferroni_family(self):
        r=simultaneous_differences([.5,.5],[.001,.001],[.5,.6],[.001,.001])
        self.assertEqual(r['family_size'],2);self.assertEqual(r['consistent'].tolist(),[True,False])

if __name__=='__main__':unittest.main()
