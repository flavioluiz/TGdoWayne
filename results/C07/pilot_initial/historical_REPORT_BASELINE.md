# Piloto C07: resultado do integrador com amostragem da priori

**O piloto real de16 realizações foi executado; a inferência completa ainda não passou os critérios numéricos. SBC500 não foi executado.**

Todas as análises usam as mesmas16 verdades contínuas e dados físicos/Gaussianos pareados. O experimento12×4 e suas prioris estão congelados em `config.json`. Os quatro níveis iniciais e quatro refinamentos foram preservados em `results/`.

## Separação dos erros

A malha uniforme atribuiu peso excessivo ao valor de extremo em `u=1`. Foram adicionados painéis na camada de pequeno β do primeiro canal, mantendo os pesos de integração em `du`. Com os mesmos2048 pontos de nuisance por scramble, o refinamento75→139 nós efetivos produziu máximos de ΔlogZ=0,000566; Δquantil/largura da priori=0,000254; ΔPIT marginal=0,000258; ΔPIT de log-verossimilhança=0,00110. Isso aprova essa comparação da quadratura de massa; novas propostas de nuisance ainda devem confirmar essa estabilidade.

O aumento para8192 pontos de nuisance em quatro scrambles, seguido de um conjunto independente de quatro scrambles, deixou as seguintes diferenças máximas:

| Família | ΔlogZ independente | Δquantil/largura da priori | Quantis de massa aprovados em ambos os testes de nuisance |
|---|---:|---:|---:|
| A0_CN | 0.021668 | 0.023461 | 6/16 |
| A_CN | 0.051476 | 0.062102 | 3/16 |
| B_CN | 0.009986 | 0.012269 | 7/16 |
| A_G | 0.060639 | 0.044025 | 2/16 |
| B_G | 0.006772 | 0.014248 | 7/16 |

As metas foram mantidas: ΔlogZ≤0,001, diferenças de quantis≤0,001 da largura de priori e ΔPIT≤0,002. Nenhuma família aprovou todos os parâmetros de todas as16 realizações. Os índices e as estimativas parcialmente estáveis estão em `results/partial_numerical_acceptance.json`; aprovação em uma comparação isolada não basta.

## Referências independentes e custo

O kernel CN foi comparado com uma normal real24D; os momentos com traços matriciais diretos; a verossimilhança real com SciPy. Cinco testes passaram. A quadratura de cinco dimensões passou em duas sementes independentes contra uma normal truncada fatorizada analítica: máximos |erro logZ|=1,20×10⁻⁴, erro de quantil=4,27×10⁻⁴ e erro de PIT=2,49×10⁻⁴. Esses testes verificam a implementação, não a resolução das posteriores físicas.

Cada matriz ORF foi calculada em duas resoluções harmônicas. O erro máximo na primeira tabela foi8,01×10⁻¹³; sete entradas comparadas com quadratura direta independente diferiram menos de5×10⁻¹⁵. A comparação de todos os elementos por método independente não foi realizada. O valor mínimo de autovalor−2,74×10⁻¹⁶ é arredondamento; não houve clipping.

A aceleração `FastLikelihood` preservou logL a melhor que3,7×10⁻¹³ nas regiões relevantes. Em um benchmark com500 colunas formadas repetindo os dados salvos,512 pontos de parâmetros custaram1,28s no kernel original e0,088s no novo. Isso projeta aproximadamente13min de likelihood para139×8192×4 pontos e500 colunas por família, ou26min para dois conjuntos independentes, excluindo ORFs, resumos, IO e adaptação. Essa resolução continua reprovada; o número é custo de referência, não promessa de custo final. Duas matrizes grandes de pesos nessa configuração consomem aproximadamente1,31GB, antes dos demais buffers; processamento por grupos é necessário para controlar memória.

## Dependência dos dados e interpretação

O piloto calcula PITs de `log L(theta; dados)` e o controle negativo que ignora os dados e devolve a priori. O controle negativo é útil porque PITs somente de parâmetros podem ser uniformes mesmo quando a inferência não usa os dados. Os valores numéricos permanecem provisórios até resolver a quadratura; não foi feito teste conclusivo de uniformidade com16 realizações.

A massa está fracamente identificada neste cenário de quatro canais: o KL marginal A0 em relação à priori ficou aproximadamente0,0001–0,0315 no conjunto mais recente. Não se trata de um limite observacional ou demonstração robusta de ausência de informação, pois a integração dos nuisances ainda não passou. A revisão de identificabilidade e da priori permanece parte do plano científico.

A e B usam uma família normal aproximada para os dados quadráticos CN. Falhas físicas de calibração não podem ser atribuídas à compressão até separar o erro numérico e a família de verossimilhança. A0_CN e A_G/B_G fornecem os controles apropriados. As evidências de A0/A/B não são diretamente razões de Bayes entre si, pois se referem a diferentes dados/medidas.

## Trabalho em andamento

Propostas defensivas contínuas por grupos de quatro realizações estão sendo treinadas somente com os pesos marginais normalizados do piloto. A produção usa scrambles independentes e redes Sobol completas por componente, com denominador da mistura baseado nos pesos efetivos. A comparação com o integrador da priori é preservada. Em paralelo, a marginalização de uma escala comum está sendo investigada em `tmp/c07_scale/`. Nenhuma dessas alternativas está aprovada pelo presente relatório.
