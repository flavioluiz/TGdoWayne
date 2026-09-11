from harness import *
from time import perf_counter
import hashlib
sys.path.insert(0,str(ROOT/'tmp/c07_efficiency'))
from proposal import fit_proposal
out=Path(__file__).resolve().parent/'results';meta=json.loads((out/'pilot553_refresh.json').read_text());draws=np.load(out/'pilot553_refresh_draws.npy',mmap_mode='r');targets=[0,3,8,9,11,14,20,25,28,35,46,51,52,62,67,78];indices=np.linspace(0,len(draws)-1,512).astype(int);rows=[];t=perf_counter()
for target in targets:
    x=np.asarray(draws[indices,target]).reshape(-1,5);proposal,diagnostics=fit_proposal(x,np.zeros(len(x)),components=4,iterations=80,covariance_floor=.03,inflation=1.10)
    rows.append(dict(target=target,weights=proposal.component_weights.tolist(),means=proposal.means.tolist(),covariances=proposal.covariances.tolist(),global_mean=meta['mean'][target],global_cholesky=meta['cholesky'][target],random_walk_logscale=meta['logscale'][target],fit_diagnostics=diagnostics))
r=dict(status='frozen_proposal_training_only',targets=targets,training_source='pilot553_refresh_draws.npy; previous pilot excluded from new production',training_source_sha256=hashlib.sha256((out/'pilot553_refresh_draws.npy').read_bytes()).hexdigest(),points_per_target=2048,components=4,defensive_student_fraction=.15,student_df=5.,student_scale=3.,uses_truth=False,records=rows,seconds=perf_counter()-t)
(out/'mixture_training.json').write_text(json.dumps(r,indent=2));print(json.dumps(dict(done=True,targets=targets,seconds=r['seconds'])),flush=True)
