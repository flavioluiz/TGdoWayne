# Driver portátil C07

Integração: copie somente `scripts/run_calibration_campaign.py` para o mesmo
caminho na raiz, e o teste para `tests/test_campaign_driver.py`. Não modifica
runtime/produtor/diagnóstico ou critérios científicos. Requer os módulos C07
v2 e o leitor compacto já integrados.

A CLI exige os caminhos `--experiment`, `--data`, `--table`, `--table-manifest`,
`--validation-config`, `--run-config`, `--protocol`, `--truth-data`, `--truth-logl`
e `--output`. Opções nativas são explícitas: `--native-library`,
`--native-build-manifest`, `--training-threads 1`, `--threads 6`. Sem `--execute`,
só realiza preflight e imprime o plano. `--plan-file` grava uma cópia exclusiva.
A configuração também precisa permitir execução. O modo padrão exige exatamente
500 dados e todos2.500 IDs model-major; `--engineering` autoriza um ensaio separado,
rotulado como engenharia, com seu próprio protocolo de multiplicidade.

Um runtime é reutilizado: treino de cada bloco64, seguido por produção dos dois
níveis, diagnóstico, arquivo e retirada do raw de cada alvo antes do próximo.
Diretórios relativos ao destino explícito são `proposals`, `production`, `raw`,
`diagnostics`, `state`, `ledger` e `driver_provenance`. O ajuste não recebe verdades;
preflight apenas verifica hashes dos arquivos de diagnóstico. A logL direta na
verdade é lida exclusivamente pela etapa de diagnóstico já integrada.

O driver NÃO usa uniformidade da SBC como regra de parada. Alvos numericamente
não resolvidos são arquivados com suas flags e IDs e a campanha prossegue. Erros
computacionais ou de integridade interrompem a tentativa com registro explícito.
Um lock exclusivo impede duas instâncias de escrever na mesma campanha.

`--resume` exige a mesma identidade de runtime, fontes do driver/leitor e entradas.
Produtos concluídos são verificados por hashes, recibos de arquivo e inventário de
raw retirado, sem novo treino/produção. Propostas e replicações parciais usam os
mecanismos de retomada v2. Cada estado/alvo, intenção/fim de operação, início/fim
de tentativa e resumo de bloco é um JSON novo; nenhum checkpoint é sobrescrito.

O ledger reserva avaliações antes de cada operação e registra a diferença real
do contador do runtime depois. Falha capturada registra o custo tentado; queda
sem encerramento conserva a reserva inteira, explicitamente conservadora.
Treino/produção/total são limitados também entre tentativas. Sob o lock exclusivo,
o ledger valida o histórico uma vez e guarda totais/índice em memória, atualizados
a cada intenção/fim. Uma retomada revalida todos os bytes; o encerramento faz
auditoria integral independente do cache. Não há releitura quadrática por alvo. Antes de retomar,
verifica o custo mínimo restante junto ao histórico e o raw ativo. Isso fecha a
lacuna do contador por processo sem alterar a aleatoriedade ou a likelihood.
A estimativa de armazenamento inclui a quota raw,1MiB de arquivo por alvo e512MiB
de margem; a campanha não acumula os~94GB de raw bruto.

Fontes Python/CPP e entradas permanecem vinculadas pelo runtime. O driver adiciona
snapshot/hashes do próprio script, leitor, utilitários IID, protocolo e logL direta.
Logs compactos são emitidos no começo/fim de blocos; os marcos por alvo permitem
retomada granular. `campaign_complete.json` significa produtos arquivados de todos
os alvos, explicitamente sem declaração de uniformidade/calibração da SBC.

Cinco testes TOY independentes do problema PTA passaram: ordem de fases e contagem
180, manutenção de alvo não resolvido, parada por falha e retomada sem repetir
alvo retirado (contagem204 incluindo o trabalho falho), reservas abandonadas e
teto antes de trabalho, além de lock concorrente. O teste de complexidade contou200 leituras JSON para
auditar100 eventos e200 na reabertura; adicionar outros100 eventos não reabriu
histórico, confirmando custo linear de auditoria. São testes operacionais; nenhuma
campanha500 foi iniciada por esta entrega.
