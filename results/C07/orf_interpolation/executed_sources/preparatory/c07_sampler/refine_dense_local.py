"""Local refinement selected from a preserved, failed validation, plus new holdouts."""
from harness import *
from inference.orf_backend import ExactNodeORF
from inference.orf_table_builder import ConstructionBudget,build_checked_nodes,token,read_validated_entry
import hashlib
cfg,e,data=load();out=Path(__file__).resolve().parent/'results';old=np.load(out/'dense_validation_arrays.npz');rng=np.random.default_rng(7078901);rng.random((4096,5))
# Reproduce only the prior masses (the first random operation in validate_dense).
prior=np.random.default_rng(7078901).random((4096,5));beta=np.sqrt((1-prior[:,0])*(1+prior[:,0]));delta=abs(old['8193_prior']-old['4097_prior']);selected=beta[delta>.0005]
# Fixed threshold layer: first16 cells of the8193 grid. Local refinement uses
# no additional PTA truths or production results; the failed check is archived.
intervals=sorted(set(int(np.floor(b*4096)) for b in selected));bc=np.arange(65)/32768;bf=np.arange(129)/65536
for j in intervals:
 left=max(0,j-2);right=min(4096,j+3)
 bc=np.r_[bc,np.arange(left*4,right*4+1)/16384];bf=np.r_[bf,np.arange(left*8,right*8+1)/32768]
coarse=np.load(out/'table_beta4097.npz');fine=np.load(out/'table_beta8193.npz');add=np.unique(np.sqrt((1-np.unique(bf))*(1+np.unique(bf))));known=set(fine['nodes']);requested=np.array([u for u in add if u not in known]);dest=Path(__file__).resolve().parent/'orf_cache_local_refinement';meta=ExactNodeORF(e,cfg['orf'],dest)
plan=dict(parent_validation_sha256=hashlib.sha256((out/'dense_validation.json').read_bytes()).hexdigest(),selection_margin=.0005,selected_prior_points=int(np.sum(delta>.0005)),selected_base4097_intervals=intervals,layer_beta_max=16/8192,layer_coarse_step=1/32768,layer_fine_step=1/65536,requested_new_nodes=len(requested),criteria_unchanged=True)
(out/'local_refinement_plan.json').write_text(json.dumps(plan,indent=2));print(json.dumps(plan),flush=True)
manifest=build_checked_nodes(e,cfg['orf'],requested,dest,budget=ConstructionBudget(maximum_requested_nodes=300),validate_direct=True);(out/'local_refinement_construction.json').write_text(json.dumps(manifest,indent=2))
extra={}
for u in requested:
 extra[u]=read_validated_entry(dest/(token(meta.signature,u)+'.npz'),signature=meta.signature,u=u,K=4,P=12,tolerance=cfg['orf']['maximum_matrix_abs_difference'])[0]
lookup={float(u):g for u,g in zip(fine['nodes'],fine['matrices'])};lookup.update(extra)
for name,base,b in [('table_beta4097_local',coarse,bc),('table_beta8193_local',fine,bf)]:
 us=np.unique(np.r_[base['nodes'],np.sqrt((1-np.unique(b))*(1+np.unique(b)))]);np.savez_compressed(out/(name+'.npz'),nodes=us,matrices=np.array([lookup[float(u)] for u in us]));print(json.dumps(dict(table=name,nodes=len(us))),flush=True)
