"""Fresh process: export explicit C_full coefficients, no model-density bank."""
import os
os.environ['VECLIB_MAXIMUM_THREADS']='1'
from pathlib import Path
import sys,json,hashlib,time,resource
import numpy as np
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];OLD=ROOT/'tmp/c08_beta_table';sys.path.insert(0,str(OLD))
from beta_builder import sha_file,canonical,write_json,write_npz
from curve_algebra_v2 import bernstein_eigenvalues

def run():
 a=json.loads((HERE/'execution_authorized.json').read_text());identity=hashlib.sha256(canonical(a).encode()).hexdigest();out=HERE/'results';r=json.loads((out/'gate_report.json').read_text());start=time.perf_counter()
 if r['identity']!=identity or r['status']!='C_FULL_GATES_PASS_PENDING_EXPORT' or r['resource_totals']!={'real':0,'angular':0,'logL':1322688}:raise RuntimeError('Own C_full gates required')
 for p,h in a['input_source_sha256'].items():
  if sha_file(ROOT/p)!=h:raise RuntimeError('Frozen input changed: '+p)
 def rss():
  peak=int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
  if peak>a['maximum_RSS_bytes']:raise MemoryError('RSS ceiling exceeded')
  return peak
 try:
  with np.load(OLD/'first_curve_root.npz',allow_pickle=False) as z:n=z['nodes'].copy();g=z['matrices'].copy();c=z['coeff'].copy()
  estimated=n.nbytes+g.nbytes+c.nbytes+4*g.nbytes+4*c.nbytes+64*1024**2
  if estimated>a['maximum_numeric_bytes']:raise MemoryError('Numeric export estimate exceeded')
  gg=np.repeat(g,4,axis=1);cc=np.repeat(c,4,axis=2);rss()
  if not all(np.array_equal(gg[:,k:k+1],g) and np.array_equal(cc[:,:,k:k+1],c) for k in range(4)):raise RuntimeError('Expansion is not bit exact')
  checks=bernstein_eigenvalues(cc);rss();dest=out/'C_full_table.npz';write_npz(dest,nodes=n,matrices=gg,coeff=cc,coordinate=np.array('minus_beta'),response=np.array('C_full: first-frequency physical ORF repeated; channel spectra and noise unchanged'),construction_identity=np.array(identity));peak=rss()
  report=dict(status='C_FULL_PASS_STATED_FINITE_TABLE_GATES_ONLY',scientific_variant='C_full',identity=identity,table_sha256=sha_file(dest),gate_report_sha256=sha_file(out/'gate_report.json'),authorization_sha256=sha_file(HERE/'execution_authorized.json'),nodes=len(n),channels=4,first_curve_repeated_bitexact=True,source_coefficients_used_without_respline=True,checks=checks,resource_totals=r['resource_totals'],export_seconds=time.perf_counter()-start,export_RSS_peak_bytes=peak,export_numeric_estimate_bytes=estimated,maximum_worker_RSS_bytes=max(peak,r['RSS_peak_bytes']),no_new_quadratures=True,no_posterior_or_native_bank=True,finite_checks_not_uniform_proof=True);write_json(out/'final_report.json',report);print(json.dumps(report),flush=True)
 except Exception as exc:
  write_json(out/'failure_export.json',dict(status='FAILED_NO_AUTOMATIC_RETRY',identity=identity,type=type(exc).__name__,message=str(exc),RSS_peak_bytes=int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss),seconds=time.perf_counter()-start));raise
if __name__=='__main__':run()
