"""Make a new continuation source; preserve the executed original byte-for-byte."""
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
s=(ROOT/'tmp/c08_beta_table_v2/run_local_v2.py').read_text();imports=s[:s.index('def run():')];imports=imports.replace('from patch_curve import stitch','')
suffix=s[s.index('  direct=[]'):];suffix=suffix.replace("load_curve(out/f'curve_channel", "load_curve(CURVES/f'curve_channel")
suffix=suffix.replace("expected=dict(real=plan['cost']['planned_new_real_products'],angular=plan['cost']['planned_new_direct_angular_work'],logL=plan['cost']['planned_new_logL'])", "expected=json.loads((HERE/'preflight.json').read_text())['remaining_work']")
suffix=suffix.replace("status='C_BETA_V2_PASS_STATED_FINITE_TABLE_GATES_ONLY'", "status='C_BETA_V2_PASS_STATED_FINITE_TABLE_GATES_ONLY',technical_continuation_preserves_failed_attempt=True,previous_failed_execution_sha256=sha_file(V2/'results/failure.json')")
prefix='''def run():
 auth=json.loads((HERE/'execution_authorized.json').read_text());V2=ROOT/'tmp/c08_beta_table_v2';CURVES=V2/'results';plan=json.loads((V2/'preflight.json').read_text());identity=hashlib.sha256(canonical(auth).encode()).hexdigest();out=HERE/'results'
 if (out/'gate_request.json').exists():raise FileExistsError('No implicit resume/overwrite of gates')
 def verify():
  for p,h in auth['input_source_sha256'].items():
   if sha_file(ROOT/p)!=h:raise RuntimeError('Frozen input/source changed: '+p)
 verify();write_json(out/'gate_request.json',dict(identity=identity,authorization_sha256=sha_file(HERE/'execution_authorized.json'),authorization=auth,worker_files={str(p.relative_to(ROOT)):sha_file(p) for p in out.glob('oracle_k4_*.npz')}))
 baseline=auth['baseline'];caps=auth['cumulative_limits'];delta_limits={k:caps[k]-baseline[k] for k in caps};delta_limits['logL']=min(delta_limits['logL'],auth['maximum_additional_logL']);ledger=Ledger(out/'resource_delta_ledger.jsonl',delta_limits,identity)
 def totals():return {k:baseline[k]+ledger.totals[k] for k in baseline}
 def rss(phase):
  peak=int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
  if peak>auth['maximum_RSS_bytes']:raise MemoryError('Observed Darwin RSS ceiling exceeded at '+phase)
  return peak
 cfg=json.loads((OLD/'inputs/experiment.json').read_text());e=experiment(cfg);P=len(e['points']);phase=2*np.pi*e['f'][:,None]*e['distance_ly'][None]*YEAR;cos=np.clip(e['points']@e['points'].T,-1,1);start=time.perf_counter();stages={}
 try:
  stages['local_curves']=json.loads((CURVES/'local_curves.json').read_text());newu=np.array(plan['validation']['new_control_u']);neworacle=np.empty((72,4,P,P),complex);oraclereports=[]
  for k in range(1,5):
   if k<4:
    with np.load(CURVES/f'oracle_channel{k:02d}.npz',allow_pickle=False) as z:
     if not np.array_equal(z['u'],newu):raise RuntimeError('Reused oracle coordinates changed')
     co=z['Gamma_coarse'].copy();fi=z['Gamma_fine'].copy();r=json.loads(str(z['record']))
     if r['channel']!=k or r['identity']!=auth['previous_execution_identity']:raise RuntimeError('Reused oracle identity changed')
   else:
    arrays=[]
    for label in ['coarse','fine']:
     with np.load(out/f'oracle_k4_{label}.npz',allow_pickle=False) as z:
      r=json.loads(str(z['record']))
      if not np.array_equal(z['u'],newu) or r['identity']!=identity or r['channel']!=4 or r['resolution']!=label or r['orders']!=plan['rows'][3]['oracle_orders_'+label]:raise RuntimeError('Fresh worker identity mismatch')
      arrays.append(z['Gamma'].copy())
    co,fi=arrays
   matrices(co,72,P);matrices(fi,72,P);error=float(np.max(abs(co-fi)))
   if error>1e-8:raise RuntimeError('Oracle harmonic convergence gate failed')
   neworacle[:,k-1]=fi;oraclereports.append(dict(channel=k,error=error,reused_v2=(k<4)));del co,fi
  stages['new_oracles']=oraclereports;write_json(out/'new_oracles.json',oraclereports)
'''
with (HERE/'continuation_gates.py').open('x') as f:f.write(imports+prefix+suffix)
