"""Compare the regenerated tensorial truth responses and observations."""
import argparse,hashlib,json,shutil
from pathlib import Path
import numpy as np
p=argparse.ArgumentParser();p.add_argument('--clean-root',type=Path,required=True);a=p.parse_args()
R=Path(__file__).resolve().parents[1];clean=a.clean_root
old=clean/'results/C07/prior_predictive';new=clean/'tmp/c13_c07_generation_new'
ref=json.loads((old/'orf_construction.json').read_text());fresh=json.loads((new/'orf_construction.json').read_text())
assert fresh['status']==ref['status']=='COMPLETE'
assert fresh['config_sha256']==ref['config_sha256']
paths=[Path(r['path']) for r in ref['final_copied_nodes']]
assert set(paths)=={Path(r['path']) for r in fresh['final_copied_nodes']} and len(paths)==503
paths.append(Path('data.npz'));records=[];count=0;not_identical=0;maximum=0;metadata_records=0
for rel in paths:
    with np.load(old/rel,allow_pickle=False) as x,np.load(new/rel,allow_pickle=False) as y:
        assert set(x.files)==set(y.files)
        for key in x.files:
            u,v=x[key],y[key]
            if key=='record':
                def normalized(value):
                    if isinstance(value,dict):return {k.replace(str(R),'<ROOT>').replace(str(clean),'<ROOT>'):normalized(z) for k,z in value.items() if k!='seconds'}
                    if isinstance(value,list):return [normalized(z) for z in value]
                    if isinstance(value,str):return value.replace(str(R),'<ROOT>').replace(str(clean),'<ROOT>')
                    return value
                one,two=normalized(json.loads(str(u))),normalized(json.loads(str(v)))
                assert one==two,(str(rel),'scientific metadata differ')
                metadata_records+=1
                continue
            assert u.shape==v.shape and u.dtype==v.dtype
            if np.issubdtype(u.dtype,np.number):
                assert np.isfinite(u).all() and np.isfinite(v).all()
                error=float(np.max(abs(u-v))/max(1.,float(np.max(abs(u))))) if u.size else 0.
                assert error<=1e-12,(str(rel),key,error)
                maximum=max(maximum,error)
            else:assert np.array_equal(u,v)
            count+=1;not_identical+=not np.array_equal(u,v)
    records.append({'path':str(rel),'reference_sha256':hashlib.sha256((old/rel).read_bytes()).hexdigest(),'regenerated_sha256':hashlib.sha256((new/rel).read_bytes()).hexdigest()})
report={'passed':True,'truth_nodes':503,'prior_realizations':500,'npz_files':len(paths),'arrays':count,'arrays_not_bitwise_identical':not_identical,'maximum_scaled_absolute_error':maximum,'tolerance':1e-12,'metadata_records_equal_except_seconds_and_root_paths':metadata_records,'files':records,'scope':'Regenerated physical truth/anchor ORFs and all prior-predictive observations; not posterior inference.'}
out=R/'results/C13';(out/'c07_generation_comparison.json').write_text(json.dumps(report,indent=2)+'\n')
for name in ('orf','data'):shutil.copy2(clean/f'tmp/c13_c07_{name}_io.json',out/f'c07_{name}_io.json')
print(json.dumps({k:v for k,v in report.items() if k!='files'}))
