# Produção C10 após o piloto controlado

Estado atual: campanha e síntese concluídas; 6.344 análises auditadas, sem descarte.
Não há novas otimizações planejadas. As seções abaixo preservam a evolução do desenho;
o fechamento está em `docs/c10_restauracao_producao.md` e nas notas v0.10.0.
O piloto e os testes de integração somam 14.980.724 avaliações, com 36/36 eventos operacionais aprovados,
sem promover os controles finitos a certificado físico uniforme. Recibos:
`results/C10/taylor_event_final_gate/audit.json` e auditorias vinculadas.

## Escopo preservado

O protocolo candidato `tmp/c10_execution_design/c10_protocol_candidate_v1.json`
prevê 500 dados nulos, 500 da priori conjunta e 192 de recuperação. Manter
sementes, seleção C, limiar BF10=10 e famílias de testes, após conferir a
consistência dos indicadores e hipóteses. São 5.960 análises D e 384 C,
totalizando 6.344. Não agrupar células de recuperação para fabricar uma taxa
binomial homogênea. Não comparar evidências A0/A/B entre espaços de dados.

Os parâmetros condicionais continuam u e epsilon, com nuisances fixadas.
O diagnóstico local de Fisher tem seis coordenadas e oito pontos, conforme
protocolo; deve incluir convergência das derivadas, projeção das nuisances e
condicionamento. Não substitui recuperação global ou um posterior de seis
parâmetros.

## Custos e reutilização a preparar

A malha 257 × 129 exige 210.322.632 valores para 6.344 análises. O teto
candidato de produção é 300.000.000. Repetir diretamente todas as referências
GL192/GL384 pode consumir o saldo antes de concluir os 500 dados SBC.
Não reduzir automaticamente as contagens ou declarar PITs tabulados como
validados no contínuo para fazer a campanha caber.

Uma alternativa agora verificada no piloto reutiliza os valores exatos
das malhas aninhadas, sem interpolar ORFs:

1. Manter as células de evento e a interseção Taylor/perturbação.
2. Integrar as uniões classificadas em epsilon com Simpson composto positivo,
   em duas resoluções aninhadas, reaproveitando a malha epsilon existente.
   Painéis finais nas fronteiras dyádicas requerem avaliações adicionais
   explicitamente cobradas. Diferenças de quadratura continuam operacionais.
3. Usar regras positivas aninhadas em u sobre os nós já calculados, comparando
   129/257/513 nós no piloto. O eixo u congelado é Chebyshev–Lobatto, não
   uniforme: usar pesos positivos de Clenshaw–Curtis, conferindo os nós reais
   de `axes.json`. Simpson uniforme em u seria incorreto; Simpson em epsilon
   continua possível porque esse eixo é uniforme. Confrontar as CDFs com as referências GL já
   aprovadas e com a representação bilinear, mantendo tolerâncias originais.
4. Medir custo completo por dado/modelo, memória e saída e congelar o executor de
   produção. Restam 35.182 avaliações no teto do piloto e 39,98 s
   de sua CPU de execução, incluindo uma reserva conservadora para a tentativa
   com falha de serialização; contabilizar qualquer experimento adicional.

Essa alternativa passou na comparação operacional do piloto: 18.468/18.468
fatias, 36/36 comparações completas e 80.564 avaliações adicionais na execução
integral. A auditoria independente reproduziu Simpson com diferença escalada
máxima de 4,43e-16 e os agregados CC sem diferença observada. Recibo:
`results/C10/nested_integral_audit/audit.json`. Isso não é um certificado
uniforme da quadratura física nem calibração populacional. Evitar reexecutar
os bancos GL concluídos: eles são a referência independente disponível.
A função atual de margem de massa foi escrita para as referências GL; uma
versão Simpson deve usar campos e metadados corretos e não renomear resultados
Simpson como GL16/32. Não acumular novamente margens de arredondamento em
relatórios já ajustados sem registrar a composição.

## Reserva de arquivos

O problema de espaço do primeiro refinamento foi registrado. As execuções
Taylor seguintes reservaram espaço antes de cada fatia e respeitaram os tetos.
Para muitos milhares de arquivos, percorrer toda a pasta antes de cada escrita
produz custo quadrático. Foi implementada uma contabilização incremental com tamanho
máximo de serialização/cache, reserva terminal e verificação final, mantendo
os limites reais. A execução aninhada consumiu 152.375.838 bytes antes do
recibo terminal, respeitando 192 MiB. Não alterar fontes ou ledger de execuções já congeladas.

## Cache, inventário e Fisher

O cache dos momentos independentes das observações reproduziu exatamente
5.160 replays em 2.580 casos. CPU do trecho comparado: 13,531 s sem cache e
12,169 s com cache; CPU total do benchmark: 27,422 s. Foram 259 entradas,
4.475.520 bytes numéricos e nenhuma nova densidade. A redução de tempo é
10,07%; não confundir a razão de velocidades 1,112 com redução de 11,2%.

A extrapolação simples desse trecho para 2.500 eventos e 257 massas é
3.030,42 s. Não é um limite superior e exclui densidades novas, ORFs nas
verdades, geração, tabelas, resumos e I/O. Ainda é necessário medir o executor
completo frente ao alvo de 3.600 s; a extrapolação isolada não ativa produção.

O inventário `results/C10/production_preflight_v1/plan.json` fixa 1.192
registros e enumera as famílias de 39/26/6 hipóteses. Nenhuma observação foi
gerada. A conferência corrigiu um erro anterior de resumo: os IDs 133 e 165
da recuperação já estavam no JSON original. Portanto são 96 dados C, não 94,
com 6.344 análises totais. O JSON original e as sementes foram preservados.
Restam 89.677.368 avaliações após o custo da malha fina. O lote candidato de
64 dados exige 10.608.960 valores D, abaixo do limite local de 15 milhões.

O módulo de Fisher dispõe de quatro testes analíticos aprovados: equivalência
CN/normal real de dimensão dobrada, informação de média e variância conhecida,
projeção de nuisance com degenerescência exata e estênceis nas fronteiras.
Não houve avaliação física de Fisher. A projeção usa o espaço dos escores e
não inverte direções singulares; diferenças finitas permanecem dentro do suporte.

## Medição do fluxo completo

`results/C10/full_flow_benchmark_v1/audit.json` confere a execução nos dados
existentes 0 e 3: dez análises D, 331.530 avaliações de malha e 10.766
avaliações adicionais para 2.570 eventos. As dez comparações primárias e os
vinte agregados CC passaram; os extremos das CDFs coincidiram com os do banco
independente anterior, sem diferença observada. Nenhuma população foi gerada.

CPU total: 15,976860 s; tempo decorrido: 16,57 s. O total do piloto passou a
14.964.818 avaliações, com CPU superior contabilizada de 1.760,024657 s.
Saída de 7.353.291 bytes antes do recibo terminal, inferior a 64 MiB.

A extrapolação linear dos trechos medidos é 3.823,59 s para eventos,
281,22 s para malhas e 31,70 s para resumos: 4.136,52 s, acima do alvo de
3.600 s. Não é um limite superior e o lote de dois dados D não caracteriza
exatamente lotes de 64 nem a complexidade C. O resultado impede considerar
a viabilidade já demonstrada. A próxima revisão deve reduzir o custo dos
callbacks das densidades adicionais, conservando as leis normalizadas,
contadores, referências e populações. Não repetir a malha do benchmark:
seus valores e caches estão preservados para reutilização exata.

## Requisitos para ativação

- Pré-requisito C09 e fechamento do piloto vinculados por SHA-256.
- Desenho final, eixos, sementes, métodos, recursos e códigos congelados.
- Testes e benchmark do executor com lote limitado, sem chamar produção
  automaticamente a partir de um teste sintético.
- Falhas e reservas incompletas preservadas; contagens globais não reiniciadas.
- Critérios estatísticos e numericamente indeterminados definidos antes das
  observações da população. Publicação somente após fechar C10 no alcance
  efetivamente demonstrado e atualizar PDF, README, manifesto e notas.

Essas revisões são de engenharia/científicas dentro do trabalho autorizado,
não uma solicitação de confirmação adicional ao usuário.

Referência metodológica a consultar na implementação dos pesos:
[Trefethen, Clenshaw–Curtis and Gauss Quadrature, capítulo 19](https://epubs.siam.org/doi/10.1137/1.9781611975949.ch19).
A comparação de métodos não dispensa os testes de positividade, soma dos pesos,
integração de polinômios e coincidência com o eixo realmente congelado.

## Execução da campanha

A comparação dos avaliadores preparados e limites de Taylor em lote concluiu
2.570 eventos: 5.140 pontes internas e 10.766 avaliações adicionais. A maior
diferença de densidade foi 2,14e-14 e os extremos das CDFs não mudaram.
O piloto ficou em 14.980.724 valores e 1.775,859936 s de CPU superior
contabilizada. Seus limites históricos não foram modificados.

A estimativa inicial de 3.600 s da produção foi revista prospectivamente para
7.200 s, antes de gerar a população. O teto de 300 milhões de avaliações,
as populações e as hipóteses estatísticas permanecem iguais. A revisão está
em `configs/scalar/c10_production_v1.json`; não é aprovação retrospectiva
de uma execução que excedeu o limite. Atende também à orientação do usuário
de priorizar a execução e encerrar otimizações adicionais.

`tmp/c10_population_v1` contém 1.192 observações, com 1.000 novas massas e
30.000 matrizes ORF. A auditoria em `results/C10/population_generation_audit`
reconstruiu todas as verdades exatamente e os dados com diferença escalada
máxima de 4,09e-16. A produção está em `tmp/c10_production_v1`, com log
`tmp/c10_production_stdout.log`. Verificar o processo e os recibos antes de
retomar; nunca reiniciar uma pasta existente. São 6.344 análises esperadas.

O diagnóstico de Fisher foi concluído em `results/C10/fisher_v4`, após
preservar tentativas rejeitadas pelos controles de simetria das diferenças
finitas. A parte antissimétrica, limitada pela escala de arredondamento das
diferenças, foi projetada; não houve clipping de autovalores. Os passos
foram refinados até 0,001/512, com estênceis unilaterais no suporte. As 24
matrizes passaram na convergência e em `results/C10/fisher_audit`, com erro
relativo independente máximo de 1,89e-5. Os postos são diagnósticos nas
escalas e no limiar numérico declarados, não provas de posto físico exato.

As tentativas de ORF de Fisher sem medição terminal receberam reservas
conservadoras de 60 s cada; o total superior de ORF é 267,287417 s. As
tentativas posteriores reutilizaram os nós. Esse número é um limite
contábil, não uma medição de CPU realizada.

A síntese foi congelada em `results/C10/population_synthesis/plan.json`.
Depois da conclusão e da auditoria da produção, executar a síntese, incorporar
os resultados populacionais, arquivar os dados e preparar o commit/release
v0.10.0. A existência de resultados de Fisher não encerra C10.
