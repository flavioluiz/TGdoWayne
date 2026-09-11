from pathlib import Path
import hashlib,json,sys,numpy as np
BASE=Path(__file__).resolve().parent;ROOT=BASE.parents[1];sys.path.insert(0,str(BASE/'executed_sources/src'))
from inference.orf_interpolation import EvenThresholdCubicORF
old=ROOT/'tmp/c07_sampler/results/table_beta8193_local.npz';root=ROOT/'results/C07/orf_interpolation/orf_table_pilot12x4.npz';ds=[]
for p in [old,root]:
 with np.load(p) as f:ds.append((f['nodes'].copy(),f['matrices'][:,0:1].copy()))
assert np.array_equal(ds[0][0],ds[1][0]) and np.array_equal(ds[0][1],ds[1][1]);a=EvenThresholdCubicORF(*ds[0],coordinate='beta');b=EvenThresholdCubicORF(*ds[1],coordinate='beta');assert np.array_equal(a.coeff,b.coeff)
r=dict(status='ROOT_FIRST_CURVE_IDENTITY_PASS',paths={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [old,root]},nodes_bit_equal=True,first_channel_matrices_bit_equal=True,first_channel_cubic_coefficients_bit_equal=True,first_channel_cubic_shape=list(b.coeff.shape),first_channel_matrices_sha256=hashlib.sha256(ds[1][1].tobytes()).hexdigest(),nodes_sha256=hashlib.sha256(ds[1][0].tobytes()).hexdigest(),first_channel_cubic_sha256=hashlib.sha256(b.coeff.tobytes()).hexdigest(),coefficient_coordinate='minus_beta',numpy_version=np.__version__,source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
with (BASE/'first_curve_identity.json').open('x') as f:json.dump(r,f,indent=2);f.write('\n')
with (BASE/'first_curve_root.npz').open('xb') as f:np.savez(f,nodes=ds[1][0],matrices=ds[1][1],coeff=b.coeff,coordinate=b.alpha)
print(json.dumps(r,indent=2))
