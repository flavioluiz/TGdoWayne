#!/usr/bin/env python3
"""Read-only attribution per function of the already hash-verified mask failure."""
import time
START=time.process_time()
from pathlib import Path
import os,json,hashlib,io,resource
for name in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','VECLIB_MAXIMUM_THREADS'):os.environ[name]='1'
import numpy as np
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
source=HERE/'resolution500';inventory=json.loads((source/'hash_inventory.json').read_text())
original=json.loads((source/'review.json').read_text());mask=np.load(source/'independent_resolved.npy',allow_pickle=False)
assert original['status']=='PASS' and original['processed_targets']==2500
names=['high_CDF_precision','weight_guard','saturation_guard','logZ_replicates','logZ_refinement','own_replicates','own_refinement'];indices=[0,5,10,15,20,25]
counts=np.zeros((5,6,7),int);reconstructed=np.zeros_like(mask);bytes_read=0
for row in inventory:
    if time.process_time()-START>15:raise RuntimeError('Predeclared15s extension cap reached; no automatic continuation.')
    target=row['target'];m,d=divmod(target,500);p=ROOT/'tmp/c07_posterior500_v1/diagnostics'/f'diagnostic_target_{target:06d}.npz';blob=p.read_bytes();bytes_read+=len(blob)
    if hashlib.sha256(blob).hexdigest()!=row['npz_sha256']:raise RuntimeError('Previously audited compact changed.')
    with np.load(io.BytesIO(blob),allow_pickle=False) as f:
        a={key:f[key] for key in ('pit_precision_pass','weight_deletion_guard_by_level','saturated_weight','replication_specification','replication_pass','refinement_pass')}
    spec=a['replication_specification'];rep=a['replication_pass'];ref=a['refinement_pass']
    common=[bool(a['weight_deletion_guard_by_level'].all()),bool((a['saturated_weight']<=1e-12).all()),bool(rep[spec[:,1]==26].all()),bool(ref[6])]
    for j,index in enumerate(indices):
        passed=[bool(a['pit_precision_pass'][j]),*common,bool(rep[spec[:,1]==index].all()),bool(ref[j])]
        counts[m,j]+=~np.asarray(passed,bool);reconstructed[m,d,j]=all(passed)
if not np.array_equal(mask,reconstructed):raise RuntimeError('Cause decomposition differs from independently reconstructed mask.')
if dict(zip(names,map(int,counts.sum(axis=(0,1)))))!=original['unresolved_cause_occurrences']:raise RuntimeError('Cause totals changed.')
result=dict(status='PASS_CAUSE_ATTRIBUTION_FOR_VERIFIED_MASK',names=names,models=['A0_CN','A_CN','B_CN','A_G','B_G'],functions=['u','log10_Agw','gamma_gw','log10_Ar','log10_EFAC','logL_at_truth'],counts_model_function_cause=counts.tolist(),counts_function_cause=counts.sum(axis=0).tolist(),cause_occurrences_overlap=True,unresolved_unique_by_function=(~mask).sum(axis=(0,1)).tolist(),source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),input_mask_sha256=hashlib.sha256((source/'independent_resolved.npy').read_bytes()).hexdigest(),input_inventory_sha256=hashlib.sha256((source/'hash_inventory.json').read_bytes()).hexdigest(),process_cpu_seconds=time.process_time()-START,maximum_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,compact_bytes_read=bytes_read,raw_reads=0,ORF_evaluations=0,likelihood_evaluations=0)
p=source/'causes_by_function.json'
if p.exists():raise FileExistsError('Preserve cause attribution.')
p.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:result[k] for k in ('status','process_cpu_seconds','maximum_rss_bytes','unresolved_unique_by_function')}))
