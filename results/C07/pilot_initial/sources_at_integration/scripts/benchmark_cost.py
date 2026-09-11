"""Timing only: repeat existing pilot data to size500; this generates no SBC realization."""
from pathlib import Path
from time import perf_counter
import json
import numpy as np
from scipy.stats import qmc
from inference_pilot import experiment,ExactNodeORF,Likelihood
ROOT=Path(__file__).resolve().parents[1]


def main():
    cfg=json.loads((ROOT/'config.json').read_text());e=experiment(cfg);d=np.load(ROOT/'results/data.npz')
    provider=ExactNodeORF(e,cfg['orf'],ROOT/'results/orf_cache');gamma=provider.evaluate(.5)
    bounds=np.array(cfg['prior']['bounds'])[1:]
    eta=bounds[:,0]+qmc.Sobol(4,scramble=True,seed=7076001).random_base2(9)*np.diff(bounds,axis=1).ravel()
    out=[]
    for size in [16,500]:
        idx=np.arange(size)%len(d['q'])
        like=Likelihood(e,d['q'][idx],d['x_physical'][idx],d['x_gaussian'][idx]);basis=like.prepare(gamma)
        like(eta[:4],gamma,basis)
        timings=[];checksum=0.
        for trial in range(3):
            t=perf_counter()
            for start in range(0,len(eta),128):checksum+=float(np.sum(like(eta[start:start+128],gamma,basis)))
            timings.append(perf_counter()-t)
        rate=float(np.median(timings)/len(eta))
        out.append(dict(dataset_columns_per_method=size,number_distinct_saved_pilot_datasets=len(d['q']),parameter_points=len(eta),five_model_columns=5*size,seconds=timings,median_seconds_per_parameter_point=rate,projection_139_mass_8192_nuisance_4_scrambles_seconds=rate*139*8192*4,checksum=checksum))
    report=dict(scope='Likelihood timing with repeated saved data, not500 independent simulations or calibration. Excludes ORF generation, summaries, IO and adaptation; simultaneous workspace tasks may affect wall time.',results=out,numpy=np.__version__)
    (ROOT/'results/timing_projection.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))


if __name__=='__main__':main()
