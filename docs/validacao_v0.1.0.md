# Validação local de C01 / v0.1.0

Data: 10 de setembro de 2026. Documento: proposta de pesquisa, 22 páginas A4.

## Verificações executadas

- `python3 scripts/checagens_preliminares.py`: aprovado; aritmética racional nos vínculos e curvatura,
  aritmética decimal nas escalas físicas. A saída está em `output/pesquisa/checagens_preliminares.json`.
- `python3 -m py_compile scripts/*.py`: scripts compilados sem erros de sintaxe.
- Compilação com pdfLaTeX, latexmk e Biber concluída; nenhuma citação ou referência indefinida,
  nenhum quadro de texto ultrapassando a margem (`Overfull`).
- Todas as 22 páginas foram renderizadas com Poppler e inspecionadas: capa, sumário, texto,
  tabelas, equações, notas, cabeçalhos, paginação e referências. Foram corrigidas quebras indevidas
  de tabelas e a distribuição de conteúdo; a versão final não contém texto do exemplo do template.
- Conferência byte a byte dos 57 arquivos extraídos do ZIP do template: nenhuma modificação.
- Treze arquivos de plano individual presentes e ligados ao roadmap; estado do README conferido
  pelo gerador. Os marcos futuros estão explicitamente identificados como planejados.

## PDF inspecionado

SHA-256: `3ac4674de3b363cb9606f1851895ab876d6e057cc930fa439b1d068328dd1b18`.

O manifesto da versão deve registrar o mesmo hash. Os avisos herdados do template sobre
`tracklang`, opção antiga de `hyperref`, `epstopdf` com shell escape desabilitado e caixas
`Underfull` no sumário não impediram a compilação; sua saída foi conferida visualmente.
A versão não usa conversão externa de EPS nem shell escape.

## Alcance

A validação acima cobre a proposta, sua apresentação e as checagens cinemáticas implementadas.
Não valida uma ORF, um amostrador, dados observacionais ou a originalidade definitiva do recorte.
A integridade de publicação é verificada pelo workflow e pela comparação do PDF baixado do release
com o manifesto. Essa verificação remota sucede o commit; não é um resultado científico adicional.
