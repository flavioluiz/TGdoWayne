# v0.8.9 — Piloto D3 com 16 dados e 140 inferências nominais

Gerados 16 casos de engenharia com respostas refinadas nas massas de geração.
As 140 inferências dos 14 casos de distância nominal passaram nos controles
operacionais de normalização, CDF, quantis, momentos e KL. O lote de posteriores
consumiu 3030608 avaliações e 222,08 s CPU; verificações finitas acrescentaram
5600 avaliações. Esses casos não integram a futura amostra SBC.

Novos componentes cobrem dipolo, controles próprios de covariância e mistura
global de distâncias, com quatro testes aprovados. A falha por memória e a
continuação em processos separados estão preservadas, assim como fontes,
dados, respostas, referências e caches. O PDF cumulativo apresenta os resultados
e as pendências; C09 continua aberto.

Ainda faltam posteriores da mistura de distâncias, controles próprios,
contaminantes omitidos, W1/eventos dos novos dados e produção D3/SBC.
