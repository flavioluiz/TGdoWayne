"""Conservative array-memory workload estimate; not a resident-memory measurement."""
import json
from cubature import HERE
rows=[]
for order,ng,cases in [([12,12,12],27,1),([20,20,20],35,1),([32,32,32],47,1),([20,20,20],20,21),([32,20,12],12,21),([64,64,64],79,1)]:
    nb,na,_=order;n=3*na*ng;nmass=1 if nb==64 else 139
    # Allow20 simultaneous float64 arrays of the largest N×K×P shape,
    # plus64 N-vectors and all complex ORF matrices. These are allocations of
    # the numerical workload only; imported-library/runtime memory is separate.
    estimated=20*8*n*4*12+64*8*n+nmass*4*12*12*16
    rows.append(dict(order_b_a_gamma=order,actual_gamma_nodes=ng,mass_nodes=nmass,
                     numerator_plus_denominator_integrals=cases,
                     parameter_points=nmass*9*nb*na*ng*cases,
                     conservative_array_bytes=estimated,
                     estimate_under_128_MiB=estimated<128*1024**2))
out=dict(scope='Array-workload estimate only, not RSS measurement; points limited before execution by each script',
         maximum_array_estimate_bytes=max(r['conservative_array_bytes'] for r in rows),levels=rows)
(HERE/'results/resource_estimate.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
