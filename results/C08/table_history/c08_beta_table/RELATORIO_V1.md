# C_beta v1: construção concluída; gate de interpolação reprovado

A candidata **não está aprovada**. A construção e todos os controles originais
foram concluídos, preservando a primeira interrupção e a continuação diagnóstica
posteriormente autorizada. Nenhuma tabela comum ou posterior foi publicada como
validada, e nenhum refinamento foi iniciado automaticamente.

A origem do canal1 foi conferida contra
`results/C07/orf_interpolation/orf_table_pilot12x4.npz`: arquivoSHA75632dfb…,
nós, matrizes e coeficientes da primeira curva coincidem bit a bit com a fonte
histórica. A derivada emβ=0 calculada nos coeficientes é1,43e−16.

| Verificação | Resultado |
|---|---|
| Quadratura harmônica coarse/fine, todos os nós | Passou≤1e−8 |
| Limiarβ=0 | Posto5 em todos os canais; erro analítico≤2,46e−13 |
| Limite masslessβ=1 | Matrizes idênticas à ROOT |
| PSD dos controles Bernstein | Sem fallback em todas as curvas |
|24 casos/p pares em quadratura angular direta | Máximo erro1,58e−13, abaixo de1e−7 |
|143 controles de matriz fine/oráculo | Máximo6,11e−6 |
|143 controles de logL fine/oráculo | Máximo0,000161165; todos≤0,001 |
|143 controles de logL coarse/fine | Uma falha: máximo0,001870588>0,001 |

A falha ocorreu emu=0,999999806610848, β=0,000621914999539. Os índices[14,9]
identificam a nuisance sorteada14 e a observação física9 do conjunto antigo
com16 dados; não são a verdade ou a posterior do dado14. O maior fine/oráculo
ocorreu emβ≈0,001, nuisance13/observação física9.

O primeiro processo parou após121 massas e743.424 logL, como prescrito. O root
autorizou concluir somente as22 massas restantes com mais135.168 logL, sem
alterar malha, limiar, resultados antigos ou classificação. A continuação
confirmou uma única falha coarse/fine e nenhuma fine/oráculo. Não se trata de
aprovação da candidata pelo abandono de um critério: a v1 continua reprovada.

## Recursos observados

- Construção:48.508.435.951.296 produtos reais de coeficientes, exatamente o
  preflight;1.945,90s, picoRSS1.360.314.368bytes (1,267GiB).
- Gates iniciais:2.051.757.104 pontos/produtos de ordem angular;239,40s,
  picoRSS971.505.664bytes.
- LogL originais totais:878.592, abaixo de1M. Continuação0,421s,
  picoRSS90.554.368bytes.
- Um worker, Apple Accelerate comVECLIB_MAXIMUM_THREADS=1. RSS é pico por
  processo, em bytesDarwin, e não inclui a campanha C07 em outro processo.
- Testes unitários sintéticos leves têm contadores separados no registro dos
  gates. Não foram usados para ocultar custo científico ou aprovar a tabela.

A estimativa máxima de arrays de construção foi≈653MB, enquanto o picoRSS
foi1,36GB. O teto operacional1,5GiB foi respeitado; a estimativa de arrays não
foi tratada como garantia de memória residente.

## Evidência preservada

- `execution_authorized.json`, `gates_frozen.json`, `environment.json`;
- `results/matrix_manifest.json`, canais e206 checkpoints harmônicos;
- `results/gates/curves_and_anchors.json`, `direct_checks.json`;
- `results/gates/likelihood_failed.json` e `failure.json` originais;
- `results/original_diagnostic_continuation/authorization_and_inputs.json`
  e `report.json`, com hashes do material antigo;
- caches de logL por massa, dados/escala/nuisance identificados, e ledger;
- fontes executadas, testes, logs e primeira curvaROOT identificada.

A proposta de correção geométrica local está separada em
`../c08_beta_table_v2/PREFLIGHT.md`, ainda sem autorização/execução no momento
deste relatório. Ela deve usar o fine v1 inteiro como novo coarse, refinar o
novo fine e acrescentar controles independentes. Fontes e resultados v1 não
serão reinterpretados como v2.
