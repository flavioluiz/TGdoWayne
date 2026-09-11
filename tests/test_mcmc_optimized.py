import sys,unittest
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from inference import mcmc_diagnostics as reference
from inference import mcmc_optimized as optimized


def compare_nested(a,b,path=''):
    if isinstance(a,dict):
        if a.keys()!=b.keys():raise AssertionError(path+' keys')
        for key in a:compare_nested(a[key],b[key],path+'/'+str(key))
    elif isinstance(a,list):
        if len(a)!=len(b):raise AssertionError(path+' length')
        for j,(first,second)in enumerate(zip(a,b)):compare_nested(first,second,path+'/'+str(j))
    elif isinstance(a,(bool,str,int))or a is None:
        if a!=b:raise AssertionError((path,a,b))
    elif a!=b:
        if not(np.isfinite(a)and np.isfinite(b)and abs(a-b)<=1e-12):raise AssertionError((path,a,b))


class OptimizedTests(unittest.TestCase):
    def check(self,x,truth,ll=None,lt=None):
        compare_nested(reference.target_diagnostics(x,truth,loglikelihood=ll,loglikelihood_truth=lt),
                       optimized.target_diagnostics(x,truth,loglikelihood=ll,loglikelihood_truth=lt))

    def test_even_odd_and_ties(self):
        rng=np.random.default_rng(71101)
        for n in [8,9,32,33,511,512]:
            x=np.round(rng.uniform(size=(n,4,5)),2)
            ll=-np.sum(x*x,axis=2)
            self.check(x,np.array([0.,.05,.5,.95,1.]),ll,-1.)

    def test_constant_and_different_constant_chains(self):
        self.check(np.ones((128,4,5))*.4,np.ones(5)*.5,np.ones((128,4)),1.)
        x=np.broadcast_to(np.array([.1,.2,.8,.9])[None,:,None],(128,4,5)).copy()
        self.check(x,np.ones(5)*.5)

    def test_folded_scale_difference_preserved(self):
        x=np.random.default_rng(71102).uniform(size=(1024,4,5))
        x[:,0]=.5+.01*(x[:,0]-.5)
        self.check(x,np.full(5,.5))
        result=optimized.target_diagnostics(x,np.full(5,.5))
        self.assertGreater(result['convergence']['parameter_0']['rhat']['folded_rank_split'],1.1)

    def test_sorted_quantiles_match_numpy(self):
        rng=np.random.default_rng(71103)
        for n in [8,9,128,1024]:
            x=np.round(rng.normal(size=n),2)
            probs=np.r_[0.,1.,.05,.5,.9,.95,rng.uniform(size=20)]
            np.testing.assert_array_equal(optimized._quantiles_sorted(np.sort(x),probs),np.quantile(x,probs))

    def test_rank_scores_match_scipy(self):
        rng=np.random.default_rng(71104)
        x=np.round(rng.normal(size=(1024,4)),2)
        z,ordered=optimized._scores_and_sorted(x)
        np.testing.assert_array_equal(z,reference.rank_normalize(x))
        np.testing.assert_array_equal(ordered,np.sort(x.ravel()))

    def test_invalid_input_contract(self):
        x=np.ones((32,4,5))*.5
        for bad in [np.full_like(x,np.nan),np.ones((32,3,5)),x+1]:
            with self.assertRaises(ValueError):optimized.target_diagnostics(bad,np.ones(5)*.5)
        with self.assertRaises(ValueError):optimized.target_diagnostics(x,np.ones(5)*.5,loglikelihood=np.ones((32,4)))


if __name__=='__main__':unittest.main()
