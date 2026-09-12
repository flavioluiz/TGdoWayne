#!/usr/bin/env python3
"""Tabela editorial a partir das referências D2 auditadas; sem simulação."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]


def main():
    audit=json.loads((ROOT/'results/C09/D2_continuacao/audit.json').read_text())
    assert audit['completed_analyses']==audit['primary_passed']==40
    rows={r['prior_id']:r for r in audit['analyses'] if r['curve_id']=='baseline_d2'}
    specs=[('uniform_u_a0_b1','Uniforme em massa $[0,1]$',.95),
           ('uniform_u_squared_a0_b1','Uniforme em massa ao quadrado $[0,1]$',.95**.5)]
    specs += [(f'log_uniform_u_a{a:g}_b1',f'Logarítmica $[{a:g},1]$',a**.05) for a in (.0001,.001,.01)]
    specs.append(('uniform_u_a0_b0.8','Uniforme em massa $[0,0.8]$',.76))
    lines=[r'\begin{table}[htbp]',r'\centering\small',
        r'\caption{Estimativas para a mesma observação ID~2, análise A0. Referências funcionais concluídas no domínio operacional finito; sem certificado uniforme físico.}',
        r'\label{tab:d2-prioris-concluidas}',r'\begin{tabular}{@{}lrrrr@{}}\toprule',
        r'Priori e suporte & $Q_{0,95}^{\pi}$ & $Q_{0,95}^{\rm tab}$ & $E_{\rm tab}[u]$ & $D_{\rm KL}^{\rm tab}$ \\',r'\midrule']
    for key,label,prior_q in specs:
        row=rows[key];assert row['all_primary_passed']
        nums=[prior_q,sum(row['quantile_95_bracket'])/2,row['mean'],row['KL']]
        lines.append(label+' & '+' & '.join(f'{v:.4f}' for v in nums)+r' \\')
    lines += [r'\bottomrule\end{tabular}',r'\end{table}',
        r'\noindent A divergência é expressa em nats. O quantil tabulado é o da interpolação positiva da likelihood salva, com intervalo numérico próprio conferido contra a referência. Ele não representa um intervalo de confiança populacional.']
    (ROOT/'latex/tabelas/d2_continuacao_prioris.tex').write_text('\n'.join(lines)+'\n')


if __name__=='__main__':main()
