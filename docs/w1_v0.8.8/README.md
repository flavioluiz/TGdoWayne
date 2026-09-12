# Distância W1: referência independente e resultados D2

As 40 análises das 13 curvas D2 passaram no controle operacional próprio de
W1 entre posterior e priori. Os cinco controles primários da v0.8.7 permanecem
preservados. C09 continua em andamento: esta extensão não é calibração SBC.

A referência integra conjuntamente a massa posterior acumulada e
`abs(F_posterior - F_priori) * cos(alpha)`, com `alpha = asin(u)`, usando
DOP853 e likelihoods do backend ORF congelado. Não utiliza o interpolante
posterior. As normalizações vêm da quadratura independente publicada em D2.
As integrações respeitam o suporte de cada priori e os cortes CDF já registrados.
Dois refinamentos (`rtol` 1e-8/1e-9, `atol` 1e-10/1e-11 e passo máximo
0,01/0,005) são confrontados com três integrais tabuladas. O critério W1 é
0,001; CDF e normalização também têm controles próprios.

Quatro testes analíticos passaram: likelihood constante em dez medidas
próprias; inclinação linear, com W1 igual ao deslocamento exato da média;
CDFs com múltiplos cruzamentos; e retenção da sensibilidade à normalização.
No controle constante, refinar as tolerâncias reduziu W1 espúrio de
1,57e-8 para 7,98e-10. O limiar do teste não foi afrouxado.

O piloto consumiu 10594 avaliações e 7,36 s CPU; a extensão sequencial,
77393 avaliações e 46,17 s CPU. Todos os 13 caches anteriores foram
conferidos bit a bit e três avaliações por curva verificaram a ponte
com o mesmo kernel. Não foram gerados novos dados ou tabelas ORF.
Maior discrepância W1: 3,654e-6. Os refinamentos são controles operacionais,
não limites rigorosos uniformes do erro físico. Comparar esses valores
entre prioris diferentes também altera a distribuição de referência.
Os tempos deste lote medem o trecho instrumentado do driver, após as
importações numéricas; não representam todo o custo editorial ou de testes.

- [Auditoria e 40 resultados](../../results/C09/W1/audit.json).
- [Fontes e execuções](../../results/C09/W1/fontes_execucoes.zip).
- [Manifesto e dependências](../../results/C09/W1/manifest.json).

Os arquivos de execução foram preservados com seus recibos e caches. O piloto
inicial precedeu a generalização do driver para as demais curvas; essa mudança
de interface e verificação foi registrada no manifesto. As expressões numéricas
e os controles do piloto não foram alterados. A reprodução exige restaurar
também as dependências dos arquivos D2 e dos snapshots anteriores.

Permanecem pendentes os eventos de log-likelihood e D3: estudos representativos
de ruído, espectros, contaminantes, distâncias, variabilidade e calibração SBC.
