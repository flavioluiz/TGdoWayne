# C07: inferência portátil, entrega para integração

Este pacote prepara treino e produção contínua IID com proposta defensiva GMM+Student.
A campanha de 500 dados **não foi executada**. A configuração prospectiva mantém
`execution_enabled=false` até o ensaio integral no runtime integrado. O piloto
independente de 16 alvos aprovou N65536×4; o ensaio frio de treino8192 aprovou54
cortes no alvo selecionado. Esses resultados não certificam todos os alvos novos.

Integre somente os arquivos listados em `integration_manifest.json`. A pasta
`src` contém cópias de dependências existentes para testes de staging; elas estão
em `existing_dependencies.json` e **não devem sobrescrever os módulos da raiz**.
O adaptador nativo, fonte C++ e builder são mantidos pelo root, fora deste pacote.
Todos os imports do código entregue são relativos a `inference`/`pta`.

## Contrato e custo

A proposta é treinada em8192 passos adaptativos de quatro cadeias, selecionando
2048 estados da segunda metade para EM. Esses estados não são produto posterior.
Treino não lê verdades. Proposta congelada e validada antecede ambas produções
IID,16384 e65536 pontos por replicação, quatro replicações independentes cada.
Seeds usam identificador global do alvo, nível e replicação; agrupamento, ordem
ou retomada não mudam a agenda aleatória. Nenhum peso é suavizado ou recortado.

Treino usa blocos64, produção blocos16 e raws podem ser diagnosticados/liberados
um alvo por vez. O nativo aceita `--training-threads 1 --threads 6`; só avaliações
determinísticas são despachadas a workers. O pool/banco são compartilhados entre
fases e o plano de threads integra a identidade da execução. Referência NumPy
permanece serial. Benchmarks separados mediram treino64×8192+EM em78,73s serial
e76,83s com4threads; diferença pequena. Tempo de todo fluxo ainda deve incluir
montagem, geração/logq, I/O e diagnóstico no runtime integrado.

Preflight500 planeja819.200.000 avaliações de produção +81.930.000 de treino,
incluindo inicialização =901.130.000. Limites explícitos:900M produção,90M treino,
1bilhão total planejado,4GiB estimativa numérica e1GiB raw ativo. O contador real
por processo recusa exceder o teto antes da avaliação. Reinícios/repetições de
processos não formam uma quota global automática; o custo efetivo exige somar
os registros das execuções. Estimativas de arrays não são teto do RSS do sistema.

ZIP_STORED temporário evita a compressão como gargalo: cerca37,55MB previstos por
alvo nos dois níveis,600,83MB por16. Se todos os raws fossem retidos seriam93,88GB.
Saídas usam criação exclusiva e SHA256, sem sobrescrever. `--resume` verifica
checkpoints; se uma queda ocorrer entre raw e checkpoint, reproduz a mesma receita
RNG e exige igualdade exata dos arrays órfãos antes de concluir o registro.
Treino interrompido reinicia apenas propostas não concluídas, com sementes idênticas.

## Execução após integração

A CLI exige caminhos explícitos, sem diretório temporário implícito:

```sh
python scripts/infer_calibration.py preflight \
  --experiment configs/calibration/prior_predictive_500_v1.json \
  --data results/C07/prior_predictive/data.npz \
  --table CAMINHO_TABELA.npz --table-manifest MANIFESTO_TABELA.json \
  --validation-config configs/calibration/pilot_initial.json \
  --run-config CONFIGURACAO_EXECUCAO.json --output RESULTADOS \
  --native-library BIBLIOTECA --native-build-manifest MANIFESTO_BUILD \
  --training-threads 1 --threads 6 --plan-file PLANO_NOVO.json
```

Trocar `preflight` por `train --block 0 --execute` grava propostas na pasta
`--output`. `produce --target 0 --proposals PROPOSTAS --raw RAW --execute` produz
um alvo. Escolher `--block` na produção usa blocos16; no treino,64. O comando nunca
inicia os2.500 alvos implicitamente. NumPy é selecionado omitindo as duas opções
nativas; biblioteca e manifesto nativo devem ser fornecidos conjuntamente.

O produtor verifica hashes de experimento, dados, tabela, configuração de validação,
configuração de execução, fontes Python, fonte C++ e binário/manifesto quando nativo.
A identidade da proposta vincula física/dados/prioris; a identidade de execução
adiciona algoritmo, fontes, backend, configuração e plano de threads. Assim uma
proposta pode ser usada por backend equivalente sem refazer ajuste, com ambas
proveniências preservadas. O backend opcional `inference.module:factory` deve ser
explícito e oferecer `set_workers` para planos diferentes entre fases.

O leitor de dados abre somente observações e metadados geométricos. Ler o SHA do
arquivo completo não desserializa a verdade. A CLI de diagnóstico será separada;
seu formato está em `DIAGNOSTIC_SCHEMA.md`. O estágio `archive --target ... --proposals PROPOSTAS --diagnostic DIAGNOSTICO.json`
verifica e preserva o JSON/NPZ completo, proposta, oito checkpoints/RNG, configuração
e hashes, inclusive quando a precisão falha. Ele emite `RAW_ARCHIVE_VERIFIED`,
com estado numérico explícito e todos os IDs/flags preservados. O comando
`release --target ... --diagnostic RECIBO_ARQUIVO.json` verifica esse recibo e
remove somente os oito raws identificados. Integridade do arquivo não equivale
a calibração científica nem a precisão aprovada. Uma posterior não resolvida
pode ter seu raw temporário retirado, mantendo sua receita de reprodução e seu
resultado não resolvido na síntese. A regra anterior v1 está preservada em
`archive/portable_producer_v1/`; nenhuma execução histórica foi reclassificada.

## Verificação já concluída

Sete testes de contrato passaram: agenda RNG por alvo sob reordenação/subconjuntos,
lei da mistura IID contra CDF independente, paralelismo determinístico com troca
de fase, proibição de leitura de verdade, quota antes de gerar, checkpoints e
liberação explícita, recuperação de interrupção por reprodução exata.
O teste Beta contínuo em cinco dimensões passou com4000 passos de treino e32768×4
estados; é verificação da lei MH, explicitamente distinta de calibração PTA.
Os módulos científicos portados preservam as implementações previamente auditadas;
o mapa de origem está em `source_map.json`.
