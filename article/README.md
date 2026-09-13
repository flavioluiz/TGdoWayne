# Artigo metodológico para revisão

**Revisão atual: 13 de setembro de 2026 — 9 páginas, 2 figuras e 10 referências.**

- [PDF atual](manuscript.pdf)
- [Fonte LaTeX](manuscript.tex)
- [Notas da revisão científica e editorial](REVISION_NOTES.md)

O manuscrito em inglês apresenta um desenho controlado para distinguir aproximação normal de estimadores quadráticos, compressão em frequência e substituição da resposta dispersiva. A população ampliada permanece como resultado central. A discussão relaciona calibração, informação e sensibilidade à priori, incluindo a degenerescência escalar como motivação para extensões.

A autoria **Gráviton de Souza** é definitiva, conforme escolha do usuário. O artigo não foi submetido; não há periódico escolhido ou aceitação editorial. O release v1.0.0 conserva a redação anterior. Esta revisão é identificada pela data e pelo commit, sem alterar aquele release.

## Compilação e figuras

Na raiz, `make article` compila com pdfLaTeX/Biber, exige referências resolvidas e ausência de caixas excedentes, e atualiza `article/manuscript.pdf` e `output/pdf/article/manuscript.pdf`.

A Figura 1 é um fluxograma vetorial em TikZ no próprio LaTeX. A Figura 2 usa `figures/information_academic.pdf`, gerada por `scripts/figura_artigo_c13.py`, sem mudança dos resultados. São usadas somente as 500 realizações da priori por configuração; os 96 casos de recuperação são separados.

As referências compartilhadas estão em `latex/referencias/referencias.bib`; `references.bib` acrescenta a dissertação como fonte dos resultados complementares. Os relatórios C12/C13 documentam as redações históricas, não esta revisão.

O PDF revisado foi conferido visualmente nas nove páginas. Não foram executadas novas simulações nesta revisão. As instruções de reprodução científica permanecem em `docs/reproducao.md`.
