#!/usr/bin/env python3
"""Render already computed C07 summaries as LaTeX, with explicit TOY handling.

No likelihood or statistical test is executed. The full JSON remains the
authority; tables retain numerical sensitivity and do not certify calibration.
"""
from pathlib import Path
import argparse,hashlib,json,math

MODELS=['A0_CN','A_CN','B_CN','A_G','B_G']
PARAMETERS=['u','log10_Agw','gamma_gw','log10_Ar','log10_EFAC']
SCOPE='CONTINUOUS_PRIOR_PREDICTIVE_SBC_WITH_NUMERICAL_SENSITIVITY'
TOY='TOY64_ANALYTIC_PIPELINE_VALIDATION_NOT_PTA'


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def require(condition,message):
    if not condition:raise ValueError(message)
def count(x,n):
    require(type(x) is int and 0<=x<=n,'Integer count out of range.')
    return str(x)
def number(x,*,probability=False):
    require(type(x) in (float,int) and math.isfinite(x),'Finite real table value required.')
    require(not probability or 0<=x<=1,'Probability outside support.')
    if x==0:return '0'
    if x==1:return '1'
    if abs(x)<.001:
        mantissa,power=f'{x:.2e}'.split('e')
        return mantissa.replace('.','{,}')+r'\times10^{'+str(int(power))+'}'
    return f'{x:.3f}'.replace('.','{,}')
def interval(x,*,probability=False):
    require(isinstance(x,list) and len(x)==2 and x[0]<=x[1],'Ordered interval required.')
    return '['+number(x[0],probability=probability)+';'+number(x[1],probability=probability)+']'
def model(name):
    require(name in MODELS,'Unknown scientific model.')
    return name.replace('_',r'\_')


def load_summary(path,arrays,*,toy64=False):
    r=json.loads(Path(path).read_text());n=64 if toy64 else 500
    require(r.get('scope')==(TOY if toy64 else SCOPE),'Use explicit --toy64 for TOY data; production requires completed500 summary.')
    require(r.get('models')==MODELS and r.get('parameters')==PARAMETERS and r.get('simulations_per_model')==n and r.get('all_simulations_retained') is True,'Complete model/parameter/count contract required.')
    require(r.get('arrays_sha256')==sha(arrays),'Summary/arrays hash differs.')
    require(r.get('quantile_horizontal_precision_not_certified_by_cdf_mcse') is True and r.get('nonrejection_does_not_prove_correctness') is True,'Scientific limitations must be preserved.')
    tests=r['tests'];require(len(tests)==155 and len(r['paired_central90'])==15,'Frozen test inventories155/15 required.')
    require([x['model'] for x in r['model_summary']]==MODELS,'Model summaries must retain all five models in order.')
    inventory={}
    for t in tests:
        key=(t['method'],t['target'],t['diagnostic'])
        require(key not in inventory and t['method'] in MODELS,'Duplicate/unplanned test.')
        group='correct' if t['method'] in ['A0_CN','A_G','B_G'] else 'approximate'
        require(t['group']==group and t['family_size']==(93 if group=='correct' else 62),'Hypothesis family changed.')
        require(t['nominal']['n']==n and t['sensitivity']['n']==n,'Test denominator changed.')
        inventory[key]=t
    return r,n,inventory


def table(caption,label,columns,header,rows,note,*,toy64):
    prefix='Controle TOY de 64 dados, sem resultados PTA. ' if toy64 else ''
    return '\n'.join([r'\begin{table}[htbp]',r'\centering',r'\caption{'+prefix+caption+'}',
        r'\label{tab:c07-'+label+('TOY' if toy64 else '')+'}',r'\begingroup\small\setlength{\tabcolsep}{4pt}',
        r'\begin{tabular}{@{}'+columns+r'@{}}',r'\toprule',header+r' \\',r'\midrule',
        *[' & '.join(row)+r' \\' for row in rows],r'\bottomrule',r'\end{tabular}',r'\endgroup',
        r'\par\smallskip\begin{minipage}{0.96\textwidth}\footnotesize '+note+r'\end{minipage}',r'\end{table}',''])


def render(path,arrays,output,*,toy64=False):
    r,n,tests=load_summary(path,arrays,toy64=toy64)
    require(not output.exists(),'Output must be new; preserve rendered tables.')
    output.mkdir(parents=True)
    parts=[];data_rows={}
    rows=[]
    for s in r['model_summary']:
        counts=s['functions_resolved_by_parameter'];require(len(counts)==6,'Six PIT coordinates required.')
        rows.append([model(s['model']),*[count(c,n) for c in counts],count(s['simulations_with_all_six_resolved'],n)])
    data_rows['resolution']=rows
    parts.append(table(f'Resolução numérica dos PITs: número de funções resolvidas entre os {n} dados de cada modelo.',
        'resolucao-producao','lrrrrrrr',r'Modelo & $u$ & $\log A$ & $\gamma$ & $\log A_r$ & $\log E$ & $\log L$ & Todas',rows,
        r'As colunas seguem os cinco parâmetros e a log-verossimilhança na verdade. Cada função é avaliada pelos seus próprios diagnósticos; funções não resolvidas conservam o intervalo $[0,1]$. A última coluna exige os seis PITs resolvidos na mesma realização e não aprova todos os vinte quantis.',toy64=toy64))
    rows=[]
    for s in r['model_summary']:
        selected=[t for t in r['tests'] if t['method']==s['model']];require(len(selected)==31,'Thirty-one tests per model required.')
        nominal=sum(t['nominal_reject'] for t in selected);robust=sum(t['rejection_robust_to_sensitivity'] for t in selected)
        possible=sum(t['rejection_not_excluded_by_sensitivity'] for t in selected)
        require(nominal==s['nominal_rejections'] and robust==s['robust_rejections'],'Rejection summary differs from test inventory.')
        rows.append([model(s['model']),str(selected[0]['family_size']),count(nominal,31),count(robust,31),count(possible,31)])
    data_rows['tests']=rows
    parts.append(table(r'Contagem de rejeições entre os 31 testes de cada modelo, com ajuste de Holm a 5\%.',
        'testes-producao','lrrrr','Modelo & Família & Nominais & Robustas & Possíveis',rows,
        r'As famílias de 93 e 62 hipóteses são separadas. Uma rejeição robusta persiste para todos os PITs dos envelopes numéricos; uma rejeição possível não é excluída por esses envelopes. As contagens são testes dependentes, não descobertas independentes. Não rejeitar não demonstra correção.',toy64=toy64))
    rows=[]
    for name in MODELS:
        t=tests[name,'u','PIT']
        rows.append([model(name),'$'+number(t['nominal']['statistic'])+'$',
            '$'+number(t['nominal_holm_pvalue'],probability=True)+'$',
            '$'+interval(t['sensitivity_holm_pvalue_bounds'],probability=True)+'$',count(t['numerical_resolved'],n)])
    data_rows['mass_pit']=rows
    parts.append(table('Teste de Kolmogorov--Smirnov para o PIT da massa adimensional $u$.',
        'pit-massa','lrrrr',r'Modelo & $D_{\rm KS}$ & $p_{\rm Holm}$ & Faixa de $p_{\rm Holm}$ & Resolvidos',rows,
        r'O teste nominal condiciona-se aos PITs calculados. A faixa é uma análise de sensibilidade à margem $0{,}002+z\,\mathrm{MCSE}$ e aos intervalos $[0,1]$ das funções não resolvidas; não é um intervalo de confiança exato para o valor-$p$. A margem determinística é operacional, não uma garantia uniforme da integral.',toy64=toy64))
    rows=[]
    for diagnostic,label in [('below_q0.95',r'$\mathrm{PIT}_u\leq0{,}95$'),('central_90',r'$0{,}05\leq\mathrm{PIT}_u\leq0{,}95$')]:
        for name in MODELS:
            t=tests[name,'u',diagnostic];nom=t['nominal'];sens=t['sensitivity']
            rows.append([model(name),label,count(nom['covered'],n)+'/'+str(n),
                '$'+interval(nom['exact_interval'],probability=True)+'$',
                '$'+interval(sens['fraction_bounds'],probability=True)+'$'])
    data_rows['mass_coverage']=rows
    parts.append(table('Coberturas da massa sob a priori e sua sensibilidade numérica.',
        'cobertura-massa','llrrr',r'Modelo & Evento & Contagem & IC binomial 95\% & Fração possível',rows,
        r'O intervalo binomial de Clopper--Pearson é ponto a ponto e condiciona-se à contagem nominal; não é simultâneo entre modelos ou eventos. A última coluna representa a faixa de frações compatíveis com os PITs numéricos. As uniões de intervalos binomiais correspondentes estão no JSON completo. Eventos são avaliados diretamente pela CDF, sem supor erro horizontal nulo nos quantis.',toy64=toy64))
    tex='% Automatically rendered from a complete C07 summary; no new statistics.\n% Summary SHA256: '+sha(path)+'\n'+''.join(parts)
    (output/'tabelas.tex').write_text(tex)
    manifest=dict(status='RENDERED_EXISTING_SUMMARY_NO_NEW_STATISTICS',scope=r['scope'],simulations_per_model=n,
        summary_sha256=sha(path),arrays_sha256=sha(arrays),script_sha256=sha(__file__),
        tables_sha256=sha(output/'tabelas.tex'),display_rows=data_rows,
        scientific_validation_claimed=False)
    (output/'manifest.json').write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+'\n')
    return manifest


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--summary',type=Path,required=True)
    p.add_argument('--arrays',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--toy64',action='store_true');a=p.parse_args()
    print(json.dumps({k:v for k,v in render(a.summary,a.arrays,a.output,toy64=a.toy64).items() if k!='display_rows'}))
