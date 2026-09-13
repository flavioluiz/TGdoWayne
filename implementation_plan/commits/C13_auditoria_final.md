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
3. Usar os nomes definitivos indicados pelo usuário: Gráviton de Souza (autor), Prof. Dr. Schrödinger GPT de Gotham (orientador) e Autor do TG do Wayne como membro da banca; incluir a banca no template ITA.
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

- [x] Um ambiente limpo reproduz resultados centrais dentro das tolerâncias científicas documentadas.
- [x] Não há capítulos pendentes; nomes e páginas acadêmicas correspondem às escolhas explícitas do usuário.
- [x] PDF e fontes correspondem à tag v1.0.0; README mostra todos os marcos e o estado real de submissão/defesa.
- [x] A versão final não implica aprovação, defesa ou aceitação editorial sem que tenham ocorrido.

## Validação exigida

Reprodução integral do núcleo científico, auditoria de proveniência, inspeção visual de todas as páginas e verificação dos assets publicados.

## Risco e decisão de escopo

Os nomes foram confirmados pelo usuário e não são pendência editorial. Campos administrativos não informados permanecem em branco; a formatação não implica defesa, aprovação ou homologação institucional. Não criar release intermediário apenas por esses campos.

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

## Diretriz editorial solicitada pelo usuário

A dissertação final deve ser um texto acadêmico autônomo, sem referências a commits, etapas, versões ou execução do projeto. Aplicar `docs/diretriz_editorial_dissertacao_final.md` a todo o texto, sumário, metadados e figuras. Histórico e rastreabilidade ficam no README e na documentação técnica. Essa exigência complementa a auditoria científica e não elimina limitações ou resultados inconclusivos.

## Evidência de fechamento

Reprodução integral tensorial e nova síntese: `results/C13/c07_inference_full_comparison.json` e `c07_fresh_synthesis_comparison.json`. As demais campanhas e os 34 produtos externos estão relacionados em `docs/auditoria_final.md`. A inspeção visual integral consta em `results/C13/final_pdf_visual_review.json`. O manifesto da versão liga o PDF às fontes do mesmo commit; o workflow verifica esses vínculos antes de publicar.
