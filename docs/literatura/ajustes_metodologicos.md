# Ajustes pontuais aos planos C05–C10 decorrentes de C03

Ajustes incorporados ao plano no commit C03. Mantém etapas, tags, produtos, testes já exigidos e publicação de PDF a cada commit. Não reduz nenhum critério científico anterior. Base: matriz de originalidade e segunda leitura independente de Han–Zhao e Franciolini et al.; revisão Liang–Trodden v3 de 24/07/2026.

## Vocabulário operacional comum

- **A0:** referência probabilística em coeficientes Fourier gaussianos sob as hipóteses de geração explicitadas.
- **A:** estimadores angulares que conservam frequências e família de verossimilhança definida.
- **B:** mesmos estimadores de A comprimidos em frequência por operador previamente definido; modelo e covariância passam pelo mesmo operador.
- **C:** mesmos dados e operador de B, com substituição em `f_ref` especificada componente por componente.

A0–A avalia redução para estimadores e aproximação probabilística. A–B isola a compressão espectral somente quando todos os demais elementos estão compatibilizados e calibrados. B–C avalia a substituição da resposta. A0 é controle adicional; as três análises centrais permanecem A/B/C. Não chamar B de exata apenas porque seus momentos foram propagados.

## C05 — resposta e ORF

**Acrescentar ao item 4:** “Fixar Liang–Trodden arXiv:2108.05344v3 (24/07/2026) e Cordes et al. arXiv:2407.04464v2 como versões dos benchmarks. Registrar equação, normalização, unidades e ramo de velocidade em cada configuração; revisão posterior ao artigo original não é uma nova medição.”

**Novo item de trabalho:** “Documentar a resposta geral incluindo termos temporais da métrica e quatro-velocidades dos observadores; verificar sua redução tensorial. Deixar a implementação da população escalar para C10, sem transplantar fórmulas antigas de códigos sem comparação com a revisão consultada.”

**Novo critério:** “A normalização não é refixada em cada massa de modo a absorver inadvertidamente o sinal dispersivo. Autocorrelação e coincidência angular de pulsares distintos são tratadas separadamente.”

## C06 — simulador e operadores

**Ampliar o item 3:** “Implementar estimadores angulares por frequência e sua compressão, com pesos, tratamento de pares, unidades e covariância documentados. Guardar a estatística anterior à compressão. Fixar os pesos antes de avaliar parâmetros; quando aprendidos dos dados, repetir sua construção em cada realização. Pesos calculados com a verdade injetada são controle idealizado, não análise observacional realizável.”

**Novo produto:** `docs/contrato_comparacoes.md`, especificando A0/A/B/C; dados de entrada; família probabilística; médias; covariâncias; normalização; suporte espectral; `f_ref`; pesos e variáveis que mudam em cada contraste.

**Novos critérios:** “Mesma binagem angular atua na estatística e na previsão. Propagação dos momentos pelo operador é verificada contra realizações. Gaussianidade de estimadores quadráticos não é presumida pelo fato de o campo gerador ser gaussiano.”

## C07 — inferência e calibração

**Ampliar o item 1:** “Implementar referência A0 e controle A de mesma família probabilística que será usada em B/C. Retê-los separados para medir o efeito da aproximação de verossimilhança antes da campanha de compressão.”

**Acrescentar ao item 4:** “SBC sorteia parâmetros da priori; cobertura em valores fixos e P–P condicionais são experiências distintas, com denominadores e incertezas reportados. Tratar massa zero, limite superior unilateral e censura pelo suporte cinemático. Uma previsão Asimov dimensiona recursos, mas não valida cobertura.”

**Novo critério:** “Campanha possui controles com mesma família de verossimilhança e estimadores antes/depois da compressão. Divergências A0–A não são atribuídas a perda de frequência.”

## C08 — campanha de compressão

**Substituir item 1:** “Executar A/B/C nas mesmas realizações e comparar também com A0 em cenários centrais. Relatar separadamente A0–A, A–B e B–C, segundo o contrato de comparações aprovado em C06.”

**Ampliar item 2:** “Evidências devem preservar normalizações e ser comparadas como fatores de Bayes entre hipóteses no mesmo espaço de dados. Não subtrair evidências absolutas de A e B como se fossem um único fator de Bayes.”

**Novo item:** “Definir se C troca a ORF somente na média ou também na covariância do sinal. Uma troca somente na média mantendo massa dispersiva na covariância é ablação explicitamente denominada; a análise de frequência única completa deve aplicar a escolha consistentemente. Não alterar ao mesmo tempo o suporte dos canais sem uma experiência própria.”

**Novo critério:** “Mapa de validade quantitativo em massa, espectro e sinal/ruído inclui diferença de limites, calibração, erro Monte Carlo e erro numérico. Posterior mais estreita ou mera diferença entre Gaussian e Whittle não satisfaz a pergunta principal.”

## C09 — prioris e covariâncias

**Ampliar item 3:** “Fatorial separado para covariância completa/diagonal e fixa/variável com parâmetros. Quando variável, incluir log-determinante e avaliar sua adequação probabilística. Medir empiricamente a direção do efeito; não pressupor conservadorismo.”

**Ampliar item 5:** “Distinguir informação da forma angular, da distribuição em frequência e do corte cinemático. Variar priori em massa mantendo constantes os demais elementos da análise; mudanças de medida requerem Jacobiano. Prioris logarítmicas possuem corte inferior próprio e não contêm massa zero.”

**Novo critério:** “SBC e distribuições condicionais de limites são recalibradas para prioris e modelos representativos. Resultado Asimov não é apresentado como distribuição de limites obtida por realizações.”

## C10 — helicidade zero

**Ampliar item 1:** “Derivar a resposta completa de Fierz–Pauli a partir dos vínculos e do desvio de frequência incluindo observadores, e confrontá-la com Liang–Trodden v3 Eq.(22). Confrontar também as combinações escalares de Bernardo–Ng/PTAfast, compatibilizando teoria e amplitude. A presença de um vínculo transversal/longitudinal por si só tem antecedentes.”

**Ampliar item 2:** “Distinguir a amplitude de população da normalização da polarização e da eficiência de excitação pela fonte. Equipartição e desacoplamento no limite sem massa não são impostos silenciosamente. Declarar se a população é fenomenológica ou derivada de modelo de fonte.”

**Novo critério:** “Subconjunto escalar conserva os controles A0/A/B/C de C06–C09, incluindo covariância. Testar o limite tensorial ao zerar a amplitude escalar; não exigir que o modelo completo de Fierz–Pauli se reduza a RG apenas fazendo a massa tender a zero.”

## Referências que motivam os ajustes

- [Liang–Trodden v3, seção III](https://arxiv.org/html/2108.05344v3).
- [Han–Zhao v2, seções III–V](https://arxiv.org/html/2604.23384v2).
- [Franciolini et al., seção IV.C e apêndice A](https://arxiv.org/html/2505.24695v1).
- [Cordes et al. v2](https://arxiv.org/html/2407.04464v2).
- [Bernardo–Ng, notebooks associados](https://github.com/reggiebernardo/PTAfast/tree/1ea54bf5456635d1301d5c6b42d98e2c601d3a02/app3_cvlimitedgravity).
