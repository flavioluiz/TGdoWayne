# Transporte C08 v3 — namespace de artefatos offline

Candidato não executado sobre os produtos reais. Não foi criado inventário
real, ZIP real ou árvore restaurada real. O v2 permanece intacto, SHA
`323b2cf7467bd1618917a0afec4d17ce6556d5bfe9c63c337cfa7bf2c3822f07`.
A proposta de seleção é `selection_proposal.json`; não é um arquivo aceito
por `planejar` e não contém hashes/contagens inventados dos futuros recibos.

## Delta mínimo

`v3.patch` altera somente `audit_offline`, o schema do bundle para
`C08_LOSSLESS_EVIDENCE_BUNDLE_v3` e a lista de schemas legíveis(v1/v2/v3).
Todos os demais corpos de função têm AST idêntica ao v2, incluindo auditoria
de engenharia/main/replay, locks, hashing, ZIP, restauração e dependências.
A nova semântica aplica-se somente a `kind=offline`.

A completion ROOT fica numa **nova pasta de metadados**. Ela pode declarar
`artifact_namespace:"repository"`; nesse caso cada artefato usa
`{"path":"caminho/relativo/ao/repositorio","sha256":"...","bytes":N}`.
Cada path deve ser canônico, relativo e membro do inventário efetivamente
selecionado, com o mesmo SHA e tamanho. Existir no disco, ter SHA correto
ou estar apenas nas dependências externas não o torna artefato transportado.
`file` não pode aparecer junto com essa modalidade. Completion e revisão
ROOT também devem estar na seleção.

A revisão ROOT exige explicitamente o mesmo `artifact_namespace`, uma
identity não vazia coincidente e `artifact_count` inteiro exato, além dos
campos legados de completion SHA, root path, lock path e status. Não há
inferência de PASS científico. Nenhuma completion é adicionada às pastas
históricas: a execução finita original continua FAILED e sua continuação
continua com os próprios registros, custos e resultados.

Quando o namespace não é declarado (ou é `base`), os artefatos legados
`{"file":"nome/relativo/a/base",...}` continuam relativos à base da
completion. A saída dessa auditoria legada também mantém seu formato v2.

## Contrato proposto para ROOT

A nova pasta sugerida é `tmp/c08_offline_transport_ROOT/`, ainda não criada
pelo pacote. Sua `complete.json` usa o schema existente
`C08_OFFLINE_ROOT_COMPLETE_v1`, status
`ALL_SELECTED_ANALYSIS_BYTES_PRESERVED`, `scope`, `identity`,
`workers_exited:true`, `all_failures_preserved:true`, `no_uniform_proof:true`,
`artifact_namespace:"repository"` e a lista real de artefatos com path/SHA/bytes.

A revisão `ROOT_C08_OFFLINE_ROOT_REVIEW_v1` usa status
`OFFLINE_ROOT_COMPLETE_REVIEWED`, `root_path` apontando para essa nova pasta,
`lock_path` explícito, `completion_sha256`, a mesma `identity`,
`artifact_namespace:"repository"` e `artifact_count`. Os dois documentos
podem viajar como metadados adicionais; sua própria inclusão não exige um
SHA autorreferente na lista da completion.

A seleção real continuará `C08_ARCHIVE_SELECTION_v1`: a única campanha
`kind=offline` aponta para a nova pasta de metadados; `include` contém as
raízes físicas e de análise originais. Assim não é necessário copiar126MB
para uma pasta intermediária. `plan` faz a união dos caminhos selecionados,
e `pack` grava exatamente esses caminhos relativos. A restauração produz
`NOVO_PREFIXO / caminho_relativo_original`, nunca
`NOVO_PREFIXO / nova_metadata / caminho_relativo_original`.
Strings absolutas dentro dos JSON históricos não são reescritas.

## Seleção proposta, ainda não inventariada

O JSON de proposta distingue:

- raiz finita original `tmp/c08_finite_domain_execution_CANDIDATE`;
- continuação `tmp/c08_finite_assess_continuation_OUTPUT`;
- recibos/fontes/autorização original e continuação em `tmp/c08_finite_ROOT`;
- suplemento/evidência/índice e lifecycle/revisão da síntese em
  `tmp/c08_supplemental_ROOT`;
- resultados compactos e PDFs em `tmp/c08_paired_synthesis_OUTPUT`;
- os fontes congelados, testes, plano e subsídios C08 usados nesses passos;
- QA visual opcional e o orçamento explícito da continuação.

As tabelas, campanhas C07, engenharia/main C08 e replay/optionalKL já têm
bundles ou referências externas. Não se incluem essas árvores novamente.
Dependências path/SHA necessárias à reprodução deverão ser extraídas dos
manifestos congelados existentes, sem inventar hashes nem copiar o conteúdo
ou as árvores restauradas. Os snapshots de fontes já pertencentes à raiz
finita original são preservados como parte de seus bytes históricos.
As clouds finitas de LL/nuisance são resultados de controles autorizados;
não são os diretórios de raw posterior IID, que continuam excluídos.
Nenhuma raiz C09 é proposta.

O arquivo de inventário e o futuro bundle devem ficar fora das raízes
selecionadas. A lista individual do próprio pacote v3 evita incluir seus
próprios futuros inventários/bundles recursivamente. A seleção final e seus
recibos pertencem a ROOT; este pacote não chama `planejar` sobre os dados reais.

## Um TOY de transporte

Um cenário sintético realizou plan/pack/verify/restore de três arquivos
pequenos em duas raízes, com a completion numa terceira pasta. Verificou:
restauração no prefixo original, igualdade dos hashes, preservação de FAILED
e de `scientific_pass:false`, rejeição de artefato não selecionado apesar
de existente, divergências de namespace/identity/contagem na revisão,
traversal e compatibilidade do formato legado relativo à base. O teste também
compara a AST de todas as outras funções com o v2.

Resultado:1 teste PASS,0.026821sCPU (0.065013s com imports), RSS33,013,760B.
É um teste somente de bytes sintéticos; não interpreta NPZ, não verifica
resultados científicos e não executa física.

```sh
.venv/bin/python -B tmp/c08_campaign_archive_v3/tests/test_repository_namespace.py
```

Após ROOT consolidar seus recibos, ler o delta e autorizar o inventário,
o CLI v3 aceita os mesmos comandos `planejar`, `empacotar`, `verificar` e
`restaurar`. O primeiro passo real é somente `planejar`; o inventário ainda
precisa ser revisado antes de qualquer pack. Nenhuma execução real desses
comandos foi iniciada aqui.
