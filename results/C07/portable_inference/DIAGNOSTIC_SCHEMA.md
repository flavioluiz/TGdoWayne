# C07: produto numérico por alvo, versão 1

Um alvo é `(model, datum)`; `target = model_index * n_data + datum`, em ordem
`A0_CN, A_CN, B_CN, A_G, B_G`. Nenhum alvo é descartado por falha. O modelo e o
identificador constam também do pequeno JSON de metadados. A tabela de síntese
usa os 2.500 alvos; os 16 dados históricos são engenharia e têm outro hash.

A leitura das verdades é exclusiva do diagnóstico, mediante `--truth-data`
explícito e SHA256 idêntico ao arquivo de observações usado pelo produtor.
O treino e a produção jamais desserializam `truth`.

O artefato numérico será `diagnostic_target_XXXXXX.npz`, acompanhado de um JSON
pequeno com SHA256, configuração, identidade, proposta, oito raws, fontes,
referências de validação e flags agregadas. Arrays numéricos aceitam `inf` para
MCSE não resolvida; o JSON usa `null` com flags explícitas. Não confundir uma
amostra descritiva reamostrada com pontos IID da posterior.

| Campo NPZ | Forma | Definição |
|---|---|---|
| `target`, `datum`, `model_index` | escalar | Identidade inequívoca; sem descarte de IDs |
| `probabilities` | 4 | `[.05, .5, .9, .95]` |
| `pit` | 6 | CDF posterior na verdade dos cinco parâmetros, seguida de CDF de `log L(theta_true; mesmo dado)` |
| `pit_mcse`, `pit_resolved`, `pit_precision_pass` | 6 | Máximo das influências IID e entre replicações; constante não resolvida |
| `quantiles_unit`, `quantiles_physical` | 5 × 4 | Quantis ponderados do nível maior; unidades da priori e físicas |
| `independent_cuts_unit` | 5 × 4 | Quantis fixados exclusivamente pelo nível menor |
| `cut_cdf`, `cut_mcse`, `cut_resolved`, `cut_precision_pass` | 5 × 4 | CDFs no nível maior nesses cortes independentes |
| `log_evidence`, `log_evidence_mcse` | escalar | Constantes completas da priori/likelihood/proposta; erro delta explícito |
| `weight_ess`, `maximum_weight`, `single_deletion_bound` | escalar | Concentração observada, sem certificado de cauda não observada |
| `cdf_estimates_by_level`, `cdf_mcse_by_level`, `cdf_resolved_by_level`, `cdf_precision_by_level` | 2 × 26 | Ordem: para cada parâmetro, verdade + quatro cortes; depois logL na verdade |
| `cdf_replicate_estimates`, `cdf_replicate_mcse` | 2 × 26 × 4 | Preserva comparação entre as quatro replicações |
| `replication_difference`, `replication_mcse`, `replication_resolved`, `replication_pass` | 204 | Contrastes formais, ordem fixa descrita abaixo |
| `refinement_difference`, `refinement_mcse`, `refinement_resolved`, `refinement_pass` | 7 | Cinco PITs, logL-PIT e logZ; ordem fixa |
| `saturated_rows`, `saturated_weight` | 2 × 4 | Extremos de `expit` observados; não há clipping |

O leitor não impõe envelope `PIT ± 4 MCSE`. A síntese usa o envelope prospectivo
já congelado pelo projeto, incluindo erro determinístico e multiplicidade.
Quando `pit_resolved` é falso, o intervalo de sensibilidade é `[0,1]`, sem
MCSE zero artificial. As famílias científicas 93/62/15 são responsabilidade da
síntese; este pacote verifica a precisão dos posteriors.

## Famílias numéricas congeladas

Existem seis pares de replicações, na ordem `(0,1),(0,2),(0,3),(1,2),(1,3),(2,3)`.
No nível menor os seis PITs e logZ geram 42 contrastes. No nível maior as 26 CDFs
(cinco verdades + vinte cortes independentes + logL verdade) e logZ geram 162.
Total: **204 por alvo; 510.000 na campanha completa**. CDFs avaliadas nos próprios
quantis do nível menor são descritivas e excluídas dessa família.

O refinamento compara níveis independentes apenas nos cinco PITs, logL-PIT e
logZ: **7 por alvo; 17.500 na campanha completa**. Os cortes escolhidos no nível
menor não são usados como contraste formal de refinamento. Bonferroni global
usa alpha=.05 para cada uma dessas duas famílias. A referência externa A0d14
é um controle de engenharia vinculado ao hash do fixture; não é aplicada ao
novo datum14 de 500 observações.

## Integridade, estado numérico e liberação (revisão operacional v2)

O diagnóstico retorna todos os valores, flags e falhas. Um recibo separado
`RAW_ARCHIVE_VERIFIED` confirma proposta, oito checkpoints/RNG, configurações,
resumo completo JSON/NPZ e hashes preservados. Seu estado numérico é
`RECORDED_NUMERICAL_CHECKS_PASSED` ou `NUMERICALLY_UNRESOLVED`; nenhum dos dois
é uma declaração de calibração científica da campanha. Alvos imprecisos são
mantidos com flags e intervalos não resolvidos, nunca descartados.

A liberação explícita de raws exige esse recibo íntegro, e não exige passar a
SBC ou todas as verificações de precisão. Isso limita o armazenamento temporário
sem apagar resultados desfavoráveis: permanecem os produtos completos, receita
RNG, proposta e hashes para reprodução determinística. Só os oito raws listados
podem ser removidos. A antiga regra v1 exigia aprovação numérica; seu código foi
preservado antes desta revisão, que precede a nova campanha.
