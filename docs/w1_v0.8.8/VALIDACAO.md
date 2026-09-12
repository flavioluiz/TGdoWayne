# Verificação da v0.8.8

- 217 testes científicos existentes aprovados: 19 C04, 23 C05, 11 C06 e
  164 C07. Os 58 casos salvos de ORF também foram conferidos.
- Quatro testes analíticos W1 aprovados, com log preservado no arquivo.
- Duas referências por curva, 40 análises aprovadas e 13 caches anteriores
  preservados bit a bit. Contagem reconstruída como novos valores salvos
  mais três avaliações de ligação por curva: 87987 avaliações.
- Entradas vinculadas conferidas por SHA-256, assim como todos os membros
  do arquivo compactado de fontes, resultados, recibos e caches.
- PDF cumulativo com 130 páginas, sem overfull, citações ou referências
  indefinidas. Todas as páginas foram renderizadas: 108 são pixel a pixel
  idênticas a páginas da v0.8.7 já revisadas. As 22 diferentes foram
  inspecionadas visualmente; resumo e nova derivação também individualmente.
  Não foram observados cortes, sobreposições ou palavras-chave órfãs.
- README, estado dos capítulos, fontes e manifesto conferidos antes do commit.

O resultado é operacional no backend congelado. Não conclui os eventos de
log-likelihood, a campanha D3/SBC ou o marco C09 integral.
