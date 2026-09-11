# Estado da integração das tabelas C08

A cópia mínima foi realizada e conferida por SHA-256: **218 arquivos, 297.710.158 bytes**. O registro efetivo está em [table_publication_copy.json](../../results/C08/table_publication_copy.json), SHA-256 `96c1ac156477e5ccf6f817d9f1d2951765b4f3f2bbe7e620dddb6eed8f351de3`.

As partes comprimidas e as receitas estão em `results/C08/orf_tables/`; as fontes e evidências selecionadas ficam em `results/C08/table_history/`. O transporte preserva os bytes das tabelas finais. Não foram duplicados os 815,5 MB descomprimidos nem incluídos todos os caches intermediários necessários para repetir cada quadratura histórica. As tabelas finais e as tentativas anteriores com falhas continuam identificadas separadamente.

O inventário abaixo é o registro histórico **anterior à cópia**. Expressões como “proposto” ou “a integrar” pertencem àquele planejamento; o recibo acima registra o trabalho efetivamente realizado. A portabilidade dos arquivos não constitui aprovação científica das posteriores.

---

# Proposta de integração das tabelas C08

**Estado: inventário e proposta; nenhuma integração executada.** Esta leitura de
11/09/2026 não importou módulos científicos, abriu arrays, calculou ORFs/logL,
executou testes ou recalculou hashes de tabelas. O inventário leu aproximadamente
2,14 MB de textos/metadados, abaixo do teto de 64 MiB. Não alterou C07, `src/`,
configurações ou resultados oficiais.

`integration_plan.json` é a lista completa, sem globs: cada entrada fornece
origem, destino futuro, tamanho em bytes, categoria, operação proposta, caminho
original de replay e identidade disponível. São 1.337 entradas nas dez árvores
C08 examinadas, além de 16 referências externas. As categorias são alternativas
de publicação/replay; **não se recomenda copiar todas indiscriminadamente**.
`build_inventory.py` apenas inventaria arquivos e lê metadados; não é um runner
numérico. Os destinos são candidatos para revisão pelo ROOT.

## Resultado físico que acompanha os arquivos

As duas tabelas passaram nos **gates finitos de tabela**, para a geometria C07
de 12 pulsares e quatro frequências. Esse estado não aprova posteriores C08,
precisão Monte Carlo, calibração, mapas de T/janela nem uma cota uniforme de erro.

| Artefato | Nós | NPZ original (bytes) | Transporte gzip (bytes) |
|---|---:|---:|---:|
| C_beta | 9.248 | 426.186.968 | 238.124.760 |
| C_full | 8.448 | 389.316.712 | 57.536.079 |

Identidades dos NPZ originais, citadas dos manifestos e roundtrips existentes:

- C_beta: `4944d15738864697afe19c159a6da7b732ac712d6308806427a9a3106d2c84d7`.
- C_full: `96e552bc97b4978fbe8c8c825c63cef8c7cf6ad31895b4eb22204aaaf0f150ed`.

Ambas armazenam coeficientes cúbicos explícitos na coordenada **x = −β**. C_beta
congela β na frequência de referência, mantendo as fases físicas de cada canal.
C_full congela a resposta matricial completa na primeira frequência, repetindo
seus coeficientes bit a bit nos quatro canais; espectros e ruídos continuam
variando com a frequência. Não refazer spline pelas matrizes da união de nós:
isso pode produzir outra função, diferente daquela validada.

A primeira curva vem de
`results/C07/orf_interpolation/orf_table_pilot12x4.npz` (42.670.838 bytes,
SHA `75632dfbdd9cce8b60b9f760a3177a76798a4adb7ac9ccc724092aeaf53ad70d`).
Esse arquivo já existe no repositório e deve ser referenciado, sem duplicação.
A cópia histórica `tmp/c07_sampler/results/table_beta8193_local.npz` tem a mesma
identidade registrada e pode ser restaurada como alias apenas no workspace de
replay. A curva coarse histórica de 4.169 nós,
`tmp/c07_sampler/results/table_beta4097_local.npz`, tem 21.357.765 bytes e SHA
`ceafa7abcb53c405665cad4babff787ebd3ca9a33ca85d9f6cfd72ce3e7cc740`;
é dependência opcional do replay histórico, não o backend C08 aprovado.

Os dados de engenharia estão em
`tmp/c08_beta_table/inputs/pilot_data.npz` (25.248 bytes, SHA
`05122aa29322d820e2806b069578cfd7e00b9c68995cdb9f60f24f1d9dc485b8`),
com configuração congelada em `inputs/experiment.json`. As 32 observações
utilizadas nos gates e os índices de nuisance não são uma campanha C08 de
posteriores ou calibração.

## Falhas e continuações que devem permanecer juntas

| Etapa | Evidência principal na árvore original | Estado preservado |
|---|---|---|
| C_beta v1 | `tmp/c08_beta_table/RELATORIO_V1.md`; `results/gates/likelihood_failed.json` | ΔlogL coarse/fine = 0,001870588 > 0,001 |
| Continuação diagnóstica v1 | `tmp/c08_beta_table/results/original_diagnostic_continuation/authorization_and_inputs.json` e `report.json` | Completou 143 controles, mantendo a falha |
| C_beta v2 interrompida | `tmp/c08_beta_table_v2/execution_authorized.json`; `results/failure.json`; ledger | Guard de RSS falhou ao preparar a base coarse k4 |
| C_beta v2 sequencial | `tmp/c08_beta_table_v2_continuation/preflight.json`; `execution_authorized.json`; `results/final_report.json` | Nova continuação técnica aprovada, sem apagar a interrupção |
| C_full inicial | `tmp/c08_full_table_execution/RELATORIO_FALHA.md`; `results/likelihood_failed.json` | coarse 4.169 falhou: ΔlogL ≈ 0,00111433 |
| C_full continuação original | `tmp/c08_full_original_diagnostics/RELATORIO.md`; `execution/authorization.json` | Completou 215 controles e 54 referências; candidata continua FAILED |
| C_full local v2 | `tmp/c08_full_local_v2_design/preflight.json`; `tmp/c08_full_local_v2_execution/authorization.json`; `results/final_report.json` | Nova curva e novos gates finitos PASS |

O fracasso de RSS da primeira execução C_beta v2 foi
2.109.554.688 bytes > 1,5 GiB, em 47,247 s. A interrupção aconteceu antes da nova
avaliação em β do canal 4: a contagem de novos produtos desse canal foi zero,
mas o custo da preparação, CPU e memória permaneceu real. O novo preflight
separou coarse k4, fine k4 e gates/exportação em três processos sequenciais,
sem repetir as quadraturas já concluídas ou ampliar o teto.

Na integração, os preflights, fontes executadas, autorizações, logs, ledgers e
relatórios de cada etapa devem ser preservados **byte a byte**. O inventário
inclui as versões provisórias/executadas e os pareceres de revisão; não substitui
um relatório antigo por um resumo final. A autorização histórica é evidência de
escopo da execução ocorrida, não autorização aberta para novos cálculos.

## Evidência que permite reutilizar nós e coeficientes

**C_beta.** O fine v1 inteiro tornou-se coarse v2. A v2 subdividiu por oito os
intervalos uniformes com β ≤ 1/64, preservando os nós antigos e todos os
coeficientes externos bit a bit. A primeira curva individual manteve a identidade
C07. A união comum usa subdivisão algébrica dos polinômios; o maior desvio de
avaliação registrado foi 1,11×10⁻¹⁶, abaixo de 10⁻¹¹. Os relatórios
`first_curve_identity.json`, `results/local_curves.json`, `results/new_oracles.json`,
`results/final_report.json` e as fontes `curve_algebra_v2.py`/`patch_curve.py`
devem acompanhar essa alegação.

Dos 143 controles históricos, 36 dentro do patch exigiram recalcular o novo fine;
107 externos reutilizaram logL **somente após igualdade bit a bit de Γ**.
Somaram-se 72 controles e 64 nuisances novos, fixados antes da execução. A
auditoria leu 215 caches e conferiu 213 identidades de fontes/insumos. Esses dois
números não significam que os 215 caches tenham todos um SHA individual publicado.

**C_full.** A primeira curva física de 8.336 nós tornou-se coarse; 112 novos nós
subdividiram por dois os intervalos uniformes com β ≤ 1/64. Nós, patches e
coeficientes externos foram preservados. A exportação repete matrizes e
coeficientes do primeiro canal nos quatro canais de forma bit a bit.
Dos 215 controles históricos, 57 foram recalculados dentro do patch e 158
externos foram reutilizados após a mesma verificação de Γ. Há mais 72 controles,
54 referências finitas independentes e auditoria de 287 caches/272 arquivos
congelados. Os registros relevantes são `results/local_report.json`,
`results/likelihood_checks.json`, `results/export_report.json`,
`results/independent_references.json` e `audit_completed.json`.

O corte geométrico foi definido antes das novas avaliações, sem seleção por PIT,
verdade ou posterior. Essas identidades justificam reutilização das partes
inalteradas; não transformam coarse=fine em erro nulo contra o oráculo.

| Gate final | C_beta | C_full | Critério |
|---|---:|---:|---:|
| Oráculo harmônico: resolução/método | 7,53×10⁻¹³ | 1,96×10⁻¹³ | 10⁻⁸ |
| Comparação angular nova | 2,45×10⁻¹⁴ (12) | 1,21×10⁻¹⁴ (4) | 10⁻⁷ |
| ΔlogL coarse/fine | 1,87888×10⁻⁴ | 3,72222×10⁻⁵ | 10⁻³ |
| ΔlogL fine/oráculo | 8,84463×10⁻⁵ | 1,29513×10⁻⁵ | 10⁻³ |
| Traços independentes: média/covariância | — | 3,18×10⁻¹⁶ / 1,07×10⁻¹⁵ | 10⁻¹⁰ |
| SciPy logpdf normalizado | — | 5,01×10⁻¹² | 10⁻⁸ |

Os controles Bernstein passaram PSD/Hermiticidade, sem clipping ou fallback.
Há verificações de continuidade e paridade no limiar. Em C_full, u=1 tem posto
tensorial cinco; em u=0 os canais 2–4 ainda diferem de B por fases congeladas,
com máximos de cerca de 7,04×10⁻⁴, 6,70×10⁻⁴ e 5,46×10⁻⁴. Portanto o transporte
não deve rotular C_full como B no ponto de massa zero dessa geometria finita.

Custo cumulativo registrado de C_beta: 48.948.941.796.288 produtos harmônicos,
2.057.601.896 pontos angulares e 1.394.688 logL. A continuação levou 50,475 s e
atingiu RSS de 1.377.828.864 bytes. C_full local v2 acrescentou
16.722.391.296 produtos, 1.352.456 pontos angulares e 560.832 logL; seu cumulativo
próprio chegou a 1.883.520 logL, abaixo do novo teto de dois milhões. Os cinco
workers levaram cerca de 25,8 s e atingiram RSS de 712.392.704 bytes. Essas são
medições históricas/contagens declaradas, não medições deste inventário.

## Publicação mínima, replay e arquivos opcionais

O conjunto mínimo proposto inclui o transporte das duas tabelas, 186 arquivos
de fontes/evidências de linhagem, o loader explícito e sua revisão, e pequenos
insumos de replay. Ocupa aproximadamente **298 MB decimais**, sem o novo documento
e o próprio inventário. Ele permite restaurar as tabelas finais e examinar sua
origem. Não permite prometer que cada runner/auditor histórico funcionará sem os
intermediários adicionais.

| Categoria no JSON | Arquivos | Bytes | Decisão proposta |
|---|---:|---:|---|
| `minimum_restore_payload` | 11 | 295.686.733 | Publicar partes, manifests e utilitário |
| `minimum_transport_evidence` | 8 | 6.558 | Publicar roundtrips e testes históricos |
| `minimum_lineage_sources_and_evidence` | 186 | 1.805.404 | Publicar cadeia completa de fontes/textos |
| `minimum_loader_source_and_evidence` | 8 | 37.727 | Publicar loader explícito, versões e revisão |
| `small_replay_seed_input` | 5 | 173.736 | Insumos pequenos; identidades ausentes permanecem explícitas |
| `optional_intermediate_replay_input` | 31 | 1.199.571.498 | Curvas/oráculos/matrizes; dependem do nível de replay desejado |
| `optional_construction_resume_cache` | 206 | 118.928.588 | Chunks para retomar construção |
| `optional_historical_audit_cache` | 860 | 44.486.358 | Necessários para auditores históricos que os leem |
| `optional_future_runtime_design` | 18 | 186.392 | Candidato de runtime futuro; não validação de posterior |

O conjunto de intermediários/caches ocupa cerca de **1,363 GB**, além dos insumos
externos. Algumas curvas intermediárias excedem 100 MiB; não devem ser copiadas
diretamente para Git caso se decida publicá-las. Precisariam de transporte próprio
e decisão separada. As duas tabelas NPZ brutas somam 815.503.680 bytes e são
**destinos de restauração**, não cópias adicionais propostas para o Git. As duas
cópias `*_restored.npz` têm o mesmo total e ficam excluídas por duplicação.
`__pycache__`, `.pyc` e caches do sistema ficam excluídos.

Não é obrigatório publicar chunks para usar os coeficientes finais. Contudo,
chamar um cache de opcional para publicação não o torna dispensável para
`audit_completed.py` ou para um runner inalterado cuja autorização vincula seu
hash. A reprodução científica desde as fontes exigirá novo orçamento, ambiente
de replay e controle dos diretórios de saída; não está autorizada neste pacote.

## Transporte e destinos explícitos

As seguintes linhas são o núcleo do mapa. **O JSON lista individualmente todos
os demais arquivos**, incluindo tamanho e SHA disponível; não há cópia implícita
por wildcard.

| Origem | Destino futuro | Bytes |
|---|---|---:|
| `tmp/c08_transport/C_beta_parts/manifest.json` | `results/C08/orf_tables/C_beta_parts/manifest.json` | 991 |
| `tmp/c08_transport/C_beta_parts/payload.gz.part0000` | `results/C08/orf_tables/C_beta_parts/payload.gz.part0000` | 94.371.840 |
| `tmp/c08_transport/C_beta_parts/payload.gz.part0001` | `results/C08/orf_tables/C_beta_parts/payload.gz.part0001` | 94.371.840 |
| `tmp/c08_transport/C_beta_parts/payload.gz.part0002` | `results/C08/orf_tables/C_beta_parts/payload.gz.part0002` | 49.381.080 |
| `tmp/c08_transport/C_full_parts/payload.gz.part0000` | `results/C08/orf_tables/C_full_parts/payload.gz.part0000` | 57.536.079 |
| `tmp/c08_runtime_design/src/frozen_coefficient_orf_v2.py` | `results/C08/table_history/c08_runtime_design/src/frozen_coefficient_orf_v2.py` | 13.297 |
| `tmp/c08_beta_table_v2_continuation/RELATORIO.md` | `results/C08/table_history/c08_beta_table_v2_continuation/RELATORIO.md` | Ver JSON |
| `tmp/c08_full_local_v2_execution/RELATORIO.md` | `results/C08/table_history/c08_full_local_v2_execution/RELATORIO.md` | Ver JSON |
| `tmp/c08_table_integration_plan/INVENTARIO.md` | `docs/C08/INTEGRACAO_TABELAS.md` | Documento novo |
| `tmp/c08_table_integration_plan/integration_plan.json` | `results/C08/table_integration_plan.json` | Inventário novo |

Cada bundle inclui também seu README e uma cópia byte exata de
`compactar_arquivo.py`. Os manifests completos trazem os SHA de cada parte e do
fluxo gzip. O utilitário tem SHA
`1b4c7baaecb339daa6a96614b232920f41dedeb56e5f56a547d6a6f7ce6395b4`.
Seu transporte usa gzip determinístico, `mtime=0`, nível 6, partes de no máximo
90 MiB. A leitura descompactada não interpreta conteúdo científico.

Os registros `C_beta_transport_validation.json` e
`C_full_transport_validation.json` declaram `PACK_RESTORE_EXACT_BYTES`.
`tests.log` preserva três testes pequenos aprovados em 0,290 s. Eles não foram
repetidos agora. A igualdade de transporte confirma bytes, não a ciência das
tabelas; os gates físicos vêm das autorizações/relatórios separados.

Comandos **propostos após uma integração futura**, não executados aqui:

```sh
python3 results/C08/orf_tables/C_beta_parts/compactar_arquivo.py unpack \
  --bundle results/C08/orf_tables/C_beta_parts \
  --output results/C08/orf_tables/C_beta_common_table.npz
python3 results/C08/orf_tables/C_full_parts/compactar_arquivo.py unpack \
  --bundle results/C08/orf_tables/C_full_parts \
  --output results/C08/orf_tables/C_full_table.npz
```

O utilitário confere partes, tamanho e hash final e não sobrescreve destino.
O loader v2 verifica os coeficientes por tiles, faz cópias próprias somente após
conferir o orçamento e não refaz spline. Seus 14 testes pequenos históricos estão
documentados em `loader_v2_review.json`; não substituem revisão de memória do
runtime completo. Para as curvas físicas, ativar os guards C1 e paridade
explicitamente. A memória do chamador, descompressão e bancos posteriores não
está incluída no orçamento interno do loader.

## Fontes necessárias e limites do replay

A construção C_beta começa em `beta_builder.py`, com as 15 fontes congeladas de
`executed_sources/src/{inference,pta}` descritas em `source_manifest.json`.
Os gates originais usam `validate_table.py`, `curve_algebra_v2.py`,
`gate_kernel.py` e a referência em `gate_sources/likelihood_reference_snapshot.py`.
`continue_original_diagnostics.py` registra a conclusão do diagnóstico v1.
A execução local v2 usa `run_local_v2.py`/`patch_curve.py`; a continuação usa
`run_sequential.py`, `harmonic_worker.py` e `continuation_gates.py`, seguida pelo
auditor de leitura. Preservam-se também geradores de preflight/autorizações e
testes executados, sem gerar nova autorização retroativamente.

C_full inicial usa `run_sequential.py`, `full_gates.py`, `full_export.py` e
`independent_moments.py`; a continuação diagnóstica está em
`c08_full_original_diagnostics/execution/run.py`. A v2 local usa seu próprio
`run_sequential.py`, `worker.py`, `freeze.py` e `audit_completed.py`, com o
preflight em `c08_full_local_v2_design`. Esses arquivos importam fontes históricas
C_beta e dependem das identidades congeladas; trocar pelas versões atuais de
`src/` não é automaticamente equivalente.

Os scripts antigos calculam ROOT a partir de sua posição e abrem caminhos
`ROOT/tmp/...`. O destino versionado evita um diretório literal `tmp`, abrangido
pelo ignore do projeto. Para replay, restaurar cada entrada no
`restore_original_workspace_relative_path` **em um workspace separado** e
reconstituir as referências externas de identidade compatível. Executar os
scripts diretamente dentro do arquivo histórico sem esse mapeamento muda suas
resoluções de caminho. Runners também recusam diretórios de saída existentes:
não apagar evidência para contornar esse guard. Um controlador portátil futuro
deve ter identidade própria e preservar os snapshots executados.

Por fim, o inventário não inventa identidades faltantes: 512 binários enumerados
não tiveram um SHA de arquivo unívoco localizado nos metadados consultados. Isso
inclui caches/intermediários, não as partes e tabelas finais, cujas identidades e
roundtrips estão completos. O campo `sha256` fica `null` nesses casos; as
referências existentes e o motivo ficam ao lado. Qualquer integração futura que
selecionar esses arquivos deverá fechar sua própria identidade antes de publicar.
Os hashes dos pequenos textos lidos agora não apresentaram divergência frente
aos hashes históricos encontrados. Nenhuma dessas verificações de inventário
reclassifica falhas nem valida posterior C08.
