from pathlib import Path
import json
from unittest.mock import patch
import sys
REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
OUTPUT = REPO / "results/C07/validation"
OUTPUT.mkdir(parents=True, exist_ok=True)

import inference.scale_gaussian as g


def main():
    cases=[('negative_norm',(-1.,0.,1.,0.,10,-.3,.3),dict(coarse_order=32,fine_order=64),ValueError),
           ('cauchy_violation',(1.,2.,1.,0.,10,-.3,.3),dict(coarse_order=32,fine_order=64),ValueError),
           ('zero_norm_nonzero_linear',(0.,1e-15,1.,0.,10,-.3,.3),dict(coarse_order=32,fine_order=64),ValueError),
           ('zero_interval',(1.,0.,1.,0.,10,.3,.3),dict(coarse_order=32,fine_order=64),ValueError),
           ('unordered_resolutions',(1.,0.,1.,0.,10,-.3,.3),dict(coarse_order=64,fine_order=32),ValueError),
           ('unresolved_rule',(10.,1.,1.,0.,40,-.3,.3),dict(coarse_order=2,fine_order=4,relative_tolerance=1e-12),ArithmeticError)]
    passed=[]
    for name,args,kw,error in cases:
        try:g.gaussian_log_scale_integral(*args,**kw)
        except error:passed.append(name)
        else:raise AssertionError(name+' failed to reject')
    with patch.object(g,'_piece',side_effect=AssertionError('Numerical integration should not start')):
        try:g.gaussian_log_scale_integral(1.,0.,1.,0.,10,-.3,.3,coarse_order=32,fine_order=64,maximum_evaluations=95)
        except ValueError:passed.append('budget_before_quadrature')
        else:raise AssertionError('Missing resource preflight')
    out={'status':'PASS_explicit_failure_guards','cases':passed}
    (OUTPUT/'validation_guards.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out))


if __name__=='__main__':main()
