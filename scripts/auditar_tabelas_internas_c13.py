"""Bind every inline numeric table to archived numerical values and displayed precision.

This checks transcription and rounding, not a new physical inference.
"""
from pathlib import Path
import csv,hashlib,json,re,zipfile
R=Path(__file__).resolve().parents[1];inputs={};checks=[]
def read(name):
 p=R/name;inputs[name]=hashlib.sha256(p.read_bytes()).hexdigest();return json.loads(p.read_text())
def csvread(name):
 p=R/name;inputs[name]=hashlib.sha256(p.read_bytes()).hexdigest();return list(csv.DictReader(p.open()))
def table(file,index):
 p=R/'latex/capitulos_dissertacao'/file;inputs[str(p.relative_to(R))]=hashlib.sha256(p.read_bytes()).hexdigest()
 return re.findall(r'\\begin\{table\}.*?\\end\{table\}',p.read_text(),re.S)[index]
def bind(file,index,expected,upper_rows=(),lower_rows=()):
 text=table(file,index); rows=[]; header=True
 for line in text.splitlines():
  if '&' not in line:continue
  if header:header=False;continue
  cells=line.split('&')[1:];values=[]
  for cell in cells:
   cell=cell.replace(r'\,','').replace('{,}',',')
   cell=re.sub(r'\\times10\^\{(-?\d+)\}',r'e\1',cell)
   cell=cell.replace('{','').replace('}','')
   tokens=re.findall(r'(?<![A-Za-z_])[-+]?\d+(?:,\d+)?(?:e-?\d+)?',cell)
   values += tokens
  if values:rows.append(values)
 assert len(rows)==len(expected),(file,index,len(rows),len(expected))
 for ri,(actual,want) in enumerate(zip(rows,expected)):
  assert len(actual)==len(want),(file,index,ri,actual,want)
  for ci,(token,value) in enumerate(zip(actual,want)):
   val=float(token.replace(',','.'));mantissa,_,exp=token.partition('e');digits=len(mantissa.split(',')[1]) if ',' in mantissa else 0
   quantum=10.**(int(exp or 0)-digits)
   conservative=(ri,ci) in upper_rows
   lower=(ri,ci) in lower_rows
   ok=(val>=value-1e-15*max(abs(value),1e-12) and val-value<=quantum*1.001) if conservative else abs(val-value)<=.500001*quantum
   if lower:ok=val<=value+1e-15*max(abs(value),1e-12) and value-val<=quantum*1.001
   checks.append(dict(chapter=file,table_index=index,row=ri,column=ci,displayed=token,source_value=value,quantum=quantum,conservative_upper=conservative,conservative_lower=lower,passed=ok))
   assert ok,checks[-1]
q=read('results/C07/reference/quantiles/posterior_reference.json');bind('06_validacao.tex',0,q['quantiles_original'])
d=read('results/C07/orf_interpolation/dense_local_validation.json');t=read('results/C07/truth_interpolation500/validation.json')
rows=[[d['comparisons'][k]['points'],d['comparisons'][k]['maximum_abs_loglikelihood_difference']] for k in ['posterior','prior','new_coarse_nodes','offgrid']]
rows += [[d['comparisons']['offgrid']['points'],d['tables']['8193']['maximum_offgrid_abs_loglikelihood_error']],[t['protocol']['targets'],t['maximum_absolute_difference']]]
bind('06_validacao.tex',1,rows,upper_rows={(5,1)})
pairs=[('B','C_beta'),('B','C_full'),('C_beta','C_full')]
c=csvread('results/C08/maps/window/summary/envelopes.csv');bind('07_resultados_compressao.tex',0,[[max(float(r[k+'_maximum']) for r in c if (r['p'],r['q'])==pair) for k in ['KL_p_to_q','mean_shift_metric_p_squared','covariance_difference_metric_q']] for pair in pairs])
c=csvread('results/C08/maps/g2_weak/summary/g2_envelopes.csv');bind('07_resultados_compressao.tex',1,[[max(float(r[k+'_max']) for r in c if (r['p'],r['q'])==pair) for k in ['KL','mean_squared_in_p','covariance_in_q']] for pair in pairs])
d=read('results/C08/c07_descriptive/results/summary.json');rows=[]
for ci in range(3):
 selected=[r for r in d['all500'] if r['contrast_index']==ci and r['parameter']=='u']
 q=next(r for r in selected if r['quantity']=='quantile' and r['probability']==.95);w=next(r for r in selected if r['quantity']=='central90_width');rows.append([q['mean'],q['median'],w['mean'],w['median']])
bind('07_resultados_compressao.tex',2,rows)
# Recover the model-specific control counts from the SHA-bound assessment records.
d=read('results/C08/paired32/ROOT_finite_review.json');need={str(Path(r['path']).relative_to(R)):r['sha256'] for r in d['assessment_records'] if Path(r['path']).name.startswith('main_')};counts={m:[0,0] for m in ['A0_CN','A_CN','B_CN','A_G','B_G','C_beta_CN','C_beta_G','C_full_CN','C_full_G']}
for archive in sorted((R/'results/C08/campaign_archives/offline_v1').glob('*.zip')):
 with zipfile.ZipFile(archive) as z:
  for name in set(z.namelist())&need.keys():
   raw=z.read(name)
   if hashlib.sha256(raw).hexdigest()!=need[name]:continue
   r=json.loads(raw);model=Path(name).stem.removeprefix('main_').rsplit('_',1)[0];status=r['status'];assert status in ['FINITE_RULES_PASS_AWAITING_REVIEW','UNRESOLVED_FINITE_CONTROLS'],status
   counts[model][status=='UNRESOLVED_FINITE_CONTROLS']+=1;del need[name]
assert not need,need
assert all(sum(x)==32 for x in counts.values());bind('07_resultados_compressao.tex',3,list(counts.values())+[[sum(v[i] for v in counts.values()) for i in range(2)]])
d=read('results/C08/paired32/summary.json')['bootstrap'];bind('07_resultados_compressao.tex',4,[[x,*d['point_bootstrap_interval'][i],*d['bootstrap_numeric_envelope'][i]] for i,x in enumerate(d['point_mean'])])
d=read('results/C08/paired32/ROOT_replay_review.json');bind('07_resultados_compressao.tex',5,[[r['KL_A_G_to_B_G'],r['MCSE']] for r in d['optional_pairs']])
d=read('results/C09/robustness_synthesis/paired_contrasts.json');bind('08_producao_c09.tex',0,[[[.25,1,.25,1][i],*next(r['mean_delta_q95'] for r in d if r['label']==f'contaminant_{i}_A0_CN_omitted_minus_included')] for i in range(4)])
d=read('results/C11/statistical_audit.json')['decisions'];bind('10_aplicacao.tex',0,[[d[k][n] for n in ['tests','persistent','indeterminate']] for k in ['correct','approximate']])
d=read('results/C13/conditional_contrasts/results.json')['contrasts']
bind('10b_contrastes_condicionais.tex',0,[[r['mean'],*r['mean_numerical_interval'],r['maximum_numerical_radius']] for r in d],upper_rows={(i,j) for i in range(4) for j in (2,3)},lower_rows={(i,1) for i in range(4)})
result=dict(scope='Eleven inline numeric tables: cell transcription and rounding against retained numerical sources. Not a physical replay.',tables=11,cells=len(checks),passed=all(c['passed'] for c in checks),inputs_sha256=inputs,checks=checks)
(R/'results/C13/inline_tables_audit.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps(dict(tables=11,cells=len(checks),passed=result['passed'])))
