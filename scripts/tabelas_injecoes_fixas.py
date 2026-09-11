#!/usr/bin/env python3
"""Display completed fixed96 summaries; no new posterior or statistical test."""
from pathlib import Path
import argparse,json
from tabelas_calibracao import sha,require,count,number,interval

SCENARIOS=['mass_zero_signal_present','near_kinematic_edge','no_gravitational_signal']
LABELS=[r'$u=0$, com GW',r'$u=0{,}995$, com GW','Sem GW']
PARAMETERS=['u','log10_Agw','gamma_gw','log10_Ar','log10_EFAC','logL_at_truth']
SCOPE='FIXED96_CONDITIONAL_STRESS_SUMMARY_NOT_SBC'
TOY='TOY_FIXED96_SYNTHESIS_EXAMPLE_NO_PTA_POSTERIORS'


def table(caption,label,columns,header,rows,note,*,toy):
    prefix='Controle TOY, sem resultados PTA. ' if toy else ''
    return '\n'.join([r'\begin{table}[htbp]',r'\centering',r'\caption{'+prefix+caption+'}',
        r'\label{tab:c07-fixed-'+label+('TOY' if toy else '')+'}',
        r'\begingroup\small\setlength{\tabcolsep}{4pt}',r'\begin{tabular}{@{}'+columns+r'@{}}',
        r'\toprule',header+r' \\',r'\midrule',*[' & '.join(row)+r' \\' for row in rows],
        r'\bottomrule',r'\end{tabular}',r'\endgroup',
        r'\par\smallskip\begin{minipage}{0.96\textwidth}\footnotesize '+note+r'\end{minipage}',
        r'\end{table}',''])


def render(summary,arrays,output,*,toy=False):
    r=json.loads(summary.read_text())
    require(r.get('scope')==(TOY if toy else SCOPE),'Only a complete fixed96 summary or explicitly labelled TOY is accepted.')
    require(r.get('population_targets')==96 and r.get('models')==['A0_CN'],'Fixed96/A0 model inventory changed.')
    for name in ['all_ids_retained','no_KS_or_uniformity_test','pointwise_CP_only_no_familywise_claim',
                 'no_Bayes_factors','numerical_failures_do_not_trigger_target_selection']:
        require(r.get(name) is True,'Missing fixed-scenario limitation: '+name)
    if not toy:
        require(arrays is not None and r.get('arrays_sha256')==sha(arrays),'Production requires the matching synthesized arrays.')
    elif arrays is not None:
        require(r.get('arrays_sha256')==sha(arrays),'Supplied TOY arrays must also match the summary.')
    require([s['id'] for s in r['scenarios']]==SCENARIOS,'Three frozen scenarios required.')
    for i,s in enumerate(r['scenarios']):
        require(s['n']==32 and s['targets']==list(range(32*i,32*(i+1))),'Keep every fixed target ID.')
    functions={(f['scenario'],f['parameter']):f for f in r['functions']}
    quantiles={(q['scenario'],q['parameter']):q for q in r['quantiles']}
    require(len(r['functions'])==len(functions)==18 and set(functions)=={(s,p) for s in SCENARIOS for p in PARAMETERS},'Six function slots per scenario required.')
    require(len(r['quantiles'])==len(quantiles)==15 and set(quantiles)=={(s,p) for s in SCENARIOS for p in PARAMETERS[:5]},'Keep all15 quantile rows.')
    parts=[];display={};rows=[]
    for i,s in enumerate(SCENARIOS):
        row=[LABELS[i]]
        for p in PARAMETERS:
            f=functions[s,p];applicable=i!=2 or p in ['log10_Ar','log10_EFAC']
            require(f['applicable'] is applicable,'Undefined GW truth must remain masked.')
            if not applicable:
                row.append('---');continue
            require(f['n']==32 and f['target_ids']==list(range(32*i,32*(i+1))),'Function target IDs changed.')
            structural=32 if i==0 and p=='u' else 0
            require(f['structural_count']==structural,'Structural mass-zero status changed.')
            row.append(count(f['resolved_count'],32)+(r'$^\ast$' if structural else ''))
        rows.append(row)
    display['resolution']=rows
    parts.append(table('Funções resolvidas nos três cenários fixos: 32 dados A0 em cada cenário.',
        'resolucao','lrrrrrr',r'Cenário & $u$ & $\log A$ & $\gamma$ & $\log A_r$ & $\log E$ & $\log L$',rows,
        r'O asterisco indica $F_u(0)=0$ estrutural, sem integração numérica. Traços indicam ausência de verdade geradora definida: sem GW não há massa, amplitude ou inclinação do sinal a recuperar. As duas funções de ruído permanecem aplicáveis. Nenhum dado é removido.',toy=toy))
    rows=[]
    for i,p,plabel in [(0,'u',r'$u$'),(1,'u',r'$u$'),(2,'log10_Ar',r'$\log A_r$'),(2,'log10_EFAC',r'$\log E$')]:
        f=functions[SCENARIOS[i],p]
        for name,event in [('upper90',r'$F\leq0{,}90$'),('central90',r'$0{,}05\leq F\leq0{,}95$')]:
            c=f[name];require(c['n']==32 and c['no_test_of_universal_nominal_coverage'] is True,'No uniformity/null-coverage test is permitted here.')
            certain,possible=c['certainly_covered'],c['possibly_covered']
            count(certain,32);count(possible,32)
            require(certain<=possible and c['coverage_fraction_sensitivity']==[certain/32,possible/32],'Coverage sensitivity count/range mismatch.')
            rows.append([LABELS[i],plabel,event,count(c['calculated_count'],32)+'/32',
                '$'+interval(c['pointwise_cp95'],probability=True)+'$',
                '$'+interval(c['coverage_fraction_sensitivity'],probability=True)+'$'])
    display['coverage']=rows
    parts.append(table('Coberturas condicionais selecionadas nos cenários fixos.',
        'coberturas','lllr rr',r'Cenário & Par. & Evento & Cont. & IC 95\% & Faixa',rows,
        r'$F$ é a CDF posterior na verdade. Os ICs de Clopper--Pearson são ponto a ponto, condicionados à contagem calculada; as faixas usam a sensibilidade numérica operacional e $[0,1]$ para funções não resolvidas. Em $u=0$, as coberturas de $[0,U_{90}]$ e do intervalo central são estruturalmente 1 e 0. Não se exige cobertura nominal de 90\% para toda verdade fixa e não se executa SBC nestes cenários.',toy=toy))
    rows=[]
    for i,s in enumerate(SCENARIOS):
        q=quantiles[s,'u']
        require(q['probabilities']==[.05,.5,.9,.95] and q['descriptive_only'] is True and q['CDF_precision_does_not_certify_horizontal_quantile_error'] is True,'Quantile limitations changed.')
        require(q['no_recovery_bias_if_truth_undefined'] is (i==2),'Undefined-truth quantile interpretation changed.')
        vals=q['across32_quantiles_min_median_max']
        require(len(vals)==3 and all(len(v)==4 for v in vals),'Three summaries of four quantiles required.')
        for j in range(4):
            require(0<=vals[0][j]<=vals[1][j]<=vals[2][j]<=1,'Quantile order/support changed.')
        rows.append([LABELS[i],*['$'+number(vals[1][j],probability=True)+'$' for j in [1,2,3]],
            '$'+interval([vals[0][3],vals[2][3]],probability=True)+'$'])
    display['descriptive_quantiles']=rows
    parts.append(table('Quantis de massa calculados: descrição das 32 realizações por cenário.',
        'quantis','lrrrr',r'Cenário & Mediana $Q_{50}$ & Mediana $Q_{90}$ & Mediana $Q_{95}$ & Extremos $Q_{95}$',rows,
        r'As medianas e os extremos são tomados entre os 32 dados; não são intervalos de erro numérico. Precisão da CDF não certifica precisão horizontal dos quantis. Sem GW, estes números descrevem o ajuste de um modelo com sinal, sem representar recuperação de uma massa geradora nem detecção.',toy=toy))
    require(not output.exists(),'Output must be new; preserve prior renderings.')
    output.mkdir(parents=True)
    (output/'tabelas.tex').write_text('% Existing summary only; no new statistical tests.\n% SHA256: '+sha(summary)+'\n'+''.join(parts))
    manifest=dict(status='RENDERED_EXISTING_FIXED96_SUMMARY_NO_NEW_STATISTICS',scope=r['scope'],
        summary_sha256=sha(summary),arrays_sha256=sha(arrays) if arrays else None,
        script_sha256=sha(__file__),formatting_source_sha256=sha(Path(__file__).with_name('tabelas_calibracao.py')),
        tables_sha256=sha(output/'tabelas.tex'),display_rows=display,scientific_validation_claimed=False)
    (output/'manifest.json').write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+'\n')
    return manifest


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ['summary','output']:p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--arrays',type=Path);p.add_argument('--toy',action='store_true');a=p.parse_args()
    print(json.dumps({k:v for k,v in render(a.summary,a.arrays,a.output,toy=a.toy).items() if k!='display_rows'}))
