# Validação de C03 / v0.3.0

Data: 10/09/2026. PDF cumulativo: 23 páginas A4. SHA-256: `0a41841c8accb5b6a9ec9a9bed20736f12155f6038d90614f52f709d8605979a`.

## Conteúdo e bibliografia

Introdução atualizada e revisão com nove seções, seis equações e confronto dos antecedentes
mais próximos. As 25 chaves citadas no documento pertencem à bibliografia, sem duplicatas.
O protocolo, a matriz de 17 entradas e a decisão registram uma busca dirigida, sem alegação
de exaustividade. Uma segunda leitura dos métodos de Han–Zhao e Franciolini et al. verificou
páginas e equações e motivou controles adicionais nos planos C05–C10.

A revisão matemática corrigiu a expressão geral de correlação escalar: os dois termos cruzados
entre setores e pulsares são preservados, inclusive quando a ORF é complexa. A redução a uma
parte real não é imposta a distâncias arbitrárias. O operador de compressão atua em um vetor
real de estimadores, com partes real e imaginária separadas quando necessárias.

## Acervo e receita

22 PDFs, 452 páginas, 25.149.237 bytes. Conferidos formato PDF, número de páginas, identificador
nas primeiras páginas, tamanho e SHA-256; hashes também comparados com `shasum -a 256`.
As licenças indicadas foram confrontadas com registros primários, sem atribuir licença de projeto
a arquivos de terceiros. O grau de leitura é individual, não presumido pelo download.

`python3 scripts/download_papers.py --verify` passou 22/22 no layout definitivo.
Em checkout temporário foram verificadas ausência de acesso à rede com `--verify`, rejeição
de URL sem versão e rejeição de hash divergente preservando o arquivo existente.
As evidências estão em `docs/literatura/auditoria_acervo.json` e `verificacao_download.json`.

## PDF e publicação

Compilação pdfLaTeX/Biber sem citações ou referências indefinidas e sem caixas Overfull.
Todas as 23 páginas foram renderizadas com Poppler e inspecionadas. A inspeção identificou
sobreposição do cabeçalho longo com a paginação; foi corrigida por um título curto de navegação.
As entradas bibliográficas passaram a permanecer inteiras na mesma página. Capa, resumo,
quadro de capítulos, sumário, corpo e referências foram conferidos na versão corrigida.

README, metadados, estado dos capítulos e manifesto são verificados pelos scripts de publicação.
O manifesto inclui catálogo e documentação do acervo, excluindo PDFs locais de terceiros.
A verificação editorial e bibliográfica não é validação de inferência estatística; C04–C13
continuam sujeitos aos respectivos critérios científicos.
