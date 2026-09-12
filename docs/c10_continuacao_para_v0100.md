# Continuação C10 para v0.10.0

**Fechamento:** C10 concluído no alcance condicional; consulte as notas v0.10.0 e `docs/c10_restauracao_producao.md`. O texto abaixo preserva o histórico de preparação.


A v0.9.0 foi publicada e conferida remotamente no commit
`5c0ef80380dd9cbe776aa7246071e3fbfab20c91`. A extensão escalar permanece
aberta; não haverá release por lote intermediário.

## Estado terminal do primeiro piloto

O processo terminou normalmente, com todas as etapas previstas registradas,
11.930.676 avaliações de likelihood cobradas e concluídas e 365,109322 s
CPU agregada. Foram gravadas 20.736 fatias de referência, com 2.227.236
valores em cache. Nenhuma reserva ficou sem conclusão. A contagem não
equivale à aprovação numérica de todos os resultados.

A auditoria `results/C10/pilot_terminal_audit/audit.json` reconstruiu,
com operações independentes, a soma ponderada de numerador, massa ambígua
e denominador em todas as regras de integração: diferença máxima zero
em relação aos agregados registrados, sem denominadores ausentes.
Das 36 referências finais de evento, três passaram operacionalmente e
33 permaneceram [0,1]. Todas essas 33 falharam na largura do envelope
de CDF e na comparação com o evento bilinear. As mudanças de logZ entre
regras de u ficaram abaixo de 0,001; portanto, não se deve confundir a
estabilidade da normalização com resolução da fronteira do evento.

Persistem também as três falhas fina/grossa descritas abaixo. Não há
campanha populacional aprovada ou iniciada. O próximo trabalho é diagnosticar
e refinar os envelopes de classificação em epsilon e tratar as falhas
primárias, reutilizando os caches. Este registro substitui a indicação
de processo ativo dos parágrafos históricos seguintes.

## Piloto físico iniciado

Foi revisado o pacote `tmp/c10_exact_lifecycle_v1/`, com fontes e eixos
congelados. Os 11 testes sintéticos passaram novamente. Os recibos em
`results/C10/pilot_activation/` vinculam o pré-requisito C09, a revisão
da execução e a reutilização somente dos nós ORF históricos. A interpolação
linear histórica reprovada não foi aprovada nem usada.

O piloto contém 16 dados fixos de engenharia e nove análises, em geometria
C06 P10/K3/T15. A amplitude de população escalar multiplica a potência de
um único modo FP vinculado; as deformações transversal e longitudinal não
são ajustadas independentemente. O orçamento é 14.991.120 avaliações
alocadas, teto de 15 milhões, CPU agregada de 1.800 s e saída até 1 GiB.
O teto ORF herdado é 600 s, incluindo 133,905984 s históricos. Os limites
de RSS são 4 GiB no processo principal e 512 MiB em cada filho sequencial.
Isso é ativação de piloto, não aprovação de uma população de 500 dados.

O processo ativo foi iniciado com saída em `tmp/c10_physical_pilot_v1/`.
Na última inspeção, as três respostas refinadas, os dados, controles e
malhas estavam completos, e as referências dos eventos continuavam em
execução. Não iniciar novamente esse diretório: consultar primeiro o
processo e os recibos `complete.json` ou `FAILED_PRESERVED.json`.

## Verificações já concluídas

- Os controles SciPy passaram: diferença máxima de logL 3,4461e-13;
  limite epsilon=0 na fixture C06, 6,3949e-14.
- Foram verificadas 4.608 desigualdades de perturbação em epsilon nos
  controles finitos, sem violações. Isso não é certificado físico global.
- A reconstrução independente dos 16 dados, usando as sementes originais
  e contrações diretas, teve erro relativo escalado máximo 2,2204e-16.
  Recibo: `results/C10/pilot_generation_audit/audit.json`.
- A integração independente por pesos trapezoidais das 216 tabelas
  positivas reproduziu evidências H0/H1 e diferenças com erro máximo
  7,1054e-15, sem novas likelihoods. Recibo:
  `results/C10/pilot_normalization_audit/audit.json`.

As comparações fina/grossa das 144 análises apresentaram falhas de
`logZ_H1` em `A_CN:9` e `A_CN:15`, e de `logL_CDF` em `C_full_G:14`.
As comparações de malha alta e produto independente nos quatro dados
selecionados não mostraram falhas nesses registros. As falhas fina/grossa
não são apagadas por esse resultado ou pelos controles SciPy.

O inventário terminal e a auditoria das referências foram concluídos, com
as falhas preservadas. Faltam avaliar os refinamentos e decidir a campanha
de identificação com base nos resultados. Recuperação, falsos positivos e degenerescências
de população ainda não foram validados por este piloto de dados fixos.

## Diagnósticos de subdivisão e continuação limitada

Foram congeladas e executadas duas seleções numéricas, sem novas ORFs ou
observações. Em `results/C10/slice_refinement_probe_v2/`, 28 das 36 fatias
selecionadas passaram com até 256 subdivisões (uma passava antes). Foram
cobradas 9.604 avaliações, reutilizados 5.246 valores e consumidos 4,743766 s
CPU. As três avaliações de ponte por fatia coincidiram exatamente. A
primeira tentativa, preservada em `slice_refinement_probe/`, falhou no
controle RLIMIT_AS do macOS antes de criar o ledger ou avaliar likelihoods;
a execução v2 emprega controle de RSS medido, como o piloto original.

Em `results/C10/slice_refinement_hard_probe/`, seis das oito restantes
passaram com até 2.048 subdivisões. Foram cobradas mais 12.284 avaliações,
reutilizados 6.552 valores e consumidos 8,308238 s CPU. As duas fatias ainda
indeterminadas são C_beta_G/d0/u384/135 e A_G/d8/u384/90. O total acumulado
ao fim desses testes é 11.952.564 avaliações. A seleção de casos difíceis
não permite inferência populacional nem aprovação das integrais completas.

A continuação `tmp/c10_event_refinement_v1/` foi congelada para as 9.325
fatias ainda indeterminadas, em ordem decrescente de contribuição à
incerteza integral, usando os caches originais e os dois diagnósticos.
Tetos: 2.800.000 novas avaliações, 900 s CPU, 256 MiB de saída, 4 GiB de
RSS medido; por fatia, até 512 subdivisões e 1.536 novos valores. O teto
acumulado é 14.752.564, abaixo dos 15 milhões do piloto. O script preserva
falhas e valores anteriores, para antes de exceder recursos e recompõe
as 72 regras em massa. A auditoria independente está em
`scripts/auditar_refinamento_eventos_c10.py`. Consultar `complete.json`,
`FAILED_PRESERVED.json` e o ledger antes de qualquer retomada; não executar
novamente no mesmo diretório.

## Estado terminal do refinamento e próxima execução

O lote `tmp/c10_event_refinement_v1/` terminou com 3.500 fatias visitadas,
2.857 aprovadas operacionalmente e 643 indeterminadas. Foram cobradas
1.655.144 novas avaliações, sem reservas incompletas, e reutilizados
531.676 valores. CPU: 845,838415 s. O acumulado é 13.607.708 avaliações.
Nenhum processo permanece ativo. Há 5.825 fatias selecionadas não visitadas,
além das indeterminações mantidas nas visitadas.

A parada foi motivada pelo espaço. O limite local de 268.435.456 bytes foi
ultrapassado: saída final de 272.666.455 bytes, excesso de 4.230.999 bytes.
O controle verificava somente a cada 100 fatias e reservava 1 MiB, insuficiente
para esse intervalo e para os relatórios finais. O recibo
`results/C10/event_refinement_resource_review/audit.json` registra a falha;
não se aumentou retroativamente o teto. Antes de qualquer nova execução,
verificar o espaço antes de cada fatia e reservar um limite conservador para
cache, partição e relatórios finais, ou usar um contêiner com tamanho limitado.
Os limites de likelihood e CPU deste lote não foram ultrapassados.

A auditoria `results/C10/event_refinement_audit/audit.json` conferiu o
acréscimo de todos os caches, preservação exata dos valores anteriores,
contagens e recomposição independente de 72 regras em massa (diferença
máxima zero). Essa aprovação numérica é separada da falha do limite de espaço.

O diagnóstico de arredondamento em `results/C10/roundoff_diagnostic/`
mediu 363 incompatibilidades originais com diferenças relativas até
4,98245e-15. O modelo operacional explícito de arredondamento usa margem
relativa de 1e-10 e um termo para a soma positiva; rejeitou o controle
negativo com discrepância material. Ele não é um certificado de erro físico
uniforme. Isoladamente, não aprovou essas fatias, pois a ambiguidade persistia.

A recomposição em `results/C10/refined_event_recombination/` restaurou
206 numeradores antes indisponíveis e manteve três referências completas
aprovadas, 33 indeterminadas. Não confundir as 2.857 aprovações de fatias
com aprovação das integrais bidimensionais. Os controles de malha alta/fina
e independente/alta justificam usar a malha alta nos quatro dados de referência;
as falhas grossa/fina permanecem no histórico e não são apagadas.

Próximo trabalho concreto:

1. Refinar as duas análises ainda sem referência alta independente:
   A_CN/d9 e C_full_G/d14, reutilizando a malha fina e os nós ORF já disponíveis.
   A_CN/d15 já tem controles alta/fina e independente/alta aprovados; preservar
   sua reprovação histórica grossa/fina.
2. Estimar o custo das 5.825 fatias não visitadas e dos casos ainda ambíguos,
   com prioridade equilibrada entre as duas regras em massa. Congelar um
   novo plano e corrigir o controle de disco antes da execução. Restam
   1.392.292 avaliações no teto original de 15 milhões; qualquer suplemento
   exige registrar o novo orçamento e o acumulado, sem reiniciar contagens.
3. Reavaliar os controles completos e delimitar a campanha de injeções,
   falsos positivos e degenerescências. Não promover o piloto de 16 dados
   fixos a calibração populacional.

O capítulo 9 foi atualizado e o PDF local de conferência foi compilado.
A v0.9.0 publicada permanece imutável; a etapa C10 ainda não justifica commit
ou release v0.10.0. Não há bloqueio externo nem objetivo concluído.

## Piloto controlado após Taylor — estado mais recente

As análises A_CN/d9 e C_full_G/d14 passaram no refinamento alta/fina,
na referência independente/alta e nas evidências H0/H1 por produto direto.
Foram cobradas 273.038 avaliações e reutilizados 66.306 valores exatamente;
a auditoria independente de normalização teve diferença máxima 3,55272e-15.
Recibo: `results/C10/primary_grid_refinement_audit/audit.json`.

O componente `src/pta/epsilon_taylor.py` fornece um limite de Taylor em
células inteiras, com derivada local e majorante da segunda derivada. Ele
é intersectado com o envelope anterior, não supõe número de raízes e
conserva uma falha quando não há compatibilidade. A derivação está em
`tmp/c10_taylor_event_v1/DERIVACAO.md`; quatro testes sintéticos independentes
passaram. A aritmética continua float64 com margem explícita, sem certificado
uniforme físico ou arredondamento dirigido.

No teste selecionado, todas as 36 fatias passaram com 1.836 novas avaliações.
A auditoria conferiu 28.730 pares cache/célula finais. Na continuação, todas
as 4.884 fatias visitadas passaram, com 495.606 avaliações; a parada por CPU
preservou 1.579 pendências. A execução da cauda resolveu todas essas 1.579,
com 159.795 avaliações. Os recibos estão em `results/C10/taylor_probe_audit/`,
`taylor_completion_audit/` e `taylor_tail_completion_audit/`. As duas últimas
auditorias recompuseram 72 integrais cada, com diferença máxima zero. As
saídas respeitaram seus limites de espaço, com reserva antes de cada fatia.

A avaliação final `results/C10/taylor_event_final_gate/audit.json` aprovou
**36/36 referências completas**: largura da CDF, mudança de logZ,
comparações de malha e produto independente, underflow amostrado e comparação
com os eventos bilineares. O acumulado é **14.537.983 avaliações**, abaixo do
teto original de 15 milhões. A soma de CPU das execuções físicas do piloto
e seus refinamentos é 1.554,171204 s (auditorias de leitura separadas).
Não há processo em execução.

Este resultado substitui as pendências numéricas dos estados históricos
acima. Não estabelece calibração populacional, poder de detecção ou ausência
de degenerescências. A próxima fase conserva as contagens prospectivas:
500 dados nulos, 500 da priori conjunta e 192 de recuperação; cinco métodos
em todos e quatro aproximações C em 96 dados predefinidos. Há 6.344 análises.
Apenas a malha fina demanda 210.322.632 valores; o teto candidato de produção
é 300 milhões. A preparação deve reutilizar valores da malha nas referências
de evento e medir custo antes de ativar a população. Ver também
`docs/c10_producao_apos_piloto.md`. C10 ainda não está concluído.

## Integração aninhada, cache e inventário (continuação de 12/09)

A integração CC/Simpson passou em 18.468 fatias e nas 36 comparações completas
com GL. A auditoria `results/C10/nested_integral_audit/audit.json` recompôs
as regras a partir dos caches. Após a tentativa de serialização preservada
(51 valores), o teste comparado (3.924) e a execução integral (80.564), o
total é **14.622.522 avaliações**. Não foram geradas observações adicionais.

O benchmark `results/C10/moment_cache_benchmark/complete.json` reproduziu
5.160 replays em 2.580 casos, sem novas densidades, ORFs ou observações.
Tempos: 13,531 s no trecho original e 12,169 s com cache. A CPU total foi
27,422484 s. Incluindo uma reserva de 30 s para a tentativa sem medição de
CPU, o acumulado superior contabilizado é **1.744,047797 s**; restam
55,952203 s no teto do piloto e 377.478 avaliações. Essa reserva não é uma
medição retrospectiva da tentativa fracassada.

O inventário `results/C10/production_preflight_v1/plan.json` contém os IDs,
namespaces de sementes e as 71 hipóteses enumeradas em famílias 39/26/6.
Corrige-se o resumo anterior de 94 dados C: o protocolo original já continha
os IDs de recuperação 133 e 165, portanto prevê **96 dados C, 384 análises C,
6.344 análises totais e 210.322.632 valores na malha fina**. Não se alterou o
JSON original nem se descartaram realizações. O primeiro teste de inventário
reprovou a contagem textual incorreta; após a correção, os três testes passaram.

Quatro testes analíticos do módulo de Fisher passaram, sem avaliação física.
O custo completo do executor ainda precisa ser medido: a extrapolação do
trecho analítico de evento, sozinha, é 3.030,42 s e não inclui os demais custos.
Nenhuma população foi gerada; v0.10.0 segue pendente e a última publicação
continua v0.9.0. Não recriar diretórios de execuções já concluídas.

O teste seguinte do fluxo completo concluiu dez análises nos dados piloto
0 e 3, com 331.530 valores de malha e 10.766 adicionais para os eventos.
A auditoria conferiu todos os caches, dez comparações primárias e vinte
agregados CC. CPU de 15,976860 s, 2.570 eventos concluídos. O estado mais
recente é **14.964.818 avaliações e 1.760,024657 s de CPU superior contabilizada**.
Restam 35.182 avaliações e 39,975343 s no teto original do piloto.

A projeção do fluxo completo é 4.136,52 s, acima dos 3.600 s candidatos.
Ainda não há demonstração de viabilidade populacional dentro desse alvo.
O próximo trabalho é otimizar os callbacks adicionais de densidade e medir
usando os caches existentes, sem repetir a malha. Recibos e fontes:
`results/C10/full_flow_benchmark_v1/` e `scripts/medir_fluxo_completo_c10.py`.

## Campanha iniciada e Fisher concluído

O usuário orientou encerrar otimizações e priorizar execução. O orçamento
prospectivo de produção foi ajustado para 7.200 s antes da geração, sem
alterar o teto de avaliações ou os critérios estatísticos. O piloto está
encerrado em 14.980.724 avaliações, após o teste preparado. A população foi
gerada e auditada em `tmp/c10_population_v1`; as 6.344 análises estão em
execução em `tmp/c10_production_v1`. Log: `tmp/c10_production_stdout.log`.

Fisher: 24 matrizes aprovadas nos oito pontos, com refinamento de passos e
auditoria independente (`results/C10/fisher_audit/audit.json`). Fontes e
tentativas intermediárias preservadas. A síntese estatística já está
preparada em `scripts/sintetizar_campanha_escalar_c10.py`; sua execução exige
o recibo terminal completo da campanha. Não encerrar C10 nem publicar antes
da síntese, dos arquivos restauráveis e do PDF cumulativo.
