# Adequação ao template ITA fornecido

A dissertação passa a usar `\maketitle` da classe original em modo `msc`,
sem modificar `templates/ita/ita.cls`. A abertura corresponde à folha de rosto
do mestrado fornecida pelo template; a capa com logotipo dessa classe é exclusiva
do modo de graduação e não foi usada.

Foram incluídas ficha catalográfica, cessão de direitos, composição da banca,
resumo em português, abstract traduzido do resumo científico, listas de figuras,
tabelas, siglas e símbolos e folha de registro ao final. Dedicatória,
agradecimentos e epígrafe são opcionais e não foram inventados.

Os nomes indicados pelo usuário são definitivos para este documento. Os campos
administrativos de data da defesa, registro e indexação institucional ficam em
branco. A frase automática de aprovação foi substituída por indicação de avaliação
pela banca. A ficha gerada pelo modelo não representa catalogação homologada.

As adaptações locais corrigem a largura da tabela da banca, da lista de tabelas
e do parágrafo da folha de registro, além da altura do cabeçalho. A tradução tem
nome distinto do arquivo demonstrativo do template para evitar colisão no caminho
de busca TeX. O template original foi preservado.

Compilação e inspeção: `results/C13/ita_frontmatter_review.json`. PDF de conferência:
`output/pdf/conferencia/dissertacao.pdf`. Nenhum release intermediário foi criado.
A auditoria científica integral de C13 permanece pendente.

## Programa e área de concentração

Programa de Pós-Graduação em Física; área de concentração Física Nuclear (FIS-N). O enquadramento temático adotado é a linha Astrofísica, Cosmologia e Gravitação, que inclui ondas gravitacionais na [página oficial do PG-FIS](https://pgfis.ita.br/pt/post/fisica-nuclear), consultada em 12/09/2026. O campo `course` permanece Física e `area` passa a Física Nuclear. A identificação e a folha de registro do documento refletem essa distinção.
