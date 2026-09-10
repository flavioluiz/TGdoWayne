# C13 — Auditoria final e dissertação consolidada

- **Commit planejado:** `docs: publica dissertacao consolidada e auditoria final`
- **Tag e release:** `v1.0.0`
- **Janela estimada:** 22–24.
- **Dependência:** C12 publicado e validado. As etapas anteriores permanecem incorporadas ao PDF.
- **PDF obrigatório:** `output/pdf/v1.0.0/dissertacao.pdf` — disponível após concluir o marco.
- **Conteúdo acumulado do PDF:** Dissertação consolidada e materiais reproduzíveis.

## Objetivo

Entregar uma versão completa, consistente e reproduzível do trabalho para avaliação acadêmica.

## Trabalho que entra neste commit

1. Executar reprodução a partir de ambiente limpo e conferir todas as figuras e tabelas centrais.
2. Resolver pendências científicas e editoriais, referências, siglas, unidades e apêndices.
3. Substituir pseudônimo e identificação provisória pelos dados acadêmicos efetivos antes de uso institucional.
4. Conferir requisitos vigentes do Programa de Física e do ITA para a modalidade de entrega.
5. Publicar dissertação consolidada, código, manifesto e relatório de reprodução; registrar o estado real do artigo.

## Arquivos e produtos esperados

- `latex/dissertacao.tex e capítulos finais`
- `docs/auditoria_final.md`
- `docs/reproducao.md`
- `article/`
- `project_status.json e README.md`

Além desses arquivos, atualizar `project_status.json`, o painel do `README.md`, o estado dos capítulos,
`releases/v1.0.0/RELEASE_NOTES.md`, o PDF e o manifesto da versão. Diretórios científicos
previstos serão criados quando necessários; sua presença neste plano não significa que já existam.

## Critérios de conclusão

- [ ] Um ambiente limpo reproduz resultados centrais dentro das tolerâncias científicas documentadas.
- [ ] Não há capítulos pendentes nem metadados acadêmicos fictícios na versão destinada à instituição.
- [ ] PDF e fontes correspondem à tag v1.0.0; README mostra todos os marcos e o estado real de submissão/defesa.
- [ ] A versão final não implica aprovação, defesa ou aceitação editorial sem que tenham ocorrido.

## Validação exigida

Reprodução integral do núcleo científico, auditoria de proveniência, inspeção visual de todas as páginas e verificação dos assets publicados.

## Risco e decisão de escopo

Se autoria ou requisitos institucionais ainda estiverem pendentes, manter uma versão preliminar adicional; não rotular a entrega como dissertação institucional final.

## Fechamento e publicação

1. Concluir as tarefas e registrar as verificações efetivamente executadas nas notas do release.
2. Atualizar o estado e gerar o README; preparar a versão com o procedimento do [plano geral](../README.md#procedimento-de-fechamento-de-cada-marco).
3. Compilar e inspecionar o PDF completo. Resolver falhas antes de fazer o commit.
4. Incluir fontes, resultados pertinentes, plano atualizado, PDF e manifesto no **mesmo commit**.
5. Criar a tag `v1.0.0`, enviar commit e tag e conferir o PDF anexado ao GitHub Release.
6. Não considerar o marco publicado enquanto o download e seu SHA-256 não forem conferidos.

A aceitação científica é avaliada pelos critérios acima. O sucesso da compilação ou a existência de uma
tag, isoladamente, não significa que os experimentos estejam validados. Correções posteriores seguem a
regra de nova versão descrita no plano geral, preservando o histórico publicado.
