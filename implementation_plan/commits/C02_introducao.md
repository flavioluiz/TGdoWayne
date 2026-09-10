# C02 — Introdução da dissertação concluída

- **Commit planejado:** `docs: conclui introducao da dissertacao`
- **Tag e release:** `v0.2.0`
- **Janela estimada:** 1.
- **Dependência:** C01 publicado e validado. As etapas anteriores permanecem incorporadas ao PDF.
- **PDF obrigatório:** `output/pdf/v0.2.0/dissertacao.pdf` — disponível após concluir o marco.
- **Conteúdo acumulado do PDF:** Introdução concluída; capítulos seguintes identificados como planejados.

## Objetivo

Estabelecer o problema científico e abrir o documento cumulativo da dissertação.

## Trabalho que entra neste commit

1. Criar latex/dissertacao.tex com o template ITA e reutilizar configuração e bibliografia.
2. Redigir motivação, continuidade com o TG de 2003, publicação de 2004 e importância da faixa de PTA.
3. Delimitar a pergunta sobre frequência explícita, compressão consistente e frequência de referência.
4. Fixar objetivos, hipóteses, escopo e organização da dissertação, distinguindo deformações geométricas de graus de liberdade.
5. Incluir um quadro inicial com o estado de cada capítulo e atualizar o README para C02.

## Arquivos e produtos esperados

- `latex/dissertacao.tex`
- `latex/capitulos_dissertacao/01_introducao.tex`
- `latex/estado_capitulos.tex`
- `latex/referencias/referencias.bib`

Além desses arquivos, atualizar `project_status.json`, o painel do `README.md`, o estado dos capítulos,
`releases/v0.2.0/RELEASE_NOTES.md`, o PDF e o manifesto da versão. Diretórios científicos
previstos serão criados quando necessários; sua presença neste plano não significa que já existam.

## Critérios de conclusão

- [x] Introdução contém problema, justificativa, objetivos verificáveis e delimitação de 24 meses.
- [x] Não afirma originalidade confirmada nem detecção de polarizações adicionais.
- [x] PDF cumulativo contém a introdução completa e explicita o que ainda não foi escrito.

## Validação exigida

Revisão textual e de consistência das citações; compilação completa e inspeção visual da capa, sumário e introdução.

## Risco e decisão de escopo

Se os objetivos dependerem de dados ainda não acessíveis, manter o núcleo com simulações e explicitar a condição para a aplicação observacional.

## Fechamento e publicação

1. Concluir as tarefas e registrar as verificações efetivamente executadas nas notas do release.
2. Atualizar o estado e gerar o README; preparar a versão com o procedimento do [plano geral](../README.md#procedimento-de-fechamento-de-cada-marco).
3. Compilar e inspecionar o PDF completo. Resolver falhas antes de fazer o commit.
4. Incluir fontes, resultados pertinentes, plano atualizado, PDF e manifesto no **mesmo commit**.
5. Criar a tag `v0.2.0`, enviar commit e tag e conferir o PDF anexado ao GitHub Release.
6. Não considerar o marco publicado enquanto o download e seu SHA-256 não forem conferidos.

A aceitação científica é avaliada pelos critérios acima. O sucesso da compilação ou a existência de uma
tag, isoladamente, não significa que os experimentos estejam validados. Correções posteriores seguem a
regra de nova versão descrita no plano geral, preservando o histórico publicado.

## Evidência da entrega

Introdução redigida e revisada em `latex/capitulos_dissertacao/01_introducao.tex`;
PDF cumulativo de 12 páginas, com capa, resumo provisório, quadro de capítulos,
sumário, introdução e referências. Verificações locais registradas em
`docs/validacao_v0.2.0.md`; hashes no manifesto do release.
