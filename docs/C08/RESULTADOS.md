# C08 — compressão, resposta de referência e resolução numérica

O marco separa compressão dos dados e aproximação da resposta. A descrição
dos 500 dados de C07, os mapas de momentos e a comparação pareada de 32
dados foram executados. **A coorte não resolveu equivalência nem diferença
material dos limites de massa na escala prospectiva de 0,01 da largura da
priori.** Esse resultado inconclusivo permanece explícito no capítulo 7.

## Experimentos e resultados

| Produto | Execução e alcance |
|---|---|
| Descrição C07 | 2.500 posteriores nos mesmos 500 dados; três contrastes, sem descartar pendências. As médias pontuais não certificam erro horizontal ou equivalência. |
| Mapas da resposta | B, C_beta e C_full; duração 4,5/9/15 anos, massa, espectro, amplitudes e janelas retangular/Hann projetada. Não representam análise de TOAs irregulares. |
| Dispersão fraca | Diferença C_beta−B começa em u²; restos avaliados em três pequenas massas seguem a tendência u⁴. Não é limite uniforme junto ao limiar. |
| Engenharia C | Quatro dados × duas distribuições × duas variantes: 16 alvos concluídos. |
| Campanha C | 128 alvos concluídos; um diagnóstico geral de peso pendente em C_beta e cinco em C_full, todos preservados. |
| Reprodução C07 | 160 alvos, 640 réplicas HIGH com SHA dos dados brutos e estados RNG originais reproduzidos; nenhuma nova realização independente. |
| Controles finitos | 288 nuvens, 324 vínculos e 416.856 comparações. 76/288 vínculos principais e 9/36 de engenharia satisfazem as regras. Quatro nuvens saturadas foram preservadas. |
| Quantis suplementares | 1.460 intervalos operacionais e 4.300 intervalos inconclusivos [0,1], dos 5.760 quantis. Cortes, pesos, MCSE e diagnósticos originais inalterados. |
| Comparação pareada | 24 IDs sorteados e oito de fronteira separados; sete contrastes, 4.480 diferenças de quantis e 1.120 diferenças de larguras. Todas as 224 comparações primárias individuais e as sete médias piloto são inconclusivas. |
| Forma posterior | KL de A_G para B_G em quatro IDs fixos: 0,63803; 1,47700; 3,49123; 0,58490 nats. MCSE entre 0,00250 e 0,00378. Não é fator de Bayes nem média populacional. |

Os mapas normais em parâmetros fixos medem discrepâncias distribucionais.
Não convertem automaticamente a discrepância em viés, perda de cobertura
ou deslocamento de quantis. A demonstração de processamento de dados exige
o mesmo modelo gerador; B−C inclui também mudança de modelo físico.

## Protocolos, resultados e figuras

- [Configurações e coorte](../../configs/compression/), incluindo os antecedentes prospectivos sem reescrever seu estado histórico.
- [Protocolo pareado congelado](PROTOCOLO_PAREADO.md), fixado antes de C e da reprodução HIGH, mas depois da campanha C07 conhecida.
- [Descrição dos 500 dados](../../results/C08/c07_descriptive/) e [mapas](../../results/C08/maps/).
- [Síntese pareada](../../results/C08/paired32/summary.json), [quantis](../../results/C08/paired32/paired_quantiles.csv) e [larguras](../../results/C08/paired32/paired_widths.csv).
- [Intervalos de cada dado](../../figures/compressao/pareado32/u95_individual_intervals.pdf) e [médias do piloto](../../figures/compressao/pareado32/u95_representative_mean.pdf).
- Revisões dos [controles finitos](../../results/C08/paired32/ROOT_finite_review.json), da [reprodução e KL](../../results/C08/paired32/ROOT_replay_review.json) e da [síntese pareada](../../results/C08/paired32/ROOT_result_review.json).

Os caminhos absolutos em recibos históricos apontam para o ambiente da
execução. Os arquivos comprimidos conservam seus bytes e permitem
restaurar a estrutura relativa; a mudança de prefixo deve ser explícita.
A figura das médias recebeu apenas ajuste de legenda e espaçamento do
título depois da revisão visual; o original e a fonte do ajuste foram
preservados, sem recalcular o bootstrap.

## Limitação determinante

As diferenças finitas de logL entre implementações foram pequenas nos
pontos examinados: máximo nativo–harmônico de 8,88e−6, harmônico–harmônico
de 9,54e−8 e SciPy–harmônico de 1,60e−11. Isso não constitui uma prova
uniforme sobre o domínio posterior.

A avaliação de CDF por nuvens finitas usa 512 grupos independentes,
cada um compartilhando 17 massas. A maior alteração absoluta da CDF da
medida de controle ao refinar a massa foi 0,1888. Sua estabilidade entre
implementações não certifica a quadratura absoluta. MCSE nula sem a
identidade algébrica exigida também permaneceu como falha, sem presumir
erro físico grande nem relaxar a regra após observar os resultados.

A escala prospectiva de interesse é ±0,01. Os intervalos operacionais
propagados não têm resolução para classificar os contrastes nesse nível.
As médias pontuais pequenas de B−C não são evidência de equivalência.
O bootstrap com n=24 é aproximado, conserva todos os casos e não fornece
certificação conjunta de cobertura de 95% com os intervalos assintóticos.

## Custos e interrupção preservada

A execução física dos controles terminou. Seu processamento estatístico
atingiu o teto original de CPU após 143 relatórios; o marcador original
permanece `FAILED_PRESERVED_NO_RETRY`. Uma execução separada calculou só os
181 relatórios faltantes, com a mesma álgebra e sem nova LL, ORF ou amostra.

| Execução | CPU externa, incluindo saída | Informação preservada |
|---|---:|---|
| Controles originais | 597,413 s | Teto original 600 s, falha final explícita, 143 relatórios completos |
| Continuação estatística | 56,304 s | Teto adicional 300 s, 181 relatórios, zero física nova |
| Total dessas duas execuções | 653,717 s | Não altera retroativamente o orçamento original |
| Síntese pareada e figuras iniciais | 15,181 s | Teto 60 s, bootstrap por ID; zero MC posterior novo |

Os controles cobraram 9.892.288 das 10.031.616 LL reservadas, pois quatro
nuvens interromperam por saturação. Os arquivos físicos e estatísticos
originais mais a continuação somam 126.286.202 bytes, abaixo de 128 MiB.
Os recibos individuais distinguem CPU, tempo decorrido, RSS e memória dos
arrays. Tempos de transporte, revisão, redação e compilação não estão
embutidos nesses números científicos.

## Reprodutibilidade e próximos estudos

[Integração das tabelas](INTEGRACAO_TABELAS.md) documenta transporte sem perda
e os refinamentos necessários. Os [pacotes das campanhas](../../results/C08/campaign_archives/)
retêm produtos compactos, propostas, sementes, estados, recibos e histórico
de falhas. Seus verificadores internos preservam a versão usada em cada
transporte. A verificação de SHA prova identidade dos arquivos, não
validade científica das aproximações.

C09 examina prioris, covariâncias e ruídos em desenhos próprios. Melhorar
a resolução horizontal dos quantis deste C08 permanece uma extensão
metodológica identificada, sem aprovação implícita pela execução das
etapas seguintes. C08 não reivindica um domínio de equivalência de limites
de massa, prioridade absoluta frente à literatura recente, análise de
dado observacional ou artigo já aceito.
