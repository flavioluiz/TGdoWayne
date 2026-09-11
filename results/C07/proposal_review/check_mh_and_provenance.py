from pathlib import Path
from unittest.mock import patch
import hashlib,json,sys
import numpy as np
from scipy.special import expit,logit,betaln
ROOT=Path.cwd();HERE=Path(__file__).resolve().parent;S=ROOT/'tmp/c07_sampler';sys.path[:0]=[str(S),str(ROOT/'src')]
from mixture_proposal import GaussianDefensiveProposal
from mh_mixture import FrozenMixtureMH

def prior_jac(z):return (-np.logaddexp(0,-z)-np.logaddexp(0,z)).sum(axis=-1)
def target(z,ids):
    logs=-np.logaddexp(0,-z);log1s=-np.logaddexp(0,z)
    ll=(4*(logs+log1s)-betaln(5,5)).sum(axis=-1)
    return ll+prior_jac(z),ll

def mh_check():
    q=GaussianDefensiveProposal(np.array([[.3,.7]]),np.array([[np.zeros(5),np.ones(5)*.3]]),np.array([[np.eye(5),np.eye(5)*1.7]]),np.zeros((1,5)),np.eye(5)[None])
    proposal=np.full((4,5),2.);noise=np.ones((4,5))*1.5;move=np.array([.05,.25,.5,.95]);unit=np.full(4,.9);coordinate=np.full(4,.6)
    current=np.zeros((4,5));candidate=current+noise
    candidate[0]=current[0];candidate[0,0]=logit(.9)
    candidate[1]=current[1];candidate[1,3]=logit(.9)
    candidate[2]=proposal[2]
    lp,ll=target(current,np.zeros(4,int));plp,pll=target(candidate,np.zeros(4,int))
    delta=plp-lp
    # Independently add reverse/forward log proposal densities in z space.
    for i,axis in [(0,0),(1,3)]:
        jac_current=-np.logaddexp(0,-current[i,axis])-np.logaddexp(0,current[i,axis])
        jac_proposed=-np.logaddexp(0,-candidate[i,axis])-np.logaddexp(0,candidate[i,axis])
        delta[i]+=jac_current-jac_proposed
    delta[2]+=q.logpdf(current)[2]-q.logpdf(candidate)[2]
    assert np.all(delta<-.1)
    checks=[]
    for accepted in [np.array([True,False,True,False]),np.array([False,True,False,True])]:
        sampler=FrozenMixtureMH(target,[0],q,np.eye(5)[None],np.zeros(1),seed=907102001)
        sampler.z=current.copy();sampler.lp=lp.copy();sampler.ll=ll.copy()
        # Exactly below/above each independent Hastings threshold.
        uniforms=np.exp(delta+np.where(accepted,-.01,.01))
        stream=[move,noise,unit,coordinate,unit,uniforms]
        with patch.object(sampler,'rand',side_effect=stream),patch.object(q,'sample',return_value=proposal.copy()):
            sampler.step()
        expected=np.where(accepted[:,None],candidate,current)
        np.testing.assert_allclose(sampler.z,expected,atol=1e-14,rtol=0)
        checks.append({'expected_acceptance':accepted.tolist(),'actual_acceptance':np.any(sampler.z!=current,axis=1).tolist()})
    return {'moves':['mass_prior','nuisance_prior','mixture_independent','symmetric_random_walk'],'full_hastings_logratios':delta.tolist(),'checks':checks,'jacobian_included':True}

def streamed_sha(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
    return h.hexdigest()

def provenance():
    training=json.loads((S/'results/mixture_training.json').read_text());old=json.loads((S/'results/pilot553_refresh.json').read_text());new=json.loads((S/'results/pilot553_mixture.json').read_text())
    source=S/'results/pilot553_refresh_draws.npy';digest=streamed_sha(source);assert digest==training['training_source_sha256']
    assert hashlib.sha256((S/'results/mixture_training.json').read_bytes()).hexdigest()==new['proposal_training_sha256']
    assert training['targets']==new['targets']
    assert old['targets']==list(range(80))
    checks=[]
    for row in training['records']:
        k=row['target'];assert row['global_mean']==old['mean'][k];assert row['global_cholesky']==old['cholesky'][k];assert row['random_walk_logscale']==old['logscale'][k]
        checks.append(k)
    x=np.load(source,mmap_mode='r');indices=np.linspace(0,len(x)-1,512).astype(int)
    assert len(np.unique(indices))==512 and x.shape==(32768,80,4,5)
    sample=np.stack([np.asarray(x[indices,k]).reshape(-1,5) for k in training['targets']])
    assert sample.shape==(16,2048,5) and np.all((sample>0)&(sample<1))
    # This freezes what inspection established; flags alone are not evidence.
    return {'training_source_sha256_matches':True,'training_array_shape':list(x.shape),'selected_training_shape':list(sample.shape),
            'selected_training_points_sha256':hashlib.sha256(sample.tobytes()).hexdigest(),'global_parameters_exactly_match_previous_metadata':checks,
            'old_seed':old['seed'],'new_MH_seed':new['seed'],'new_production_adaptation':new['production_adaptation'],
            'fit_implementation_inspection':'fit_mixture.py reads only old pilot draws and old MH metadata; fit_proposal accepts only unit_points/log_weights and settings. No truth or new-production array is passed. run_mixture.py uses truth only after sampling, in diagnostics.',
            'provenance_limit':'Training JSON originally hashes old draws but omits old metadata and fit-source hashes. This audit preserves those current bytes separately; it does not retroactively claim those hashes were recorded before the old run.'}
if __name__=='__main__':
    out={'status':'PASS','MH':mh_check(),'provenance':provenance(),'audit_source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    (HERE/'mh_provenance_audit.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
