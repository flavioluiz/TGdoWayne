# Segunda leitura independente: antecedentes metodológicos de C03

Consulta em 10/09/2026. Páginas abaixo são páginas do PDF, contadas a partir de 1; coincidem com a numeração impressa nestas versões. Leitura das formulações, experiências e conclusões pertinentes, com conferência visual das equações centrais. Nenhum código dos autores foi executado nesta segunda leitura.

## Han–Zhao: o que foi efetivamente implementado

[Texto primário, versão 2](https://arxiv.org/html/2604.23384v2); [PDF](https://arxiv.org/pdf/2604.23384v2). Cópia local: `literature/papers/2604.23384v2.pdf`.

- Seção II, p.5, Eqs.(4)–(5): canais independentes em frequência e dispersão dependente de massa. Hipóteses: fundo gaussiano, estacionário, isotrópico e não polarizado.
- Seção III, pp.6–10, Eqs.(8)–(18): estimadores quadráticos binados angularmente e covariâncias sinal–sinal, sinal–ruído e ruído–ruído.
- Seção IV.A, p.12, Eqs.(20)–(26): parâmetros amplitude, índice espectral e massa; estatística independente dos parâmetros; mesma binagem angular no modelo; covariância corretamente reescalada.
- P.13, Eq.(27): verossimilhança gaussiana com soma sobre frequências e log-determinante. Eq.(30): log-verossimilhança média/Asimov, incluindo termo de traço devido à covariância variável.
- Pp.14–16: geração gaussiana complexa via Cholesky; 10.000 realizações validam a covariância. Essa validação não mede cobertura dos intervalos de massa. O forecast evita uma campanha de distribuição dos limites, conforme p.13.
- P.14: priori uniforme de massa limitada por `h f_min/c²`; p.18: teste de prioris espectrais; p.19: covariância fixa versus variável, com diferença aproximada de 5% no limite conjunto.

**Antecipação:** multifrequência, binagem consistente e covariância completa já integram inferência de massa. A comparação central apresentada é entre canais PTA/astrometria; não é A/B/C com compressão espectral e `f_ref`.

## Franciolini et al.: o que foi efetivamente implementado

[Texto primário, versão 1](https://arxiv.org/html/2505.24695v1); [PDF](https://arxiv.org/pdf/2505.24695v1). Cópia local: `literature/papers/2505.24695v1.pdf`.

- Seção II, pp.3–5, Eqs.(1)–(11): Whittle sob gaussianidade/estacionariedade, frequências independentes e estatística quadrática suficiente; Eqs.(12)–(15): redução gaussiana sob hipóteses adicionais.
- Seção IV.C, p.14, Eqs.(61)–(67): três detectores, espectros coloridos com formas conhecidas, parâmetros de amplitude; comparação de Whittle, Fisher e verossimilhanças reduzidas por frequência.
- P.15, Eqs.(69)–(73): filtro de amplitude com covariância conhecida e covariância entre pares derivada por Isserlis. P.16, Eqs.(74)–(77): compressão em frequência com filtro ótimo sob sinal fraco e autopoderes condicionados.
- Figura 5, pp.16–17: estimativas de autopoder afetam viés. Apêndice A, pp.20–24, figuras 8–9: 1.000 realizações por sinal fixo, P–P e subcobertura. Não é sorteio de parâmetros da priori.
- Seção V, pp.18–19: contexto PTA de segmento único; os P–P apresentados pertencem aos exemplos anteriores, não a uma campanha de massa dispersiva em PTA.

**Antecipação:** comparação entre frequência preservada e compressão, calibração e efeitos da hipótese gaussiana já existem. Os exemplos inferem amplitudes com formas espectrais especificadas; não variam massa na resposta nem comparam essa resposta com sua avaliação em `f_ref`.

## Juízo sobre a pergunta da dissertação

Há **antecipação parcial substancial**, suficiente para descartar uma alegação ampla de pioneirismo em comparar inferência comprimida e não comprimida, usar multifrequência/covariância ou medir calibração. A ausência de uma experiência operacionalmente igual nas duas formulações examinadas não prova prioridade sobre toda a literatura.

A pergunta remanescente é específica: aplicar às mesmas realizações de uma PTA dispersiva um operador de compressão definido, comparar a previsão integrada com a substituição em `f_ref` e medir quando essa substituição altera a informação sobre massa. A defensabilidade dessa pergunta decorre da especificação diferente de parâmetros, operadores e experiências, não de uma busca por palavras ausentes.

## Consequências operacionais propostas para C06–C09

1. **Não chamar todo contraste A–B de perda de informação.** Se A usar a distribuição de coeficientes Fourier e B aproximar produtos quadráticos por uma gaussiana, mudam também a família da verossimilhança e, eventualmente, a binagem angular. Para isolar compressão espectral, acrescentar um controle com os mesmos estimadores angulares e a mesma família probabilística antes e depois da compressão. Comparar separadamente esse controle à referência Fourier. A interpretação continuará condicionada à adequação da aproximação probabilística e precisará de calibração independente.
2. **Fixar dados e operador.** Os mesmos pesos de B devem ser usados em C, independentes da massa avaliada. Se houver seleção por dados, reproduzir sua construção em cada realização. Pesos construídos com o valor verdadeiro injetado não representam automaticamente uma análise realizável.
3. **Definir a troca B–C sem ambiguidades.** Registrar se `f_ref` modifica somente a ORF ou também suporte espectral e covariância de sinal. Alterar apenas a média enquanto conservar inadvertidamente a massa na covariância define uma experiência híbrida; ela pode servir como ablação, mas deve ser nomeada.
4. **Preservar os controles estatísticos.** Medir cobertura em parâmetros fixos e calibração sob a priori como experiências diferentes. Limites de massa exigem tratamento explícito da fronteira zero e do suporte de propagação. Uma previsão sem flutuações ajuda a dimensionar custos, mas não substitui essas campanhas.
5. **Comparação entre modelos.** Conservar normalizações quando necessárias à evidência. Não comparar números absolutos de evidência para espaços de dados diferentes como se fossem o mesmo fator de Bayes. Calibrar as decisões dentro de cada análise.
6. **Critério científico de continuidade.** C08 deverá produzir regiões quantitativas de validade em massa, conteúdo espectral e sinal/ruído, com incerteza Monte Carlo e erro numérico demonstrados. Apenas reproduzir diferenças entre Gaussian e Whittle ou obter uma posterior mais estreita não satisfaz esse objetivo.

Esta leitura sustenta continuar com recorte estreito e controles explícitos. Não sustenta declarar que o artigo futuro será necessariamente original ou publicável.
