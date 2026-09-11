import numpy as np
from beta_builder import HERE,sha_file,write_json
from curve_algebra_v2 import coordinate
p=HERE/'first_curve_root.npz'
with np.load(p,allow_pickle=False) as z:
 n=z['nodes'];c=z['coeff'][-1]
x=coordinate(n);derivative=-(c[1]+2*c[2]+3*c[3])/(x[-1]-x[-2]);error=float(np.max(abs(derivative)))
if error>1e-7:raise ValueError('Inherited ROOT first curve has a nonzero threshold derivative beyond gate')
write_json(HERE/'first_curve_parity.json',dict(status='INHERITED_ROOT_FIRST_CURVE_PARITY_PASS',first_curve_file_sha256=sha_file(p),maximum_beta_derivative_at_zero=error,threshold=1e-7,source_sha256=sha_file(__file__),ORF_evaluations=0,likelihood_evaluations=0))
