"""Check central synthesis values and the response semantics used in C12 prose.

This is a cross-check of published numerical products, not a fresh physical run
or an automated proof that every sentence of the manuscript is correct.
"""
from pathlib import Path
import hashlib,importlib.util,json,math
from collections import Counter
R=Path(__file__).resolve().parents[1]
inputs={};claims=[]
def read(relative):
 p=R/relative;inputs[relative]=hashlib.sha256(p.read_bytes()).hexdigest();return json.loads(p.read_text())
def check(name,value,expected,source):
 assert value==expected,(name,value,expected)
 claims.append(dict(name=name,value=value,source=source))
a=read('results/C11/statistical_audit.json')
check('C11 posterior targets',a['posterior_targets'],10728,'results/C11/statistical_audit.json')
for family,tests,reject,indeterminate in [('correct',42,0,3),('approximate',84,1,1)]:
 d=a['decisions'][family]
 for name,expected in [('tests',tests),('persistent',reject),('indeterminate',indeterminate)]:check('C11 '+family+' '+name,d[name],expected,'results/C11/statistical_audit.json')
for r,mean,se in zip(a['paired_information'],[.06211,.10631],[.00477,.00695]):
 check(r['population']+' rounded KL mean',round(r['mean_KL_difference_nats'],5),mean,'results/C11/statistical_audit.json')
 check(r['population']+' rounded KL MCSE',round(r['MCSE'],5),se,'results/C11/statistical_audit.json')
c=read('results/C10/population_synthesis/results.json')
check('C10 posterior targets',c['targets'],6344,'results/C10/population_synthesis/results.json')
counts=Counter((r['family'],r['decision']) for r in c['tests'])
check('C10 approximate persistent',counts['approximate','REJECT_FOR_ALL_INTERVAL_VALUES'],11,'results/C10/population_synthesis/results.json')
check('C10 correct indeterminate',counts['correct','INDETERMINATE'],1,'results/C10/population_synthesis/results.json')
c=read('results/C09/robustness_synthesis/audit.json')
for k,v in [('posteriors',25956),('paired_contrasts',39)]:check('C09 '+k,c[k],v,'results/C09/robustness_synthesis/audit.json')
c=read('results/C09/SBC_operational_events/results.json');check('C09 SBC family size',c['family_size'],126,'results/C09/SBC_operational_events/results.json')

c=read('results/C07/synthesis/summary.json')
check('C07 unresolved PITs',sum(sum(500-n for n in r['functions_resolved_by_parameter']) for r in c['model_summary']),243,'results/C07/synthesis/summary.json')
check('C07 approximate persistent',sum(r['rejection_robust_to_sensitivity'] for r in c['tests'] if r['group']=='approximate'),10,'results/C07/synthesis/summary.json')
check('C09 indeterminate SBC decisions',sum(r['decision']=='NUMERICALLY_INDETERMINATE' for r in read('results/C09/SBC_operational_events/results.json')['tests']),10,'results/C09/SBC_operational_events/results.json')
c=read('results/C09/production_mass_PIT/records.json');check('C09 unresolved mass PITs over all25956',sum(not r['mass_resolved'] for r in c),834,'results/C09/production_mass_PIT/records.json')
paths=['results/C09/events_direct_threshold/records.json','results/C09/events_distance_direct_threshold/records.json'];count=sum(sum(not r['finite_operational_gates_passed'] for r in read(p)) for p in paths);check('C09 unresolved logL events over all25956',count,2287,paths)

p=R/'tmp/c11_pilot16_candidate_v2/semantics.py';inputs[str(p.relative_to(R))]=hashlib.sha256(p.read_bytes()).hexdigest()
spec=importlib.util.spec_from_file_location('c11_semantics_audited',p);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
for u in (0.,.5,.995,1.):
 for channel in (1,2,8):
  assert math.isclose(module.beta(u,channel,'B'),math.sqrt((1-u/channel)*(1+u/channel)),abs_tol=1e-15)
  assert math.isclose(module.beta(u,channel,'C_beta'),math.sqrt((1-u)*(1+u)),abs_tol=1e-15)
  full=module.canonical_response(u,channel,'C_full');assert full['channel']==1 and full['u_hex']==u.hex() and full['law']=='B'
claims.append(dict(name='Response semantics',value='B beta_k; C_beta beta_1 with y_k; C_full B channel1 at same u',source='tmp/c11_pilot16_candidate_v2/semantics.py',cases=12))
for relative in ['article/manuscript.tex','latex/capitulos_dissertacao/10_aplicacao.tex']:
 text=(R/relative).read_text();assert 'frozen at unity' not in text and 'massless first-channel' not in text and 'fixa a velocidade relativa em um' not in text
 inputs[relative]=hashlib.sha256((R/relative).read_bytes()).hexdigest()
result=dict(passed=True,claims=claims,input_sha256=inputs,source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),scope=__doc__)
(R/'results/C12/narrative_audit.json').write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n')
print(json.dumps(dict(passed=True,central_claims=len(claims))))
