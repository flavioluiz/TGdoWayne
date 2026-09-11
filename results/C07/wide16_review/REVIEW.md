# Ensaio independente de diagnóstico IID: proposta ampla, 16 alvos

Data: 10/09/2026. Escopo: escolha prospectiva de proposta computacional para C07.
Este registro não é uma campanha SBC de 500 realizações, não altera protocolos
históricos e não constitui autorização automática de inferência ou descarte dos raws.

**Parecer:** o nível de 65.536 amostras por réplica, com quatro réplicas IID,
satisfaz os critérios numéricos previamente definidos neste ensaio dos 16 alvos.
Os resultados apoiam congelar a política de ampliação para uma nova execução,
mantendo diagnósticos por função em todos os alvos e registrando eventuais falhas.
Os checkpoints integrados precisam de identidade e hash de conteúdo novos.

## Execução identificada

Alvos: `[0,3,8,9,11,14,20,25,28,35,46,51,52,62,67,78]`, com
`target = 16 × model_index + data_index` e modelos
`[A0_CN,A_CN,B_CN,A_G,B_G]`. São 16 alvos selecionados de um piloto de 16 dados;
não são 16 novos experimentos independentes entre todas as famílias.

A proposta é `q = 0,75 GM(C) + 0,10 GM(9C) + 0,15 Student_5_global`.
Preserva os 16 ajustes frios originais de 8.192 passos, sem novo ajuste.
Os dois níveis independentes têm 16.384 e 65.536 amostras por réplica, quatro
réplicas cada, semente-base 907150101. A produção usou a tabela de 8.336 nós
`table_beta8193_local.npz`, SHA256
`75632dfbdd9cce8b60b9f760a3177a76798a4adb7ac9ccc724092aeaf53ad70d`.
A aprovação numérica dessa tabela pertence ao relatório específico da ORF.

O índice é `tmp/c07_cold_tail_review/wide_production/execution_summary.json`.
Conferi os SHA256 dos 128 raws, a identidade exata dos pesos completos
`logw = logL + log_prior_logit − log_proposal`, os índices e formas, as fontes
do dado/experimento e as verdades utilizadas apenas no diagnóstico.
Também reconferi os 22 arquivos de entrada e 31 fontes do manifesto da execução:
nenhuma divergência. O conversor local somente reorganiza arrays e seleciona
limiares; não realiza sorteios nem avaliações de verossimilhança.

## Resultado principal, protocolo IID v1 intacto

Cada alvo tem seis PITs (cinco parâmetros e logL no valor verdadeiro) e 20 CDFs
nos quantis 0,05/0,50/0,90/0,95 dos cinco parâmetros. Estes 20 cortes foram
selecionados pelo nível menor, independentemente das amostras do nível maior.
Consequentemente, suas CDFs no nível menor são descritivas e ficam fora dos
testes formais de estabilidade que exigem cortes independentes.

| Verificação | 16.384 × 4 | 65.536 × 4 |
|---|---:|---:|
| CDFs com MCSE ≤ 0,00335 | 375/416 | 416/416 |
| CDFs não resolvidas | 0 | 0 |
| Alvos com todas as 26 CDFs precisas e controle de peso | 2/16 | 16/16 |
| Maior MCSE | 0,007749686 | 0,002623853 |
| Brackets de referência A0d14 consistentes | 20/20 | 20/20 |
| Brackets também precisos em MC | 19/20 | 20/20 |

No nível maior, os **96/96 PITs** têm precisão suficiente. O maior MCSE é
0,0026238533972477644 para `target62 = A_G, data14`, na CDF de logL verdadeiro;
a estimativa é 0,49693418751292806. O segundo maior é 0,002621426642928163
para `target78 = B_G, data14`, no corte q0,9 de log10_Ar.

Os 3.264 contrastes entre réplicas têm zero falhas e zero não resolvidos:
máximo padronizado 4,2136864777, abaixo de z = 4,3240561576.
A família compreende 6 pares de réplicas por função, com sete funções no
nível menor (seis PITs e logZ) e 27 no maior (26 CDFs e logZ), por alvo.
Os 152 contrastes de refinamento têm zero falhas e zero não resolvidos:
máximo padronizado 2,4818783843, abaixo de z = 3,5913675273. São 112 contrastes
de PIT/logZ e 40 nos extremos dos 20 brackets de A0d14.
Cada família utiliza alpha = 0,05 e a aproximação normal de Bonferroni
pré-existente; não são testes finitos exatos.

A referência externa `results/C07/reference/quantiles/posterior_reference.json`
corresponde ao mesmo dado e configuração. Os 20 brackets são comparados por
40 desigualdades unilaterais, com z = 3,0233414397, componente determinístico
CDF 0,002 e largura horizontal 0,001 da priori. Não se identifica a CDF no
ponto médio com a probabilidade nominal do quantil.

O maior peso normalizado observado no nível maior é 0,0013607220; o controle
de remoção de um peso passa nos 16 alvos. A maior massa ponderada dos logits
cuja transformação saturou numericamente, em todos os arquivos, é
3,8064 × 10⁻¹⁶. Isso quantifica somente as amostras observadas.
O ESS de concentração dos pesos fica entre 74.579 e 144.562 no nível maior;
não foi tratado como tamanho de amostra binomial nem como certificado de caudas.

O erro delta de logZ é registrado como diagnóstico do denominador, sem exigir
0,001 em todos os alvos ou interpretar esses valores como Bayes factors.
Por exemplo, A0d14 tem logZ = −76,0814699877 e MCSE delta = 0,0019483433
no nível maior. A comparação específica de evidências de alta precisão
permanece restrita à sua validação determinística própria.

## Grade adicional de 54 cortes sem verdades

A grade foi congelada em
`tmp/c07_iid_portable/results/gmm_truth_blind_planning.json`, SHA256
`c46649ff4b26d0c65fe65e355b532592b56427169e7b53ed5cc553de68fe1ad3`.
São nove cortes de probabilidade `[0,01;0,05;0,1;0,25;0,5;0,75;0,9;0,95;0,99]`
para cada parâmetro e logL. O produtor e essa grade não consultam verdades.

O agente produtor calculou a grade com uma cópia byte a byte do módulo IID v1.
Reproduzi independentemente **todas as 1.728 CDFs dos dois níveis**, os 32
resumos de pesos e os 864 contrastes de refinamento com o módulo otimizado
ROOT e a conversão dos raws. Os 33.251 campos numéricos diferem em no máximo
6,1583 × 10⁻¹⁷; todos os 15.874 campos de decisão/texto são idênticos.
O script dessa reprodução não lê os membros de verdade dos NPZ.

No nível maior, **864/864 cortes** atingem a meta, com 16/16 controles de
peso aprovados. O máximo MCSE é 0,0025890081298098953 (`target78`, log10_Ar,
corte 0,75). Os 864 refinamentos não têm conflito, com máximo padronizado
3,1726992014. Essa família da grade fixa é distinta das famílias 3.264/152;
não se afirma um erro familiar conjunto de 5% entre todas essas verificações.

## Custos, limites e integração

A produção acrescentou 5.242.880 avaliações de logL, totalizando 8.028.204
na subtarefa autorizada sob teto de 10 milhões. Foram 10,70 s de preparação
e 8,77 s de produção/I/O na máquina em uso. O leitor das 26 CDFs e brackets
levou 2,17 s; a reprodução independente da grade54, 2,05 s. Esses tempos são
medições deste ensaio, sem extrapolação garantida para 2.500 alvos.

Quatro réplicas, boas estimativas de variância e pesos observados moderados
não excluem modos ou caudas não visitados. A seleção dos 16 alvos é um piloto
de engenharia. A campanha maior deve conservar todos os alvos e flags,
separar elegibilidade numérica de calibração científica e manter precisão por
função. Não é necessário que modelos aproximados passem calibração científica.

**Ressalva concreta de proveniência:** os JSON das propostas derivadas
herdaram `identity` e `proposal_content_hash` do ajuste original. O produtor
temporário usa os novos SHA256 dos arquivos em configuração/índice/manifesto,
todos conferidos, e não esses campos herdados. Portanto a evidência numérica
permanece rastreável; porém esses JSON **não são checkpoints ROOT válidos**.
Na integração, preserve o hash do ajuste original em campo específico e gere
novo hash de conteúdo/identidade que inclua a transformação e sua política.
O registro original está em `wide_production/PROVENANCE_NOTE.md` e permanece
intacto. Não promova automaticamente o arquivo histórico ao driver integrado.

## Arquivos para preservação

- `diagnostics_v1_wide16.json`: diagnóstico detalhado das 26 funções/brackets,
  famílias, hashes e configuração efetivamente utilizada.
- `diagnostics_v1_wide16_summary.json`: resumo do mesmo cálculo.
- `inputs/input_manifest.json`: 128 raws, identidade dos pesos e conversão.
- `execution_source_audit.json`: reconferência dos 22 inputs/31 fontes.
- `fixed_grid_independent_verification.json`: comparação campo a campo da
  grade independente, com os hashes da referência e scripts.
- `prepare_inputs.py` e `verify_fixed_grid.py`: utilitários desta auditoria.
- `package_manifest.json`: hashes finais do pacote e antecedentes utilizados.

Os NPZ convertidos em `inputs/` são intermediários locais volumosos; os raws e
seus índices continuam sendo a evidência primária. Nenhum arquivo versionado
foi modificado por esta auditoria.

## Reprodução

Executar a partir da raiz, com o ambiente `.venv` já preparado:

```sh
.venv/bin/python tmp/c07_wide16_diagnostics/prepare_inputs.py \
  --index tmp/c07_cold_tail_review/wide_production/execution_summary.json \
  --manifest tmp/c07_cold_tail_review/wide_production/execution_manifest.json \
  --production-config tmp/c07_cold_tail_review/wide_production/config.json \
  --protocol configs/calibration/diagnostics_iid_v1.json \
  --data results/C07/fixtures/pilot_data.npz \
  --experiment configs/calibration/pilot_initial.json \
  --truth-logl tmp/c07_integrated_engineering/truth_log_likelihood.json \
  --output tmp/c07_wide16_diagnostics/inputs
.venv/bin/python scripts/diagnosticar_importancia_iid_otimizada.py \
  --low tmp/c07_wide16_diagnostics/inputs/iid_N16384.npz \
  --high tmp/c07_wide16_diagnostics/inputs/iid_N65536.npz \
  --truth-logl tmp/c07_wide16_diagnostics/inputs/truth_logl_selected.json \
  --reference results/C07/reference/quantiles/posterior_reference.json \
  --protocol tmp/c07_wide16_diagnostics/inputs/protocol_execution.json \
  --output tmp/c07_wide16_diagnostics/diagnostics_v1_wide16.json
.venv/bin/python tmp/c07_wide16_diagnostics/verify_fixed_grid.py \
  --project-root . --inputs tmp/c07_wide16_diagnostics/inputs \
  --grid tmp/c07_iid_portable/results/gmm_truth_blind_planning.json \
  --reference tmp/c07_cold_tail_review/wide_production/fixed_grid_diagnostics.json \
  --output tmp/c07_wide16_diagnostics/fixed_grid_independent_verification.json
```
