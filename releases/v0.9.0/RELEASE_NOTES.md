# v0.9.0 — Robustez condicional, informação e limites numéricos

Entrega C09 do plano original, com dissertação cumulativa e C10–C13 abertos.

- 5.396 observações verificadas, 25.956 posteriores de base e painel pareado
  de 1.600 integrações para cinco prioris e dez análises sobre 32 dados.
- 90 grupos descritivos e 39 contrastes, com 14.268 diferenças pareadas:
  covariâncias, contaminantes, ruídos, espectros, distâncias e fronteiras.
- Diagonalização apresenta efeitos dos dois sinais. Omissão de contaminantes
  pode reduzir artificialmente limites. Mudanças de priori e suporte são
  distinguidas da informação efetiva e da escala h/T.
- Família SBC de 18 grupos/126 testes completa: 116 não rejeições condicionais
  e 10 indeterminados. Todos os IDs permanecem; intervalos não resolvidos
  usam [0,1]. Não se afirma calibração física completa ou aprendizado da massa.
- 834 análises de massa e 2.287 eventos permanecem sem resolução operacional.
  Limiares físicos e referências SciPy foram calculados; os domínios
  interpolados não possuem certificado físico uniforme.
- 67.072.009 avaliações acumuladas de likelihood; D3 registra 7.920 nós
  e 85.695.910.009.872 produtos reais estimados, incluindo o histórico.
- 24.238 arquivos restaurados e relidos com SHA-256. Onze ZIPs novos
  reutilizam dependências em 20 anteriores; três caches grandes têm partes
  ordenadas, reconstruídas pelo script de restauração.

Validação: 164 testes de componentes e nove testes C09; controles anteriores
de fundamentos, ORF e simulador; compilação, manifesto e inspeção visual do PDF.
Os checks verificam seu escopo específico e não aprovam casos indeterminados.

Consulte `docs/c09_restauracao_producao.md` para restauração e o capítulo 8
para resultados, hipóteses, limitações e distinção entre histórico e produção.
O trabalho permanece um experimento Fourier periódico com parâmetros
auxiliares conhecidos, sem reanálise observacional ou validação da extensão
escalar. C10, C11, C12 e C13 serão entregues nos próximos marcos originais.
