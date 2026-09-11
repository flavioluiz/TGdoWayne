# Otimizações equivalentes da proposta e custos do pipeline

Todos os arquivos neste diretório são temporários. Nenhuma campanha de 500
dados foi iniciada e nenhuma fonte histórica ou versionada foi modificada.

`multiple_rhs.py` fornece `MultipleRHSGaussianDefensiveProposal`, que herda o
contrato guardado da GMM v2. A API `logpdf(z)` conserva os eixos achatados por
alvo da referência. Cada fator triangular é aplicado a vários pontos de uma
vez; o método padrão `matmul` usa a inversa triangular já calculada por
substituição direta. As alternativas `forward` e `solve` são controles de
equivalência. As constantes normalizadas da mistura, os pesos e a distribuição
Student defensiva permanecem iguais. `logaddexp` acumula os componentes sem
renormalizar pesos amostrais. Não há clipping, regularização adicional ou
ajuste usando dados de produção.

Para integrar, substituir somente os imports externos pelas versões relativas
do pacote: a classe guardada em `gmm_proposal` e `forward_substitution` em
`linalg_batch`. A referência deve permanecer disponível. Os quatro testes em
`test_equivalence.py` verificam os três caminhos de álgebra, a densidade
conjunta contra SciPy, eixos/entradas inválidas e amostragem escalar independente.

| Ensaio de densidade | Referência | Matmul | Ganho |
|---|---:|---:|---:|
| 16 alvos × 8192 pontos | 0.22007 s | 0.06366 s | 3.46× |
| 1 alvo × 65536 pontos | 0.11432 s | 0.03025 s | 3.78× |

As maiores diferenças em logq foram 1.42e−14 contra a referência e 2.47e−13
contra a densidade conjunta normalizada SciPy. As medições usam Apple
Accelerate com `VECLIB_MAXIMUM_THREADS=1`; são tempos locais, não garantias de
throughput concorrente. Fontes e hashes estão em `density_benchmark.json` e
`executed_sources/`.

`audit_vector_sampler.py` preserva uma cópia integral do produtor portátil do
outro agente e executa suas funções reais extraídas por AST. Em 16 alvos com
65536 amostras cada, 336 CDFs de projeções, incluindo direções conjuntas,
tiveram maior desvio 3.270σ frente ao limite normal/Bonferroni 3.793σ. A
normalização escalar de cada projeção combina as Gaussianas e a Student com
sua matriz de escala correta. É um teste finito independente de simulação,
complementar à identidade algébrica, sem certificado de caudas arbitrárias.

`vector_sample.py` agrupa produtos matriciais pelo componente escolhido. Ele
consome exatamente as mesmas sequências de uniformes, normais e qui-quadrados
do produtor portátil: componentes e estado final de RNG foram idênticos; a
diferença máxima das amostras foi 1.78e−15 e de logq, 7.11e−15. O ganho
adicional foi apenas 5%; manter o sampler portátil existente é razoável. A
vetorização por alvo, por sua vez, reduz o custo histórico de 1.755 s para
0.025 s por 65536 amostras. A receita por alvo/réplica é nova e não reinterpreta
as antigas amostras com SeedSequence por coluna.

`logistic_jacobian.py` oferece a identidade estável
`-abs(z)-2*log1p(exp(-abs(z)))`, somada nas coordenadas. Ela é exatamente o
log-Jacobiano da transformação logística com priori uniforme no cubo; as
larguras da priori física cancelam o Jacobiano das coordenadas físicas. Nos
20204 pontos de teste até |z|=1000, o erro contra a expressão com dois
`logaddexp` foi 7.11e−15 e contra `scipy.stats.logistic.logpdf`, 4.44e−16.
A diferença máxima na soma 5D foi 1.07e−14. Expit mais Jacobiano passou de
0.04936 s para 0.02122 s em 65536 pontos. O uso é opcional e matematicamente
equivalente.

`benchmark_pipeline_overheads.py` mede I/O em cópias descartáveis, sem inferência
nova. Em uma réplica de 65536 pontos, NPZ comprimido custou 0.75244 s e
6983991 bytes; NPZ sem compressão custou 0.00652 s e 7407878 bytes. Ambos
reproduziram todos os arrays bit a bit. A diferença é 115× no tempo de escrita
por 6.1% de espaço adicional. Para os resultados temporários, recomenda-se
`np.savez` com quota ativa e remoção somente após diagnóstico rastreável. A
estimativa de quota precisa incluir os cabeçalhos ZIP/NPY, além dos arrays.

Estimativa de trabalho para 500 dados × 5 famílias × 4 réplicas × 65536 pontos:

| Parcela | Extrapolação local |
|---|---:|
| 655360000 logL, usando os 428 mil/s informados pelo root para C++/6 threads | 25.5 min |
| Proposta vetorizada, densidade e Jacobiano | 12.4 min |
| Escrita NPZ sem compressão, hash e leitura verificada | 4.0 min |
| 54 CDFs e diagnósticos de pesos, medidos em 0.918 s/alvo | 38.2 min |
| EM otimizado, usando 0.29–0.35 s/alvo | 12–15 min |

A soma das quatro primeiras parcelas é cerca de 80 min, antes de treinamento,
construção, coordenação, possíveis reexecuções e outros diagnósticos. Não se
deve somar ou extrapolar timings concorrentes como se fossem independentes.
A compressão original acrescentaria cerca de 125 min só na escrita. Retenção
integral de todas as amostras ocuparia aproximadamente 74 GB em NPZ sem
compressão; execução por lotes e liberação auditada limitam o armazenamento
ativo sem alterar resultados científicos.

O treinamento é a incerteza principal de custo: o caso frio escalar mediu
13.49 s/alvo para 8192×4 passos, cuja extrapolação direta seria 9.37 h. O
treinamento batelado precisa de medição própria; os 428 mil logL/s da avaliação
IID não se transferem automaticamente a uma cadeia sequencial com adaptação
e RNG. Construir o banco uma única vez e compartilhá-lo é necessário. Este
relatório não escolhe novos algoritmos, densidades ou critérios estatísticos.
