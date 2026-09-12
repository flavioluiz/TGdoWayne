"""Archive completed adaptive references, retaining the charged interface failure."""
from pathlib import Path
import hashlib,json,zipfile
import numpy as np

ROOT=Path(__file__).resolve().parents[1]


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    old=ROOT/'tmp/c09_production_references_v1'
    base=ROOT/'tmp/c09_production_references_v2'
    summary=json.loads((base/'summary.json').read_text())
    failure=json.loads((old/'refined/receipt.json').read_text())
    assert failure['status']=='FAILED' and failure['budget']['additional_charged_values']==3
    charged=passed=total=0;maxima={};bindings={}
    for path in sorted(base.glob('*/receipt.json')):
        receipt=json.loads(path.read_text());activation=json.loads((path.parent/'activation.json').read_text())
        assert receipt['status']=='COMPLETED_WITH_GATES'
        assert receipt['budget']['failed_reserved_values']==0
        for rel,digest in receipt['inputs_sha256'].items():
            source=path.parent/'source.py' if rel=='scripts/referencias_producao_c09.py' else ROOT/rel
            assert sha(source)==digest,rel
            bindings[rel]=digest
        assert sha(path.parent/'source.py')==activation['inputs_sha256']['scripts/referencias_producao_c09.py']
        with np.load(path.parent/'reference_cache.npz') as cache:
            assert len(cache['u'])==receipt['budget']['additional_charged_values']
            assert np.all(np.diff(cache['u'])>0) and np.isfinite(cache['log_likelihood']).all()
        comparisons=json.loads((path.parent/'comparisons.json').read_text())
        for comparison in comparisons:
            expected=all(v <= (.002 if k in ('CDF','CDF_ODE') else .001) for k,v in comparison['delta'].items())
            expected=expected and all(comparison['quantiles_passed']) and comparison['ODE_normalization_delta']<=.001
            assert expected==comparison['passed']
            for k,v in comparison['delta'].items():maxima[k]=max(maxima.get(k,0),v)
        total+=len(comparisons);passed+=sum(r['passed'] for r in comparisons)
        charged+=receipt['budget']['additional_charged_values']
    assert total==13 and passed==13 and charged==summary['charged']==80120
    assert summary['cumulative_C09']==54787604+charged+3
    out=ROOT/'results/C09/production_references';out.mkdir(parents=True,exist_ok=True)
    archive=out/'sources_executions.zip';members={}
    with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for directory in (old,base):
            for path in sorted(directory.rglob('*')):
                if path.is_file():
                    rel=str(path.relative_to(ROOT));members[rel]=sha(path);z.write(path,rel)
    assert archive.stat().st_size<90*1024**2
    with zipfile.ZipFile(archive) as z:
        assert sorted(z.namelist())==sorted(members)
        for name,digest in members.items():assert hashlib.sha256(z.read(name)).hexdigest()==digest
    audit=dict(schema='C09_PRODUCTION_REFERENCE_ARCHIVE_v1',passed=True,reference_posteriors=13,
        primary_and_W1_passed=13,new_likelihood_values=charged,prior_failed_attempt_values=3,
        cumulative_C09=summary['cumulative_C09'],maxima=maxima,CPU_completed=summary['CPU'],
        CPU_failed_attempt=failure['CPU'],archive_sha256=sha(archive),archive_bytes=archive.stat().st_size,
        dependencies_sha256=bindings,archive_members_sha256=members,
        scope='Refined omitted-monopole datum49 and extra log cutoffs0.0001/0.01 on core-U data0/31 for A0, full-variable B_CN and B_G. Representative checks, not all1280 reweighted posteriors or SBC.',C09_complete=False)
    (out/'audit.json').write_text(json.dumps(audit,indent=2,allow_nan=False)+'\n')
    print(json.dumps({k:v for k,v in audit.items() if k not in ('dependencies_sha256','archive_members_sha256')}))


if __name__=='__main__':main()
