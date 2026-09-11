# Ensaio prospectivo de treinamento frio — alvo A_G d14

O treino de 8192 passos por quatro trajetórias, iniciado da priori e seguido de
uma proposta GMM congelada, atingiu a precisão operacional em todos os 54 cortes
de controle no nível independente de 65536 pontos IID por quatro réplicas.
Esse resultado complementa o piloto dos 16 alvos; não representa calibração
SBC de 500 realizações nem prova de cobertura de caudas não amostradas.

Os 54 cortes foram definidos no antigo nível GMM1024 antes destes experimentos,
em cinco parâmetros e na log-verossimilhança, para probabilidades
0.01/0.05/0.10/0.25/0.50/0.75/0.90/0.95/0.99. Nenhuma verdade foi lida para
determinar os cortes, ajustar as propostas ou avaliar a precisão desta grade.
O script `diagnose_fixed_grid.py` lê somente `targets`, `x_unit`,
`log_weights` e `log_likelihood` dos NPZ. Os antigos cortes em logL, obtidos
com 553 nós, são apenas limiares escalares fixos; os dois ensaios frios usam a
mesma tabela validada de 8336 nós. Não se transfere aprovação da interpolação
antiga para a nova.

| Treino × trajetórias | IID por réplica × réplicas | Cortes com MCSE ≤ 0.00335 | Maior MCSE | Função limitante |
|---|---:|---:|---:|---|
| 4096 × 4 | 32768 × 4 | 51/54 | 0.003973546 | logL, corte Q50 |
| 8192 × 4 | 32768 × 4 | 53/54 | 0.004055923 | γ_gw, corte Q50 |
| 8192 × 4 | 65536 × 4 | 54/54 | 0.002721447 | log10 A_r, corte Q50 |

A ordem dos parâmetros no arquivo original é
`[u, log10_Agw, gamma_gw, log10_Ar, log10_EFAC]`.
Os nomes da função referem-se ao quantil do piloto que definiu o corte, não
a um quantil recalculado para forçar a CDF atual ao valor nominal.

O nível final usa a mesma proposta de 8192 passos, sem novo ajuste, e a semente
nova 907103401. Seu orçamento de 300000 avaliações foi registrado antes da
produção; executou 262144. Os níveis de 32768 usaram sementes 907103301 e
907103302. Os treinos independentes usaram 907103101 e 907103102. Todos os
arquivos anteriores e seus hashes permanecem preservados.

A comparação dos dois treinos no nível inicial é consistente nos 54 cortes
(maior diferença padronizada 2.2863). O refinamento independente de 32768 para
65536 da proposta fixa também é consistente nos 54 cortes (máximo 2.4159),
usando os erros operacionais e a família normal/Bonferroni explícita. A
ausência de discordância detectável não comprova ausência de viés ou de modos
omitidos. O MCSE é o maior entre a influência IID reunida e a influência entre
réplicas; não é uma aproximação binomial baseada no ESS dos pesos.

No nível final, ESS descritivo de concentração = 106256.45 em 262144 pontos,
peso normalizado máximo = 0.000444577 e guarda de exclusão de um único ponto
aprovada. A log-evidência estimada é 12.43383797, com MCSE delta operacional
0.00272878. Sua diferença para o nível anterior corresponde a 1.250σ numa
família descritiva separada de um contraste. Nenhuma meta retrospectiva de
0.001 para evidência foi imposta ou declarada satisfeita.

O treino de 8192 passos custou 13.49 s no kernel NumPy escalar por alvo,
mais 1.58 s de EM original. A construção compartilhável da interpolação e dos
bancos custou cerca de 56 s. O nível final levou 17.08 s para IID e escrita,
usando a receita histórica com geradores por coluna. A produção vetorizada
nova será uma execução diferente, com sementes e fontes próprias. O pico de
RSS Darwin foi 2084339712 bytes, cerca de 63 MB abaixo de 2 GiB nominais; o
orçamento preflight de arrays não é garantia de RSS.

Arquivos completos: `results/fixed_grid_diagnostics.json`,
`results/fixed_grid_summary.json`, `results/evaluation_summary.json`,
`evaluation_config.json` e `evaluation_source_manifest.json`.
A comparação anterior permanece em
`../c07_cold_training/results/fixed_grid_diagnostics.json`.

Recomendação: manter 8192 passos de treino como receita prospectiva inicial e
65536×4 como tamanho inicial da produção aprovada pelo piloto, preservando
diagnósticos por alvo. O ensaio frio cobre um caso difícil e não substitui as
checagens de cada novo conjunto de dados. Uma falha futura deve ser registrada
e motivar um novo nível explicitamente planejado, sem afrouxar os critérios.
