from pathlib import Path
from time import perf_counter
import argparse
import json
import numpy as np
import sys
import hashlib
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"src"))
from inference.model import experiment, covariance_batch
from inference.orf_backend import ExactNodeORF
from inference.likelihood_reference import Likelihood
from inference.quadrature import integrate_level
def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()
from inference.likelihood import FastLikelihood
from pta.simulation import paired_physical_and_gaussian

ROOT=Path(__file__).resolve().parents[1]


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--config',type=Path,default=ROOT/'configs/calibration/pilot_initial.json');parser.add_argument('--output',type=Path,default=ROOT/'tmp/reproduction/rqmc_pilot');parser.add_argument('--kernel',choices=['reference','fast'],default='reference');parser.add_argument('--dry-run',action='store_true');parser.add_argument('--levels',nargs='*');parser.add_argument('--level-file',type=Path);parser.add_argument('--skip-direct',action='store_true',help='Use only after independent direct checks have been saved.');args=parser.parse_args()
    cfg=json.loads(args.config.read_text());e=experiment(cfg);results=args.output
    levels=cfg['levels'] if args.level_file is None else json.loads(args.level_file.read_text())['levels']
    if args.dry_run:
        selected=[level for level in levels if not args.levels or level['name'] in args.levels]
        print(json.dumps({'configuration':str(args.config),'config_sha256':sha256(args.config),'output':str(results),'data_generation':False,'integration':False,'n_realizations':cfg['n_realizations'],'models':cfg['models'],'levels':[dict(level=level,parameter_points_upper_bound=(level['mass_nodes']+len(level.get('endpoint_beta_nodes',[])))*(2**level['nuisance_power'])*level['scrambles'],two_nuisance_weight_arrays_bytes=2*8*level['scrambles']*(2**level['nuisance_power'])*len(cfg['models'])*cfg['n_realizations']) for level in selected],'status':'cost_and_contract_preview_only; convergence_and_independent_reference_required_before_SBC500'},indent=2));return
    if cfg.get('status')=='draft_unconverged_campaign':raise RuntimeError('This campaign is a draft: numerical convergence has not been established. Revise the integration specification after the pilot, preserving all seeds and scientific criteria.')
    results.mkdir(parents=True,exist_ok=True)
    provider=ExactNodeORF(e,cfg['orf'],results/'orf_cache')
    datafile=results/'data.npz';bounds=np.asarray(cfg['prior']['bounds'])
    if datafile.exists():
        data=np.load(datafile);truth=data['truth'];q=data['q'];xp=data['x_physical'];xg=data['x_gaussian']
        if str(data['config_sha256'])!=sha256(args.config):raise RuntimeError('Frozen config differs from saved data. Do not overwrite seeds/truth.')
    else:
        truth=bounds[:,0]+np.random.default_rng(cfg['truth_seed']).uniform(size=(cfg['n_realizations'],5))*np.diff(bounds,axis=1).ravel()
        q=[];xp=[];xg=[];rng=np.random.default_rng(cfg['data_seed'])
        for index,theta in enumerate(truth):
            gamma=provider.evaluate(float(theta[0]));cov,_=covariance_batch(theta[None,1:],gamma,e)
            a,b,c=paired_physical_and_gaussian(cov[0],e['H'],1,rng)
            q.append(a[0]);xp.append(b[0]);xg.append(c[0]);print(f'continuous truth/data {index+1}/{len(truth)}',flush=True)
        q=np.array(q);xp=np.array(xp);xg=np.array(xg)
        np.savez_compressed(datafile,truth=truth,q=q,x_physical=xp,x_gaussian=xg,config_sha256=sha256(args.config),directions=e['points'],distances_ly=e['distance_ly'],sigma=e['sigma'],red_pattern=e['red'],frequency_hz=e['f'],scale=e['scale'])
    directpath=results/'orf_direct_checks.json'
    if args.skip_direct:
        if not directpath.exists():raise RuntimeError('Cannot skip absent independent checks.')
    elif not directpath.exists():directpath.write_text(json.dumps(provider.direct_checks(),indent=2)+'\n')
    likelihood=(Likelihood if args.kernel=='reference' else FastLikelihood)(e,q,xp,xg)
    for level in levels:
        if args.levels and level['name'] not in args.levels:continue
        if (results/(level['name']+'.json')).exists():print(f'preserving existing {level["name"]}',flush=True);continue
        result=integrate_level(level,cfg,e,provider,likelihood,truth,results)
        print(json.dumps({'level':level['name'],'seconds':result['wall_seconds'],'max_evidence_relative_se':float(np.max(result['evidence_relative_standard_error']))}),flush=True)
    records={x['u']:x for x in provider.records}
    if not records:return
    report={'config_sha256':sha256(args.config),'exact_mass_nodes_requested_this_run':len(records),'maximum_coarse_fine_difference':max(x['maximum_coarse_fine_difference'] for x in records.values()),'minimum_eigenvalue':min(x['minimum_eigenvalue'] for x in records.values()),'resolutions':{'lmax':provider.l.tolist(),'nmu':provider.n.tolist(),'fine_lmax':provider.lf.tolist(),'fine_nmu':provider.nf.tolist()},'records':list(records.values()),'status':'every_requested_matrix_refined; sparse_independent_pair_checks; not_full_independent_matrix_certification'}
    (results/'orf_audit.json').write_text(json.dumps(report,indent=2)+'\n')


if __name__=='__main__':main()
