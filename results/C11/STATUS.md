# C11 — Trabalho em andamento

A v0.10.0 foi publicada e validada; C11 ainda não está concluído.
A decisão de ramo está em `branch_decision.json`, com documentação em `docs/dados_publicos.md`.
Sete testes determinísticos passaram. O candidato foi congelado em `tmp/c11_pilot16_candidate_v1/manifest.json`.
A primeira tentativa parou pela proibição de /bin/ps no sandbox (2,129012 s CPU).
A segunda terminou em 108,394218 s CPU e 107,911531 s de parede, RSS máximo 699383808 bytes.
Não foram gerados dados ou posteriores C11; foram executadas respostas e controles do benchmark.

O gate estrito falhou apenas no máximo subset/rotation: 4,575092527048241e-10 > 1e-10.
Comparações coarse/fine, céu independente e limites analíticos satisfizeram as respectivas tolerâncias.
O diagnóstico usa somente respostas armazenadas, sem recalcular ORFs nem aprovar a falha.
Próxima ação: separar subset de rotation e conferir a construção da rotação em response_worker.py;
executar apenas o controle necessário, preservando o candidato congelado e contabilizando todas as tentativas.
Nenhuma campanha de 500 réplicas foi autorizada. Os controles funcionais de CDF, quantis e eventos
continuam pendentes antes da campanha. Não criar release intermediário nem marcar C11 concluído.
Não há processos ativos destas duas tentativas.

## Atualização: benchmark corrigido aprovado

O candidato v2 aplica P_l(1)=1 na diagonal, preservando integralmente off-diagonal. Oito testes passaram.
Benchmark corrigido: tmp/c11_benchmark_v3, todos os gates aprovados; 110,779158 s CPU.
Erro rotação/subset 4,1818429158538366e-16; referência céu 6,139533326209256e-14.
Recibos preservados em results/C11/benchmark_v2. Histórico CPU das três tentativas: 221,302388 s.
Piloto curves autorizado em tmp/c11_pilot16_candidate_v2/curves_authorization.json.
Processo iniciado: sessão exec 41711, saída tmp/c11_curves_v1; verificar esse handle e execution_end.json antes de retomar.
Log tmp/c11_curves_v1_controller.log; recibo externo final tmp/c11_curves_v1_lifecycle.json.
Não reiniciar por timeout de observação. Fontes e manifestos congelados não devem ser editados.
Nenhuma produção de 500 aprovada. Próximo passo após curves: examinar todos os 288 alvos e controles; completar controles funcionais antes de produção.

## Preparação da análise funcional

Rotina tmp/c11_functional_v1/density.py: densidade positiva em alpha, CDF/quantis, extremos da diferença de CDFs e massas de eventos com tratamento de átomos. Quatro testes analíticos passaram em 0,036 s; recibo validation.json. Sem novas ORFs/likelihoods/draws.
Após curves terminar com passed=true, executar:

```sh
OPENBLAS_NUM_THREADS=1 .venv/bin/python tmp/c11_functional_v1/assess.py --candidate tmp/c11_pilot16_candidate_v2 --run tmp/c11_curves_v1 --output results/C11/pilot_functional_assessment.json
```

O assessor retém todos os 288 alvos e não aprova inferência física por concordância de interpolantes. Controles independentes de integrais nos quantis e cruzamentos de logL permanecem necessários. C11/C12/C13 continuam abertos.

## Piloto terminado

Sessão 41711 TERMINAL com sucesso; não voltar a consultá-la. Fonte congelada v2.
Saída tmp/c11_curves_v1; recibo externo 693,163412 s CPU, 535,531887 s de parede, RSS 719060992 B.
Total de CPU das três tentativas de benchmark e fase curves: 914,465800 s.
288 posteriores/16 realizações/572544 likelihoods. Zero falhas nas 288 comparações alpha32/64 e nos 18+18 controles independentes u8/u16 e alpha/u.
Assessor funcional terminou (sessão 99550 TERMINAL); 288 alvos retidos, zero falhas de comparação de interpolantes.
Geração auditada em generation_audit.json: 16 IDs, estados RNG exatos, erro escalado máximo 3,2131e-16.
Controles físicos diretos de quantis/eventos ainda pendentes; não liberar campanha de 500 só com comparação de interpolantes.
Próxima ação: preparar referência física delimitada para integrais em extremos de quantis e cruzamentos de logL, aproveitando os 18 alvos independentes prospectivos, respostas já calculadas e todos os dados preservados. Nenhum processo está ativo.
A matriz de objetivos em docs/matriz_objetivos_resultados.md é uma preparação parcial C12 e não deve ser interpretada como fechamento desse marco.

## Referências diretas em execução

Após o piloto, foram preparados 18 alvos prospectivos (os mesmos pares population/model/datum do piloto).
A v1 de tmp/c11_direct_functionals_v1 usa GL16/32 global: alvo 0 executou, mas falhou em precisão.
A v2 subdivide nos cortes de massa do piloto: alvo 0 passou nos critérios gerais, mas não confirmou todos os brackets.
A v3 usa GL32/64 nesses cortes: alvo 0 passou quantis e controles; nenhuma tolerância foi relaxada.
Os diretórios v1/v2/v3 e recibos preservam as tentativas. Sessões 35976,11884,14097 são TERMINAIS.
A sessão ATIVA é 1184: executa batch.py v3, alvos 1..17 uma vez, teto de 900 s CPU por alvo/7200 s acumulados no lote.
Antes de retomar, consultar esse handle. Log tmp/c11_direct_functionals_v3/batch.log, recibo final batch_end.json.
O review.py v3 reportou 7/18 completos, zero falhas numéricas/quantis, dois eventos não resolvidos (IDs 5 e 6, sem sinais físicos divergentes fora das bandas).
Não reiniciar o lote por timeout. Depois de todos os alvos, executar review.py uma única vez para gravar results/C11/direct_functional_review.json; se o arquivo já existir, ler antes de executar novamente.
Eventos usam intervalos de fronteira conservadores. Os dois primeiros indeterminados precisam reduzir a massa ambígua; não descartar nem atribuir erro zero.
As verificações continuam finitas; não constituem prova global de ausência de cruzamentos não amostrados.

Desenho da produção registrado em configs/application/c11_production_design.json (AINDA NÃO autorizado/executado): 500 massas uniformes + três células de 32 (u=0 central, u=.995 central, u=.5 ruído vermelho forte), 596 realizações, 10728 posteriores.
Famílias Holm separadas: 42 testes corretos, 84 aproximados. Semente mestre 20260912011; nenhum sorteio de massa de produção realizado.
Componente tmp/c11_production_v1/generation.py amplia somente o intervalo de IDs para 0..595. Dois testes passaram: igualdade bit a bit com o gerador validado para ID compartilhado e suporte/extremo de IDs. Esse componente ainda não gerou observações de produção.
Próximos passos: revisar os 18 controles, resolver eventos pendentes com execução delimitada, implementar/congelar produção e executar após aprovação numérica. C11/C12/C13 permanecem abertos; release seguinte v0.11.0.

## Continuação: refinamento dos eventos P12K4

Lote principal v3 continua na sessão 1184; último alvo completo observado: ID 9 (primeiro P16K8). Não reiniciar.
Os nove alvos P12K4 confirmaram quantis; eventos 5,6,7 ficaram inicialmente não resolvidos por massa nas bandas, sem sinais divergentes fora delas.
Novo plano tmp/c11_event_refinement_v1/plan.json usa os mesmos três dados, integrais GL32/64 por painéis e bandas de 1e-5 em u, com raízes estimadas da união dos nós do piloto e referência v3. Quantis não são recalculados; revisão herda os confirmados em v3.
Alvo 5 terminou na sessão 55013 (TERMINAL), passou revisão, largura bruta de evento 7,08045e-5, CPU36,439462s.
Alvo 6 terminou na sessão 18984 (TERMINAL), passou revisão, largura bruta 9,96546e-5, CPU46,531210s.
Alvo 7 está ATIVO na sessão 47364, log tmp/c11_event_refinement_v1/run_07.log.
Depois do alvo 7, executar review.py desse diretório (uma vez ao completar) para results/C11/event_refinement_review.json. Ler arquivo se já existir para evitar colisão.
Fonte de produção population.py preparada mas NÃO executada: exige aprovação vinculada ao config e referências antes dos 500 sorteios da priori; persiste estado RNG antes/depois e constrói IDs0..595. Nenhum dado de produção foi gerado.
Ainda falta implementar o controlador completo de produção, consolidar todos os controles, executar campanha e síntese, finalizar C11/PDF/commit/push.

Atualização final do refinamento: sessão 47364 TERMINAL; os três alvos de eventos foram executados. Revisão gravada em results/C11/event_refinement_review.json — consultar seus campos para a decisão. A sessão 1184 permanece como lote principal a acompanhar.

## Controlador de produção implementado, não executado

Arquivo tmp/c11_production_v1/run.py preparado e compilado. Reutiliza a tabela exata do piloto, calcula as respostas das até 500 massas novas, audita coarse/fine, gera 596 dados pareados e calcula 18 x 596 posteriores e logL na verdade em dois níveis.
Preflight em implementation_preflight.json: máximo de 20.855.232 likelihoods de base, 15.000 matrizes Gamma novas, CPU7200s, RSS2GiB, saída4GiB. Sem CDF/eventos adicionais nesses valores.
Exige aprovação ROOT vinculada ao código/config/referências; ainda não existe aprovação e nada de produção foi executado. Antes de liberar, terminar a revisão dos 18 alvos e implementar/auditar síntese funcional da produção; conferir o controlador e usar wrapper externo de ciclo de vida para registrar eventual término pelo limite rígido.
Na última observação, lote sessão1184 vivo e ID10 encerrado: P16K8_A_CN, controles/quantis aprovados, CPU272,69s. ID9 também aprovado (CPU241,30s). Os refinamentos P12K4 dos IDs5/6/7 já estão todos concluídos e aprovados na revisão de eventos.

## Síntese funcional de produção preparada e conferida no piloto

functional.py e synthesize.py em tmp/c11_production_v1 implementados; a síntese ainda NÃO executou produção. Reutiliza funções auditadas de sensibilidade SBC, famílias Holm42/84, preserva os596 IDs e separa32/célula de SBC500.
Três testes analíticos passaram (uniforme/átomo, exponencial/W1, falha harmônica com intervalo[0,1]).
Primeira construção com margem fixa de logL=.001 gerou251 eventos não resolvidos no piloto; fonte/resultado preservados em functional_history_fixed_allowance.
Nova construção usa união de raízes dos dois interpolantes com bandas de1e-5 em u e sua massa ambígua, concordância entre ordens e margem operacional PIT±.002; não afirma limite global físico nem ausência provada de cruzamentos escondidos.
check_pilot_roots.py terminou (sessão82889 TERMINAL):288 alvos, nenhum mass PIT não resolvido,23 eventos não resolvidos,18,465s, sem novas avaliações físicas. Sessão8412 também TERMINAL (primeiro check).
Comparação parcial em direct_comparison_partial.json:14 referências diretas (refinamentos paraIDs5/6/7), todos os intervalos diretos contidos nos da rotina de produção, nenhuma falha de quantis. Ainda exigir comparação final dos18 antes da aprovação.
Lote principal sessão1184 permanece ativo; último ID13 completo. Faltam14..17. Não alterar fontes/planos do lote em execução.
Após completar: revisararquivo direct_functional_review.json, tratar eventuais pendências P16, repetir comparação final com rotina de produção, congelar fontes/config/aprovação e só então executar controlador. Atualizar preflight dos arquivos novos antes de congelar; o preflight anterior contém hashes anteriores ao functional.py.

## Atualização: figura e supervisão de produção

launch.py em tmp/c11_production_v1 preparado/compilado para registrar inicialização, fontes e término completo do processo de produção, inclusive falha de startup/limite rígido, com reserva superior quando o resultado for parcial. Nenhuma produção iniciada.
Figura científica figures/aplicacao/geometria.pdf/png criada por scripts/figura_geometria_c11.py; projeção Aitoff, RA astronômica, 12 pontos compartilhados +4 adicionais. Inspeção visual realizada; inserida no capítulo C11 com atribuição CC BY4/DOI. Recibo results/C11/geometry_figure.json.
README e project_status atualizados com o andamento C11, mantendo C10 como última etapa concluída e v0.10.0 como último PDF publicado.
Controle ID14 (P16K8_A_G) terminou com quantis/integrais aprovados mas intervalo de evento bruto0,00991. Refinamento somente desse evento preparado em tmp/c11_event_refinement_p16_14 (raízes com dados diretos, banda1e-5).
REFINAMENTO14 ATIVO: sessão50652; log tmp/c11_event_refinement_p16_14/run_14.log. Após terminar executar review.py uma vez, saída results/C11/event_refinement_p16_14.json.
LOTE PRINCIPAL também ATIVO: sessão1184; último ID14 completo, faltam15..17. Não reiniciar nenhum por timeout de observação.

## Consolidação e referências P16

review_references.py em tmp/c11_production_v1 implementado/compilado. Exige os18 controles completos, valida hashes, incorpora refinamentos de eventos sem mudar os alvos, confere quantis herdados e inclusão das referências nos intervalos do check do piloto. Gera reference_consolidation.json, mas não autoriza produção automaticamente.
ID14 refinado concluído: sessão50652 TERMINAL, CPU388,256540s; revisão results/C11/event_refinement_p16_14.json aprovada (largura bruta0,0002395).
ID15 do lote principal confirmou quantis/integrais mas evento bruto0,002935. Novo refinamento em tmp/c11_event_refinement_p16_15 (1848 nós); sessão11106 ATIVA. Log run_15.log; após término executar review.py uma vez para results/C11/event_refinement_p16_15.json.
Lote principal sessão1184 ATIVA; último ID15 completo, faltam16 e17. Manter ambos os processos, não reiniciar.
Síntese explicita que cobertura central em u=0 sob priori contínua é estruturalmente nula e não é teste SBC; células fixas continuam descritivas.

## PRODUÇÃO E SÍNTESE CONCLUÍDAS; fechamento C11 pendente

TODAS as sessões recentes são TERMINAIS:1184,11106,84310,47785,99052. Não as consultar novamente. Nenhum processo desta etapa permanece ativo.
Os18 controles diretos foram consolidados e aprovados em results/C11/reference_consolidation.json, com refinamentos de eventos IDs5/6/7/14/15.
Fontes/config foram congelados e a aprovação gerada em tmp/c11_production_v1/approval.json (151 vínculos). NÃO editar código/config/fontes vinculadas; eventuais mudanças requerem versão preservada nova.
Produção tmp/c11_production_run_v1:596 realizações,10728 posteriores,20855232 likelihoods; CPU233,556885s, parede242,7900895s, RSS2086305792bytes. Sessão84310 terminou com exit0 e recibo completo.
500 novas massas,15000 matrizesGamma novas; coarse/fine máximo4,79516e-12. Auditoria de geração results/C11/production_generation_audit.json passou:596 IDs, semente nominal/estados RNG exatos, população500+96 correta, erro escalado máximo8,81072e-16.
Síntese tmp/c11_synthesis_v1:18 produtos completos,10728 alvos; CPU659,636590s, parede659,9469115s, RSS310624256bytes. Resultados agregados copiados para results/C11/production_synthesis/synthesis.json.
Resumo ainda a auditar estatisticamente: família correta42 testes,0 rejeições persistentes/3 indeterminados; aproximada84,1 persistente/1 indeterminado. Todos os PITs de massa resolvidos; eventos não resolvidos permanecem[0,1]. median_KL dos produtos mistura596 dados — para informação média sob a priori, derivar separadamente somente os500 SBC.

Próximas ações prioritárias: (1) auditoria independente da agregação SBC/Holm e contagens, derivar tabelas/figuras incluindo informação nos500 da priori; (2) concluir texto C11 e registrar limites, sem declarar equivalência de modelos por teste não rejeitado; (3) arquivar todos os temporários fechados com scripts/arquivar_c11.py, restaurar em diretório fresco e verificar; (4) fechar estado C11, notasv0.11.0, compilar/inspecionar PDF, commit/push/tag e conferir publicação/download; (5) C12 discussão/manuscrito e C13 auditoria final.
Scripts de arquivo/restauração C11 preparados e compilados, AINDA NÃO EXECUTADOS. Reutilizam o mecanismo C10; incluem tmp/c11* e vínculos já disponíveis em arquivos antigos. Verificar dependências/reuso e portabilidade na restauração.
Makefile e workflow agora incluem restauração C11 e check-application. Wrapper tests/test_c11_components.py passou (3 suites,13 casos internos); recibo results/C11/component_tests/validation.json.
README e capítulo foram atualizados ao início da produção e ainda dizem em execução — atualizar para síntese concluída enquanto o fechamento permanece pendente. Não publicar release intermediário.

## FECHAMENTO CIENTÍFICO C11

Campanha e síntese concluídas. Auditoria da geração aprovada; agregação independente aprovada em 396 verificações, com 0/3 rejeições persistentes/indeterminações na família correta e 1/1 na família aproximada. Texto cumulativo e figuras atualizados. Pacote de 106941 arquivos lógicos restaurado; 13 casos de componentes passaram a partir das fontes restauradas. Publicação v0.11.0 depende do fechamento Git, workflow e conferência de download, registrados fora do manifesto imutável depois do envio. C12 e C13 permanecem abertos.
