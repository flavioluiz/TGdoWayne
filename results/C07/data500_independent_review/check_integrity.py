"""Completeness and independent nominal geometry checks for the completed audit."""
from pathlib import Path
import hashlib,json
import numpy as np
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent

def main():
    cfgpath=ROOT/'configs/calibration/prior_predictive_500_v1.json'
    base=ROOT/'results/C07/prior_predictive';cfg=json.loads(cfgpath.read_text())
    gen=json.loads((base/'generation.json').read_text());review=json.loads((HERE/'review.json').read_text())
    N=cfg['n_realizations'];n=cfg['n_pulsars'];j=np.arange(n)
    assert len(gen['truth_orf_records'])==N==500
    assert len(review['all_rows'])==N and [r['index'] for r in review['all_rows']]==list(range(N))
    assert len({r['file'] for r in gen['truth_orf_records']})==N
    with np.load(base/'data.npz',allow_pickle=False) as f:arrays={k:f[k] for k in ['truth','q','x_physical','x_gaussian','directions','sigma','red_pattern','distances_ly']}
    assert arrays['truth'].shape==(N,5) and arrays['q'].shape==(N,4,n)
    assert arrays['x_physical'].shape==arrays['x_gaussian'].shape==(N,4,10)
    assert all(np.isfinite(a).all() for a in arrays.values())
    polar=np.arccos(1-(2*j+1)/n);azimuth=j*np.pi*(3-np.sqrt(5))
    positions=np.column_stack((np.sin(polar)*np.cos(azimuth),np.sin(polar)*np.sin(azimuth),np.cos(polar)))
    ds,ss,rs=cfg['geometry_seeds'];lo,hi=cfg['distance_range_light_years']
    distance=np.linspace(lo,hi,n)[np.random.default_rng(ds).permutation(n)]
    sigma=(1e-7*5**(j/(n-1)))[np.random.default_rng(ss).permutation(n)]
    red=(.5*4**(j/(n-1)))[np.random.default_rng(rs).permutation(n)]
    errors=dict(directions_max_absolute=float(np.max(abs(positions-arrays['directions']))),distances_max_absolute=float(np.max(abs(distance-arrays['distances_ly']))),sigma_max_relative=float(np.max(abs(sigma/arrays['sigma']-1))),red_pattern_max_relative=float(np.max(abs(red/arrays['red_pattern']-1))))
    assert all(v<1e-14 for v in errors.values())
    # Recheck every recorded input, including all500 payloads, after computation.
    for path,digest in review['source_sha256'].items():assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==digest
    for name,digest in review['cache_payload_hashes'].items():assert hashlib.sha256((base/'orf_cache'/name).read_bytes()).hexdigest()==digest
    result=dict(status='PASS_COMPLETENESS_AND_NOMINAL_DESIGN',realizations=N,unique_truth_cache_files=N,geometry_errors=errors,all_recorded_inputs_unchanged=True,audit_sha256=hashlib.sha256((HERE/'review.json').read_bytes()).hexdigest(),source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    with (HERE/'integrity.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
    print(json.dumps(result,indent=2))

if __name__=='__main__':main()
