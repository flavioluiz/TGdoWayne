"""Native algebra against direct matrix formulas and guarded-memory contracts."""
from pathlib import Path
from types import SimpleNamespace
import copy,importlib.util,sys,unittest
from concurrent.futures import ThreadPoolExecutor
import numpy as np
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from inference.native_likelihood import NativeLikelihood
from pta.simulation import JULIAN_YEAR_SECONDS as YEAR,residual_power_spectrum

BOUNDS=np.array([[0,1],[-16,-14],[3,5.5],[-17,-14.5],[-np.log10(2),np.log10(2)]])

def fixture(seed=707950201):
    rng=np.random.default_rng(seed);P=3;K=3;D=3;nd=3
    def hermitian():
        a=rng.normal(size=(P,P))+1j*rng.normal(size=(P,P));return (a+a.conj().T)/np.sqrt(4*P)
    def spd():
        a=rng.normal(size=(P,P))+1j*rng.normal(size=(P,P));return a@a.conj().T/P+np.eye(P)
    bern=np.array([spd() for _ in range(2*4*K)]).reshape(2,4,K,P,P)
    coeff=np.stack([bern[:,0],3*(bern[:,1]-bern[:,0]),3*(bern[:,2]-2*bern[:,1]+bern[:,0]),bern[:,3]-3*bern[:,2]+3*bern[:,1]-bern[:,0]],axis=1)
    H=np.array([hermitian() for _ in range(D)]);red=np.full(P,.7);sigma=np.full(P,2e-7)
    exp=dict(f=np.arange(1,K+1)/(4.5*YEAR),scale=np.array([1e-6,2e-7,5e-8]),dt=14*86400.,
             points=np.zeros((P,3)),H=H,red=red,sigma=sigma,weights=np.arange(1,K+1,dtype=float)/6)
    q=(rng.normal(size=(nd,K,P))+1j*rng.normal(size=(nd,K,P)))/np.sqrt(2)
    yp=np.array([[[np.vdot(q[r,k],h@q[r,k]).real for h in H] for k in range(K)] for r in range(nd)])
    yg=rng.normal(size=(nd,K,D))+.2;y=np.stack([yp,yg]);z=np.einsum('gmkd,k->gmd',y,exp['weights'])
    means=np.empty((2,K,6,D));cov=np.empty((2,K,21,D,D))
    for segment in range(2):
        for k in range(K):
            C=[*coeff[segment,:,k],np.diag(red**2),np.diag(sigma**2)]
            for s in range(6):
                for a in range(D):means[segment,k,s,a]=np.trace(H[a]@C[s]).real
            pair=0
            for s in range(6):
                for t in range(s,6):
                    for a in range(D):
                        for b in range(D):
                            val=np.trace(H[a]@C[s]@H[b]@C[t])
                            if s!=t:val+=np.trace(H[a]@C[t]@H[b]@C[s])
                            cov[segment,k,pair,a,b]=val.real
                    pair+=1
    return SimpleNamespace(n=nd,e=exp,table=SimpleNamespace(nodes=np.array([0,.4,1.]),coeff=coeff,coordinate_name='beta'),
        data=dict(q=q,x_physical=yp,x_gaussian=yg),y=y,z=z,meanbank=means,covbank=cov)

def direct_formula(model,theta,targets):
    e=model.e;H=e['H'];K=len(e['f']);P=len(e['points']);D=len(H);out=[]
    for th,target in zip(theta,targets):
        u,g,gamma,r,t=th;segment=min(np.searchsorted(model.table.nodes,u,side='right')-1,1)
        x=-np.sqrt((1-u)*(1+u));grid=-np.sqrt((1-model.table.nodes)*(1+model.table.nodes))
        f=(x-grid[segment])/(grid[segment+1]-grid[segment]);c=model.table.coeff[segment]
        G=c[0]+f*(c[1]+f*(c[2]+f*c[3]))
        sg=residual_power_spectrum(e['f'],g,gamma)/e['scale'];sr=residual_power_spectrum(e['f'],r,4)/e['scale'];sw=10**(2*t)*2*e['dt']/e['scale']
        C=sg[:,None,None]*G+sr[:,None,None]*np.diag(e['red']**2)+sw[:,None,None]*np.diag(e['sigma']**2)
        typ,datum=divmod(int(target),model.n)
        if typ==0:
            ll=0.
            for k in range(K):
                sign,ld=np.linalg.slogdet(C[k]);assert abs(sign-1)<1e-10
                q=model.data['q'][datum,k];ll-=np.vdot(q,np.linalg.solve(C[k],q)).real+ld+P*np.log(np.pi)
        else:
            means=[];cov=[]
            for ck in C:
                hc=np.array([h@ck for h in H]);means.append(np.trace(hc,axis1=-2,axis2=-1).real)
                cov.append(np.einsum('iab,jba->ij',hc,hc).real)
            means=np.array(means);cov=np.array(cov);y=model.y[int(typ>=3),datum]
            if typ in [2,4]:
                means=np.sum(means*e['weights'][:,None],axis=0)[None]
                cov=np.sum(cov*e['weights'][:,None,None]**2,axis=0)[None]
                y=np.sum(y*e['weights'][:,None],axis=0)[None]
            ll=0.
            for mean,cv,obs in zip(means,cov,y):
                d=obs-mean;sign,ld=np.linalg.slogdet(cv);assert sign>0
                ll-=.5*(d@np.linalg.solve(cv,d)+ld+D*np.log(2*np.pi))
        out.append(ll)
    return np.array(out)

class NativeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec=importlib.util.spec_from_file_location('project_native_builder',ROOT/'scripts/build_native.py')
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        cls.library,cls.manifest=module.build()
    def setUp(self):
        self.model=fixture();self.native=NativeLikelihood(self.model,BOUNDS,self.library)
        rng=np.random.default_rng(707950202);self.theta=BOUNDS[:,0]+rng.random((150,5))*np.diff(BOUNDS,axis=1)[:,0]
        self.theta[:5,0]=[0,np.nextafter(0.,1.),.4,np.nextafter(1.,0.),1.];self.targets=np.arange(150)%(5*self.model.n)
    def test_against_direct_complex_matrix_formulas(self):
        np.testing.assert_allclose(self.native(self.theta,self.targets),direct_formula(self.model,self.theta,self.targets),rtol=1e-11,atol=1e-9)
    def test_constructor_rejects_invalid_banks_and_observations(self):
        edits=[lambda m:setattr(m,'meanbank',m.meanbank[...,:2]),lambda m:setattr(m,'covbank',m.covbank[:,:,:20]),
          lambda m:m.covbank.__setitem__((0,0,0,0,1),123.),lambda m:m.table.coeff.__setitem__((0,0,0,0,0),1+3j),
          lambda m:m.data.__setitem__('q',m.data['q'][:,:2]),lambda m:m.z.__setitem__((0,0,0),123.),
          lambda m:m.table.nodes.__setitem__(1,1.),lambda m:m.e['sigma'].__setitem__(0,0.),
          lambda m:m.e['f'].__setitem__(0,0.),lambda m:m.e['scale'].__setitem__(0,0.),lambda m:m.e.__setitem__('dt',-1),
          lambda m:setattr(m,'n',0)]
        for i,edit in enumerate(edits):
            with self.subTest(case=i):
                m=copy.deepcopy(self.model);edit(m)
                with self.assertRaises(ValueError):NativeLikelihood(m,BOUNDS,self.library)
    def test_batch_input_contract_and_safe_empty_or_unaligned_input(self):
        for theta,ids in [(self.theta.astype(str),self.targets),(self.theta.astype(complex),self.targets),
            (np.full_like(self.theta,np.nan),self.targets),(self.theta,self.targets+.1),
            (self.theta,np.full_like(self.targets,-1)),(self.theta,np.full(150,np.iinfo(np.uint64).max,dtype=np.uint64)),
            (self.theta+np.array([0,10,0,0,0]),self.targets)]:
            with self.assertRaises(ValueError):self.native(theta,ids)
        self.assertEqual(self.native(np.empty((0,5)),np.empty(0,dtype=int)).shape,(0,))
        raw=bytearray(self.theta.nbytes+1);unaligned=np.ndarray(self.theta.shape,dtype=float,buffer=raw,offset=1);unaligned[:]=self.theta
        np.testing.assert_array_equal(self.native(unaligned,self.targets),self.native(self.theta,self.targets))
    def test_owned_state_survives_source_mutation(self):
        before=self.native(self.theta,self.targets);m=self.model
        m.table.coeff*=2;m.table.nodes[1]=.9;m.meanbank+=1;m.covbank*=2;m.e['f']*=2;m.e['scale']*=3;m.e['dt']*=7
        m.data['q']*=1j;m.y+=1;m.z*=-1
        np.testing.assert_array_equal(before,self.native(self.theta,self.targets))
        with self.assertRaises(ValueError):self.native.gamma[0,0,0,0,0]=0
    def test_nonpositive_covariance_raises_without_jitter(self):
        m=copy.deepcopy(self.model);m.covbank*=-1;native=NativeLikelihood(m,BOUNDS,self.library)
        with self.assertRaises(np.linalg.LinAlgError):native(self.theta[:1],np.array([m.n]))
    def test_threaded_evaluation_and_call_buffers(self):
        expected=self.native(self.theta,self.targets)
        with ThreadPoolExecutor(max_workers=4) as pool:
            parts=list(pool.map(lambda i:self.native(self.theta[i:i+10],self.targets[i:i+10]),range(0,150,10)))
        np.testing.assert_array_equal(np.concatenate(parts),expected)
        function=self.native.function;observed=[]
        def inspect(*args):
            observed.append(np.shares_memory(args[8],self.targets));return function(*args)
        self.native.function=inspect;self.native(self.theta,self.targets);self.assertEqual(observed,[False])

if __name__=='__main__':unittest.main()
