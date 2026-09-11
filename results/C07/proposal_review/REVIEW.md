# Auditoria independente da proposta GMM com Student defensiva

A proposta treinada válida passou nas verificações da densidade conjunta, do sorteio e da razão MH. A auditoria também identificou falhas de validação de entradas no construtor original; elas foram corrigidas em um módulo v2 separado, sem alterar as fontes ou os resultados da execução histórica.

## Densidade conjunta e simulação

A distribuição em cinco coordenadas logit é `q(z)=0,85 Σ_k w_k N(z;μ_k,Σ_k)+0,15 t_5(z;m,S)`, com quatro componentes Gaussianas e `S=3²(5−2)/5 LLᵀ`. A matriz S é a matriz de escala da Student; a covariância de seu componente é `9 LLᵀ`. A amostra Student usa `m+3 L ε sqrt(3/χ²_5)`. O logpdf soma a mistura completa, incluindo constantes, determinantes e pesos. A ordenação de entrada/saída da implementação original é alvo primeiro e amostra/cadeia depois.

Todos os 16 alvos do treino têm pesos positivos e soma unitária a 1,11×10⁻¹⁶. A menor covariância de componente tem autovalor 0,04328; o menor elemento diagonal do Cholesky global é 0,25182 e sua parte triangular superior é zero.

A avaliação de 4112 densidades conjuntas contra misturas de `scipy.stats.multivariate_normal` e `multivariate_t` teve diferença máxima de logpdf de 3,18×10⁻¹³. Não foram comparadas somente as marginais.

Foram sorteados 65536 pontos por alvo pelo sampler congelado. Compararam-se 336 CDFs de projeções: as cinco coordenadas e duas combinações lineares que dependem das covariâncias conjuntas, em três cortes fixados pelos parâmetros da proposta. A CDF de cada projeção foi calculada independentemente como mistura de normais univariadas e Student univariada. O maior desvio padronizado foi 3,714. O desvio padrão usado aqui é o binomial exato de sorteios IID com limiar fixo, não um ESS de pesos.

A normalização em todo R⁵ foi também verificada por importância com um envelope Student-t3 independente, de média global e matriz de escala `4 LLᵀ`. A média de `q/h` deve ser 1. Quatro réplicas de 16384 pontos por alvo tiveram desvio máximo agrupado de 1,892 erros padrão de Monte Carlo. Esta checagem finita é evidência complementar à fórmula normalizada; não é uma prova numérica absoluta de integral 1.

## Razão MH e Jacobiano

O alvo em z é `L(θ(z)) Π_j x_j(1−x_j)`, pois os fatores da largura da priori física uniforme cancelam os mesmos fatores do Jacobiano. Para a proposta independente entra `log q(z_atual)−log q(z_novo)`; para o passeio aleatório fixo a proposta é simétrica. Ao renovar u ou uma nuisance pela priori uniforme em x, a densidade logística da proposta em z cancela exatamente o Jacobiano da coordenada renovada, restando a diferença de log-likelihood.

A implementação foi exercitada com quatro movimentos distintos na mesma chamada: renovação de massa, renovação de nuisance, GMM independente e passeio simétrico. Um alvo Beta(5,5) em cinco dimensões forneceu log-likelihood e Jacobiano separadamente. Foram calculadas as razões de Hastings completas por uma derivação independente; uniformes imediatamente abaixo/acima de cada limiar produziram exatamente as oito decisões esperadas. Isso verifica a razão implementada, sem alegar mistura rápida ou calibração posterior.

## Origem do ajuste

O hash do array antigo `pilot553_refresh_draws.npy` coincide com o registrado em `mixture_training.json`. O treino selecionou 512 índices temporais fixos, quatro cadeias por alvo, totalizando 2048 pontos por alvo. Os parâmetros globais e escalas do passeio coincidem exatamente com `pilot553_refresh.json`. Os pontos de treino estavam no interior do cubo unitário.

A inspeção de `fit_mixture.py` e `fit_proposal` confirmou que somente os estados e metadados do piloto anterior entram no ajuste. Nenhum parâmetro verdadeiro nem amostra da nova produção é passado ao ajuste. O script de nova produção usa as verdades somente depois de amostrar, nos diagnósticos. Os seeds das execuções antiga e nova são distintos e a adaptação da produção está desativada.

O JSON histórico do treino registrava o hash dos estados antigos, mas não os hashes dos metadados antigos ou da implementação de ajuste. A auditoria preserva esses bytes e hashes agora, explicitamente como registro posterior; não os apresenta como se já estivessem registrados antes da execução antiga. Para novos treinamentos, esses hashes devem integrar o manifesto antes da produção.

## Falhas de contrato encontradas e v2

O construtor v1 aceitava cinco entradas inválidas testadas: Cholesky global com parte superior não nula, diagonal negativa, covariância assimétrica, ν=NaN e pesos cuja soma era 1,000001. O primeiro caso torna o sampler e a densidade inconsistentes: o sorteio usa a matriz inteira, enquanto a substituição progressiva usada pelo logpdf ignora sua parte superior. Esses casos não ocorrem no artefato treinado auditado.

A v2 acrescenta guards, cópia dos arrays recebidos e checagem de finitude das precisões/normalizações. Todos os cinco contraexemplos foram recusados. Ela normaliza explicitamente apenas o erro de arredondamento dos pesos, limitado a 10⁻¹⁴, e registra a diferença de soma original. No caso treinado, a diferença de logpdf versus v1 foi no máximo 1,78×10⁻¹⁵ e os sorteios comparados foram bit a bit idênticos. Nenhuma covariância ou Cholesky é reparada.

A proposta v2 foi então usada num novo benchmark IID separado em `tmp/c07_iid_gmm/`, com sementes novas e o mesmo protocolo da Student anterior. A tabela ORF553 permanece sem aprovação de precisão; a aprovação desta proposta não aprova o interpolador, as posteriores ou SBC500. Nenhum arquivo versionado foi alterado nesta auditoria.
