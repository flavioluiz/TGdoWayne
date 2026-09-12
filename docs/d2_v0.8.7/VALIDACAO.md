# Verificação da v0.8.7

- 217 testes científicos existentes aprovados: 19 C04, 23 C05, 11 C06 e 164 C07.
  Os 58 casos salvos da campanha ORF também foram conferidos.
- Seis testes específicos de retomada/alocação e seis testes de runtime passaram.
  A serialização JSON completa passou após a correção de tipos NumPy.
- Regressão com arquivos reais: recuperação de 38 análises sem avaliador físico,
  identificando exatamente baseline_d7/d13 como referências ainda pendentes.
- Execução final: 40 análises aprovadas nos cinco controles primários; contagens
  reconstruídas e valores importados verificados bit a bit em cada continuação.
- 609 membros do arquivo de fontes, execuções e referências relidos e conferidos
  por SHA-256; falha de serialização e limites por curva preservados.
- PDF final com 129 páginas, sem overfull ou referências/citações indefinidas.
  Todas as páginas foram renderizadas com Poppler: 107 são pixel a pixel idênticas
  a páginas da v0.8.6 já inspecionadas; as 22 diferentes foram revisadas visualmente.
  O resumo foi ajustado para manter as palavras-chave na mesma página.
  As novas tabelas foram examinadas individualmente, sem cortes ou sobreposição.
- Estado editorial, README e manifesto conferidos antes do commit.

Os testes e a auditoria sustentam o alcance funcional descrito, sem concluir
W1, eventos de log-likelihood, D3, SBC ou o marco C09 integral.
