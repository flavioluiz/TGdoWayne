"""Build only3 fresh anchor nodes; compare matrices and all80 likelihood outputs."""
from pathlib import Path
import sys
REPO=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(REPO/"src"))
import hashlib,json,time
import numpy as np
from scipy.stats import qmc
from inference.orf_table_builder import build_checked_nodes,ConstructionBudget,token
from inference.model import experiment
from inference.orf_backend import ExactNodeORF
from inference.likelihood_reference import Likelihood

HERE=REPO/'tmp/c07_integrated_orf_validation';HERE.mkdir(parents=True,exist_ok=True)
cfg=json.loads((REPO/'configs/calibration/pilot_initial.json').read_text());e=experiment(cfg)
out=build_checked_nodes(e,cfg['orf'],np.array([0.,.5,1.]),HERE/'cache_validation',budget=ConstructionBudget(maximum_requested_nodes=8),validate_direct=True)
meta=ExactNodeORF(e,cfg['orf'],HERE/'cache_validation')
data=np.load(REPO/'results/C07/fixtures/pilot_data.npz');likelihood=Likelihood(e,data['q'],data['x_physical'],data['x_gaussian'])
bounds=np.array(cfg['prior']['bounds'])[1:];x=qmc.Sobol(4,scramble=True,seed=7110301).random_base2(5);eta=bounds[:,0]+x*np.diff(bounds,axis=1).ravel()
rows=[]
for u in [0.,.5,1.]:
    filename=token(meta.signature,u)+'.npz'
    with np.load(REPO/'results/C07/fixtures/orf_cache'/filename) as p:old=p['Gamma'].copy()
    with np.load(HERE/'cache_validation'/filename) as p:new=p['Gamma'].copy();record=json.loads(str(p['record']))
    matrix_error=float(np.max(abs(new-old)));lo=likelihood(eta,old);ln=likelihood(eta,new);error=float(np.max(abs(lo-ln)))
    if matrix_error>1e-8 or error>1e-7:raise AssertionError((u,matrix_error,error))
    rows.append(dict(u=u,matrix_max_abs_difference=matrix_error,likelihood_values=lo.size,maximum_logL_difference=error,
                     compatible_signature=record['signature']==meta.signature))
out['legacy_cache_and_likelihood_comparisons']=rows;out['frozen_nuisance_test_seed']=7110301
out['scope']='Only three anchor nodes in a new private cache; not a5000-node table or interpolation approval.'
(REPO/'results/C07/validation').mkdir(exist_ok=True);(REPO/'results/C07/validation/orf_blas_builder.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps({'status':out['status'],'new_nodes':out['new_nodes'],'maximum_direct_error':max(row['absolute_difference'] for row in out['sparse_direct_checks']),'comparisons':rows,'seconds':out['seconds']},indent=2),flush=True)
