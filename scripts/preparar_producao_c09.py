#!/usr/bin/env python3
"""Freeze C09 production IDs and continuous truths; no ORFs or likelihoods."""
from pathlib import Path
import json,hashlib
import numpy as np
R=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,x):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
def rng(master,stage,prior,scenario,datum):return np.random.Generator(np.random.PCG64(np.random.SeedSequence([master,stage,prior,scenario,datum])))
def build(design):
 seeds=design['seeds'];uniforms=np.array([[rng(seeds['core_truth'],1,p,0,i).random() for i in range(500)] for p in range(3)])
 truths=np.stack((uniforms[0],np.sqrt(uniforms[1]),.001**(1-uniforms[2])))
 rows=[];central=[-15.,13/3,-15.5,0.];trio=['A0_CN','B_CN_full_variable','B_G_full_variable']
 def add(stage,prior_id,scenario,i,u,scale,eta,models,master,**extra):
  rows.append(dict(id=f's{stage}_p{prior_id}_c{scenario}_d{i}',stage_id=stage,prior_id=prior_id,scenario_id=scenario,datum_id=i,truth_u=float(u),distance_scale=float(scale),eta=eta,models=models,data_seed=[master,stage,prior_id,scenario,i],engineering=False,**extra))
 for p in range(3):
  for i,u in enumerate(truths[p]):add(1,p,0,i,u,1.,central,design['core_models'],seeds['core_data'],kind='core',prior=design['priors'][p]['name'])
 for c,variant in enumerate(design['covariance_factorial']['matched_self_controls']['variants']):
  for i,u in enumerate(truths[0]):add(2,0,c,i,u,1.,central,['B_G_'+variant],seeds['covariance_self_control'],kind='self_control',variant=variant,prior='uniform_u')
 for c,noise in enumerate(design['noise_cases']):
  eta=central.copy();eta[2]=noise['log10_Ar'];eta[3]=float(np.log10(noise['EFAC']))
  for i,u in enumerate(truths[0]):add(3,0,c,i,u,1.,eta,trio,seeds['noise'],kind=noise['name'],prior='uniform_u')
 for c,(gamma,u) in enumerate((g,u) for g in design['spectral_subset']['gamma'] for u in design['spectral_subset']['fixed_u']):
  eta=central.copy();eta[1]=gamma
  for i in range(64):add(4,0,c,i,u,1.,eta,trio,seeds['spectra'],kind='spectral_fixed',prior='uniform_u',SBC=False)
 for c,(kind,rho) in enumerate((k,r) for k in design['contaminants']['types'] for r in design['contaminants']['pivotal_PSD_ratios']):
  for i in range(64):add(5,0,c,i,.5,1.,central,[m+'__'+mode for mode in ('known_included','omitted') for m in trio],seeds['contaminants'],kind=kind,contaminant_ratio=rho,prior='uniform_u',SBC=False)
 for i,u in enumerate(truths[0]):
  latent_seed=[seeds['distances'],6,0,0,i];scale=float(rng(*latent_seed).choice(design['distances']['scales'],p=design['distances']['probabilities']))
  add(6,0,1,i,u,scale,central,[m+'__'+mode for mode in ('correct_mixture','nominal_scale_only') for m in trio],seeds['distances'],kind='distance',prior='uniform_u',latent_seed=latent_seed,latent_not_supplied_to_inference=True)
 for c,u in enumerate(design['fixed_truth']['u']):
  for i in range(128):add(7,0,c,i,u,1.,central,trio,seeds['boundary'],kind='boundary_fixed',prior='uniform_u',SBC=False)
 assert len(rows)==5396 and len({r['id'] for r in rows})==len(rows)
 assert len({tuple(r['data_seed']) for r in rows})==len(rows)
 assert sum(len(r['models']) for r in rows)==25956
 pairs=sorted({(r['truth_u'],r['distance_scale']) for r in rows})
 indices={pair:i for i,pair in enumerate(pairs)}
 for r in rows:r['truth_response_index']=indices[(r['truth_u'],r['distance_scale'])]
 return rows,np.array(pairs),truths
def main():
 source=R/'configs/robustness/c09_prospective_original_v1.json';design=json.loads(source.read_text());rows,pairs,truths=build(design)
 out=R/'tmp/c09_production_v1/prepared';out.mkdir(parents=True,exist_ok=False)
 np.savez_compressed(out/'truths.npz',u=pairs[:,0],distance_scale=pairs[:,1],core_truth_u=truths)
 write(out/'rows.json',rows)
 config=dict(design, schema='C09_PRODUCTION_FROZEN_v1',status='IDS_AND_TRUTHS_FROZEN_NO_PHYSICAL_GENERATION',execution_enabled=False)
 config['final_c07_manifest']=sha(R/'releases/v0.7.0/manifest.json');config['final_c08_manifest']=sha(R/'releases/v0.8.0/manifest.json')
 config['costs']=dict(design['costs'],maximum_real_ORF_multiplications=90_000_000_000_000,additional_distance_reference_node_reserve=2016)
 config['stage_namespace']={'core':1,'self_control':2,'noise':3,'spectra':4,'contaminants':5,'distances':6,'boundary':7}
 config['distance_seed_namespace']='scenario 0 for latent, scenario 1 for observations; shared core uniform-u truths, independent global latent per datum'
 config['extension_models']=['A0_CN','B_CN_full_variable','B_G_full_variable']
 config['production_inputs']={str(p.relative_to(R)):sha(p) for p in (source,Path(__file__),out/'truths.npz',out/'rows.json',R/'tmp/c09_D3_reference_continuation/DECISAO.md')}
 write(R/'configs/robustness/c09_production_v1.json',config)
 receipt=dict(datasets=len(rows),posterior_integrals=sum(len(r['models']) for r in rows),truth_response_pairs=len(pairs),truths_continuous_not_table_nodes=True,global_distance_counts={str(s):sum(r['kind']=='distance' and r['distance_scale']==s for r in rows) for s in (.9,1.,1.1)},ORF_evaluations=0,likelihood_evaluations=0,observations_generated=0)
 write(out/'receipt.json',receipt);print(json.dumps(receipt,indent=2))
if __name__=='__main__':main()
