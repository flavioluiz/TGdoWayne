from harness import *
from inference.orf_backend import ExactNodeORF
from inference.orf_table_builder import read_validated_entry,token,matrix_digest
from time import perf_counter
import hashlib,shutil
cfg,e,data=load();here=Path(__file__).resolve().parent;out=here/'results';dest=here/'delivery';dest.mkdir(exist_ok=True);t=perf_counter();fine=out/'table_beta8193_local.npz';validation=json.loads((out/'dense_local_validation.json').read_text());assert validation['passes_tested_domain']
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
assert sha(fine)==validation['table_sha256'][str(fine)]
meta=ExactNodeORF(e,cfg['orf'],here/'orf_cache_dense');inventory=[]
with np.load(fine) as saved:
 nodes=saved['nodes'];matrices=saved['matrices']
 for u,g in zip(nodes,matrices):
  key=token(meta.signature,u);candidates=[here/'orf_cache_dense'/(key+'.npz'),here/'orf_cache_local_refinement'/(key+'.npz')];path=next(p for p in candidates if p.exists());got,record=read_validated_entry(path,signature=meta.signature,u=u,K=4,P=12,tolerance=cfg['orf']['maximum_matrix_abs_difference']);assert np.array_equal(g,got)
  inventory.append(dict(u=float(u),u_hex=float(u).hex(),cache_relative=str(path.relative_to(here)),file_sha256=sha(path),bytes=path.stat().st_size,Gamma_sha256=matrix_digest(g),coarse_fine_abs_error=record['maximum_coarse_fine_difference'],backend=record['construction_backend']['name']))
 numeric_hash=hashlib.sha256(nodes.tobytes()+matrices.tobytes()).hexdigest()
name='orf_table_pilot12x4.npz';shutil.copyfile(fine,dest/name)
records=['dense_preflight.json','dense_construction.json','dense_validation_protocol.json','dense_validation.json','local_refinement_plan.json','local_refinement_construction.json','dense_local_validation_protocol.json','dense_local_validation_construction.json','dense_local_validation.json','evenness_validation.json','evenness_direct_validation.json']
for name2 in records:shutil.copyfile(out/name2,dest/name2)
(dst:=dest/'cache_inventory.json').write_text(json.dumps(dict(nodes=len(nodes),scope='Local construction caches; do not require these files in Git. Every packaged matrix compared bit-for-bit against its validated cache row.',records=inventory),indent=2))
source_names=['build_dense.py','refine_dense_local.py','validate_dense.py','validate_dense_local.py','cubic_even.py','cubic.py','pointwise.py','linalg_batch.py','harness.py','package_table.py']
sources={}
for source in [here/p for p in source_names]+[ROOT/'src/inference'/p for p in ['model.py','orf_backend.py','orf_table_builder.py','orf_blas.py']]:
 rel=source.relative_to(ROOT);d=dest/'executed_sources'/rel;d.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,d);sources[str(rel)]=sha(source)
# Preserve the exact v1 constructor snapshot referenced by the dense request.
v1=here/'executed_sources/dense8193';shutil.copytree(v1,dest/'executed_sources/dense8193_v1',dirs_exist_ok=True)
manifest=dict(status='VALIDATED_IN_STATED_NUMERICAL_TEST_DOMAIN',artifact=name,file_sha256=sha(dest/name),bytes=(dest/name).stat().st_size,nodes=len(nodes),shape=list(matrices.shape),canonical_nodes_and_matrices_sha256=numeric_hash,physical_signature=meta.signature,config_file='configs/calibration/pilot_initial.json',config_sha256=sha(CONFIG),validation_data_file='results/C07/fixtures/pilot_data.npz',validation_data_sha256=sha(DATA),coordinate='minus beta_1 = -sqrt((1-u)(1+u)); prior remains uniform in u',interpolator='EvenThresholdCubicORF; cubic, not-a-knot at beta1=1 and zero derivative at beta1=0; PSD Bernstein controls, no eigenvalue clipping',minimum_Bernstein_eigenvalue=validation['tables']['8193']['minimum_Bernstein_eigenvalue'],fallback_intervals=[],validation_tolerance_abs_loglikelihood=.001,validation_report='dense_local_validation.json',validation_report_sha256=sha(dest/'dense_local_validation.json'),cache_inventory_file='cache_inventory.json',cache_inventory_sha256=sha(dst),sources_sha256=sources,seconds=perf_counter()-t,limits='Finite validation set at the frozen12-pulsar4-frequency experiment and rectangular priors; not a global analytic likelihood-error bound or authorization to reuse a different geometry.',historical_failed_tables_preserved=True)
(dest/'orf_table_manifest.json').write_text(json.dumps(manifest,indent=2));print(json.dumps({k:manifest[k] for k in ['status','nodes','bytes','file_sha256','seconds']},indent=2))
