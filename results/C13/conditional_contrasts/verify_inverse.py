from pathlib import Path
import argparse,importlib.util,json,numpy as np
parser=argparse.ArgumentParser();parser.add_argument('--clean-root',type=Path,required=True);args=parser.parse_args()
R=Path.cwd();out=R/'results/C13/conditional_contrasts';c=args.clean_root
spec=importlib.util.spec_from_file_location('density',out/'density_reference.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
r=json.loads((out/'results.json').read_text());plan=json.loads((c/'tmp/c11_pilot16_candidate_v2/preflight.json').read_text())
z,w=np.polynomial.legendre.leggauss(4);checks=[]
def integral(d,x):
    cuts=np.unique(np.r_[d.x[d.x<x],x]);lo=cuts[:-1];width=np.diff(cuts)
    return float(np.sum(d.pdf(lo[:,None]+width[:,None]*(z+1)/2)*w*width[:,None]/2))
for model in r['config']['models']:
    with np.load(c/f'tmp/c13_population_reproduced_third/likelihood/P16K8_{model}.npz') as data:
        lookup={float(x).hex():i for i,x in enumerate(data['u'])}
        nodes=np.unique(np.r_[[0,.0001,.001,.01,.05,.25,.5,.75,.9,.99,1],plan['rules']['alpha64']['u']])
        ix=[lookup[float(x).hex()] for x in nodes]
        for datum in range(50):
            d=m.Density(nodes,data['logL'][1,ix,datum]);normalization=integral(d,np.pi/2)
            for p in (.948,.95,.952):
                error=abs(integral(d,np.arcsin(d.quantile(p)))/normalization-p)
                assert error<1e-10;checks.append(error)
result={'independent_piecewise_gauss_inversion_checks':len(checks),'maximum_cdf_residual':max(checks),'method':'Four-node Gauss-Legendre on every polynomial segment; independent of Pchip antiderivative used by quantile inversion.'}
(out/'inverse_verification.json').write_text(json.dumps(result,indent=2)+'\n');print(result)
