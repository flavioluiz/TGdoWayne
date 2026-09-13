# Revisão editorial e científica — 13 de setembro de 2026

O manuscrito foi reestruturado para apresentar o desenho de comparação como contribuição metodológica. Esta revisão usa os resultados existentes: não altera os experimentos nem acrescenta novas simulações.

## Alterações

- Resumo centrado no problema, no desenho controlado e nas conclusões, retirando contagens operacionais.
- Introdução com contexto observacional, lacuna de atribuição causal entre escolhas de análise e três contribuições explícitas.
- Figura 1 em TikZ com os geradores CN e G, estatísticas, compressão e substituições da resposta. A figura de informação passa a ser a Figura 2.
- Resultados organizados em calibração, perda de informação e sensibilidade condicional B/C. A comparação condicional saiu da Discussão e passou para Resultados.
- Discussão com recomendações de interpretação dos limites: KL marginal da massa, sensibilidade à priori e calibração. A referência analítica sem aprendizado ganhou uma equação própria.
- Extensão escalar com a degenerescência no limiar e citação direta da dissertação que a demonstra.
- Detalhes de resolução e quadratura preservados no apêndice A.

## Limites das afirmações propostas

Não foi encontrada base para afirmar que o desenho é absolutamente inédito ou que toda a literatura confunde as três operações. A introdução identifica um exemplo concreto e reconhece trabalhos antecedentes.

Zhao e Wang (seção III, página 4 do PDF arXiv:2607.14790v1) distinguem duas razões: a compressão em frequência motiva a frequência de referência; a indisponibilidade da covariância completa motiva a aproximação diagonal. O artigo agora preserva essa distinção.

A falha de calibração no experimento sintético identifica uma limitação no regime testado. Não demonstra falha necessária em todo conjunto observacional nem determina o sinal de um viés de massa.

O relato de KL é proposto como recomendação, junto a outras verificações. KL elevado não garante validade do modelo, e KL conjunto pode ser dominado por parâmetros auxiliares. Não se impõe um limiar universal de KL.

A degenerescência escalar torna a identificabilidade uma questão central, mas não prova amplificação catastrófica dos erros. A pequena diferença condicional B/C também não demonstra que a compressão causou essa semelhança nem estabelece equivalência populacional.

## Fontes e verificações

Referências adicionais no texto: Wu et al. (2024), Agazie et al. (2024), Zhao e Wang (2026) e a dissertação. Liang–Trodden e Cordes et al. foram incorporados à motivação inicial; Franciolini et al. e Han–Zhao continuam explicitamente reconhecidos como antecedentes.

As fontes bibliográficas foram conferidas no acervo e nas páginas primárias disponíveis. O trecho de Zhao–Wang foi lido no PDF local. A revisão preserva os números de calibração, informação e contrastes já publicados no repositório. Os relatórios C12/C13 continuam sendo registros das revisões históricas; não são certificados desta nova redação.

A versão revisada deve ser identificada pela data e pelo commit. O release v1.0.0 permanece como registro da versão anterior; não houve submissão editorial.
