from pathlib import Path
import hashlib,json,shutil,subprocess,sys,time
ROOT=Path.cwd();HERE=ROOT/'tmp/c07_generator_review';HERE.mkdir(exist_ok=True)
source_paths=[ROOT/'scripts/gerar_calibracao.py',ROOT/'configs/calibration/prior_predictive_500_v1.json']+list((ROOT/'src/inference').glob('*.py'))+list((ROOT/'src/pta').glob('*.py'))
snap=HERE/'executed_sources';snap.mkdir(exist_ok=True);source_hashes={}
for p in source_paths:
    rel=p.relative_to(ROOT);target=snap/rel;target.parent.mkdir(parents=True,exist_ok=True)
    data=p.read_bytes()
    if target.exists() and target.read_bytes()!=data:raise RuntimeError('Existing review source changed; preserve this execution.')
    if not target.exists():target.write_bytes(data)
    source_hashes[str(rel)]=hashlib.sha256(data).hexdigest()
(HERE/'source_manifest.json').write_text(json.dumps(source_hashes,indent=2)+'\n')
config=json.loads((ROOT/'configs/calibration/prior_predictive_500_v1.json').read_text())
config.update(status='temporary_toy_generator_review',scope='Four new truths; short distances test mechanics, not an observational PTA or SBC.',n_realizations=4,truth_seed=907081301,data_seed=907081302,distance_range_light_years=[.02,.06])
config['orf'].update(lmax_margin=32,nmu_margin=90,fine_lmax_addition=8,fine_nmu_addition=20,maximum_phase=1.,maximum_total_work_units=10_000_000,maximum_estimated_memory_bytes=8*1024**2)
config['generation_orf_budget'].update(maximum_estimated_numeric_memory_bytes=32*1024**2,maximum_total_real_multiplications=10_000_000,maximum_requested_nodes=8,batch_size=4,maximum_batch_real_multiplications=1_000_000)
configpath=HERE/'toy_config.json';configpath.write_text(json.dumps(config,indent=2)+'\n')
output=HERE/'toy_product';cache=HERE/'construction_cache';logs=HERE/'logs';logs.mkdir(exist_ok=True)
rows=[]
def run(action,*,out=output,expect=0,suffix=''):
    args=[str(ROOT/'.venv/bin/python'),str(ROOT/'scripts/gerar_calibracao.py'),action,'--config',str(configpath),'--output',str(out),'--construction-cache',str(cache)]
    start=time.perf_counter();result=subprocess.run(args,cwd=ROOT,text=True,capture_output=True)
    (logs/(action+suffix+'.log')).write_text(result.stdout+result.stderr)
    row=dict(action=action,suffix=suffix,command=args,returncode=result.returncode,seconds=time.perf_counter()-start,expected_returncode=expect)
    rows.append(row);print(json.dumps(row),flush=True)
    if (result.returncode==0)!=(expect==0):raise AssertionError(result.stdout+result.stderr)
    return result
for action in ['preflight','build-orfs','generate','verify']:run(action)
def files(directory):return {str(p.relative_to(directory)):hashlib.sha256(p.read_bytes()).hexdigest() for p in directory.rglob('*') if p.is_file()}
before=files(output)
run('generate',expect=1,suffix='_refuse_overwrite');run('build-orfs',expect=1,suffix='_refuse_overwrite')
assert files(output)==before
corrupt=HERE/'altered_manifest_product';shutil.copytree(output,corrupt)
p=corrupt/'orf_construction.json';doc=json.loads(p.read_text());doc['review_extra_metadata']='modified after generation without updating recorded construction hash';p.write_text(json.dumps(doc,indent=2)+'\n')
# Currently expected to PASS: diagnose whether the stored construction hash is checked.
result=run('verify',out=corrupt,suffix='_altered_construction_manifest')
unchanged=all(hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==h for path,h in source_hashes.items())
assert unchanged
summary=dict(scope='Four new toy truths only, not production500 or calibration',stages=rows,source_hashes_preserved=unchanged,output_files_preserved_after_refusals=files(output)==before,
             unexpected_acceptance_altered_construction_manifest=(result.returncode==0),source_sha256=source_hashes,original_product_sha256=before)
(HERE/'review_summary.json').write_text(json.dumps(summary,indent=2)+'\n')
