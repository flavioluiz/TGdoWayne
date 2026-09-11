# C07 — campanha de inferência e interpretação dos resultados

A campanha de 500 realizações da priori e cinco análises por dado foi encerrada, com **2500 alvos arquivados**. O diagnóstico de calibração usa todos os dados, incluindo casos numericamente não resolvidos. Este documento acompanha a seção de resultados do capítulo 6.

## Proveniência e custo

- Experimento: `configs/calibration/prior_predictive_500_v1.json`.
- Dados independentes: `results/C07/prior_predictive/data.npz`, SHA-256 `63679c96852f3c0aa1e25c8a3f087c0646ceb22cd7701758491cabdd42ac0103`.
- Plano congelado: `configs/calibration/campaign_500_execution_v1.json`; sementes 907110101/907110102 para treino/produção.
- Runtime: `fd68cec0fea6ee43f7691cd39a201b8d6e8dc349536d501303cd6b05402ad280`; driver: `59dd247cc7a2fa6889dfa773400cf1610e708223ed35ef33cffef5c71fbe9ea6`.
- Contagem efetiva: **81.930.000** avaliações de verossimilhança de treino e **819.200.000** de produção; total **901.130.000**. Quatro réplicas por alvo e dois níveis, 16384/65536.
- Fechamento original: `campaign_complete.json`, SHA-256 `1daa0948e9d55f6537cd7c25870c609ea9e1c8019dc59dc8abea899ff6b2c9e2`, incluído no arquivo restaurável.
- Síntese: [`summary.json`](../../results/C07/synthesis/summary.json), SHA-256 `909ef28817342c19293fe9cb832bcf659dd480be5fd82c3708ee73b832cd4f9a`.

## Três contagens diferentes

| Quantidade | Resultado | Interpretação |
|---|---:|---|
| Alvos com todos os cinco flags agregados | 2419/2500 | Inclui precisão de cortes de quantis e outros controles; não equivale à calibração científica. |
| Alvos com algum flag agregado falso | 81/2500 | Nenhum removido ou substituído; A0/A/B/AG/BG: 4/27/10/25/15. |
| Funções PIT não resolvidas | 243/15000 | Máscara específica por função; recebem intervalo `[0,1]`. |

As causas por função podem se sobrepor: 222 falhas da guarda de pesos, 32 de precisão da CDF, seis de saturação e uma incompatibilidade de réplicas específica da função. Os critérios de logZ e refinamento não acrescentaram falhas nessa reconstrução. Essas contagens descrevem os controles operacionais, não taxas de erro conhecidas da integral.

A família de 15000 envelopes usa `PIT ± (0.002 + 4.970830636716245 × MCSE)`, limitada ao suporte de probabilidade. O ponto PIT não sofre clipping. A parte determinística é margem operacional e a parte Monte Carlo é assintótica. “Robusto” abaixo significa persistir para todos os PITs nesses envelopes, condicionado à validade deles.

## Calibração sob a priori

| Modelo | Família Holm | Rejeições nominais / 31 | Robustas / 31 |
|---|---:|---:|---:|
| A0_CN | 93 | 0 | 0 |
| A_G | 93 | 0 | 0 |
| B_G | 93 | 0 | 0 |
| A_CN | 62 | 8 | 6 |
| B_CN | 62 | 5 | 4 |

São famílias prospectivas separadas, sem alegação de FWER global entre elas. Os 31 testes de um modelo reutilizam dados e não representam descobertas independentes. Os modelos de referência não tiveram rejeição nominal; isso é compatibilidade com a calibração no experimento, não prova de correção universal. Uma hipótese de A_G ainda admite rejeição possível no envelope numérico.

Nos modelos normais aproximados aplicados às estatísticas físicas, os desvios robustos concentram-se em `log10_EFAC` e `logL_at_truth`. A cobertura central nominal de 90% do fator de ruído foi 446/500 em A0_CN, **313/500 em A_CN** e **412/500 em B_CN**, contra 449/500 em A_G e 457/500 em B_G. As frações numéricas possíveis de A_CN/B_CN foram `[0.598,0.650]` e `[0.802,0.838]`. O desvio existe em A_CN, que conserva frequências: não deve ser atribuído exclusivamente à compressão.

A massa marginal não apresentou rejeição KS em nenhum modelo: valores de Holm iguais a 1. Coberturas centrais nominais da massa: 455–460/500; limites superiores de 95%: 478–482/500. Isso não estabelece calibração conjunta, equivalência de posteriores ou ausência de desvios condicionais.

Dos 15 contrastes pareados de cobertura central, oito foram rejeições nominais e dois persistiram na sensibilidade: `log10_EFAC` em A_CN–B_CN e A0_CN–A_CN. Nenhum contraste nominal da massa rejeitou. Diferenças de quantis ainda são descritivas porque a precisão vertical da CDF não certifica erro horizontal do quantil; C08 prevê reavaliação em subamostra congelada.

## Reprodução e arquivo

[`posterior500_compact`](../../results/C07/posterior500_compact/README.md) armazena sem perda os **125233 arquivos** da campanha e suplementos em blocos ZIP menores que 90 MiB. Volume compactado: 345533563 bytes; restauração: 645792263 bytes. Os 2500 IDs, 81 estados não resolvidos, propostas, sementes e recibos são mantidos. Os arrays brutos retirados podem ser regenerados, mas não são fingidos como presentes no arquivo.

A extração para uma pasta nova verificou o SHA-256 de cada arquivo antes e depois de restaurar. O registro está em [`posterior500_restoration.json`](../../results/C07/posterior500_restoration.json). A auditoria de integridade não substitui a auditoria estatística.

```sh
.venv/bin/python scripts/compactar_calibracao.py extract \
  --bundle results/C07/posterior500_compact \
  --destination tmp/c07_posterior500_restored_new
```

O diretório de destino deve ser novo. Os registros preservam os caminhos históricos da execução; os comandos de síntese recebem explicitamente os novos caminhos para `diagnostics` e `production`. Ver `results/C07/synthesis/README.md` e os protocolos em `configs/calibration/`.

## Injeções fixas concluídas

As 96 inferências A0 encerraram com todos os cinco flags numéricos aprovados. São 32 observações por cenário, 416 PITs numéricos aplicáveis, 32 estruturais e 128 mascarados. Foram contabilizadas 34603392 avaliações de verossimilhança, com sementes 907120101/907120102. A síntese em `results/C07/fixed_synthesis/` possui SHA-256 `1273de6e7f2b835a5c349c5df243b60ac5f865ff0f55f61bfb2715e0ac0c11d5`.

Em u=0, a cobertura de [0,U90] é estruturalmente 1, e a central de 90% é 0. Em u=0.995, ambos os eventos tiveram 0/32, com IC binomial 95% [0,0.1088812], persistindo na sensibilidade numérica. A mediana do Q95 calculado foi 0.9543, próxima ao quantil 0.95 da priori uniforme. Isso expõe pouca capacidade do experimento para levar seus limites até essa verdade extrema; não conflita logicamente com SBC marginal sob a priori, que não garante cobertura em todo parâmetro fixo.

Sem GW, os parâmetros do sinal e logL na verdade permanecem mascarados. Os quantis calculados de massa descrevem o ajuste do modelo com sinal e não são recuperação ou detecção. As coberturas centrais de ruído foram 30/32 para logAr e 29/32 para logE. A precisão horizontal dos quantis continua descritiva. Não se executam KS, Holm ou fatores de Bayes nesta síntese condicional.

A [auditoria independente da campanha principal](../../results/C07/synthesis_independent_review/PARECER.md) e seu inventário preservam fontes, comandos e evidências. A ausência de rejeições nos controles e os resultados favoráveis dos testes numéricos não substituem os limites de escopo descritos acima.

A [auditoria independente dos 96 controles](../../results/C07/fixed96_independent_review/PARECER.md) aprovou 6508 verificações e confirmou máscaras, contagens e todos os 1920 quantis descritivos, sem ler raws ou recomputar verossimilhanças.
