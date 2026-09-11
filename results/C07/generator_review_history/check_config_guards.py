from pathlib import Path
import copy,hashlib,json,subprocess
ROOT=Path.cwd();HERE=ROOT/'tmp/c07_generator_review';dest=HERE/'guard_review';dest.mkdir(exist_ok=True)
cfg=json.loads((HERE/'toy_config.json').read_text());rows=[]
for name,changes,valid in [('positive',{},True),('nonconsecutive',{'positive_channels':[1,2,4,8]},False),('three_channels',{'positive_channels':[1,2,3]},False),('different_red_slope',{'fixed_red_slope':4.5},False)]:
    case=copy.deepcopy(cfg);case.update(changes);path=dest/(name+'.json');path.write_text(json.dumps(case,indent=2)+'\n')
    cmd=[str(ROOT/'.venv/bin/python'),str(ROOT/'scripts/gerar_calibracao.py'),'preflight','--config',str(path),'--output',str(dest/(name+'_product'))]
    result=subprocess.run(cmd,cwd=ROOT,text=True,capture_output=True);(dest/(name+'.log')).write_text(result.stdout+result.stderr)
    assert (result.returncode==0)==valid
    assert not (dest/(name+'_product')).exists()
    rows.append(dict(name=name,returncode=result.returncode,expected_success=valid,no_output_created=True))
source={}
for rel in ['src/inference/data_generation.py','scripts/gerar_calibracao.py']:
    p=ROOT/rel;data=p.read_bytes();target=dest/'sources'/rel;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data);source[rel]=hashlib.sha256(data).hexdigest()
out={'status':'PASS','rows':rows,'source_sha256':source};(dest/'summary.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
