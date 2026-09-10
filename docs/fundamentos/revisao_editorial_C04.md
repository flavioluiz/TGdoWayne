# QA editorial independente — C04 / v0.4.0

Inspeção de 10/09/2026. **Nenhum truncamento, sobreposição ou inconsistência bloqueadora foi encontrado nas páginas PDF 1–20 examinadas.** Nenhum arquivo versionado foi alterado, e nenhum PDF foi recompilado ou gerado nesta auditoria.

## Evidência do artefato e da renderização concluída

- `pdfinfo tmp/latex/dissertacao/dissertacao.pdf`: **36 páginas A4**, 421345 bytes; assunto “Dissertação de mestrado em desenvolvimento — v0.4.0”; autor “Gráviton de Souza (pseudônimo)”.
- Antes da inspeção foram confirmados os **36 arquivos `page-01.png` a `page-36.png`**, todos não vazios, e as **nove folhas `sheet-1.jpg` a `sheet-9.jpg`**, também não vazias, em `tmp/pdfs/v0.4.0/`.
- SHA-256 do PDF inspecionado: `cdd5339121aa9f45a0216263fd67bb5068ee680d082892158945aefb9e1ea93f`.

Após esta inspeção, a raiz informou uma única correção tipográfica na página 33, fora deste escopo: preservar os dois hífens literais de `--check`. As páginas 1–20 não foram alteradas. A nova cópia foi conferida por metadados, sem recompilação nesta auditoria: **36 páginas**, 421287 bytes, mesma versão e autor; SHA-256 `1b35fc07e946ab78782598e7fd095ab6a9cc1e308912940b46ee09001a4553a0`. A inspeção visual de sua página 33 ficou com a raiz.

## Achados visuais

| Evidência | Páginas PDF | Resultado da inspeção |
|---|---:|---|
| `sheet-1.jpg` | 1–4 | Capa, resumo, quadro de capítulos e sumário íntegros. Autor “Gráviton de Souza”, pseudônimo provisório; Programa de Física; orientação identificada como “Autor do TG do Wayne”, sem atribuição formal. Capa declara v0.4.0/C04 e data de 10/09/2026. |
| `page-02.png`, ampliada | 2 | Resumo encurtado cabe integralmente na página, incluindo palavras-chave. Declara introdução, revisão e fundamentos concluídos, **19 testes**, e a ausência de nova inferência observacional ou campanha estatística concluída. Sem texto cortado na margem inferior. |
| `page-04.png`, ampliada | 4 | Sumário cabe em uma página; entradas e números permanecem separados e legíveis. Introdução inicia na página impressa 1, revisão na 7, fundamentos na 17 e referências na 30. Sem sobreposição entre títulos longos, pontilhados e números. |
| `sheet-2.jpg` | 5–8 | Introdução, seções 1.1–1.4 e Eqs. (1.1)–(1.2) legíveis, sem colisão com cabeçalhos ou margens. Continuidade de parágrafos entre páginas preservada. |
| `sheet-3.jpg` | 9–12 | Objetivos, viabilidade, organização das entregas e início da revisão íntegros. Enumeração e títulos têm espaçamento suficiente. A organização identifica C04 concluído e C05 futuro no documento. |
| `sheet-4.jpg` | 13–16 | Revisão, Eqs. (2.1)–(2.3) e citações legíveis. Conjugação das respostas e controle probabilístico aparecem no texto; nenhuma fórmula invade a numeração ou o texto adjacente. |
| `sheet-5.jpg` | 17–20 | Antecedentes de 2026, configurações A0/A/B/C, prioris e síntese crítica íntegros. Eqs. (2.4)–(2.6) e a lista de quatro configurações estão completas. A contribuição continua qualificada como candidata. |

O quadro editorial da página 3 registra capítulos 1–3 concluídos e resposta de PTA como capítulo planejado. O README informa que a implementação de C05 está em andamento. São estados compatíveis: o capítulo de C05 ainda não integra o PDF liberado, embora o trabalho preparatório esteja ativo. O próprio quadro explica essa distinção.

## Alinhamento read-only dos 19 testes e do fluxo de release

- `scripts/reproduzir_tg.py` carrega explicitamente as classes `tests.test_polarizacoes.GeneralIdentities` e `tests.test_normalizacao.EinsteinNormalization`. Contagem estática por AST: **12 + 7 = 19 métodos de teste**. O conjunto de identificadores coincide exatamente com `results/C04/validacao.json`.
- O registro contém `stage=C04`, `status=PASS`, `tests_run=19`, zero erros e zero falhas. Seu escopo é curvatura, vínculos e convenções, com exclusão explícita de inferência PTA e de afirmação de estabilidade não linear. Esta auditoria conferiu o registro e a seleção de testes; não repetiu sua execução.
- `requirements.txt`, registro e README concordam em **SymPy 1.14.0 e mpmath 1.3.0**. O modo `--check` reexecuta as provas e compara o resultado ao registro sem substituí-lo.
- O README apresenta **C04 concluído, quatro de 13 marcos**, C05 em andamento e links explícitos para o PDF de `v0.4.0`, suas notas e a cópia versionada. A identidade provisória coincide com a capa e `project_status.json`. A presença dos links foi conferida; a publicação remota dessa tag não foi testada nesta auditoria editorial.
- `Makefile`: `make check` e `make release` executam `scripts/reproduzir_tg.py --check`; o primeiro também verifica checagens preliminares, estado do README e integridade do release. `make pdf` produz somente a cópia de conferência, coerente com o README.
- `.github/workflows/release.yml`: cria ambiente científico, instala as dependências fixadas, executa os mesmos testes em `--check` e verifica o PDF versionado. A etapa de publicação usa o PDF indicado no manifesto e **não o recompila**. `verify_release.py`, chamado pelo workflow, confere também README, estado dos capítulos e hashes das entradas.

**Escopo desta aprovação:** páginas PDF 1–20 e alinhamento estático dos artefatos listados. A inspeção das páginas 21–36, das novas equações do capítulo 3 e a conferência final da publicação pertencem à auditoria conduzida pela raiz.
