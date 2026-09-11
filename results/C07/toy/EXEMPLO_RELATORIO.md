# Exemplo executado: TOY conjugado, não PTA

Seed 707209106; 4096 réplicas em 5 dimensões. Prefixo de 500 predefinido, sem independência do conjunto completo.

| N | Algoritmo | Rejeições Holm/31 | PITs de parâmetros rejeitados | KS de logL | p ajustado de logL |
|---:|---|---:|---:|---:|---:|
| 500 | TOY_EXACT | 0 | 0 | 0.031539 | 1 |
| 500 | TOY_IGNORES_DATA_RETURNS_PRIOR | 1 | 0 | 0.972455 | underflow (ver limite log10 no JSON) |
| 4096 | TOY_EXACT | 0 | 0 | 0.022706 | 0.865519 |
| 4096 | TOY_IGNORES_DATA_RETURNS_PRIOR | 2 | 0 | 0.973530 | underflow (ver limite log10 no JSON) |

Não rejeição não certifica correção. O controle negativo pode passar nos parâmetros e falhar em logL.

As rejeições adicionais abaixo são preservadas, sem trocar seed ou limiar. Para o algoritmo-priori, a cobertura dos quantis é nominal na população por identidade analítica; uma rejeição nessa contagem é erro tipo I nesta realização.

- N=4096, TOY_IGNORES_DATA_RETURNS_PRIOR, theta_3, below_q0.90: p ajustado=0.0255669.

| Verdade u (TOY separado) | Cobertura [0,U90] | Cobertura [Q05,Q95] |
|---:|---:|---:|
| 0 | 1.000 | 0.000 |
| 0.05 | 1.000 | 0.898 |
| 0.5 | 0.888 | 0.898 |
| 1 | 0.000 | 0.000 |

No ponto zero, a cobertura [0,U90]=1 é estrutural. Não foi cobrada cobertura frequentista universal de 90%.

Maior discrepância dos controles analíticos independentes: 3.33e-16 (tolerância prévia 1e-10).

Estado: PASS_TOY_CROSSCHECKS_AND_NEGATIVE_CONTROL. Nenhum resultado certifica inferência, ORF ou calibração PTA.
