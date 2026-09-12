"""Descriptive summaries of the frozen32-observation paired prior panel."""
from pathlib import Path
import json
import numpy as np

ROOT=Path(__file__).resolve().parents[1]


def main():
    base=ROOT/'results/C09/paired_prior_panel'
    rows=json.loads((base/'posteriors.json').read_text())
    contrasts=json.loads((base/'contrasts.json').read_text())
    summary=[]
    for model in dict.fromkeys(r['model'] for r in rows):
        for prior in dict.fromkeys(r['prior'] for r in rows):
            items=[r for r in rows if r['model']==model and r['prior']==prior]
            assert [r['datum_id'] for r in items]==list(range(32))
            lower=items[0]['lower']
            pq=.95 if prior=='uniform_u' else (np.sqrt(.95) if prior=='uniform_u_squared' else lower**.05)
            paired=[r for r in contrasts if r['model']==model and r['prior']==prior]
            summary.append(dict(model=model,prior=prior,n=32,prior_q95=float(pq),
                posterior_q95_median_interval=[float(np.median([r[k][3] for r in items])) for k in ('quantile_lower','quantile_upper')],
                KL_median=float(np.median([r['summary']['KL'] for r in items])),
                odds_median=float(np.median([r['posterior_to_prior_odds'] for r in items])),
                paired_q95_below_uniform=sum(r['quantile_delta_upper'][3]<0 for r in paired),
                paired_q95_above_uniform=sum(r['quantile_delta_lower'][3]>0 for r in paired),
                paired_q95_overlapping_zero=sum(r['quantile_delta_lower'][3]<=0<=r['quantile_delta_upper'][3] for r in paired)))
    (base/'descriptive_summary.json').write_text(json.dumps(summary,indent=2,allow_nan=False)+'\n')
    lines=['# Sensibilidade pareada às prioris em C09','',
        'Painel prospectivo dos primeiros 32 dados centrais gerados sob priori uniforme em u.',
        'Cada observação foi analisada com dez modelos e cinco medidas normalizadas.',
        'As 1.600 integrações incluem 320 resultados uniformes já existentes, recalculados',
        'a partir do cache. Há 1.280 contrastes adicionais; não são novas observações nem SBC.',
        '', 'A tabela apresenta medianas descritivas sobre os 32 dados. O intervalo da mediana',
        'de q95 decorre dos intervalos numéricos das duas malhas; não é intervalo de confiança',
        'populacional. KL está em nats e compara cada posterior à sua própria priori.',
        'As odds comparam a probabilidade posterior e a priori de u ≤ 0,2.', '',
        '| Modelo | Priori | q95 da priori | Mediana q95 posterior | Mediana KL | Mediana razão de odds |',
        '|---|---|---:|---:|---:|---:|']
    for r in summary:
        lo,hi=r['posterior_q95_median_interval']
        lines.append(f"| {r['model']} | {r['prior']} | {r['prior_q95']:.4f} | [{lo:.4f}, {hi:.4f}] | {r['KL_median']:.5f} | {r['odds_median']:.4f} |")
    lines += ['', 'Nas famílias completas variáveis, os quantis mudam apreciavelmente com a',
        'medida e com o corte logarítmico. Para A0, a mediana de q95 fica perto de 0,936',
        'com priori uniforme, 0,967 com uniforme em u² e 0,619–0,767 nos três cortes',
        'logarítmicos. As medianas de KL correspondentes ficam entre 0,026 e 0,049 nat.',
        'Essas duas observações devem ser apresentadas juntas: um limite menor não',
        'estabelece, por si só, maior informação dos dados. KL pequena na mediana',
        'não implica informação nula em todas as realizações.', '',
        'Os modelos CN e gaussianos usam observações pareadas com marginais diferentes;',
        'os contrastes de priori acima mantêm o mesmo dado dentro de cada modelo.',
        'As diferenças de KL entre prioris usam referências distintas e não são um teste',
        'universal de qualidade ou identificabilidade.', '',
        'Todas as comparações entre malhas passaram, preservadas as tolerâncias de C09.',
        'Os controles finitos de verossimilhança são reutilizados porque a priori não',
        'altera essa função. As referências adaptativas para os cortes logarítmicos',
        'adicionais passaram nos dados 0 e 31 para A0 e B_CN/B_G completos variáveis',
        '(12 posteriores; `results/C09/production_references/audit.json`). Isso é uma',
        'verificação representativa, não uma referência adaptativa para cada um dos',
        '1.280 contrastes. A calibração e as misturas de distância continuam pendentes.',
        'Os intervalos W1 e de distância entre CDFs nos dados brutos dizem respeito à',
        'tabela positiva normalizada; não incluem erro físico uniforme.', '',
        'Fontes: `results/C09/paired_prior_panel/` e `scripts/painel_prioris_c09.py`.',
        'Nenhuma nova avaliação de verossimilhança ou resposta física foi feita neste painel.', '']
    (ROOT/'docs/c09_sensibilidade_prioris_producao.md').write_text('\n'.join(lines))


if __name__=='__main__':main()
