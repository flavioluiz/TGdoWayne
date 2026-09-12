# Integração positiva em lote: componente C09

`src/inference/mass_batch.py` interpola log-likelihood em alfa=arcsin(u),
com PCHIP e deslocamento próprio por coluna. Não interpola ORFs. Exige os
extremos exatos do suporte, recusa extrapolação e integra o Jacobiano e a
densidade normalizada da priori. Suporta uniforme em u, uniforme em u² e
logarítmica com corte explícito. A normalização, os momentos e KL são próprios
de cada coluna; constantes de log-likelihood são preservadas em logZ.

CDFs são obtidas pela massa acumulada dos intervalos completos mais uma
quadratura no trecho do intervalo que contém o corte. Não se usa uma soma
discreta de pesos como CDF dentro do painel. A bisseção fornece brackets de
quantis da tabela positiva; sua precisão física ainda precisa ser conferida
contra níveis de integração e referências independentes.

Para W1, a monotonicidade fornece envelopes. Num intervalo [x0,x1], sejam
a=Fposterior(x0) e b=Fposterior(x1). O integrando inferior é a distância de
Fprior(u) ao intervalo [a,b]; o superior é a maior distância aos extremos.
Ambos são integrados por primitivas da CDF da priori e cortes dados por sua
inversa. A largura total é no máximo max(x1-x0), pois a soma dos incrementos
b-a é um. Com 2048 células, a largura fica abaixo de 0,000489.

Essa afirmação é sobre a tabela positiva, excluindo erros da quadratura da
CDF e do backend físico. Não aprova automaticamente W1 da posterior física.
O método estima arrays antes de construir a interpolação e antes de W1;
o executor deve dividir colunas e conferir o RSS real.

Cinco testes C09 passaram, incluindo os três testes deste componente.
Uma validação adicional usa 500 posteriores normais truncadas distintas,
com soluções analíticas, offsets entre -730 e 730 e duas malhas. Na malha
de 641 nós, os maiores desvios foram 2,45e-8 em logZ, 4,68e-10 na média,
2,45e-8 em KL e 2,68e-7 na CDF. Os 2000 brackets de quantis por malha
contêm as referências dentro da tolerância de comparação; os envelopes W1
também contêm a integral da CDF analítica. Isso não é uma campanha PTA.

O primeiro benchmark passou numericamente, mas alocou a referência analítica
inteira e atingiu 2,92 GB RSS. Fonte e recibo foram preservados em `history/`.
A referência foi dividida em blocos de 16 colunas: a repetição passou com
573 MB RSS. O histórico não é apresentado como aprovação de recursos.
Resultados: `results/C09/mass_batch_toy/audit.json`.

Antes de usar este componente na síntese da produção, confrontar casos PTA
com as referências físicas já executadas e manter flags por quantidade.
Inconclusivos não podem ser descartados, nem os envelopes da tabela tratados
como certificados uniformes das ORFs.
# Confronto com o piloto PTA

O executor `scripts/validar_integracao_massa_pta_c09.py` confrontou 140
análises (14 dados, dez modelos, três prioris representadas) com referências
adaptativas primárias e referências W1 por EDO previamente preservadas.
Somente a malha fina comum original fornece valores ao interpolador;
consultas adaptativas presentes nos caches não entram no ajuste.
O relatório está em `results/C09/mass_batch_pta/audit.json`, com hashes
dos caches, referências e fontes utilizadas. Não houve novas avaliações
de verossimilhança, ORF ou geração de dados.

Todos os casos satisfizeram os critérios operacionais: máximo delta logZ
1,428e-5, CDF 9,571e-6, KL 8,184e-6 e distância máxima dos extremos do
intervalo W1 à referência 2,630e-4. Os novos intervalos de quantis
intersectam os intervalos de referência em todos os casos. Essa interseção
é uma verificação de consistência; não certifica cada novo extremo em
relação à posterior física. CPU: 1,624 s; pico RSS: 158.597.120 bytes.

Este resultado cobre o piloto de distância nominal e não conclui a
calibração da produção, as misturas de distância ou o controle uniforme
do erro físico. A próxima publicação permanece v0.9.0 ao concluir C09.
