# Piloto D3: cenários e inferências condicionais

Foram gerados 16 casos de engenharia, excluídos da futura amostra SBC:
três prioris centrais, ruído vermelho/branco reforçado, quatro combinações
de espectro e massa, quatro contaminantes, duas distâncias alteradas e massa zero.
As massas aleatórias vêm das prioris contínuas, com namespace de RNG próprio.
Os casos de distância usam escalas fixas 0,9/1,1 como controles de estresse;
não são sorteios da mistura populacional de distâncias.

Dez pares distintos de massa/distância exigiram respostas novas, em quatro
frequências e três resoluções. As diferenças máximas foram 2,87e-12 no
refinamento angular e 4,44e-15 no harmônico. Esses controles se referem aos
pontos de geração; não validam uma interpolação nas distâncias novas.

A primeira execução atingiu o limite operacional de memória após salvar
dois canais: pico observado 1,81 GB. O teste do limite ocorreu após uma
alocação, portanto não se alega que esse pico ficou abaixo do teto.
Uma continuação em processos separados por resolução reutilizou os canais
salvos e concluiu os outros dois. Seu maior pico de worker foi 739 MB.
A falha, as operações cobradas e os arquivos anteriores foram preservados.

Os novos componentes tratam o dipolo como a matriz de Gram `p @ p.T`, com
diagonal unitária e correlações negativas preservadas. O espectro contaminante
mantém índice 13/3 e razão de PSD no pivô, mesmo quando o sinal muda de índice.
Há quatro testes de cenários aprovados, cobrindo geometria, espectro,
geração dos controles de covariância e mistura de distâncias.

Para a mistura, a soma de log-likelihoods das frequências ocorre antes de
marginalizar a escala global. Não se usa covariância média nem uma escala
independente por frequência. Os componentes matemáticos dos controles próprios
de covariância foram testados, mas seus dados e posteriores piloto ainda faltam.

Os 14 casos com distâncias nominais têm dez análises cada: A0, A_G e
o fatorial completo/diagonal e fixo/variável sobre dados CN e gaussianos.
As 140 curvas passaram nos controles finitos de resposta em 17 pontos por curva
e em três densidades SciPy independentes, antes da integração posterior.
As inferências reutilizam a integração D2 e mantêm gates próprios por quantidade.
As 140 passaram nos cinco controles primários. Foram contabilizadas 3030608
avaliações nas posteriores e 5600 nas verificações finitas. As posteriores
consumiram 222,08 s CPU; W1 e eventos dos novos dados continuam pendentes.
O [arquivo de auditoria](../../results/C09/D3_piloto/audit.json) contém os
estados individuais, inclusive qualquer quantidade não resolvida.

- [Fontes, dados, caches e recibos](../../results/C09/D3_piloto/fontes_dados_execucoes.zip).
- [Manifesto](../../results/C09/D3_piloto/manifest.json).

Ainda faltam as posteriores da mistura de distâncias, os controles próprios
de covariância, W1/eventos para os novos dados, cenários de contaminantes omitidos
e a campanha representativa D3/SBC. O piloto não mede distribuições de limites
nem encerra C09. Os controles W1 já publicados para D2 permanecem válidos
no seu escopo; não são transferidos automaticamente aos novos dados.
