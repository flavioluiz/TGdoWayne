# Extensão fixed96: evidências do compactador

Este diretório reúne a revisão de transporte da opção `--fixed96`, o achado de consistência T1 e a regressão após sua correção. **Não contém posteriores nem uma campanha fixed96 ou SBC simulada:** os testes criam fixtures de arquivos, incluindo dois NPZ pequenos com máscaras/NaNs, e verificam transporte fiel e coerência dos registros. Essas árvores temporárias e seus binários não foram incorporados.

A extensão exige96 alvos A0_CN, IDs0–95, escopo `FIXED_TRUTH96_NOT_SBC`, schema mascarado, inventário da geração e os vínculos de hashes/recibos. O zero estrutural de u=0 permanece zero; parâmetros indefinidos sem GW permanecem NaN com máscaras falsas. A operação não recalcula a validade científica desses valores, não transforma alvos não resolvidos em aprovados e não mistura o desenho fixo com os2500 alvos da campanha SBC.

## Evidências preservadas

| Registro | Conteúdo efetivamente verificado |
|---|---|
| [Parecer original](history/REVIEW.md) e [resultado independente v1](history/independent_results.json) | Cinco controles de transporte passaram; ataque na fixture do target95 reproduziu T1: rótulos e hashes religados aceitavam PASS apesar das cinco flags falsas. |
| [Regressão v2](history/REGRESSAO_V2.md) e [resultado independente corrigido](history/independent_results_v2.json) | Os cinco controles de máscaras/bytes/IDs continuam passando. O mesmo ataque é rejeitado com `Numerical state contradicts its retained flags.`; custo independente7,288sCPU. |
| [Log ROOT após a correção](logs/tests_after_consistency_fix.txt) | **10 testes ROOT passaram**, em19,769s reportados por unittest: seis testes comuns, incluindo a regressão de flags falsas/não booleanas, e quatro testes específicos fixed96. |
| [Log ROOT anterior](logs/tests.txt) e [registro histórico de nove testes](history/validation.json) | Antecedente da extensão antes da correção T1; preservado, sem reclassificação retroativa. |
| [Compatibilidade histórica](history/backward_compatibility_v2.json) | Verificação dos260 arquivos de um pacote de engenharia já existente com três alvos; não é uma nova execução física nem aprovação científica desses alvos. |

T1 era uma lacuna no ramo comum de consistência, também alcançável pelo novo modo. A reprodução controlada não é evidência de corrupção de uma campanha real. A correção exige exatamente cinco flags booleanas e confere o rótulo contra essas flags no estado, recibo, diagnóstico e inventário.

## Fontes, integração e reprodução

As19 cópias selecionadas são idênticas byte a byte às origens. Estão preservados os scripts/testes anteriores à extensão em `history/original/`, as fontes da primeira revisão e da correção em `history/review_sources/`, os scripts independentes, os resultados e os snapshots de hashes. Os logs foram renomeados de `.log` para `.txt`, mantendo os bytes, para inclusão explícita no repositório. O manifesto histórico em `history/manifest.json` conserva os nomes/caminhos da coleta anterior; o [manifesto desta integração](manifest.json) fornece o inventário dos caminhos atuais.

[ROOT_INTEGRATION.json](ROOT_INTEGRATION.json) registra o mapeamento completo e a confirmação de que as fontes ROOT atuais coincidem com os snapshots v2:

- `scripts/compactar_calibracao.py`: `380b7f938c2e7117ccb44d2441d61e0a60d898d75208a7258d88873b40682875`;
- `tests/test_compact_archive.py`: `3bbc90812bf91986021ab427e863593351b09a0b17d70377fb5031d9a34eedca`.

Nesta integração foram lidas as fontes atuais e conferidos seus hashes, as dez funções de teste e o log de sucesso. **Os testes não foram repetidos nesta cópia documental.** Não foram alterados módulos, drivers, configurações, README global ou validação de componentes.

Os [comandos de reprodução](COMMANDS.md) usam um novo diretório de trabalho e os snapshots arquivados, preservando os resultados históricos. Os scripts independentes originais assumem a estrutura `ROOT/tmp/review`; por isso não devem ser executados diretamente dentro de `history/`.

Frases históricas como “nenhuma posterior fixed96 ainda produzida” descrevem o momento da revisão original. Este pacote não determina o estado atual das campanhas. O sucesso destes testes certifica somente os aspectos de transporte e consistência examinados.
