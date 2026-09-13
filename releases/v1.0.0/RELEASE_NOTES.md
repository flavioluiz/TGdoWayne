# v1.0.0 — Dissertação consolidada e reprodução científica

A dissertação apresenta o estudo de massa do gráviton e polarizações em PTAs,
com foco na compressão em frequência, na adequação das verossimilhanças e na
informação fornecida pelos dados. O texto foi reorganizado para leitura
acadêmica, preservando resultados inconclusivos e separando as limitações
científicas dos registros técnicos de execução.

- Template ITA, Programa de Pós-Graduação em Física, área de Física Nuclear;
  autoria, orientação e banca conforme os nomes definitivos escolhidos.
- Conversões entre unidades naturais e SI; discussão de Fierz–Pauli, vDVZ,
  Boulware–Deser e Vainshtein; apêndice de bases escalares e marginalização
  da escala comum.
- Destaque à subcobertura das aproximações normais para estimadores quadráticos
  físicos e ao exemplo analítico de limite superior determinado pela priori.
- Experimento de ajuste de timing com 20.000 séries por amostragem: projeção
  dos parâmetros temporais, covariância e pseudocovariância de Fourier.
- Estudo condicional em 50 realizações, com 300 posteriores: os 200 contrastes
  têm raio de sensibilidade numérica menor que 0,01. Os intervalos numéricos
  das quatro médias ficam dentro de [-0,01;0,01]. A comparação original com
  marginalização do ruído continua inconclusiva; o novo estudo não constitui
  demonstração de equivalência populacional.
- Figuras redesenhadas, tabelas conferidas e 167 páginas inspecionadas.
  Manuscrito em inglês atualizado, com sete páginas, ainda não submetido.

A reprodução usa uma cópia isolada das fontes e dos dados, com entradas
verificadas, mantendo o ambiente científico fixado. As respostas, observações,
inferências e sínteses reproduzidas estão documentadas em `docs/reproducao.md`
e `docs/auditoria_final.md`. A execução reutiliza o ambiente local; não é uma
instalação independente em outro sistema operacional. Insumos pré-calculados
e a biblioteca nativa tensorial reutilizada estão explicitados nesses documentos.

Os sinais, distâncias e ruídos analisados são sintéticos. As posições de catálogo
ampliam a geometria dos experimentos. Não houve aplicação inferencial a tempos
de chegada observados, nova restrição observacional de massa, submissão do
artigo, defesa ou aprovação institucional.

A campanha tensorial foi inteiramente reexecutada: 2.500 alvos, 20.000 réplicas
e 175.000 arrays idênticos. Sua nova síntese reproduziu os 155 testes,
15 contrastes e 14 arrays anteriores. As campanhas escalar e de robustez
também reproduziram as 6.344 e 25.956 posteriores, respectivamente.

PDF: `output/pdf/v1.0.0/dissertacao.pdf`. O manifesto acompanha o release
e identifica as fontes e os resultados usados nesta entrega.
