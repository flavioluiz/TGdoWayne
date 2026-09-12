# Eventos de log-verossimilhança: diagnóstico da produção C09

O integrador `src/inference/likelihood_events.py` calcula a massa posterior
das regiões em que a log-verossimilhança interpolada está abaixo de um limiar.
Cada intervalo PCHIP é monotônico; cruzamentos internos são isolados por
bisseção e integrados por quadratura positiva. Regiões desconectadas são somadas.
Segmentos constantes no limiar são tratados como átomos, com CDF estrita e
inclusiva separadas. Nenhuma randomização é aplicada implicitamente.

Os envelopes das raízes têm largura em alfa de até 1e-11. Eles não incluem
erro de quadratura nem erro da interpolação da função física. Os testes
analíticos verificam orientações crescente/decrescente, offsets de ±730,
regiões desconectadas, estatísticas constantes sob três prioris, patamares
parciais e rejeição de entradas e orçamentos inválidos. Os nove testes C09
passaram na execução que introduziu este componente.

## Resultado da execução

`scripts/diagnosticar_eventos_producao_c09.py` processou todas as 25.956
análises, preservando os identificadores e substituindo somente o resultado
nominal do caso de omissão previamente refinado. Comparou malhas fina/grossa
e quadraturas de ordens 32/16. Em cada tabela, o limiar foi calculado pelo
próprio PCHIP na massa verdadeira. Isso testa a estabilidade da estatística
interpolada; não valida o limiar físico.

- 24.983 análises apresentaram envelope observado de até 0,002 e passaram
  nos critérios anteriores de malha e resposta.
- 834 mantêm falhas anteriores de resposta no cenário de distâncias.
- 139 adicionais apresentaram envelope de evento maior que 0,002.
- Não foram identificados átomos positivos nesta produção. O maior número
  de cruzamentos internos foi 195; eles não foram descartados ou truncados.
- Custo: 26,04888 s CPU; pico RSS de 1.002.487.808 bytes, abaixo de 1,5 GiB.
- Nenhuma avaliação adicional de likelihood ou resposta física foi feita.

Os registros e hashes estão em `results/C09/production_event_diagnostics/`.
O SHA-256 de `records.json` é
`e6a738c97466b485eebec27c94ada66a04fae150a2d9a0801580f95923b73228`.
Todos os hashes de entrada foram conferidos após a execução.

## Pendência antes da síntese SBC

Todos os intervalos **físicos** de PIT de log-verossimilhança permanecem
`[0,1]`, sem resolução declarada. É necessário avaliar os limiares diretamente
na massa verdadeira, comparar os domínios de evento e incorporar as limitações
da resposta. Na mistura de distâncias, os componentes precisam ser combinados
globalmente antes de formar o limiar. A estabilidade obtida com o limiar da
própria interpolação não substitui esse trabalho.

Estes resultados não alteram a síntese preliminar de massa, não concluem C09
e não geram um release intermediário. O próximo marco continua sendo v0.9.0.

## Continuação: limiares físicos nominais e controles B10

Foram avaliados os limiares nas respostas harmônicas salvas das massas
verdadeiras, após a inferência, sem reutilizar a interpolação da posterior
para definir o limiar. As âncoras de covariância fixa foram mantidas como
na produção. As 22.956 densidades passaram na comparação independente com
SciPy (maior diferença absoluta 4,8317e-13). Cada densidade e sua referência
foram contabilizadas: 45.912 avaliações novas, acumulado C09 de 67.063.009.
Não houve novos nós de resposta. Custo: 43,4792 s CPU e RSS 909.131.776 bytes.
Fontes, entradas e recibos estão em
`results/C09/physical_truth_thresholds_nominal/`.

Os eventos foram reintegrados com esses limiares nas malhas fina/grossa e
ordens 32/16, substituindo o caso nominal de omissão pelo cache refinado.
Das 22.956 análises, 21.509 passaram nos critérios operacionais e 1.447
permanecem com intervalo operacional [0,1]. A maior diferença entre limiares
físico e interpolado foi 0,00070727; todos passaram no critério pontual 0,001.
Isso não assegura estabilidade do evento: no caso `s1_p2_c0_d272__A_G`, uma
diferença de limiar de 1,2091e-5 alterou a probabilidade em 0,139777. Seu
envelope de discretização com limiar físico foi [0,772839; 0,782171], acima
da tolerância 0,002. O caso permanece indeterminado, sem exclusão do registro.

A conclusão é limitada: concordância pontual da log-verossimilhança não
fornece, por si só, um limite de erro da probabilidade de seus subníveis.
Os domínios dos eventos ainda usam PCHIP e não têm certificado físico
uniforme. Não transformar os 21.509 critérios operacionais aprovados em
uma afirmação de calibração física completa. A síntese SBC anterior ainda
não incorpora estes resultados e as 3.000 análises de distâncias continuam
pendentes de limiares completos.

`results/C09/events_direct_threshold/` contém os registros; seu SHA-256 é
`2a30855fe052f55b1d13bf95bc9c8f51df7735d4591ec02603ac0caac131b13c`.
Os hashes de registros e entradas das duas execuções foram conferidos.
A reintegração custou 21,814479 s CPU e RSS 722.124.800 bytes, sem novas
avaliações de likelihood.

## Continuação: distâncias e família SBC completa

Foram calculados somente os 735 pares massa/escala ausentes, reutilizando
765 pares já disponíveis. As três resoluções passaram: diferença angular
máxima 2,8969e-12, diferença harmônica 9,6589e-15, menor autovalor 0,196526.
O lote custou 75,854454 s CPU e 7.948.031.460.672 produtos reais estimados.
Acumulados D3: 7.920 nós e 85.695.910.009.872 produtos, dentro dos tetos
8.000 e 90 trilhões. Restam 80 nós; isso não autoriza descartar falhas.
Fontes e execuções estão em `tmp/c09_distance_truth_thresholds_v1/`, com
auditoria e banco reunido em `results/C09/distance_truth_responses/`.

Os três componentes de likelihood foram avaliados na massa verdadeira
para cada uma das 500 realizações e três análises. A mistura foi formada
globalmente com pesos 0,25/0,50/0,25, após todos os canais. As referências
SciPy concordaram em todas as 3.000 análises finais, com diferença máxima
4,5475e-13. Foram contabilizadas 9.000 avaliações novas, incluindo referências;
o acumulado C09 é 67.072.009. Custo: 6,805541 s CPU, RSS 832.978.944 bytes.

A integração com limiar físico aprovou os critérios operacionais em 2.160
das 3.000 análises de distâncias; 840 permanecem indeterminadas. Quatro
limiares diferiram do interpolado em mais de 0,001, com máximo 0,00284772.
A maior mudança de probabilidade do evento foi 0,0219865. O resultado
mantém os critérios anteriores de resposta e não substitui a posterior por
uma ajustada aos limiares. Auditorias e registros:
`results/C09/physical_truth_thresholds_distance/` e
`results/C09/events_distance_direct_threshold/`.

Assim, há eventos com limiar físico para todas as 25.956 análises de base:
23.669 passam nos critérios operacionais e 2.287 permanecem indeterminadas.
Não existe certificado físico uniforme dos domínios PCHIP.

A síntese `results/C09/SBC_operational_events/` incorporou esses eventos à
família original de 18 grupos de 500 observações e 126 testes, sem remover
IDs indeterminados. No subconjunto SBC, 8.621 PIT de massa e 8.179 PIT de
logL estão resolvidos operacionalmente. Com correção de Holm para a família
completa, 116 testes resultaram em não rejeição para todos os valores
admissíveis dos intervalos fornecidos; 10 são numericamente indeterminados.
Não há rejeição robusta, mas os resultados dependem da validade dos envelopes
numéricos observados. Não demonstram calibração física completa, equivalência
entre modelos ou aprendizado da massa. A definição contínua do PIT de logL
pressupõe estatística física não constante; nenhum átomo foi encontrado nos
interpolantes. A síntese preliminar anterior foi preservada como histórico.

Todos os hashes de entradas e registros foram conferidos após as execuções.
C09 continua aberta para consolidação científica, redação e publicação do
marco cumulativo v0.9.0; nenhum release intermediário foi criado.
