#!/usr/bin/env python3
"""Audit and archive saved W1 runs; performs no likelihood evaluations."""
from pathlib import Path
import hashlib,json,zipfile
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'tmp/c09_w1_reference_v1';DEST=ROOT/'results/C09/W1'
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    DEST.mkdir(parents=True,exist_ok=True)
    rows=[];charged=0;cpu=0.;runs=[]
    expected={r['curve_id']:r for r in read(ROOT/'tmp/c09_D2_continuation_v3/runtime_config.json')['curves']}
    for directory in [SOURCE/'pilot_execution']+sorted((SOURCE/'remaining_execution').glob('*/')):
        receipt=read(directory/'receipt.json');plan=read(directory/'plan.json');curve=plan['curve']
        assert receipt['status']=='COMPLETED' and receipt['completed_references']==2
        assert receipt['budget']['failed_reserved_values']==0
        for rel,h in receipt['bindings'].items():assert sha(ROOT/rel)==h,rel
        oldpath=ROOT/f'tmp/c09_D2_continuation_execution_v3/worker/caches/{curve}.npz'
        with np.load(oldpath,allow_pickle=False) as old,np.load(directory/'cache.npz',allow_pickle=False) as new:
            indices=np.searchsorted(new['u'],old['u'])
            assert np.array_equal(new['u'][indices].view(np.uint64),old['u'].view(np.uint64))
            assert np.array_equal(new['log_likelihood'][indices].view(np.uint64),old['log_likelihood'].view(np.uint64))
            assert len(new['u'])-len(old['u'])+3==receipt['budget']['additional_charged_values']
        comparisons=read(directory/'comparisons.json')
        assert [r['prior_id'] for r in comparisons]==expected[curve]['prior_ids']
        refs=[read(directory/f'reference_{i}.json')['results'] for i in (1,2)]
        historical=read(ROOT/f'tmp/c09_D2_continuation_execution_v3/worker/results/{curve}.json')['results']
        for i,row in enumerate(comparisons):
            a,b=refs[0][i],refs[1][i]
            cdf=max(float(np.max(abs(np.array(x['cdf'])-historical[i]['reference']['cdf']))) for x in (a,b))
            zd=max(x['normalization_relative_discrepancy'] for x in (a,b))
            assert abs(cdf-row['CDF_delta'])<1e-15 and abs(zd-row['relative_Z_delta'])<1e-15
            assert row['operational_delta']>=abs(a['W1']-b['W1'])
            passed=row['operational_delta']<=.001 and cdf<=.002 and zd<=.001
            assert (row['status']=='PASS_FINITE_DOMAIN_OPERATIONAL')==passed
            rows.append(dict(curve_id=curve,**row))
        charged+=receipt['budget']['additional_charged_values'];cpu+=receipt['CPU'];runs.append(curve)
    assert set(runs)==set(expected) and len(rows)==40
    summary=dict(analyses=40,curves=13,passed=sum(r['status']=='PASS_FINITE_DOMAIN_OPERATIONAL' for r in rows),
        additional_values=charged,CPU=cpu,cumulative_values=760969+charged,cumulative_CPU=888.798588+cpu,
        max_W1_delta=max(r['operational_delta'] for r in rows),max_CDF_delta=max(r['CDF_delta'] for r in rows),
        max_relative_Z_delta=max(r['relative_Z_delta'] for r in rows),rows=rows,
        scope='Operational W1 reference on saved ORF backend; finite physical controls inherited explicitly. Not uniform physical error, SBC, or population inference.',C09_complete=False)
    (DEST/'audit.json').write_text(json.dumps(summary,indent=2)+'\n')
    files=sorted(p for p in SOURCE.rglob('*') if p.is_file() and '__pycache__' not in p.parts)
    entries=[dict(path=str(p.relative_to(ROOT)),sha256=sha(p),bytes=p.stat().st_size) for p in files]
    archive=DEST/'fontes_execucoes.zip'
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for p in files:z.write(p,p.relative_to(ROOT))
    with zipfile.ZipFile(archive) as z:
        for x in entries:assert hashlib.sha256(z.read(x['path'])).hexdigest()==x['sha256']
    manifest=dict(archive=str(archive.relative_to(ROOT)),archive_sha256=sha(archive),files=entries,
        dependencies='D2 continuation archive, v0.8.5/v0.8.6 snapshots and bound C06-C08 inputs',
        source_note='pilot.py generalized after initial baseline_d2 run: CLI parameters and inherited finite-evidence check added; integration, kernels, controls and default baseline_d2 numerics unchanged. remaining plan binds generalized source hashes.')
    (DEST/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps({k:v for k,v in summary.items() if k!='rows'},indent=2))
if __name__=='__main__':main()
