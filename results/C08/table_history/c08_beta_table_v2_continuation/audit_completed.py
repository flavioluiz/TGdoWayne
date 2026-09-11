"""Post-execution independent cache/identity audit; no ORF integral or logL calls."""
from pathlib import Path
import hashlib,json,time,resource,sys
import numpy as np
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];OLD=ROOT/'tmp/c08_beta_table';V2=ROOT/'tmp/c08_beta_table_v2';sys.path.insert(0,str(OLD));from beta_builder import sha_file,write_json
start=time.perf_counter();a=json.loads((HERE/'execution_authorized.json').read_text());r=json.loads((HERE/'results/final_report.json').read_text())
for p,h in a['input_source_sha256'].items():
 if sha_file(ROOT/p)!=h:raise AssertionError('Frozen file changed '+p)
ledgers=[]
for folder in [OLD,V2,HERE]:
 file=folder/'results'/('resource_ledger.jsonl' if folder==OLD else 'resource_delta_ledger.jsonl');entries=[json.loads(x) for x in file.read_text().splitlines()];s={k:sum(v['amount'] for v in entries if v['kind']==k) for k in ['real','angular','logL']};ledgers.append(s)
assert {k:sum(v[k] for v in ledgers) for k in ledgers[0]}==r['resource_cumulative']
llrows=[]
for p in sorted((HERE/'results/likelihood_cache').glob('*.npz')):
 with np.load(p,allow_pickle=False) as z:
  lc,lf,lo=(z[k] for k in ['logL_coarse','logL_fine','logL_oracle']);assert all(v.shape==(64,32) and np.isfinite(v).all() for v in [lc,lf,lo]);llrows.append(dict(file=p.name,u=float(z['u']),coarse_fine=float(np.max(abs(lc-lf))),fine_oracle=float(np.max(abs(lf-lo)))))
assert len(llrows)==215
assert max(x['coarse_fine'] for x in llrows)==r['stages']['likelihood']['maximum_coarse_fine']
assert max(x['fine_oracle'] for x in llrows)==r['stages']['likelihood']['maximum_fine_oracle']
# Tiled independent coefficient substitution in the exported common intervals.
path=HERE/'results/C_beta_common_table.npz';assert sha_file(path)==r['table_sha256']
with np.load(path,allow_pickle=False) as z:
 n=z['nodes'];c=z['coeff'];m=z['matrices'];assert str(z['coordinate'])=='minus_beta' and str(z['construction_identity'])==r['identity']
x=-np.sqrt((1-n)*(1+n));reports=[]
for k in range(4):
 with np.load(V2/f'results/curve_channel{k+1:02d}.npz',allow_pickle=False) as z:on=z['nodes'];oc=z['coeff'];og=z['matrices']
 with np.load(OLD/f'results/gates/curve_channel{k+1:02d}.npz',allow_pickle=False) as z:pn=z['nodes'];pc=z['coeff'];pg=z['matrices']
 assert np.array_equal(og[np.searchsorted(on,pn)],pg)
 join=len(pc) if k==0 else int(np.searchsorted(pn,np.sqrt((1-1/64)*(1+1/64))))
 assert np.array_equal(oc[:join],pc[:join]);ox=-np.sqrt((1-on)*(1+on));error=0.;matrixerror=0.
 for first in range(0,len(c),128):
  last=min(first+128,len(c));j=np.minimum(np.searchsorted(ox,x[first:last],side='right')-1,len(ox)-2);width=ox[j+1]-ox[j];aa=((x[first:last]-ox[j])/width)[:,None,None,None];bb=((x[first+1:last+1]-x[first:last])/width)[:,None,None,None];cc=oc[j];expected=np.empty_like(cc)
  expected[:,0]=cc[:,0]+aa*(cc[:,1]+aa*(cc[:,2]+aa*cc[:,3]));expected[:,1]=bb*(cc[:,1]+aa*(2*cc[:,2]+3*aa*cc[:,3]));expected[:,2]=bb*bb*(cc[:,2]+3*aa*cc[:,3]);expected[:,3]=bb**3*cc[:,3]
  error=max(error,float(np.max(abs(expected-c[first:last,:,k:k+1]))));matrixerror=max(matrixerror,float(np.max(abs(expected[:,0]-m[first:last,k:k+1]))))
 assert error<1e-14 and matrixerror<1e-14
 reports.append(dict(channel=k+1,old_nodes_and_external_coefficients_bitexact=True,common_coeff_independent_algebra_error=error,common_left_matrix_error=matrixerror))
 del on,oc,og,pn,pc,pg
worstcf=max(llrows,key=lambda q:q['coarse_fine']);worstfo=max(llrows,key=lambda q:q['fine_oracle'])
report=dict(status='CACHE_IDENTITY_AND_ALGEBRA_AUDIT_PASS',frozen_files=len(a['input_source_sha256']),three_ledgers=ledgers,cumulative=r['resource_cumulative'],checked_LL_cache_files=len(llrows),no_ORF_or_logL_evaluations=True,worst_coarse_fine=worstcf,worst_fine_oracle=worstfo,common_nodes=len(n),channel_reports=reports,RSS_peak_bytes=int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss),seconds=time.perf_counter()-start,source_sha256=sha_file(__file__),table_sha256=sha_file(path))
write_json(HERE/'audit_completed.json',report);print(json.dumps(report,indent=2))
