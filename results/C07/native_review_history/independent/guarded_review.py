"""Guarded wrapper review with independent small matrices and mutation probes."""
from pathlib import Path
import argparse,copy,importlib.util,json,sys,types
import numpy as np
HERE=Path(__file__).resolve().parent;ROOT=Path.cwd();sys.path.insert(0,str(HERE))
from independent_review import Fixture,direct_numpy,sha
from pointwise import PointLikelihood
from inference.model import YEAR

class PhysicalFixture(Fixture):
    def __init__(self,rng):
        super().__init__(rng,3,3,3)
        self.e.update(f=np.arange(1,4)/(4.5*YEAR),scale=np.array([1e-6,2e-7,5e-8]),dt=14*86400.)
        self.e['sigma'][:]=2e-7;self.table.coordinate_name='beta';self.rebuild()
        self.weights=types.MethodType(PointLikelihood.weights,self)
    def location(self,u):
        u=np.asarray(u)
        if np.any(~np.isfinite(u)) or np.any((u<0)|(u>1)):raise ValueError('mass outside fixture')
        j=np.clip(np.searchsorted(self.table.nodes,u,side='right')-1,0,1)
        coords=-np.sqrt((1-self.table.nodes)*(1+self.table.nodes));c=-np.sqrt((1-u)*(1+u))
        return j,(c-coords[j])/(coords[j+1]-coords[j])

def main():
    p=argparse.ArgumentParser();p.add_argument('--module',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    args=p.parse_args()
    if args.output.exists():raise FileExistsError('Preserve existing review')
    spec=importlib.util.spec_from_file_location('guarded_to_review',args.module);mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    cls=mod.NativeLikelihood;library=HERE/'sources/full_guarded.dylib';rng=np.random.default_rng(707950103)
    model=PhysicalFixture(rng);bounds=np.array([[0,1],[-16,-14],[3,5.5],[-17,-14.5],[-.3010299956639812,.3010299956639812]])
    theta=bounds[:,0]+rng.random((150,5))*np.diff(bounds,axis=1)[:,0];theta[:5,0]=[0,np.nextafter(0.,1.),.4,np.nextafter(1.,0.),1.]
    targets=np.arange(150)%(5*model.n);guard=cls(model,bounds,library);before=guard(theta,targets);reference=direct_numpy(model,theta,targets)
    checks=[{'name':'guarded_beta_fixture_matches_direct_matrices','pass':bool(np.allclose(before,reference,rtol=1e-11,atol=1e-9)),'maximum_abs_difference':float(np.max(abs(before-reference)))}]
    def expect(name,fun,exception=ValueError):
        try:fun()
        except exception as err:checks.append({'name':name,'pass':True,'exception':type(err).__name__});return
        except Exception as err:checks.append({'name':name,'pass':False,'exception':type(err).__name__});return
        checks.append({'name':name,'pass':False,'exception':None})
    def ctor(name,edit):
        m=copy.deepcopy(model);m.table.location=m.location;edit(m);expect(name,lambda:cls(m,bounds,library))
    ctor('truncated_meanbank',lambda m:setattr(m,'meanbank',m.meanbank[...,:2]))
    ctor('truncated_covbank',lambda m:setattr(m,'covbank',m.covbank[:,:,:20]))
    ctor('nonfinite_covbank',lambda m:m.covbank.__setitem__((0,0,0,0,0),np.nan))
    ctor('nonsymmetric_covbank',lambda m:m.covbank.__setitem__((0,0,0,0,1),123.))
    ctor('complex_diagonal',lambda m:m.table.coeff.__setitem__((0,0,0,0,0),1+3j))
    ctor('nonhermitian_gamma',lambda m:m.table.coeff.__setitem__((0,0,0,0,1),123+4j))
    ctor('wrong_q_shape',lambda m:m.data.__setitem__('q',m.data['q'][:,:2]))
    ctor('wrong_y_shape',lambda m:setattr(m,'y',m.y[:,:,:,:2]))
    ctor('inconsistent_compression',lambda m:m.z.__setitem__((0,0,0),123.))
    ctor('nonmonotone_nodes',lambda m:m.table.nodes.__setitem__(1,1.))
    ctor('unsupported_coordinate',lambda m:setattr(m.table,'coordinate_name','alpha'))
    ctor('zero_white_pattern',lambda m:m.e['sigma'].__setitem__(0,0.))
    ctor('zero_frequency',lambda m:m.e['f'].__setitem__(0,0.))
    ctor('zero_scale',lambda m:m.e['scale'].__setitem__(0,0.))
    ctor('negative_dt',lambda m:m.e.__setitem__('dt',-1.))
    ctor('zero_dataset_count',lambda m:setattr(m,'n',0))
    for name,t,ids in [
        ('theta_strings',theta.astype(str),targets),('theta_bool',theta.astype(bool),targets),
        ('theta_complex',theta.astype(complex),targets),('theta_nan',np.full_like(theta,np.nan),targets),
        ('theta_shape',theta[:,:4],targets),('target_float',theta,targets+.1),
        ('target_bool',theta,targets.astype(bool)),('target_negative',theta,np.full_like(targets,-1)),
        ('target_too_large',theta,np.full_like(targets,5*model.n)),('target_uint_overflow',theta,np.full(len(theta),np.iinfo(np.uint64).max,dtype=np.uint64)),
        ('outside_prior',theta+np.array([0,10,0,0,0]),targets)]:
        expect(name,lambda t=t,ids=ids:guard(t,ids))
    checks.append({'name':'empty_batch_supported','pass':guard(np.empty((0,5)),np.empty(0,dtype=np.int64)).shape==(0,)})
    invalid=copy.deepcopy(model);invalid.table.location=invalid.location;invalid.covbank*=-1
    bad=cls(invalid,bounds,library)
    expect('nonSPD_moment_covariance_raises_without_jitter',lambda:bad(theta[:1],np.array([model.n])),np.linalg.LinAlgError)
    # Constructor isolation and alignment are checked before modifying source.
    owned_names=['bounds','nodes','coordinate','gamma','means','covpacked','red2','white2','frequency_weights','q','y','z','frequencies','scale']
    checks.append({'name':'static_buffers_owned_aligned_contiguous_readonly','pass':all(getattr(guard,k).flags.owndata and getattr(guard,k).flags.aligned and getattr(guard,k).flags.c_contiguous and not getattr(guard,k).flags.writeable for k in owned_names)})
    expect('static_buffer_write_raises',lambda:guard.gamma.__setitem__((0,0,0,0,0),0.))
    # Unaligned caller input must be safely copied, with unchanged values.
    raw=bytearray(theta.nbytes+1);unaligned=np.ndarray(theta.shape,dtype=np.float64,buffer=raw,offset=1);unaligned[:]=theta
    checks.append({'name':'unaligned_theta_copied_safely','input_aligned':bool(unaligned.flags.aligned),'pass':np.array_equal(guard(unaligned,targets),before)})
    model.e['f']*=2;model.e['scale']*=3;model.e['dt']*=7;model.e['red']*=5;model.e['sigma']*=11
    model.e['weights'][:]=0;model.table.nodes[1]=.9;model.table.coeff*=2;model.meanbank+=.25;model.covbank*=2
    model.data['q']*=1j;model.y+=1.3;model.z*=-1;bounds[:,0]-=1
    checks.append({'name':'source_model_and_bounds_mutation_has_no_effect','pass':np.array_equal(guard(theta,targets),before)})
    # Observe per-call ownership without introducing a concurrent mutation race.
    call_ownership={};real_function=guard.function
    def observe(*a):
        call_ownership['targets_share_caller_memory']=bool(np.shares_memory(a[8],targets))
        return real_function(*a)
    guard.function=observe;guard(theta,targets);guard.function=real_function
    result={'label':'GUARDED_CPP_CANDIDATE_INDEPENDENT_REVIEW','module':str(args.module),
        'checks':checks,'all_checks_pass':all(x['pass']for x in checks),'check_count':len(checks),
        'per_call_ownership':call_ownership,'source_mutation_test_is_separate_from_concurrent_input_mutation':True,
        'source_hashes':{str(path):sha(path)for path in [Path(__file__),HERE/'independent_review.py',args.module,library,HERE/'sources/full_guarded.cpp']}}
    args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    print(json.dumps(result,indent=2))

if __name__=='__main__':main()
