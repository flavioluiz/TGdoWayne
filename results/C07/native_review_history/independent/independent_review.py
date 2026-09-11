"""Independent matrix-formula checks of the frozen native prototype.

No source from the implementation under review is edited. Invalid raw offsets,
null pointers, undersized arrays and nd=0 are not executed: those would invoke UB.
"""
from pathlib import Path
from types import SimpleNamespace
import copy,hashlib,importlib.util,json,sys,time
import numpy as np
ROOT=Path.cwd();HERE=Path(__file__).resolve().parent
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'tmp/c07_sampler')]
spec=importlib.util.spec_from_file_location('frozen_full',HERE/'sources/full_benchmark.py')
native_module=importlib.util.module_from_spec(spec);spec.loader.exec_module(native_module)
Native=native_module.NativePrototype

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def hermitian(rng,p):
    a=rng.normal(size=(p,p))+1j*rng.normal(size=(p,p))
    return (a+a.conj().T)/np.sqrt(4*p)
def spd(rng,p):
    a=rng.normal(size=(p,p))+1j*rng.normal(size=(p,p))
    return a@a.conj().T/p+np.eye(p)

def banks(coeff,H,red,white):
    ns,_,K,P,_=coeff.shape;D=len(H);mu=np.empty((ns,K,6,D));cov=np.empty((ns,K,21,D,D))
    for segment in range(ns):
        for k in range(K):
            components=[*coeff[segment,:,k],np.diag(red**2),np.diag(white**2)]
            hc=[[h@c for h in H]for c in components]
            for s in range(6):
                for a in range(D):mu[segment,k,s,a]=np.trace(hc[s][a]).real
            pair=0
            for s in range(6):
                for t in range(s,6):
                    for a in range(D):
                        for b in range(D):
                            value=np.trace(hc[s][a]@hc[t][b])
                            if s!=t:value+=np.trace(hc[t][a]@hc[s][b])
                            cov[segment,k,pair,a,b]=value.real
                    pair+=1
    return mu,cov

class Fixture:
    def __init__(self,rng,P,K,D,nd=3):
        nodes=np.array([0.,.4,1.]);bern=np.array([[spd(rng,P)for k in range(K)]for j in range(4*(len(nodes)-1))]).reshape(len(nodes)-1,4,K,P,P)
        coeff=np.empty_like(bern)
        coeff[:,0]=bern[:,0];coeff[:,1]=3*(bern[:,1]-bern[:,0]);coeff[:,2]=3*(bern[:,2]-2*bern[:,1]+bern[:,0]);coeff[:,3]=bern[:,3]-3*bern[:,2]+3*bern[:,1]-bern[:,0]
        H=np.array([hermitian(rng,P)for j in range(D)])
        self.n=nd;self.e={'f':np.arange(1,K+1.),'points':np.zeros((P,3)),'H':H,'red':np.full(P,.7),'sigma':np.full(P,.3),'weights':np.arange(1,K+1,dtype=float)}
        self.e['weights']/=sum(self.e['weights'])
        self.table=SimpleNamespace(coeff=coeff,nodes=nodes,location=self.location)
        q=(rng.normal(size=(nd,K,P))+1j*rng.normal(size=(nd,K,P)))/np.sqrt(2)
        xp=np.array([[[np.vdot(q[r,k],h@q[r,k]).real for h in H]for k in range(K)]for r in range(nd)])
        xg=rng.normal(size=(nd,K,D))+.2
        self.data={'q':q,'x_physical':xp,'x_gaussian':xg};self.y=np.stack([xp,xg]);self.z=np.einsum('gmkd,k->gmd',self.y,self.e['weights'])
        self.rebuild()
    def location(self,u):
        u=np.asarray(u)
        if np.any(~np.isfinite(u)) or np.any((u<0)|(u>1)):raise ValueError('mass outside fixture')
        j=np.clip(np.searchsorted(self.table.nodes,u,side='right')-1,0,1)
        return j,(u-self.table.nodes[j])/(self.table.nodes[j+1]-self.table.nodes[j])
    def weights(self,theta):
        k=self.e['f'][None,:]
        return (np.exp(theta[:,1,None]-.2*theta[:,2,None]*k),
                np.exp(.3*theta[:,3,None])/(1+k),
                np.broadcast_to(np.exp(.2*theta[:,4,None]),(len(theta),len(self.e['f']))))
    def rebuild(self):
        self.meanbank,self.covbank=banks(self.table.coeff,self.e['H'],self.e['red'],self.e['sigma'])

def direct_numpy(model,theta,targets):
    """No polynomial moment banks: form C, then matrix products and solve C."""
    pg,pr,pw=model.weights(theta);seg,f=model.table.location(theta[:,0]);e=model.e;H=e['H'];K=len(e['f']);P=len(e['points']);D=len(H);answer=[]
    for i,target in enumerate(targets):
        typ,datum=divmod(int(target),model.n);c0=model.table.coeff[seg[i]]
        gamma=c0[0]+f[i]*(c0[1]+f[i]*(c0[2]+f[i]*c0[3]))
        C=pg[i,:,None,None]*gamma+pr[i,:,None,None]*np.diag(e['red']**2)+pw[i,:,None,None]*np.diag(e['sigma']**2)
        if typ==0:
            value=0.
            for k in range(K):
                sign,ld=np.linalg.slogdet(C[k]);assert abs(sign-1)<1e-10
                q=model.data['q'][datum,k];value-=np.vdot(q,np.linalg.solve(C[k],q)).real+ld+P*np.log(np.pi)
        else:
            mean=[];cov=[]
            for ck in C:
                hc=np.array([h@ck for h in H]);mean.append(np.trace(hc,axis1=-2,axis2=-1).real)
                cov.append(np.einsum('iab,jba->ij',hc,hc).real)
            mean=np.array(mean);cov=np.array(cov);kind=int(typ>=3)
            if typ in (2,4):
                mean=np.sum(mean*e['weights'][:,None],axis=0)[None]
                cov=np.sum(cov*e['weights'][:,None,None]**2,axis=0)[None]
                y=np.sum(model.y[kind,datum]*e['weights'][:,None],axis=0)[None]
            else:y=model.y[kind,datum]
            value=0.
            for m,c,obs in zip(mean,cov,y):
                residual=obs-m;sign,ld=np.linalg.slogdet(c);assert sign>0
                value-=.5*(residual@np.linalg.solve(c,residual)+ld+D*np.log(2*np.pi))
        answer.append(value)
    return np.asarray(answer)

def compare(label,model,theta,targets,absolute,relative):
    native=Native(model);a=native(theta,targets);b=direct_numpy(model,theta,targets);diff=abs(a-b)
    return {'name':label,'N':len(a),'maximum_abs_logL':float(diff.max(initial=0)),
        'maximum_scaled_difference':float(np.max(diff/(1+abs(b)),initial=0)),
        'pass':bool(np.all(diff<=absolute+relative*abs(b))),
        'tolerances':{'absolute':absolute,'relative':relative},
        'targets_covered':np.unique(targets).tolist()},a

def raw_call(native,theta,targets,**changes):
    seg,f=native.table.location(theta[:,0]);pg,pr,pw=native.model.weights(theta);out=np.full(len(theta),123.)
    arrays=dict(seg=np.ascontiguousarray(seg,dtype=np.int64),frac=np.ascontiguousarray(f),targets=np.ascontiguousarray(targets,dtype=np.int64),
        pg=np.ascontiguousarray(pg),pr=np.ascontiguousarray(pr),pw=np.ascontiguousarray(pw),means=native.means,
        covpacked=native.packed,gamma=native.gamma,red2=native.red2,white2=native.white2,freqweights=native.weights,
        q=native.q,y=native.y,z=native.z,result=out)
    dims=dict(n=len(theta),nd=native.n,K=native.K,P=native.P,D=native.D)
    for key,value in changes.items():
        if key in dims:dims[key]=value
        else:arrays[key]=value
    code=native_module.lib.full_likelihood(*dims.values(),*arrays.values())
    return int(code),out

def main():
    cfg=json.loads((HERE/'review_config.json').read_text());rng=np.random.default_rng(cfg['seed']);start=time.perf_counter();results=[]
    for P,K,D in cfg['random_fixtures']:
        model=Fixture(rng,P,K,D,nd=3 if P==3 else 7)
        theta=rng.normal(scale=.4,size=(cfg['toy_rows_each'],5));theta[:,0]=rng.random(len(theta));theta[:4,0]=[0,.4,np.nextafter(1.,0.),1.]
        targets=np.arange(len(theta))%(5*model.n);rng.shuffle(targets)
        row,a=compare(f'complex_SPD_P{P}_K{K}_D{D}',model,theta,targets,cfg['toy_absolute_tolerance'],cfg['relative_tolerance']);results.append(row)
        if P==3:
            base=model;unitary,_=np.linalg.qr(rng.normal(size=(P,P))+1j*rng.normal(size=(P,P)))
            rotated=copy.deepcopy(model);rotated.table.location=rotated.location
            rotated.table.coeff=unitary@model.table.coeff@unitary.conj().T
            rotated.e['H']=unitary@model.e['H']@unitary.conj().T
            rotated.data['q']=np.einsum('ab,rkb->rka',unitary,model.data['q']);rotated.rebuild()
            row,b=compare('unitary_rotated_inputs',rotated,theta,targets,cfg['toy_absolute_tolerance'],cfg['relative_tolerance']);results.append(row)
            results.append({'name':'unitary_invariance','maximum_abs_difference':float(np.max(abs(a-b))),'pass':bool(np.allclose(a,b,rtol=1e-11,atol=1e-9))})
    native=Native(base);theta=np.zeros((1,5));theta[:,0]=.2;checks=[]
    def expect_exception(label,x,ids,exception):
        try:native(x,ids)
        except exception as e:checks.append({'name':label,'pass':True,'exception':type(e).__name__});return
        except Exception as e:checks.append({'name':label,'pass':False,'exception':type(e).__name__});return
        checks.append({'name':label,'pass':False,'exception':None})
    expect_exception('nonfinite_theta',np.full((1,5),np.nan),np.array([0]),ValueError)
    expect_exception('negative_target',theta,np.array([-1]),ValueError)
    expect_exception('too_large_target',theta,np.array([5*base.n]),ValueError)
    expect_exception('noninteger_target',theta,np.array([.5]),ValueError)
    expect_exception('boolean_target',theta,np.array([True]),ValueError)
    expect_exception('out_of_range_mass',np.array([[1.1,0,0,0,0]]),np.array([0]),ValueError)
    # Controlled non-SPD inputs; all buffers remain correctly sized.
    for name,changes,target in [
        ('negative_CN_diagonal',{'gamma':np.zeros_like(native.gamma),'red2':-np.ones_like(native.red2),'white2':np.zeros_like(native.white2)},0),
        ('negative_normal_covariance',{'covpacked':-np.abs(native.packed)},base.n),
        ('NaN_normal_covariance',{'covpacked':np.full_like(native.packed,np.nan)},base.n)]:
        code,out=raw_call(native,theta,np.array([target]),**changes)
        checks.append({'name':name,'code':code,'pass':code==1,'output_not_consumed':True})
    # Demonstrate missing contract checks without unsafe offsets/pointers.
    vulnerabilities=[]
    for name,change,target in [('zero_K',{'K':0},0),('zero_P',{'P':0},0),('zero_D',{'D':0},base.n),('model_index_5',{},5*base.n)]:
        code,out=raw_call(native,theta,np.array([target]),**change)
        vulnerabilities.append({'name':name,'raw_code':code,'finite_output':bool(np.isfinite(out).all()),'value':out.tolist(),'expected_public_behavior':'reject before native call'})
    bad=native.gamma.copy();bad[...,np.arange(native.P),np.arange(native.P)]+=2j
    code,out=raw_call(native,theta,np.array([0]),gamma=bad)
    vulnerabilities.append({'name':'complex_diagonal_ignored','raw_code':code,'finite_output':bool(np.isfinite(out).all()),'expected_public_behavior':'reject non-Hermitian table before native call'})
    codes={}
    for key,value in [('P',17),('D',17),('K',9)]:codes[key]=raw_call(native,theta,np.array([0]),**{key:value})[0]
    checks.append({'name':'over_capacity_dimensions','codes':codes,'pass':all(x==-1 for x in codes.values())})
    # Public wrapper presently coerces numerical strings and booleans for theta.
    for name,value in [('theta_numeric_strings',theta.astype(str)),('theta_bool',theta.astype(bool))]:
        try:out=native(value,np.array([0]));accepted=bool(np.isfinite(out).all())
        except Exception:accepted=False
        vulnerabilities.append({'name':name,'currently_accepted':accepted,'expected_strict_contract':'reject before float conversion'})
    result={'label':'INDEPENDENT_CPP_PROTOTYPE_REVIEW_NOT_PUBLIC_WRAPPER_APPROVAL','configuration':cfg,
        'random_matrix_checks':results,'negative_and_input_checks':checks,'contract_findings':vulnerabilities,
        'all_valid_math_checks_pass':all(a['pass']for a in results),'all_expected_error_checks_pass':all(a['pass']for a in checks),
        'seconds':time.perf_counter()-start,'no_unsafe_memory_tests_executed':True,
        'source_hashes':{str(p):sha(p)for p in [Path(__file__),HERE/'review_config.json',HERE/'sources/full.cpp',HERE/'sources/full_benchmark.py',HERE/'sources/full.dylib']}}
    (HERE/'results/independent_fixtures.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    print(json.dumps(result,indent=2))

if __name__=='__main__':main()
