# v0.4.0 — C04: fundamentos e reprodução do TG

A dissertação cumulativa tem 36 páginas e inclui introdução, revisão e fundamentos
teóricos concluídos. O novo capítulo apresenta 41 equações, demonstrações dos vínculos
 e dos postos, reprodução das projeções do TG e comparação com Hyun et al.

## Entregas científicas

- Curvatura elétrica geral sem hipótese de propagação nula; convenções de fase, métrica,
  Riemann, traço invertido e unidades explícitas.
- Parametrizações regulares de Visser e Fierz–Pauli; provas por menores não nulos,
  limites nulo e de limiar e exemplo da não uniformidade do limite de amplitudes.
- Relação escalar vinculada de Fierz–Pauli e reprodução das Eqs.5.58–5.61 do TG por
  contração independente, distinguindo tetradas, projeções e observáveis.
- Auditoria independente de Einstein linear e dos prefatores históricos: diagnóstico
  dimensional no TG sob SI e fator dois na cadeia literal do artigo de 2004.
  Não se declara errata editorial confirmada; a massa de dispersão é definida operacionalmente.
- Tabela de escalas físicas conferida contra avaliações em precisão decimal ampliada.

## Implementação e verificação

`src/polarizacoes/`, `tests/` e `scripts/reproduzir_tg.py` integram as provas simbólicas.
Os **19 testes passaram**: doze de polarizações e sete de normalização. O registro
`results/C04/validacao.json` inclui expressões, domínios, versões e identificadores dos testes.
SymPy1.14.0 e mpmath1.3.0 estão fixados em `requirements.txt`.

A execução foi conferida também em uma cópia com layout separado, iniciada fora da raiz.
Makefile e workflow reexecutam os testes antes da publicação. O PDF foi compilado com
pdfLaTeX/Biber e teve todas as 36 páginas renderizadas e inspecionadas. Detalhes em
`docs/validacao_v0.4.0.md` e `docs/fundamentos/`.

## Alcance

A contagem é cinemática e a consistência dinâmica examinada é linear. Esta versão não
prova estabilidade não linear, continuidade física com RG para fontes, detectabilidade
ou novos limites observacionais. C05 está em andamento; suas ORFs e benchmarks ainda
não são uma entrega deste commit. O acervo local de 22 artigos permanece disponível.
