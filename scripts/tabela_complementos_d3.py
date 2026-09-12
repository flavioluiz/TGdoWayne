#!/usr/bin/env python3
"""Render audited paired contrasts and W1 status, without likelihood calls."""
from pathlib import Path
import json
R=Path(__file__).resolve().parents[1];a=json.loads((R/'results/C09/D3_complementos/audit.json').read_text())
def f(x,n=4):return f'{x:.{n}f}'.replace('.',',')
def count(n):return f'{n:,}'.replace(',',r'\,')
labels={'A0_CN':r'\(A_0\)','A_G':r'\(A_G\)','B_CN_full_variable':r'\(B_{\rm CN}\)'}
lines=[r'% Generated from the archived D3 complement audit.',
 f"A referência W1 foi concluída para \\({a['W1_analyses']}\\) análises do piloto;",
 f"\\({a['W1_passed']}\\) passaram no critério operacional de \\(0,001\\).",
 f"A maior discrepância foi \\({f(a['W1_max_delta'],8)}\\).",
 f"O lote W1 contabilizou \\({count(a['W1_charged_values'])}\\) avaliações adicionais.",
 r'\begin{table}[htbp]\centering\small',
 r'\caption{Piloto D3: diferença de \(Q_{95}\), omissão menos inclusão do contaminante, sobre o mesmo dado. Os intervalos são numéricos; cada linha é um caso de engenharia.}',
 r'\label{tab:c09-d3-omissao}',r'\begin{tabular}{rlr}\toprule',
 r'ID & Análise & Intervalo da diferença de \(Q_{95}\) \\ \midrule']
for p in sorted(a['controls']['pairs'],key=lambda x:(x['data_id'],x['analysis'])):
 lo,hi=p['interval'];lines.append(f"{p['data_id']} & {labels[p['analysis']]} & [{f(lo)}; {f(hi)}] " + r'\\')
lines += [r'\bottomrule\end{tabular}',r'\end{table}','']
(R/'latex/tabelas/d3_complementos.tex').write_text('\n'.join(lines))
