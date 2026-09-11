"""A single original A0 datum, fixed65 mass rule: compare nuisance efficiency only."""
import argparse,json,time
from pathlib import Path
import numpy as np
from scipy.special import logsumexp
from scipy.stats import qmc
from scale_marginalization import LogAmplitudeBox,cn_log_scale_integral
from compare_pilot import PILOT,FrozenMassTable
from inference_pilot import experiment,covariance_batch,trapezoid_weights,continuous_ppf
HERE=Path(__file__).resolve().parent

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--power',type=int,default=11);ap.add_argument('--seed',type=int,default=7105000);args=ap.parse_args()
    start=time.perf_counter();cfg=json.loads((PILOT/'config.json').read_text());e=experiment(cfg);q=np.load(PILOT/'results/data.npz')['q'][14:15]
    box=LogAmplitudeBox();table=FrozenMassTable(e,cfg['orf']);children=np.random.SeedSequence(args.seed).spawn(4)
    coords=np.array([box.sample_ratio_prior(qmc.Sobol(3,scramble=True,seed=np.random.default_rng(seed)).random_base2(args.power)) for seed in children])
    n=2**args.power;mass=np.linspace(0,1,65);mw=trapezoid_weights(mass);lm=np.empty((4,len(mass)));M=q.shape[1]*q.shape[2]
    for j,u in enumerate(mass):
        g=table.get(float(u))
        for r in range(4):
            values=[]
            for first in range(0,n,256):
                a,b,slope,lo,hi=coords[r,first:first+256].T
                eta=np.column_stack((a,slope,b,np.zeros(len(a))))
                C0,_=covariance_batch(eta,g,e);chol=np.linalg.cholesky(C0)
                rhs=np.broadcast_to(q.transpose(1,2,0),(len(C0),*q.transpose(1,2,0).shape))
                solved=np.linalg.solve(chol,rhs);chi=np.sum(abs(solved)**2,axis=(1,2))[:,0]
                ld=2*np.log(np.diagonal(chol,axis1=-2,axis2=-1).real).sum(axis=(-2,-1))
                values.append(cn_log_scale_integral(chi,ld,M,lo,hi,conditional_average=True))
            lm[r,j]=logsumexp(np.concatenate(values))-np.log(n)
    zr=logsumexp(lm+np.log(mw)[None],axis=1);logZ=float(logsumexp(zr)-np.log(4));ratio=np.exp(zr-logZ)
    density=np.exp(logsumexp(lm,axis=0)-np.max(logsumexp(lm,axis=0)))
    out={'scope':'one original A0 datum14; fixed65 mass rule, no full convergence or SBC claim',
         'nuisance_dimensions':3,'analytic_scale':True,'nuisance_prior':'Exact joint Rosenblatt transform of original rectangular prior',
         'nuisance_power':args.power,'scrambles':4,'seed':args.seed,'mass_nodes':65,
         'parameter_points':65*4*n,'logZ':logZ,'logZ_by_scramble':zr.tolist(),
         'relative_SE':float(np.std(ratio,ddof=1)/2),'mass_quantiles':[continuous_ppf(mass,density,p) for p in cfg['quantiles']],
         'seconds':time.perf_counter()-start}
    path=HERE/'results'/f'A0_d14_scale_{args.power}_{args.seed}.json';path.write_text(json.dumps(out,indent=2)+'\n')
    np.savez_compressed(path.with_suffix('.npz'),mass=mass,log_mass_marginal=lm)
    print(json.dumps(out,indent=2))
if __name__=='__main__':main()
