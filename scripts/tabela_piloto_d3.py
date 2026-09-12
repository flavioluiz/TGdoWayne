#!/usr/bin/env python3
"""Generate the pilot table from audited results, without numerical inference."""
from pathlib import Path
import json
R=Path(__file__).resolve().parents[1]
a=json.loads((R/'results/C09/D3_piloto/audit.json').read_text())
def f(x,n=4):return f'{x:.{n}f}'.replace('.',',')
names={0:'Central, uniforme',1:'Central, massa ao quadrado',2:'Central, logarítmica',3:'Ruído vermelho',4:'Ruído branco',
 5:r'\(\gamma=3\)',6:r'\(\gamma=3\)',7:r'\(\gamma=5,5\)',8:r'\(\gamma=5,5\)',
 9:r'Monopolo, \(\rho=0,25\)',10:r'Monopolo, \(\rho=1\)',11:r'Dipolo, \(\rho=0,25\)',12:r'Dipolo, \(\rho=1\)',15:'Massa nula'}
lines=[r'% Generated from results/C09/D3_piloto/audit.json.',
 f"Na versão~0.8.9, as integrações das {a['nominal_distance_posterior_analyses']} análises nominais foram registradas;",
 f"{a['primary_passed']} passaram nos cinco controles primários de normalização, CDF,",
 r'quantis, momentos e KL. W1 e eventos de logL desses dados ainda estavam pendentes naquele checkpoint.',
 f"O lote de posteriores contabilizou \\({a['posterior_values']:,}\\) avaliações e".replace(',','\\,'),
 f"\\({f(a['posterior_CPU'],2)}\\) segundos de CPU. As verificações finitas acrescentaram",
 f"\\({a['finite_checks_values']:,}\\) avaliações. Não se realizou SBC neste lote.".replace(',','\\,'),
 r'\begin{table}[htbp]\centering\small',
 r'\caption{Piloto D3: resultados selecionados de \(A_0\), com parâmetros auxiliares conhecidos. Os intervalos de \(Q_{95}\) são numéricos, não intervalos entre realizações.}',
 r'\label{tab:c09-d3-piloto}',r'\begin{tabular}{rlrrr}\toprule',
 r'ID & Cenário & \(u_*\) & Intervalo de \(Q_{95}\) & KL (nat) \\ \midrule']
for row in a['rows']:
 if not row['curve'].endswith('_A0_CN'):continue
 if row['status']!='PASS_PRIMARY_FINITE_DOMAIN_OPERATIONAL':
  lines.append(f"{row['row']} & {names[row['row']]} & --- & não resolvido & --- " + r"\\");continue
 lo,hi=row['q95']
 lines.append(f"{row['row']} & {names[row['row']]} & {f(row['truth_u'])} & [{f(lo)}; {f(hi)}] & {f(row['KL'])} \\\\")
lines.extend([r'\bottomrule\end{tabular}',r'\end{table}', ''])
(R/'latex/tabelas/d3_piloto_estado.tex').write_text('\n'.join(lines))
