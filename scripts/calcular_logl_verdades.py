#!/usr/bin/env python3
"""Evaluate the diagnostic statistic log L(theta_true;y) using direct truth ORFs.

This separate diagnostic command reads injected truths. Proposal training and IID
production do not call it. No posterior CDF or SBC acceptance is computed here.
"""
from pathlib import Path
import argparse, hashlib, json, sys, time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
import numpy as np
from inference.model import experiment
from inference.data_generation import StoredExactORF
from inference.likelihood_reference import Likelihood


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for key in ['experiment','data','orf_cache','output']:
        parser.add_argument('--'+key.replace('_','-'),type=Path,required=True)
    args=parser.parse_args();start=time.perf_counter()
    if args.output.exists():raise FileExistsError('Preserve the prior diagnostic output.')
    cfg=json.loads(args.experiment.read_text()); exp=experiment(cfg)
    provider=StoredExactORF(exp,cfg['orf'],args.orf_cache)
    root=Path(__file__).resolve().parents[1]
    paths=[Path(__file__),args.experiment,args.data]+[root/'src/inference'/p for p in
        ['model.py','data_generation.py','likelihood_reference.py','orf_backend.py','orf_table_builder.py']]
    paths+=list((root/'src/pta').glob('*.py'))
    sources={str(p.resolve().relative_to(root)):sha(p) for p in paths}
    with np.load(args.data,allow_pickle=False) as f:
        truth=f['truth'];q=f['q'];x=f['x_physical'];g=f['x_gaussian']
    n=len(truth)
    if truth.shape!=(cfg['n_realizations'],5) or any(len(v)!=n for v in [q,x,g]):
        raise ValueError('Truth/observation count mismatch.')
    values=np.empty((5,n))
    for i,t in enumerate(truth):
        gamma=provider.evaluate(float(t[0]))
        reference=Likelihood(exp,q[i:i+1],x[i:i+1],g[i:i+1])
        values[:,i]=reference(t[None,1:],gamma)[0]
    if not np.isfinite(values).all():raise ArithmeticError('Nonfinite diagnostic truth log likelihood.')
    if any(sha(root/p)!=digest for p,digest in sources.items()):raise RuntimeError('Input/source changed.')
    report=dict(status='DIRECT_ORF_TRUTH_LOGL_DIAGNOSTIC_ONLY',
        models=cfg['models'],shape=list(values.shape),log_likelihood=values.tolist(),
        data_sha256=sha(args.data),config_sha256=sha(args.experiment),
        truth_array_sha256=hashlib.sha256(truth.tobytes()).hexdigest(),
        source_sha256=sources,truth_orf_records=provider.records,
        interpolation_used=False,posterior_cdf_computed=False,
        statistic='log normalized likelihood at generating parameter and same observed datum; not log posterior or importance weight',
        seconds=time.perf_counter()-start)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    with args.output.open('x') as f:json.dump(report,f,indent=2,allow_nan=False);f.write('\n')
    print(json.dumps({k:report[k] for k in ['status','shape','data_sha256','seconds']}))


if __name__=='__main__':main()
