# Histórico da continuação C09 até v0.9.0

O marco v0.9.0 encerra a entrega C09 no alcance condicional descrito em
`docs/c09_auditoria_entrega.md`. Os registros abaixo preservam os estados
intermediários e suas pendências à época; não substituem o estado atual
do README, as notas do release ou a seção de produção no capítulo 8.

Após a publicação v0.8.12, o usuário pediu retorno aos marcos originais.
Não publicar um release por lote numérico. Este registro integra o trabalho
em andamento; não declara C09 concluído nem substitui o PDF publicado.

## Consolidação científica e primeira revisão editorial

Arquivamento concluído após a revisão abaixo: 24.238 arquivos lógicos em
11 ZIPs novos e 20 existentes, incluindo reconstrução de três caches
particionados. Todos foram restaurados em pasta separada e relidos para
conferência de SHA-256. Ver `docs/c09_restauracao_producao.md` e o recibo
de restauração. Os 164 testes de componentes passaram; a única mudança
no inventário C07 foi a inclusão dos dois módulos C09. Os nove testes
específicos C09 também passaram. A auditoria de publicação ainda não foi
concluída e nenhum commit de fechamento ou tag foi criado.

A síntese de produção reúne 90 grupos descritivos e 39 contrastes, com
14.268 diferenças pareadas. Os quantis de análises sem aprovação de malha
e resposta são [0,1], sem remoção de IDs. Médias e percentis propagam os
intervalos numéricos; não são intervalos de confiança populacionais.
Fontes e auditoria: `results/C09/robustness_synthesis/`. A tabela completa
está em `docs/c09_sintese_robustez_producao.md`.

O capítulo de robustez incorpora a produção em `08_producao_c09.tex`:
prioris e suporte, fatorial da covariância, omissão de contaminantes, ruído,
espectros, distâncias, SBC e interpretação de h/T. A diagonalização tem
efeitos de ambos os sinais; omissões podem reduzir artificialmente os
limites. As não rejeições SBC permanecem condicionais às verificações
numéricas, sem declaração de aprendizado ou validação observacional.

A compilação de conferência terminou com 139 páginas, sem referências
indefinidas ou caixas excedentes detectadas pelo verificador. As páginas
119–123, que contêm a nova seção e sua transição, foram renderizadas e
inspecionadas visualmente: texto e tabela legíveis, sem sobreposição.
Trata-se de PDF local de conferência em `tmp/latex/dissertacao/`, ainda
com os metadados da última versão publicada; não é o release v0.9.0.
Faltam arquivamento integral dos caches de produção, revisão do documento
cumulativo, auditoria final, metadados, manifesto, commit, tag e push.

## Diagnóstico dos eventos da produção

Estado mais recente: limiares físicos das distâncias concluídos, com 735
novos pares e 765 reutilizados; três resoluções aprovadas. Acumulados D3:
7.920 nós e 85.695.910.009.872 produtos. Acumulado C09: 67.072.009 likelihoods.
Eventos das 25.956 análises calculados: 23.669 aprovados operacionalmente,
2.287 indeterminados. Síntese SBC completa dos 18 grupos/126 testes:
116 não rejeições condicionais e 10 indeterminados, sem certificado físico
uniforme ou conclusão de aprendizado. Os parágrafos seguintes preservam a
sequência anterior; ver o documento de eventos para o resultado atualizado.

Continuação com limiares físicos: 22.956 densidades avaliadas nas respostas
salvas das massas verdadeiras, todas concordantes com SciPy; 45.912 avaliações
novas e acumulado de 67.063.009. Reintegração: 21.509 critérios operacionais
aprovados e 1.447 indeterminados. A mudança máxima de probabilidade ao trocar
o limiar interpolado pelo físico foi 0,139777, apesar de diferenças pontuais
de logL menores que 0,001. Distâncias e controle físico dos domínios dos
eventos continuam pendentes. Os números abaixo descrevem o diagnóstico
anterior com limiares interpolados.

O integrador contínuo de eventos passou nos testes analíticos e foi aplicado
às 25.956 análises: 24.983 estáveis na tabela interpolada, 834 com falhas
anteriores de resposta e 139 com envelope de evento acima de 0,002. Nenhuma
likelihood ou ORF adicional foi calculada; o acumulado continua 67.017.097
avaliações de likelihood. Os limiares físicos na massa verdadeira continuam
pendentes, e os PIT físicos de logL permanecem [0,1]. Ver
[diagnóstico dos eventos](c09_eventos_producao.md) para escopo, custos e hashes.

## Referência de distância

Seis novas ondas adaptativas foram concluídas e auditadas, sem repetir jobs.
Acrescentaram 2016 pares massa/escala, 21806285053824 produtos reais estimados
e 18468 avaliações de likelihood. Os trechos instrumentados registraram
654,75 s CPU nas respostas e 22,08 s nas densidades. O total C09 é 5812197
avaliações. Todos os controles ORF finitos e os 324 controles SciPy gravados
passaram. Não houve a falha de serialização do lote anterior.

Dez de doze referências passaram na última onda. Permanecem pendentes
A0_CN do dado 13, nominal e mistura: estimadores normalizados 0,0033506 e
0,0025045, acima de 0,001. Todas as comparações funcionais com GL64 seguem
dentro das tolerâncias. Não escolher uma onda intermediária mais favorável.
Quantis, W1 e eventos das distâncias continuam exigindo validação própria.

A continuação revisou prospectivamente o teto de produtos D3 de 60 para
90 trilhões, mantendo 8000 nós, 120 milhões de likelihoods, limites de
memória, modelos, amostras e tolerâncias. A previsão conservadora de seis
ondas e 2500 nós de geração somava 81,54 trilhões e 7538 nós. A geração
efetiva preparada exige menos nós, mas nenhuma reserva adicional foi
automaticamente transformada em uma nova onda de referência.

Fontes e recibos: `tmp/c09_D3_reference_continuation/` e
`tmp/c09_D3_distance_reference_v4/` até `v9/`. A auditoria terminal está em
`tmp/c09_D3_reference_continuation/execution/audit.json`. Esses pacotes devem
ser arquivados com hashes no fechamento C09, preservando as versões anteriores.

## Produção preparada

O desenho original foi preservado em `configs/robustness/`; a configuração
de produção congela 5396 IDs e 25956 análises. As verdades são contínuas,
obtidas por inversão das três CDFs, sem escolha entre nós de integração.
Ruído e controles reaproveitam verdades uniformes com streams de observação
distintos. Um único latente global de distância é sorteado por dado, com
stream separado da observação; as contagens foram 131/235/134 nas três escalas.

Existem 1768 pares distintos massa/escala. Três respostas fixas já verificadas
são reutilizáveis; 1765 respostas novas permanecem por calcular. O primeiro
preflight de CPU foi recusado antes da ativação. A versão particionada em
84 workers, com até 256 nós, estima no máximo 57,06 s CPU por worker diante
do teto de 120 s. Seu custo inclui as reconstruções de bases: 19094518244544
produtos. Nenhuma ORF ou observação de produção foi gerada nesta preparação.

Preflight pronto: `tmp/c09_production_truth_backend_v2/prepared/plan.json`.
Executor: `tmp/c09_production_truth_backend_v2/run_backend.py`. A versão v1
permanece não ativável, conservando o diagnóstico que motivou a partição.
Depois das respostas, ainda será necessário auditar os três refinamentos,
gerar e conferir os dados, executar as inferências e sintetizar os grupos
SBC e os contrastes condicionais completos.

Dois testes de IDs, contagens, sementes, inversão das CDFs e latentes passaram.
`make check-robustness` incorpora esses testes aos procedimentos de verificação
e release. O objetivo completo C09–C13 permanece aberto.

## Execução da produção iniciada

O preflight v2 e seus inputs foram conferidos; a produção das respostas
foi iniciada em 84 lotes sequenciais. O progresso é gravado em
`tmp/c09_production_truth_backend_v2/backend_execution/summary.json`.
A geração dos dados, a reconstrução independente por operadores branqueados
e seis posteriores nominais de engenharia foram implementadas. Ainda não
foram executadas: aguardam o término e a auditoria das respostas físicas.
Nenhum novo release ou conclusão de C09 é declarado por essa ativação.

## Geração e controles nominais concluídos

Os 84 jobs terminaram e suas respostas passaram em reconstrução, hashes,
refinamentos e PSD. Foram usados 19094518244544 produtos e 1199,20 s CPU
nos workers; maior RSS 938 MB. As 1765 respostas novas e três reutilizadas
formaram o banco de verdades. Não é validação da interpolação posterior.

Os 5396 dados foram gerados em 6,72 s CPU e reconstruídos independentemente
em 5,54 s. O maior erro absoluto foi 7,11e-15, e o relativo 6,54e-16.
Sementes, latentes globais e todos os IDs foram preservados. Nenhuma posterior
da produção foi avaliada nessa geração.

As seis posteriores nominais dos dados piloto 13/14 passaram nos controles
primários e W1. O lote acrescentou 187197 likelihoods e 74,18 s CPU;
o total C09 passou a 5999394. O piloto D3 soma 171 análises com controles
primários e W1. A referência nominal A0 do dado13 foi resolvida com integração
D2 completa, sem alterar o resultado histórico da onda9; a mistura A0
desse dado permanece pendente. Os demais produtos das misturas exigem
validação própria e a calibração da produção ainda não foi realizada.

Arquivos restauráveis: `results/C09/production_generation/` e
`results/C09/D3_distancias_continuacao/`. O componente de integração em lote
e seus limites de interpretação estão descritos em
[Integração de massa em lote](integracao_massa_em_lote_c09.md).
Todos os processos deste lote estão encerrados. O próximo trabalho é o
confronto PTA do integrador em lote e a inferência dos dados de produção.
# Preparação da inferência nominal

O confronto do integrador em lote com as 140 análises do piloto também passou
usando cada oitavo e cada décimo sexto nó da malha fina original, preservando
os extremos de suporte e as fronteiras explícitas. Os relatórios
`results/C09/mass_batch_pta/stride_8.json` e `stride_16.json` registram os
resultados e as dependências. Nenhuma consulta adaptativa das referências
entra nessas malhas de ajuste, embora o mesmo backend físico seja compartilhado.

Decisão numérica prospectiva: para a produção nominal, usar essas malhas
aninhadas com interpolação positiva de log-verossimilhança e integração
contínua em alfa, em substituição aos painéis GL32/64 inicialmente propostos.
As tolerâncias científicas, modelos, amostras e prioris permanecem as mesmas.
Cada caso de produção ainda precisa passar nas comparações entre malhas;
falhas serão retidas. A concordância no piloto não certifica a produção.

`scripts/campanha_robustez.py prepare` gerou o plano local
`tmp/c09_nominal_production_v1/plan.json`: 21.456 posteriores nominais,
44.833.040 avaliações na malha fina, com reaproveitamento exato da malha
grossa. Restam 69.167.566 avaliações no teto global depois dessa reserva
e do histórico de 5.999.394 avaliações. O plano não está ativado: faltam
o executor e sua verificação prospectiva de CPU e memória.
Outras 4.500 posteriores (autocontroles comprimidos e distâncias), o painel
de sensibilidade a prioris, eventos de log-verossimilhança e a síntese SBC
continuam explicitamente no escopo. Nenhuma posterior de produção foi
calculada nesta preparação. Próximo release: v0.9.0, após concluir C09.
# Inferência nominal de produção concluída

O executor `scripts/executar_lote_nominal_c09.py` concluiu os 20 lotes:
21.456 posteriores, 45.584.000 novas avaliações de verossimilhança e
228,583 segundos de CPU. O acumulado de C09 é 51.583.394 avaliações.
Cada curva recebeu 16 comparações com respostas harmônicas preservadas,
16 avaliações correspondentes da tabela e três controles SciPy independentes.
Todos esses controles finitos passaram. Não constituem um limite uniforme
do erro físico.

Na comparação das duas malhas, 21.455 casos passaram. O caso
`s5_p0_c1_d49__A0_CN__omitted` permanece não resolvido: delta logZ
0,001272408 excede o critério 0,001. Trata-se da análise A0 que omite o
contaminante monopolar no cenário de razão unitária. Os demais critérios
registrados desse caso passaram; não se deve excluir o dado ou relaxar a
tolerância. O próximo passo é refinar sua integração com orçamento explícito.

`scripts/auditar_lotes_nominais_c09.py` verificou o inventário, caches, nomes
das curvas, contagem de avaliações e os critérios registrados. O relatório
está em `results/C09/nominal_production/audit.json`. Essa auditoria não é uma
nova integração independente. As execuções e fontes estão preservadas em
`tmp/c09_nominal_production_v1/execution/`, ainda a arquivar para publicação.
O primeiro lote tinha guarda de RSS mas não gravava o pico no recibo;
o executor foi corrigido antes dos outros 19 lotes, preservando a fonte
original. Não houve repetição do primeiro lote.

Continuam pendentes os autocontroles comprimidos, as misturas de distância,
o painel de prioris, PIT de massa, eventos e síntese SBC. Não há processo
em execução após esta campanha; C09 permanece aberto para v0.9.0.
# Refinamento nominal e autocontroles concluídos

O caso `s5_p0_c1_d49__A0_CN__omitted` foi recalculado com as malhas
originais fina e grossa do piloto. O delta logZ caiu para 6,49935e-5;
os demais critérios entre malhas também passaram. O resultado anterior
foi preservado, e as 16.710 novas avaliações foram integralmente cobradas.
O relatório de inventário e critérios está em
`results/C09/nominal_refinement/audit.json`. Ainda cabe confrontar o caso
refinado com uma referência funcional adaptativa; a comparação entre
malhas não substitui essa integração independente.

As três famílias de autocontroles também foram executadas, com 500
observações cada: diagonal variável, completa fixa e diagonal fixa.
O executor reutiliza `SelfControlGroup` do piloto, mantendo cada vetor
B10 como observação comprimida real. Os controles SciPy usam contrações
de traço independentes, média variável e a covariância correspondente,
com âncora em u=0,5 nos modelos fixos. Não foram criados canais fictícios
nem novas observações. Todas as 1.500 posteriores passaram nos controles
finitos e nas comparações entre malhas. O relatório está em
`results/C09/self_production/audit.json`; fontes e execuções estão em
`tmp/c09_self_production_v1/` para arquivamento antes da publicação.

Os autocontroles consumiram 3.187.500 novas avaliações. Incluindo o
refinamento, C09 acumula 54.787.604 avaliações. Há 22.956 posteriores
nominais/autocontroles distintas calculadas; o refinamento não acrescenta
um dado nem uma nova análise a essa contagem. A calibração SBC não foi
declarada concluída. Permanecem distâncias, painel de prioris, referências
funcionais adicionais, eventos, síntese, redação e publicação v0.9.0.
# Painel pareado de prioris concluído

`scripts/painel_prioris_c09.py` executou as 1.600 integrações previstas
nos primeiros 32 dados centrais, dez modelos e cinco prioris/cortes,
com 1.280 contrastes em relação à uniforme. As 320 integrações uniformes
reproduzem análises existentes e não acrescentam dados à produção.
Todos os casos passaram na comparação entre malhas. O painel reutilizou
integralmente as verossimilhanças: o acumulado permanece 54.787.604.
CPU: 11,126 s; pico RSS: 409.141.248 bytes.

Os resultados e hashes estão em `results/C09/paired_prior_panel/`.
`docs/c09_sensibilidade_prioris_producao.md` apresenta as medianas
descritivas, os quantis das prioris e as medidas de informação. Há
sensibilidade dos quantis à medida e ao suporte; esse painel não autoriza
uma alegação SBC para prioris diferentes da geradora. Os cortes
logarítmicos adicionais ainda precisam de referências funcionais
independentes antes do fechamento científico de C09.
# Referências adaptativas de produção concluídas

Foram concluídas 13 verificações primárias e W1 independentes: o caso
nominal refinado e os cortes logarítmicos 0,0001/0,01 nos dados centrais
0 e 31, para A0 e B_CN/B_G completos variáveis. Todas passaram.
Os cortes de CDF e quantis foram congelados antes da referência GK21;
W1 foi confrontado com duas integrações DOP853 de tolerâncias e passos
distintos, cada posterior com seu próprio normalizador. As consultas
foram feitas diretamente ao backend de verossimilhança, sem interpolar
a tabela posterior usada no painel. Isso ainda compartilha a tabela
física de respostas e não prova erro físico uniforme.

Máximos: delta logZ 1,59291e-4, CDF 7,99159e-5, KL 9,70028e-5 e
W1 2,86066e-4. Todos os intervalos de quantis passaram no teste de
cruzamento com as incertezas operacionais da referência. O caso refinado
tem W1 de referência 0,4607538358.

A primeira tentativa falhou na interface escalar/vetor da chamada ao
integrador, após três avaliações de ligação com o cache. A correção
preservou fontes, recibo e cobrança da falha. As execuções concluídas
consumiram 80.120 novas avaliações; com as três da tentativa inicial,
o acumulado de C09 é 54.867.727. CPU concluída: 25,275 s; tentativa
inicial: 1,083 s. Não foram gerados dados ou novas respostas físicas.

`results/C09/production_references/` contém relatório e ZIP de 1.168.395
bytes, com todos os membros verificados por hash. O alcance é representativo:
não equivale a referências adaptativas para todos os 1.280 contrastes.
Continuam pendentes as misturas de distância, eventos, síntese SBC,
consolidação científica, redação e publicação de C09. Todos os processos
desta rodada terminaram.
# Distâncias: extremos concluídos, falha localizada nos controles

Foram calculadas 38 respostas completas adicionais: 19 massas para cada
escala de distância 0,9/1,1. Os extremos u=0 e u=1 entram no ajuste;
17 massas interiores por escala foram reservadas como controles. As três
resoluções físicas passaram. O acumulado de D3 é 6.841 nós e
74.016.010.752.528 produtos reais, dentro dos tetos de 8.000 e 90 trilhões.
Execuções: `tmp/c09_distance_endpoints_v1/`.

O piloto misto recebeu 396 novas avaliações de verossimilhança, elevando
C09 a 54.868.123. As seis comparações entre malhas passaram, mas os
controles separados do ajuste reprovaram os dois casos A0. A maior
discrepância foi 0,0360254 em logL no dado14, u=0,9999; na nona onda
reservada, foi 0,0144483 em u=0,973125. Os quatro casos B passaram nos
controles aplicados. Não foi ativada inferência de produção das misturas.

`scripts/diagnosticar_interpolacao_distancias_c09.py` localizou 16
intervalos de ajuste associados às falhas, sem novos cálculos físicos.
Propôs 96 novos nós completos: pontos médios para ajuste e pontos de
quarto de intervalo reservados para controle, nas duas escalas. A proposta
está em `results/C09/distance_interpolation_diagnostics/diagnostic.json`.
Ainda exige preparação de orçamento e ativação próprias. Se os antigos
pontos de controle entrarem no ajuste refinado, serão explicitamente
reclassificados; os novos controles não podem entrar nesse ajuste.

Este resultado mostra por que concordância de integrais entre malhas
não basta para aceitar a interpolação da posterior. As tolerâncias foram
mantidas e as falhas preservadas. Todos os processos desta rodada terminaram.
# Três refinamentos locais de distância concluídos

Foram executados refinamentos de 96, 48 e 6 nós físicos completos,
mantendo PCHIP e as tolerâncias. Os números de intervalos problemáticos
caíram de 16 para 8 e depois 1. As contagens de aprovação nos novos
controles foram 4/6, 5/6 e 6/6; as comparações entre malhas passaram
nos seis casos em todas essas rodadas. A última maior discrepância em
logL foi 0,000865982 para A0 do dado14, abaixo de 0,001.

O alcance da última aprovação é local: dois novos pontos por escala no
último intervalo que falhava. Controles antigos entraram nos ajustes
seguintes e deixaram de ser independentes. Portanto, ainda cabe um
controle novo mais amplo antes de ativar as 3.000 posteriores de distância
previstas. Não se deve resumir esse resultado como validação uniforme
da interpolação em todo o suporte.

Uma comparação exploratória com spline cúbica nos controles da primeira
rodada produziu máximos A0 de 0,000970845/0,000712441, menores que os do
PCHIP. Ela foi apenas diagnóstica: não mudou o método adotado, não gerou
novas avaliações e não autoriza validação após escolha do interpolador
pelos próprios controles. O refinamento foi concluído com PCHIP.

`results/C09/distance_local_refinement/` arquiva os extremos e as três
rodadas, com todos os membros ZIP verificados por hash. A auditoria
recalculou as diferenças entre resoluções a partir das matrizes, conferiu
recibos e contagem. Incluindo os extremos, são 188 novos nós e 1.908
avaliações de verossimilhança. O acumulado de C09 é 54.869.635 avaliações;
D3 soma 6.991 nós e 75.643.182.776.784 produtos reais. Restam 1.009 nós
e aproximadamente 14,36 trilhões de produtos no orçamento vigente.
Todos os processos desta rodada terminaram; nenhum release foi criado.
# Controle amplo e banco de produção das distâncias

O cálculo interrompido tinha concluído todas as respostas físicas; ele
não foi reiniciado. O controle amplo de 64 massas reprovou inicialmente
os dois casos A0. Foram então executadas correções seletivas de 24, 30
e 12 nós completos. Somente os pontos reprovados entraram nos ajustes;
os demais permaneceram reservados para controle.

A auditoria final confrontou 75 massas distintas fora do ajuste,
incluindo 60 do teste amplo. Os seis casos passaram: máximos A0 de
0,000822619 e 0,000930791 em logL; os máximos B ficaram abaixo de
0,000057. Trata-se de controles finitos de um ajuste adaptativamente
construído, não de prova uniforme nem de validação dos 500 dados de
produção. O resultado está em `results/C09/distance_broad_validation/`,
com matrizes, falhas, fontes e execuções arquivadas e verificadas.

Essa sequência consumiu 194 nós completos e 1.962 avaliações de
verossimilhança. O acumulado é 54.871.597 avaliações, 7.185 nós D3 e
77.747.878.549.200 produtos reais. Restam 815 nós e aproximadamente
12,25 trilhões de produtos no orçamento vigente.

`scripts/preparar_atlas_distancias_c09.py` organizou as respostas diretas
já calculadas para a produção: 2.621 massas de ajuste, subconjunto grosso
de 2.028 massas e 75 controles. A cópia preserva os valores float64
exatos e os hashes de origem; não interpola respostas físicas nem faz
novas avaliações. O banco está em `tmp/c09_distance_production_v1/prepared/`.
A produção das posteriores e seus controles por caso ainda não foram
ativados. Todos os processos desta rodada terminaram.
# Produção das distâncias calculada e auditada

Os 500 dados registrados foram analisados pelos três modelos em dois
modos: mistura global correta e distância nominal fixa. Foram calculadas
as 3.000 posteriores, preservando todos os IDs. Todas passaram nas
comparações entre malhas e nos controles de normalização SciPy.

O controle pontual da interpolação passou em 2.166 casos. Para A0,
passaram 121/500 misturas e 45/500 análises nominais; os 834 restantes
permanecem não resolvidos nesse critério. Os máximos delta logL foram
0,00742959 e 0,0153285, respectivamente. Os quatro grupos B passaram
em todos os 500 casos. Aprovação das integrais entre malhas e aprovação
pontual são critérios distintos; não se deve transformar uma na outra
nem excluir casos da futura síntese SBC.

A primeira execução terminou os três componentes de verossimilhança,
mas excedeu o limite de RSS ao integrar posteriores (1.844.969.472 bytes).
Os caches foram preservados; um processo separado retomou a integração
por modelo, com pico de 667.648.000 bytes, sem repetir verossimilhanças
ou respostas físicas. Os 500 resultados que estavam somente em memória
no processo inicial não foram contados como análises adicionais.
CPU inicial: 22,389 s; recuperação: 8,067 s.

O custo foi de 12.145.500 novas avaliações de verossimilhança, elevando
C09 a 67.017.097. Nenhuma nova resposta física foi necessária. O inventário,
as contagens e a preservação dos seis grupos de 500 IDs foram auditados
em `results/C09/distance_production/audit.json`. As execuções estão em
`tmp/c09_distance_production_v1/`. Os caches ainda precisam ser arquivados
para publicação. No total, as 25.956 posteriores de base previstas foram
calculadas, mas isso não conclui os critérios funcionais e a calibração.
Eventos, PIT, síntese SBC e tratamento explícito das falhas permanecem
pendentes. Todos os processos desta rodada terminaram.
