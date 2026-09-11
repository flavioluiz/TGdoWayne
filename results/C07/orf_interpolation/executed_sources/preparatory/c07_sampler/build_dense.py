from harness import *
from time import perf_counter
from dataclasses import asdict
import hashlib
sys.path.insert(0,str(ROOT/'tmp/c07_orf_efficiency'))
from cache_builder import ConstructionBudget,build_checked_nodes,token
from inference.orf_backend import ExactNodeORF
cfg,e,data=load();out=Path(__file__).resolve().parent/'results';destination=Path(__file__).resolve().parent/'orf_cache_dense'
beta=np.linspace(1,0,8193);u=np.sqrt((1-beta)*(1+beta));coarse=u[::2].copy();nodes=np.unique(np.r_[u,.5]);budget=ConstructionBudget(maximum_requested_nodes=10000,maximum_total_real_multiplications=60_000_000_000_000)
meta=ExactNodeORF(e,cfg['orf'],destination);work=int(2*len(nodes)*len(e['points'])*np.sum((meta.l-1)*meta.n+(meta.lf-1)*meta.nf))
preflight=dict(nodes=len(nodes),base_beta_nodes=8193,coarse_beta_nodes=4097,additional_anchor=.5,maximum_beta_phase_step=float(2*meta.y[0].max()/8192),maximum_beta_phase_step_coarse=float(2*meta.y[0].max()/4096),total_real_multiplications_upper_bound=work,budget=asdict(budget),raw_output_bytes=int(len(nodes)*4*12*12*16),source_config_sha256=hashlib.sha256(CONFIG.read_bytes()).hexdigest(),new_budget_namespace=True,prior_unchanged=True)
(out/'dense_preflight.json').write_text(json.dumps(preflight,indent=2));print(json.dumps(preflight),flush=True)
manifest=build_checked_nodes(e,cfg['orf'],nodes,destination,budget=budget,validate_direct=True);(out/'dense_construction.json').write_text(json.dumps(manifest,indent=2));matrices=[]
for x in nodes:
 with np.load(destination/(token(meta.signature,x)+'.npz')) as saved:matrices.append(saved['Gamma'])
matrices=np.asarray(matrices);np.savez_compressed(out/'table_beta8193.npz',nodes=nodes,matrices=matrices)
cu=np.unique(np.r_[coarse,.5]);ix=np.searchsorted(nodes,cu);assert np.array_equal(nodes[ix],cu);np.savez_compressed(out/'table_beta4097.npz',nodes=cu,matrices=matrices[ix]);print(json.dumps(dict(done=True,seconds=manifest['seconds'],fine_nodes=len(nodes),coarse_nodes=len(cu))),flush=True)
