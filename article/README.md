# Artigo metodológico para revisão

O manuscrito em inglês compara compressão, aproximação normal e resposta
dispersiva, usando a população ampliada como resultado central. A autoria
**Gráviton de Souza** é definitiva, conforme escolha do usuário. O artigo não
foi submetido; não há periódico escolhido, aceitação ou publicação editorial.

- Fonte: `manuscript.tex`.
- PDF atual: `manuscript.pdf`, com sete páginas.
- Figura atual: `figures/information_academic.pdf`, gerada por `scripts/figura_artigo_c13.py`.
- Revisão atual: `results/C13/article_review.json`; a conferência C12 documenta a redação anterior.

A revisão acrescenta o exemplo de limite imposto pela priori e os contrastes
condicionais B/C em 50 realizações, distinguindo sua sensibilidade numérica da
incerteza populacional e da comparação com marginalização. Também simplifica
a redação e amplia a figura, preservando seus resultados.

Na raiz, `make article` compila com pdfLaTeX/Biber, exige referências resolvidas
e ausência de caixas excedentes e atualiza o PDF. A figura usa somente as 500
realizações da priori por grupo; os 96 casos de recuperação são separados.
A reprodução da figura em diretório isolado produziu pixels idênticos.

A dissertação contém as derivações e experimentos complementares. As instruções
de reprodução estão em `docs/reproducao.md`, com seu alcance e suas pendências.
