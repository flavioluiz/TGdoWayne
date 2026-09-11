"""Adaptive trajectories learn a density only; no injected truths are loaded."""
from pathlib import Path
from time import perf_counter
import numpy as np
from .campaign_io import *
from .pointwise import UnitPosterior
from .mh_training import TargetSeededMH
from .linalg_batch import forward_substitution
from .gmm_fit import fit_proposal
from .gmm_density import MultipleRHSGaussianDefensiveProposal as GaussianDefensiveProposal

def train_block(runtime,targets,output_root,*,resume=False):
 runtime.require_execution();ids=np.asarray(targets,int)
 if ids.ndim!=1 or not len(ids) or any(t not in runtime.targets for t in ids):raise ValueError('Targets outside frozen campaign.')
 cfg=runtime.settings['training'];steps=positive_int(cfg['steps'],'training steps');chains=positive_int(cfg.get('chains',4),'chains');selected=positive_int(cfg.get('points_for_em',2048),'EM points')
 if steps<1000 or chains!=4 or selected%chains or steps//2<selected//chains:raise ValueError('Training length/selection violates the frozen proposal design.')
 output=Path(output_root);runtime.snapshot(output);pending=[];completed=[]
 for target in ids:
  path=output/f'target_{target:06d}.json'
  if path.exists():
   if not resume:raise FileExistsError('Existing frozen proposal: '+str(path))
   row=verify_record(path,runtime.target_identity,status='FROZEN_PROPOSAL')
   if row['training_configuration_sha256']!=canonical_hash(cfg):raise RuntimeError('Frozen training configuration changed.')
   validate_proposal(row);completed.append(row)
  else:pending.append(int(target))
 if not pending:return completed
 posterior=UnitPosterior(runtime.likelihood,runtime.bounds)
 sampler=TargetSeededMH(posterior,pending,seed=cfg['seed'],chains=4,mass_probability=.15,nuisance_probability=.20,independence_probability=.45,student_df=5.,student_scales=(1.,3.),student_weights=(.75,.25),adaptation_window=min(4000,steps));sampler.solve=forward_substitution
 selection=np.linspace(steps//2,steps-1,selected//chains).astype(int);states=[];next_index=0;start=perf_counter()
 for i in range(steps):
  x,_=sampler.step(adapt=True)
  if next_index<len(selection) and i==selection[next_index]:states.append(x.copy());next_index+=1
 elapsed=perf_counter()-start;points=np.asarray(states).transpose(1,0,2,3).reshape(len(pending),selected,5);meta=sampler.metadata()
 for index,target in enumerate(pending):
  start=perf_counter();fit,diagnostics=fit_proposal(points[index],np.zeros(selected),components=4,iterations=80,covariance_floor=.03,inflation=1.10)
  row=dict(status='FROZEN_PROPOSAL',identity=runtime.target_identity,training_execution_identity=runtime.identity,training_configuration_sha256=canonical_hash(cfg),target=target,model=MODELS[target//runtime.n],datum=target%runtime.n,uses_truth=False,weights=fit.component_weights.tolist(),means=fit.means.tolist(),covariances=fit.covariances.tolist(),global_mean=meta['mean'][index],global_cholesky=meta['cholesky'][index],random_walk_logscale=meta['logscale'][index],defensive_fraction=.15,student_df=5.,student_scale=3.,training_steps=steps,chains=chains,seed=cfg['seed'],rng_recipe=meta['rng_recipe'],selection_indices=selection.tolist(),training_points_sha256=hashlib.sha256(points[index].tobytes()).hexdigest(),training_block_seconds=elapsed,em_seconds=perf_counter()-start,em_diagnostics=diagnostics,input_sha256=runtime.input_hashes,posterior_claimed=False)
  runtime.verify_unchanged();validate_proposal(row);row['proposal_content_hash']=canonical_hash(row);write_json_new(output/f'target_{target:06d}.json',row);completed.append(row)
 return completed

def validate_proposal(row):
 return GaussianDefensiveProposal(np.asarray(row['weights'])[None],np.asarray(row['means'])[None],np.asarray(row['covariances'])[None],np.asarray(row['global_mean'])[None],np.asarray(row['global_cholesky'])[None],defensive_fraction=row['defensive_fraction'],student_df=row['student_df'],student_scale=row['student_scale'])
