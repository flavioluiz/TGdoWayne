"""Matched scalar versus batched timing and arithmetic checks."""
import time,json
import numpy as np
from bounded import HERE,CDFEvaluator,bounded_mass_batch,bounded_mass_integral,truncated_box
from cubature import diagnostic_cuts

e=CDFEvaluator((32,20,12),mass_count=129);cuts,_=diagnostic_cuts(e.cfg,e.data,14)
masses=np.array([0.,.25,.5,.75,.875,.9375,float(np.sqrt(1-.001**2)),1.]);Gs=np.stack([e.table.get(float(u)) for u in masses])
rows=[]
for index in [1,6,11,16]:
    c=cuts[index];box,lf=truncated_box(e.box,c['parameter'],c['value']);threshold=np.full(len(masses),e.logZ+np.log(1e-12)-np.log(e.maximum_nodes)-lf)
    before=time.perf_counter();scalar=[bounded_mass_integral(G,e.e,e.q,box,e.orders,log_point_cut=cut) for G,cut in zip(Gs,threshold)];ts=time.perf_counter()-before
    before=time.perf_counter();v,u,count=bounded_mass_batch(Gs,e.e,e.q,box,e.orders,log_point_cut=threshold);tb=time.perf_counter()-before
    err=float(np.max(abs(v-np.array([r[0] for r in scalar]))));bounderr=float(np.max(abs(u-np.array([r[1] for r in scalar]))))
    if err>2e-10 or bounderr>2e-10:raise AssertionError((index,err,bounderr))
    rows.append(dict(parameter=c['parameter'],log_integral_max_abs_error=err,log_omission_bound_max_abs_error=bounderr,scalar_seconds=ts,batch_seconds=tb,speedup=ts/tb))
out=dict(status='PASS',masses=masses.tolist(),rows=rows,
         scalar_seconds=sum(r['scalar_seconds'] for r in rows),batch_seconds=sum(r['batch_seconds'] for r in rows),
         maximum_log_integral_error=max(r['log_integral_max_abs_error'] for r in rows))
(HERE/'results/batch_validation.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
