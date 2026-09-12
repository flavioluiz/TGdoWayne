# Verificação da v0.8.10

- 217 testes científicos existentes aprovados e 58 casos ORF salvos conferidos.
- Teste sintético do kernel de controles próprios aprovado, com nove curvas
  comparadas a SciPy e limite de contagem verificado.
- Três testes da referência W1 aprovados: curvas/prioris/escalas distintas,
  rejeição de coluna indevidamente compartilhada e regressão de serialização.
- Nove observações reconstruídas com momentos por traços: máximo 4,44e-16.
- 21 novas análises com controles primários aprovados; doze contrastes pareados
  reconstruídos a partir dos intervalos numéricos de quantis originais.
- 161 análises aprovadas em W1. Auditoria recalculou os desvios a partir das
  duas referências e três valores tabulados e conferiu os caches anteriores
  bit a bit. Novos valores mais três ligações por curva reproduzem as contagens.
- Falha inicial de serialização preservada com fonte e log. Dez análises W1
  recuperadas sem novas likelihoods; tempo não medido mantido como desconhecido,
  com reserva de 60 s debitada explicitamente.
- 693 membros dos dois arquivos compactados relidos e verificados por SHA-256.
- PDF cumulativo de 133 páginas, sem overfull ou referências/citações indefinidas.
  Todas as páginas foram renderizadas: 111 idênticas, pixel a pixel, à versão
  anterior já revisada. As 22 diferentes foram inspecionadas visualmente,
  com exame individual da nova tabela; sem cortes ou sobreposições.
- README, estado dos capítulos e manifesto conferidos antes do commit.

Os resultados não concluem mistura de distâncias, eventos de logL ou D3/SBC.
O alcance dos controles físicos permanece finito e operacional.
