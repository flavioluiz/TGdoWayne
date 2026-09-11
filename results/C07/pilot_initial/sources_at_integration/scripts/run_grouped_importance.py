"""Data-adapted grouped deterministic-mixture RQMC, with complete Sobol strata.

Training uses normalized posterior weights only. All target priors/data remain fixed.
"""
from pathlib import Path
import argparse,json,sys
import numpy as np
from scipy.special import logit,expit,ndtri,logsumexp
from scipy.stats import qmc
from inference_pilot import experiment,ExactNodeORF,integrate_level,sha256
from likelihood_fast import FastLikelihood

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT.parent/'c07_efficiency'))
from proposal import fit_proposal,DefensiveLogitMixture


def balanced_sampler(proposal):
    k=len(proposal.component_weights)
    def sample(power,seed_sequence):
        # Every stratum is a complete independent Sobol net, no skipping/thinning.
        n=2**power;children=seed_sequence.spawn(k+1);points=[]
        for j,child in enumerate(children):
            u=qmc.Sobol(4,scramble=True,seed=np.random.default_rng(child)).random_base2(power)
            if np.any(u<=0) or np.any(u>=1):raise FloatingPointError('Transform boundary hit; do not silently clip or resample.')
            if j:u=expit(ndtri(u)@np.linalg.cholesky(proposal.covariances[j-1]).T+proposal.means[j-1])
            points.append(u)
        points=np.concatenate(points)
        weights=np.ones(k+1)/(k+1)
        return points,proposal.log_density(points,weights)
    return sample


def prepare_groups():
    out=ROOT/'results/grouped_importance';out.mkdir(exist_ok=True)
    dest=out/'training.json'
    if dest.exists():return json.loads(dest.read_text())
    cfg=json.loads((ROOT/'config.json').read_text());bounds=np.array(cfg['prior']['bounds'])[1:];width=np.diff(bounds,axis=1).ravel()
    trainfile=ROOT/'results/endpoint_129_13_marginals.npz';train=np.load(trainfile)
    eta=train['eta'].reshape(-1,4);unit=(eta-bounds[:,0])/width
    logw=train['log_eta_weights'].reshape(len(unit),80);logw-=logsumexp(logw,axis=0)
    means=np.exp(logw).T@unit
    # Group by the first principal direction of data-adapted A0/G nuisance means.
    data_means=(means[:16]+means[48:64])/2
    cov=np.cov(data_means.T);values,vectors=np.linalg.eigh(cov)
    direction=vectors[:,-1]
    if direction[np.argmax(abs(direction))]<0:direction=-direction
    order=np.argsort(data_means@direction,kind='stable');groups=np.array_split(order,4)
    output=dict(training_file=str(trainfile.relative_to(ROOT)),training_sha256=sha256(trainfile),data_sha256=sha256(ROOT/'results/data.npz'),proposal_source_sha256=sha256(ROOT.parent/'c07_efficiency/proposal.py'),grouping='Four groups of four, sorted along first principal component of unit-prior-coordinate posterior nuisance means averaged over A0_CN and A_G; data only.',principal_direction=direction.tolist(),groups=[],truth_used_for_training=False)
    for index,ids in enumerate(groups):
        cols=np.concatenate([ids+16*k for k in range(5)])
        group_logw=logsumexp(logw[:,cols],axis=1)-np.log(len(cols))
        proposal,diagnostics=fit_proposal(unit,group_logw,components=4,iterations=60,covariance_floor=.03,inflation=1.15,defensive_fraction=.2)
        output['groups'].append(dict(index=index,realization_indices=ids.tolist(),proposal=proposal.description(),diagnostics=diagnostics,production_weights=[.2]*5,production='Equal counts per Gaussian and uniform component; every component count is2**power; fitted EM weights do not replace actual balance weights.'))
        print(f'group {index} trained on realizations {ids.tolist()}',flush=True)
    dest.write_text(json.dumps(output,indent=2)+'\n')
    return output


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--groups',type=int,nargs='*',default=[0,1,2,3]);parser.add_argument('--powers',type=int,nargs='*',default=[9]);parser.add_argument('--sets',type=int,nargs='*',default=[0,1]);parser.add_argument('--train-only',action='store_true');args=parser.parse_args()
    training=prepare_groups()
    if args.train_only:return
    cfg=json.loads((ROOT/'config.json').read_text());e=experiment(cfg);data=np.load(ROOT/'results/data.npz')
    provider=ExactNodeORF(e,cfg['orf'],ROOT/'results/orf_cache')
    for gi in args.groups:
        group=training['groups'][gi];p=group['proposal'];ids=np.array(group['realization_indices'])
        proposal=DefensiveLogitMixture(p['component_weights'],p['means_logit'],p['covariances_logit'],.2)
        sampler=balanced_sampler(proposal);like=FastLikelihood(e,data['q'][ids],data['x_physical'][ids],data['x_gaussian'][ids])
        out=ROOT/'results/grouped_importance'/f'group_{gi}';out.mkdir(exist_ok=True)
        for power in args.powers:
            for replicate in args.sets:
                level=dict(name=f'group{gi}_component_power{power}_set{replicate}',mass_nodes=129,endpoint_beta_nodes=[0,.0002,.0005,.001,.002,.005,.01,.02,.05,.1,.15],nuisance_power=power,scrambles=4,seed=7078000+gi*100+replicate*10,proposal_training_sha256=sha256(ROOT/'results/grouped_importance/training.json'))
                if (out/(level['name']+'.json')).exists():continue
                result=integrate_level(level,cfg,e,provider,like,data['truth'][ids],out,batch=256,proposal_sampler=sampler)
                result['realization_indices']=ids.tolist();result['proposal_components']=5;result['points_per_scramble']=5*2**power
                (out/(level['name']+'.json')).write_text(json.dumps(result,indent=2)+'\n')
                print(json.dumps(dict(name=level['name'],seconds=result['wall_seconds'],maximum_relative_evidence_se=float(np.max(result['evidence_relative_standard_error'])))),flush=True)


if __name__=='__main__':main()
