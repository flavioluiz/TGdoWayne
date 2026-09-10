# C03 — Revisão bibliográfica e originalidade

- **Commit planejado:** `docs: consolida revisao bibliografica e matriz de originalidade`
- **Tag e release:** `v0.3.0`
- **Janela estimada:** 1–2.
- **Dependência:** C02 publicado e validado. As etapas anteriores permanecem incorporadas ao PDF.
- **PDF obrigatório:** `output/pdf/v0.3.0/dissertacao.pdf` — disponível após concluir o marco.
- **Conteúdo acumulado do PDF:** Introdução e revisão bibliográfica detalhada concluídas.

## Objetivo

Confirmar ou corrigir a lacuna candidata antes de investir na implementação principal.

## Trabalho que entra neste commit

1. Documentar bases consultadas, consultas, data de corte e critérios de inclusão em uma busca bibliográfica atualizada.
2. Comparar Visser, Fierz–Pauli e teorias modernas, polarizações exatas, ORFs, inferência de massa e publicações de 2024–2026 ou posteriores.
3. Inspecionar códigos e suplementos dos trabalhos mais próximos, especialmente compressão e prioris em PTA.
4. Criar matriz problema/modelo/dados/aproximação/validação/limitação; separar resultados publicados, preprints e apresentações.
5. Registrar uma decisão explícita sobre continuidade ou mudança do recorte e ajustar introdução, objetivos e marcos afetados.

## Arquivos e produtos esperados

- `latex/capitulos_dissertacao/02_revisao.tex`
- `docs/literatura/protocolo_busca.md`
- `docs/literatura/matriz_originalidade.csv`
- `docs/literatura/decisao_recorte.md`
- `latex/referencias/referencias.bib`

Além desses arquivos, atualizar `project_status.json`, o painel do `README.md`, o estado dos capítulos,
`releases/v0.3.0/RELEASE_NOTES.md`, o PDF e o manifesto da versão. Diretórios científicos
previstos serão criados quando necessários; sua presença neste plano não significa que já existam.

## Critérios de conclusão

- [ ] Cada afirmação de lacuna é confrontada com os trabalhos mais próximos e suas versões consultadas.
- [ ] A matriz explica o que é reprodução, contribuição candidata e hipótese ainda não testada.
- [ ] Há uma pergunta específica e viável que não depende apenas de repetir seis polarizações, incluir distância finita ou melhorar chi-quadrado.

## Validação exigida

Conferir metadados, DOI/arXiv, status editorial e citações; revisar se o projeto se distingue de códigos e análises já disponíveis.

## Risco e decisão de escopo

Se houver trabalho equivalente, delimitar cedo uma extensão concreta (por exemplo, escalar vinculada ou outro mecanismo de perda de informação). Publicar a decisão e revisar o plano no mesmo marco.

## Fechamento e publicação

1. Concluir as tarefas e registrar as verificações efetivamente executadas nas notas do release.
2. Atualizar o estado e gerar o README; preparar a versão com o procedimento do [plano geral](../README.md#procedimento-de-fechamento-de-cada-marco).
3. Compilar e inspecionar o PDF completo. Resolver falhas antes de fazer o commit.
4. Incluir fontes, resultados pertinentes, plano atualizado, PDF e manifesto no **mesmo commit**.
5. Criar a tag `v0.3.0`, enviar commit e tag e conferir o PDF anexado ao GitHub Release.
6. Não considerar o marco publicado enquanto o download e seu SHA-256 não forem conferidos.

A aceitação científica é avaliada pelos critérios acima. O sucesso da compilação ou a existência de uma
tag, isoladamente, não significa que os experimentos estejam validados. Correções posteriores seguem a
regra de nova versão descrita no plano geral, preservando o histórico publicado.
