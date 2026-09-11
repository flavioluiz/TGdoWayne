# Revisão independente dos dados de 500 realizações

A questão adicional foi verificar os sinais das estatísticas imaginárias, a
normalização complexa e os momentos do controle pareado na amplitude e no
condicionamento efetivamente atingidos pelos 500 dados. Isso amplia a checagem
anterior em quatro casos pequenos, sem repetir apenas a chamada do gerador.

`audit_500.py` usa somente NumPy e a biblioteca padrão: não importa
`experiment`, `covariance_batch`, `paired_physical_and_gaussian`,
`quadratic_statistics` ou `quadratic_moments`. Reconstitui as 500 verdades pela
semente registrada, os espectros com unidades explícitas e a sequência de
normais reais e imaginárias. As estatísticas cruzadas são calculadas diretamente
como médias de `q_a conj(q_b)`, com a ordem a<b. Os controles Gaussianos usam
traços matriciais e os mesmos latentes declarados, sem invocar o helper C06.

| Quantidade reconstituída | Maior erro em unidades do desvio padrão declarado |
|---|---:|
| Coeficientes CN complexos | 7.40e−16 |
| Estatísticas quadráticas físicas | 4.50e−15 |
| Controle Gaussiano pareado | 2.93e−15 |

As razões de potência GW/ruído por traço abrangem 5.61e−6 a 474.41. O maior
condicionamento de C é 25.00 e o de Σ, 33.50. Os índices extremos selecionados
por massa, condicionamento e razão sinal/ruído foram 138, 295, 333 e 475.
Nos seus 16 blocos de frequência, uma segunda formulação de Isserlis, via
vetor real de dimensão 24 e covariância
`V=1/2[[Re C,-Im C],[Im C,Re C]]`, confirma
`Cov(X_i,X_j)=2 tr(A_i V A_j V)` com erro relativo máximo 1.63e−16 frente à
formulação complexa. A pseudocovariância dos fatores complexos é zero.

`check_integrity.py` verifica que todas as 500 linhas e todos os 500 caches
foram realmente cobertos, confere novamente os hashes e reconstrói o desenho
nominal de direções, distâncias, ruído branco e padrão vermelho diretamente
das sementes e fórmulas geométricas. Nenhuma entrada foi alterada.

Os valores ORF dos caches previamente validados são entradas desta auditoria.
Ela não repete a quadratura nem aprova uma interpolação diferente. A reprodução
numérica não constitui convergência empírica de momentos entre verdades
diferentes, posterior calibrada, cobertura ou SBC500. O controle Gaussiano
continua sendo um experimento distinto da distribuição quadrática física.

Resultados completos e proveniência: `review.json` e `integrity.json`.
Tempo da reconstrução e auditoria principal: 2.58 s.
