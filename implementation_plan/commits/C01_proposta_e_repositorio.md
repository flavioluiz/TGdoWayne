# C01 — Proposta de pesquisa, plano e repositório

- **Commit planejado:** `docs: publica proposta de pesquisa e plano de execucao`
- **Tag e release:** `v0.1.0`
- **Janela estimada:** Preparação, antes do mês 1.
- **Dependência:** Nenhum; este é o commit inaugural.
- **PDF obrigatório:** [`output/pdf/v0.1.0/proposta_pesquisa.pdf`](../../output/pdf/v0.1.0/proposta_pesquisa.pdf) — disponível após concluir o marco.
- **Conteúdo acumulado do PDF:** Proposta de pesquisa completa; dissertação ainda não iniciada.

## Objetivo

Transformar a análise do TG em uma proposta de mestrado rastreável, compilável e publicada, com critérios de execução para todo o projeto.

## Trabalho que entra neste commit

1. Preservar TG_Wayne.pdf e o ZIP original; extrair o template ITA com sua licença e registrar a procedência.
2. Preparar a proposta em LaTeX com contexto, literatura recente, pergunta, metodologia, validação, cronograma e limites de escopo.
3. Registrar as checagens cinemáticas executadas e separar seus resultados dos experimentos futuros.
4. Criar o plano geral, os 13 planos de commit, o painel de estado no README e a automação de release.
5. Compilar, revisar visualmente todas as páginas, preparar manifesto SHA-256, inicializar Git e publicar main e v0.1.0.

## Arquivos e produtos esperados

- `latex/proposta.tex e latex/capitulos_proposta/`
- `latex/referencias/referencias.bib`
- `implementation_plan/, project_status.json e README.md`
- `scripts/, templates/ e .github/workflows/release.yml`

Além desses arquivos, atualizar `project_status.json`, o painel do `README.md`, o estado dos capítulos,
`releases/v0.1.0/RELEASE_NOTES.md`, o PDF e o manifesto da versão. Diretórios científicos
previstos serão criados quando necessários; sua presença neste plano não significa que já existam.

## Critérios de conclusão

- Proposta sem resultados estatísticos inventados, com referências verificáveis e distinção entre artigo e preprint.
- PDF sem referências indefinidas, páginas cortadas ou conteúdo fictício do exemplo ITA; autoria provisória explícita.
- Checagens preliminares passam; manifesto confere fontes e PDF; README aponta para o PDF da tag inaugural.
- O repositório contém um único commit inicial e a tag v0.1.0; o asset publicado coincide com o PDF versionado.

## Validação exigida

Executar as checagens em Python, compilar com pdfLaTeX/Biber, renderizar todas as páginas, verificar hashes e conferir o download do GitHub Release.

## Risco e decisão de escopo

Se a publicação automática falhar, diagnosticar a execução do Actions. O PDF já versionado permanece disponível; só marcar a publicação como verificada depois de conferir o asset.

## Fechamento e publicação

1. Concluir as tarefas e registrar as verificações efetivamente executadas nas notas do release.
2. Atualizar o estado e gerar o README; preparar a versão com o procedimento do [plano geral](../README.md#procedimento-de-fechamento-de-cada-marco).
3. Compilar e inspecionar o PDF completo. Resolver falhas antes de fazer o commit.
4. Incluir fontes, resultados pertinentes, plano atualizado, PDF e manifesto no **mesmo commit**.
5. Criar a tag `v0.1.0`, enviar commit e tag e conferir o PDF anexado ao GitHub Release.
6. Não considerar o marco publicado enquanto o download e seu SHA-256 não forem conferidos.

A aceitação científica é avaliada pelos critérios acima. O sucesso da compilação ou a existência de uma
tag, isoladamente, não significa que os experimentos estejam validados. Correções posteriores seguem a
regra de nova versão descrita no plano geral, preservando o histórico publicado.
