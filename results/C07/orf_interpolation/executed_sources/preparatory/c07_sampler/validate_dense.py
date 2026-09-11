"""Independent direct-moment comparison of dense interpolation, no covariance bank."""
from harness import *
from cubic_even import EvenThresholdCubicORF
from pointwise import PointLikelihood
from linalg_batch import forward_substitution
from inference.orf_backend import ExactNodeORF
from inference.orf_table_builder import ConstructionBudget,build_checked_nodes,token,read_validated_entry
from time import perf_counter
import hashlib,gc

class DirectMoments(PointLikelihood):
    solve=staticmethod(forward_substitution)
    def __init__(self,e,data,table):
        self.e=e;self.data=data;self.table=table;self.n=len(data['q'])
        self.y=np.stack((data['x_physical'],data['x_gaussian']))
        self.z=np.einsum('gmkd,k->gmd',self.y,e['weights'])
    def moments(self,theta):
        pg,pr,pw=self.weights(theta);c=pg[:,:,None,None]*self.table(theta[:,0]);ii=np.arange(c.shape[-1]);e=self.e
        c[:,:,ii,ii]+=pr[:,:,None]*e['red']**2+pw[:,:,None]*e['sigma']**2
        hc=np.einsum('iab,nkbc->nkiac',e['H'],c,optimize=True)
        return np.einsum('nkiaa->nki',hc).real,np.einsum('nkiab,nkjba->nkij',hc,hc,optimize=True).real

def evaluate(like,theta,ids,batch=128):
    result=np.empty(len(theta))
    for begin in range(0,len(theta),batch):result[begin:begin+batch]=like(theta[begin:begin+batch],ids[begin:begin+batch])
    return result

def main():
    cfg,e,data=load();out=Path(__file__).resolve().parent/'results';start=perf_counter();bounds=np.array(cfg['prior']['bounds']);width=np.diff(bounds,axis=1)[:,0];n=len(data['q']);nt=5*n
    samples=np.load(out/'pilot553_refresh_draws.npy',mmap_mode='r');indices=np.linspace(0,len(samples)-1,257).astype(int);rng=np.random.default_rng(7078901)
    posterior=np.asarray(samples[indices]).reshape(-1,5);ids=np.tile(np.repeat(np.arange(nt),4),len(indices));posterior=bounds[:,0]+posterior*width
    priortheta=bounds[:,0]+rng.random((4096,5))*width;priorids=np.arange(4096)%nt
    fine=np.load(out/'table_beta8193.npz');coarse=np.load(out/'table_beta4097.npz');new=np.array([u for u in fine['nodes'] if u not in set(coarse['nodes'])]);sid=np.tile(np.arange(nt),len(new));di=rng.integers(0,len(samples),len(sid));ci=rng.integers(0,4,len(sid));stress=bounds[:,0]+np.asarray(samples[di,sid,ci])*width;stress[:,0]=np.repeat(new,nt)
    # Freeze independent node selection before examining interpolation errors.
    beta=np.unique(np.r_[rng.random(64),1-(np.arange(8)+.37)/8192,(np.arange(8)+.37)/8192]);offu=np.sort(np.sqrt((1-beta)*(1+beta)));dest=Path(__file__).resolve().parent/'orf_cache_validation';meta=ExactNodeORF(e,cfg['orf'],dest)
    (out/'dense_validation_protocol.json').write_text(json.dumps(dict(seed=7078901,loglikelihood_absolute_tolerance=.001,posterior_points=len(ids),prior_points=len(priorids),coarse_new_exact_nodes=len(new),stress_points=len(sid),independent_beta=beta.tolist(),notes='Numerical test domain, not a global analytic interpolation bound; exact means/covariances reconstructed independently without polynomial bank.'),indent=2))
    mf=build_checked_nodes(e,cfg['orf'],offu,dest,budget=ConstructionBudget(maximum_requested_nodes=100),validate_direct=True);(out/'dense_validation_construction.json').write_text(json.dumps(mf,indent=2))
    exact=[]
    for u in offu:
        g,_=read_validated_entry(dest/(token(meta.signature,u)+'.npz'),signature=meta.signature,u=u,K=4,P=12,tolerance=cfg['orf']['maximum_matrix_abs_difference']);exact.append(g)
    exact=np.array(exact);oid=np.tile(np.arange(nt),len(offu));di=rng.integers(0,len(samples),len(oid));ci=rng.integers(0,4,len(oid));oth=bounds[:,0]+np.asarray(samples[di,oid,ci])*width;oth[:,0]=np.repeat(offu,nt)
    # Lookup exact independently evaluated matrix for each mass, never interpolate it.
    exactlike=DirectMoments(e,data,lambda u:exact[np.searchsorted(offu,u)]);lexact=evaluate(exactlike,oth,oid)
    results={};arrays={}
    for label,file in [('4097',coarse),('8193',fine)]:
        table=EvenThresholdCubicORF(file['nodes'],file['matrices']);like=DirectMoments(e,data,table)
        values={key:evaluate(like,th,ix) for key,th,ix in [('posterior',posterior,ids),('prior',priortheta,priorids),('new_coarse_nodes',stress,sid),('offgrid',oth,oid)]}
        diff=values['offgrid']-lexact
        results[label]=dict(fallback_intervals=table.fallback.tolist(),minimum_Bernstein_eigenvalue=float(table.bernstein_minimum_eigenvalue.min()),maximum_offgrid_abs_loglikelihood_error=float(abs(diff).max()),offgrid_target_of_max=int(oid[np.argmax(abs(diff))]),offgrid_mass_of_max=float(oth[np.argmax(abs(diff)),0]))
        arrays[label]=values
        print(json.dumps(dict(table=label,**results[label])),flush=True)
        del table,like;gc.collect()
    comparisons={}
    for key,th,ix in [('posterior',posterior,ids),('prior',priortheta,priorids),('new_coarse_nodes',stress,sid),('offgrid',oth,oid)]:
        d=arrays['8193'][key]-arrays['4097'][key];comparisons[key]=dict(maximum_abs_loglikelihood_difference=float(abs(d).max()),target_of_max=int(ix[np.argmax(abs(d))]),mass_of_max=float(th[np.argmax(abs(d)),0]),q99_abs=float(np.quantile(abs(d),.99)),points=len(d))
    result=dict(tables=results,comparisons=comparisons,threshold=.001,seconds=perf_counter()-start,source_sha256={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [Path(__file__),Path(__file__).with_name('cubic_even.py'),Path(__file__).with_name('pointwise.py'),ROOT/'src/inference/orf_table_builder.py',ROOT/'src/inference/orf_blas.py']},table_sha256={str(out/x):hashlib.sha256((out/x).read_bytes()).hexdigest() for x in ['table_beta4097.npz','table_beta8193.npz']})
    result['passes_tested_domain']=all(v['maximum_abs_loglikelihood_difference']<=.001 for v in comparisons.values()) and results['8193']['maximum_offgrid_abs_loglikelihood_error']<=.001
    (out/'dense_validation.json').write_text(json.dumps(result,indent=2));np.savez_compressed(out/'dense_validation_arrays.npz',**{label+'_'+key:arr for label,vs in arrays.items() for key,arr in vs.items()},offgrid_exact=lexact)
    print(json.dumps(result,indent=2),flush=True)
if __name__=='__main__':main()
