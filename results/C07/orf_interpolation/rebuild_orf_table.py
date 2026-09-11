"""Rebuild the final ORF table from the repository root; preflight by default."""
from pathlib import Path
import argparse,json,sys,hashlib
import numpy as np

def main():
 p=argparse.ArgumentParser();p.add_argument('--repository-root',type=Path,default=Path.cwd());p.add_argument('--config',default='configs/calibration/pilot_initial.json');p.add_argument('--cache',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--execute',action='store_true');a=p.parse_args();root=a.repository_root.resolve();sys.path.insert(0,str(root/'src'))
 from inference.model import experiment
 from inference.orf_backend import ExactNodeORF
 from inference.orf_table_builder import ConstructionBudget,build_checked_nodes,read_validated_entry,token
 cfg=json.loads((root/a.config).read_text());e=experiment(cfg)
 # Frozen grid: base8193, exact u=.5 anchor; threshold layer plus interval474
 # selected by the preserved first validation. All numbers are dyadic in beta.
 beta=np.linspace(1,0,8193);u=np.sqrt((1-beta)*(1+beta));extra=np.unique(np.r_[np.arange(129)/65536,np.arange(472*8,477*8+1)/32768]);nodes=np.unique(np.r_[u,.5,np.sqrt((1-extra)*(1+extra))]);assert len(nodes)==8336
 coarsebeta=np.unique(np.r_[np.linspace(1,0,4097),np.arange(65)/32768,np.arange(472*4,477*4+1)/16384]);coarse=np.unique(np.r_[np.sqrt((1-coarsebeta)*(1+coarsebeta)),.5]);assert len(coarse)==4169
 assert np.array_equal(nodes[np.searchsorted(nodes,coarse)],coarse)
 budget=ConstructionBudget(maximum_requested_nodes=10000,maximum_total_real_multiplications=60_000_000_000_000);meta=ExactNodeORF(e,cfg['orf'],a.cache);work=int(2*len(nodes)*len(e['points'])*np.sum((meta.l-1)*meta.n+(meta.lf-1)*meta.nf));preflight=dict(nodes=len(nodes),coarse_subset_nodes=len(coarse),work_upper_bound=work,physical_signature=meta.signature,output=str(a.output),cache=str(a.cache),execute=a.execute,original_artifact_sha256='75632dfbdd9cce8b60b9f760a3177a76798a4adb7ac9ccc724092aeaf53ad70d',expected_equivalence='Same matrices within construction tolerance; bitwise file identity is not required across BLAS/library/metadata versions.')
 print(json.dumps(preflight,indent=2),flush=True)
 if not a.execute:return
 if a.output.exists():raise FileExistsError('Output exists; preserve the artifact or choose a new path.')
 manifest=build_checked_nodes(e,cfg['orf'],nodes,a.cache,budget=budget,validate_direct=True)
 matrices=np.array([read_validated_entry(a.cache/(token(meta.signature,u)+'.npz'),signature=meta.signature,u=u,K=len(e['f']),P=len(e['points']),tolerance=cfg['orf']['maximum_matrix_abs_difference'])[0] for u in nodes])
 a.output.parent.mkdir(parents=True,exist_ok=True)
 with a.output.open('xb') as f:np.savez_compressed(f,nodes=nodes,matrices=matrices)
 record=dict(preflight=preflight,construction=manifest,artifact_sha256=hashlib.sha256(a.output.read_bytes()).hexdigest(),coarse_subset_indices=np.searchsorted(nodes,coarse).tolist())
 a.output.with_suffix('.json').write_text(json.dumps(record,indent=2))
if __name__=='__main__':main()
