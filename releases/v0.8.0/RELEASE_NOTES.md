# v0.8.0 — C08: compressão em frequência e resolução numérica

O PDF cumulativo incorpora o capítulo 7, com teoria da compressão, mapas da
resposta, comparação pareada e limitações de precisão explicitamente reportadas.
A campanha não resolveu equivalência nem diferença material dos limites de massa
na escala prospectiva de 0,01 da largura da priori.

## Conteúdo executado

- Mapas em massa, espectro, amplitudes, duração de 4,5/9/15 anos e janela retangular/Hann projetada; expansão fraca de C_beta−B e efeitos das fases junto ao limiar.
- Descrição dos 500 dados de C07; 16 alvos de engenharia e 128 alvos C_beta/C_full; 160 HIGH de C07 reproduzidos em 640 réplicas com SHA e estados RNG originais.
- Controles em 288 nuvens e 324 vínculos; 76/288 principais satisfazem regras finitas. Quatro nuvens saturadas permanecem inconclusivas.
- Todos os 5760 quantis preservados: 1460 intervalos operacionais, 4300 inconclusivos [0,1]. Sete contrastes pareados, 4480 diferenças de quantis e 1120 de larguras.
- Síntese piloto de 24 IDs com bootstrap pareado com 10000 réplicas; oito casos de fronteira separados. Todos os 224 contrastes individuais primários e sete médias piloto inconclusivos.
- Divergências posteriores A_G→B_G em quatro IDs fixos, com MCSE e momentos conjuntos, sem interpretação como fator de Bayes.

## Verificação

Fontes e protocolos congelados, testes sintéticos específicos, referências harmônicas
e SciPy e auditorias de produtos preservados. A síntese foi recomposta por fórmulas
independentes de diferenças, intervalos, larguras e percentis arquivados. Pacotes
sem perda foram verificados e restaurados por SHA, conservando versões dos
verificadores, dependências externas e o histórico de falhas. As verificações
científicas gerais exigidas pelo projeto integram o fechamento e o workflow.

O PDF foi renderizado e inspecionado; o manifesto vincula seus bytes às fontes.
A figura das médias recebeu somente ajuste visual de legenda e título, com
original preservado e sem recalcular valores ou bootstrap.

## Limitações e próxima etapa

A avaliação de erro da CDF é operacional e finita, sem prova uniforme. A maior
mudança absoluta na CDF da medida de controle sob refinamento de massa foi 0,1888;
estabilidade entre implementações não certifica a quadratura absoluta. Falhas
incluem MCSE nula sem identidade comprovada. Médias pontuais pequenas não
constituem evidência de equivalência.

A execução original dos controles atingiu o teto de CPU na análise compacta,
após concluir a física: 597,413 s. A continuação estatística custou 56,304 s adicionais,
reutilizou 143 relatórios e calculou 181 faltantes, sem LL/ORF/amostras novas.
O estado original de falha não foi reescrito. Esses custos têm orçamentos separados.

C09 prepara estudos de robustez a prioris, ruído e covariâncias. A melhoria da
resolução dos quantis C08 continua uma extensão metodológica identificada.
Este release não certifica calibração de 32 dados, domínio de equivalência,
prioridade absoluta, aplicação observacional ou aprovação acadêmica.
