# C12 — Discussão, conclusões e manuscrito

- **Commit planejado:** `docs: conclui discussao conclusoes e manuscrito do artigo`
- **Tag e release:** `v0.12.0`
- **Janela estimada:** 20–22.
- **Dependência:** C11 publicado e validado. As etapas anteriores permanecem incorporadas ao PDF.
- **PDF obrigatório:** `output/pdf/v0.12.0/dissertacao.pdf` — disponível após concluir o marco.
- **Conteúdo acumulado do PDF:** Texto científico integral e manuscrito de artigo preparados.

## Objetivo

Transformar os resultados validados em uma narrativa científica completa e revisável.

## Trabalho que entra neste commit

1. Redigir discussão integrando fundamentos, validação, compressão, robustez e extensão escalar efetivamente obtida.
2. Responder explicitamente aos objetivos e distinguir achados novos de reprodução.
3. Concluir limitações e perspectivas; atualizar resumo, introdução e revisão com o estado final da pesquisa.
4. Preparar manuscrito de artigo com figuras reproduzíveis e declaração de disponibilidade dos materiais.
5. Atualizar o estado dos capítulos e revisar o texto integral.

## Arquivos e produtos esperados

- `latex/capitulos_dissertacao/11_discussao.tex`
- `latex/capitulos_dissertacao/12_conclusoes.tex`
- `article/`
- `docs/matriz_objetivos_resultados.md`
- `latex/dissertacao.tex`

Além desses arquivos, atualizar `project_status.json`, o painel do `README.md`, o estado dos capítulos,
`releases/v0.12.0/RELEASE_NOTES.md`, o PDF e o manifesto da versão. Diretórios científicos
previstos serão criados quando necessários; sua presença neste plano não significa que já existam.

## Critérios de conclusão

- [ ] Toda conclusão pode ser rastreada a um resultado validado; não há afirmação de aceitação ou submissão ainda não ocorrida.
- [ ] O manuscrito tem contribuição delimitada e dialoga com os trabalhos mais próximos atualizados.
- [ ] Resumo e introdução refletem os resultados obtidos, inclusive resultados nulos e reduções de escopo.

## Validação exigida

Auditoria cruzada de números, figuras, tabelas, citações e objetivos; leitura integral dos PDFs.

## Risco e decisão de escopo

A submissão a periódico é um ato posterior com autores e orientação definidos; o objetivo deste marco é deixar o manuscrito pronto para revisão.

## Fechamento e publicação

1. Concluir as tarefas e registrar as verificações efetivamente executadas nas notas do release.
2. Atualizar o estado e gerar o README; preparar a versão com o procedimento do [plano geral](../README.md#procedimento-de-fechamento-de-cada-marco).
3. Compilar e inspecionar o PDF completo. Resolver falhas antes de fazer o commit.
4. Incluir fontes, resultados pertinentes, plano atualizado, PDF e manifesto no **mesmo commit**.
5. Criar a tag `v0.12.0`, enviar commit e tag e conferir o PDF anexado ao GitHub Release.
6. Não considerar o marco publicado enquanto o download e seu SHA-256 não forem conferidos.

A aceitação científica é avaliada pelos critérios acima. O sucesso da compilação ou a existência de uma
tag, isoladamente, não significa que os experimentos estejam validados. Correções posteriores seguem a
regra de nova versão descrita no plano geral, preservando o histórico publicado.
