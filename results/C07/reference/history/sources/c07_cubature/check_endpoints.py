"""Do not extrapolate the anisotropic u=.5 agreement to mass endpoints."""
import json
import numpy as np
from cubature import HERE
from truncated_cdf import run as run_isotropic
from anisotropic_experiment import run as run_anisotropic

for u in [0.,1.]:
    filename=HERE/'results'/f'A0_d14_endpoint_{u:.0f}_truncated_comparison.json'
    if filename.exists():
        print('Preserving',filename.name,flush=True);continue
    a=run_anisotropic([32,20,12],np.array([u]))
    b=run_isotropic(32,masses=[u],max_points=10_000_000)
    result=dict(u=u,anisotropic=a,isotropic=b,
                absolute_logZ_difference=abs(a['log_evidence']-b['log_evidence']),
                maximum_CDF_difference=float(np.max(abs(np.array(a['original_nuisance_CDF_at_frozen_cuts'])-b['original_nuisance_CDF_at_frozen_cuts']))),
                scope='Endpoint guard, not full all-target inference approval')
    filename.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ['anisotropic','isotropic']}),flush=True)
