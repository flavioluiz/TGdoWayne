from pathlib import Path
import sys,math,unittest
import numpy as np
ROOT=Path.cwd();sys.path[:0]=[str(ROOT/'src'),str(Path(__file__).resolve().parent)]
from inference import iid_diagnostics as ref
import iid_optimized as opt

def compare(a,b,path='',differences=None):
    if differences is None:differences=[]
    if isinstance(a,dict):
        if set(a)!=set(b):raise AssertionError((path,'keys',set(a)^set(b)))
        for k in a:compare(a[k],b[k],path+'/'+k,differences)
    elif isinstance(a,(list,tuple)):
        if len(a)!=len(b):raise AssertionError((path,'length'))
        for j,(x,y)in enumerate(zip(a,b)):compare(x,y,path+f'/{j}',differences)
    elif isinstance(a,np.ndarray):compare(a.tolist(),np.asarray(b).tolist(),path,differences)
    elif isinstance(a,(bool,np.bool_,int,np.integer,str)) or a is None:
        if a!=b:raise AssertionError((path,a,b))
    elif isinstance(a,(float,np.floating)):
        if a==b:return differences
        if not np.isfinite(a) or not np.isfinite(b) or abs(a-b)>1e-12:raise AssertionError((path,a,b,abs(a-b)))
        differences.append({'path':path,'reference':float(a),'optimized':float(b),'absolute_difference':float(abs(a-b))})
    else:raise TypeError((path,type(a)))
    return differences

class OptimizedTests(unittest.TestCase):
    def one(self,x,w,cuts):
        compare(ref.replicated_cdf(x,w,cuts),opt.TargetIIDContext(w).cdf(x,cuts))
        compare(ref.replicated_weights(w),opt.TargetIIDContext(w).weights())
    def test_iid_normal(self):
        r=np.random.default_rng(91021);self.one(r.normal(size=(4,4096)),r.normal(size=(4,4096)),[-3,-1,0,1,3])
    def test_ties_and_constants(self):
        r=np.random.default_rng(91022);x=r.integers(0,4,size=(4,512));w=r.normal(size=x.shape)
        self.one(x,w,[-1,0,1,2,3,4]);self.one(np.ones_like(x),w,[0,1,2])
    def test_zero_and_underflow_weights(self):
        r=np.random.default_rng(91023);w=r.normal(size=(4,512));w[:,1]=-np.inf;w[:,2]=-1000
        self.one(r.normal(size=w.shape),w,[-2,-.1,0,.1,2])
    def test_extreme_weights(self):
        r=np.random.default_rng(91024)
        for offset in (0.,1e4,1e6):
            w=r.uniform(-1000,0,size=(4,128))+offset
            self.one(r.normal(size=w.shape),w,[-20,-2,0,2,20])
    def test_small_and_subnormal(self):
        for small in (-10.,-350.,-380.,-700.,-744.,-1000.):
            self.one(np.array([[0.,1.]]*4),np.array([[small,0.]]*4),[-1,0,1,2])
    def test_quantile_exact(self):
        r=np.random.default_rng(91025);x=r.integers(0,20,size=(4,1000));w=r.normal(size=x.shape);ctx=opt.TargetIIDContext(w)
        np.testing.assert_array_equal(ref.weighted_quantiles(x.ravel(),w.ravel(),[.05,.5,.9,.95]),ctx.quantiles(x,[.05,.5,.9,.95]))
    def test_context_ownership_and_returned_summary(self):
        w=np.zeros((4,20));ctx=opt.TargetIIDContext(w);a=ctx.weights();a['replications'][0]['n']=999;w[:]=100
        self.assertEqual(ctx.weights()['replications'][0]['n'],20);self.assertEqual(ctx.weights()['log_evidence'],0)
    def test_invalid_contract(self):
        for w in (np.zeros(20),np.zeros((1,20)),np.ones((4,20),bool),np.full((4,20),np.nan),np.full((4,20),-np.inf)):
            with self.assertRaises(ValueError):opt.TargetIIDContext(w)
        ctx=opt.TargetIIDContext(np.zeros((4,20)))
        with self.assertRaises(ValueError):ctx.cdf(np.zeros((4,19)),[0])
        with self.assertRaises(ValueError):ctx.cdf(np.zeros((4,20)),[np.nan])
        with self.assertRaises(ValueError):ctx.quantiles(np.zeros((4,20)),[1])
    def test_single_row_functions(self):
        r=np.random.default_rng(91026);x=r.normal(size=4096);w=r.normal(size=4096)
        compare(ref.iid_cdf(x,w,[-1,0,1]),opt.iid_cdf(x,w,[-1,0,1]));compare(ref.weight_summary(w),opt.weight_summary(w))
    def test_precision_threshold_roundoff_boundary(self):
        rng=np.random.default_rng(901)
        for j in range(10):
            x=rng.normal(size=(4,256));w=rng.normal(size=x.shape);cuts=[-1,0,1]
            for row in ref.replicated_cdf(x,w,cuts):
                goal=row['mcse']
                compare(ref.replicated_cdf(x,w,cuts,mcse_target=goal),
                        opt.replicated_cdf(x,w,cuts,mcse_target=goal))
    def test_bracket_decision_roundoff_boundary(self):
        from scipy.stats import norm
        rng=np.random.default_rng(91028);x=rng.uniform(size=(4,2048,5));w=rng.normal(size=(4,2048))
        p=np.array([.05,.5,.9,.95]);b=np.broadcast_to(np.stack((p-.0004,p+.0004),axis=-1),(5,4,2));zero=np.zeros_like(b)
        c=ref.replicated_cdf(x[:,:,0],w,b[0].ravel())[2]
        p[1]=c['estimate']-.002-norm.isf(.05/40)*c['mcse']
        compare(ref.compare_brackets(x,w,b,p,b,zero,zero),opt.compare_brackets(x,w,b,p,b,zero,zero))
    def test_reference_brackets(self):
        r=np.random.default_rng(91027);x=r.uniform(size=(4,2048,5));w=r.normal(size=(4,2048));p=np.array([.05,.5,.9,.95])
        b=np.broadcast_to(np.stack((p-.0004,p+.0004),axis=-1),(5,4,2));zeros=np.zeros_like(b)
        compare(ref.compare_brackets(x,w,b,p,b,zeros,zeros),opt.compare_brackets(x,w,b,p,b,zeros,zeros))

if __name__=='__main__':unittest.main()
