# Referência independente dos quantis de A0, dado 14

A tarefa delimitada foi concluída para o modelo gaussiano complexo próprio A0 e a realização de índice zero 14. Os dados, as prioris e os cortes de localização foram mantidos. Não é uma campanha dos 16 dados nem SBC de 500 realizações.

Os 16 quantis dos quatro parâmetros auxiliares passaram na primeira tentativa: os mesmos intervalos contêm a probabilidade solicitada tanto em 20³ como em 32×20×12 nós de nuisance, com 75 e 139 nós de massa. Cada intervalo tem largura de 0,0009 da largura da priori; o ponto médio fica a no máximo 0,00045 dessa largura do quantil de cada CDF numérica comparada. A maior diferença entre estimativas lineares de localização foi 2,56057×10⁻⁵ da largura da priori. Comparação entre resoluções não fornece um limite analítico universal do erro de quadratura.

| Parâmetro | q05 | q50 | q90 | q95 |
|---|---:|---:|---:|---:|
| u | 0.056933481 | 0.538742056 | 0.913324274 | 0.956972398 |
| log10_Agw | -15.910362843 | -15.162743125 | -14.641542880 | -14.550874588 |
| gamma_gw | 3.136645059 | 4.250246062 | 5.212536647 | 5.351879759 |
| log10_Ar | -14.980813951 | -14.596635781 | -14.525772874 | -14.514209128 |
| log10_EFAC | -0.298113755 | -0.267859792 | -0.215899766 | -0.198445850 |

As amplitudes e o EFAC estão em log10; u e o índice espectral são adimensionais. Os valores de u acima são pontos médios do envelope das quatro quantificações de massa, e seus intervalos estão no JSON.

Não foi avaliada a CDF no ponto médio dos intervalos dos parâmetros auxiliares. O JSON fornece a CDF nos dois extremos, a variação observada entre resoluções e o limite explícito das contribuições omitidas. Pela monotonicidade, esses extremos delimitam verticalmente a CDF no ponto médio. O maior desvio vertical permitido por esse envelope é 0,00606994; cinco intervalos têm envelope maior que 0,002. Assim, não se deve substituir automaticamente F(q_médio) pela probabilidade nominal para testes de MCMC. A comparação pode usar os extremos e desigualdades unilaterais, com multiplicidade e erro de Monte Carlo explícitos.

A localização barata usa 27 massas e uma correção baseada nos cortes anteriores, apenas para propor o próximo intervalo. A aprovação usa as quatro regras completas e não herda precisão da aproximação de localização. Os numeradores por massa permitem repetir a regra de 75 nós por seleção, sem uma nova campanha de 139 massas.

Para acelerar a CDF, cada integral de escala é majorada pelo comprimento do intervalo vezes o máximo da likelihood de escala. O orçamento de omissão relativo foi 10⁻¹² por avaliação. O limite soma contribuições da quadratura finita omitidas, sem limitar o erro de substituir a integral contínua pela quadratura. A validação original teve 60 comparações de escala e 20 comparações de CDF sem omissão, com diferença máxima de CDF 1,3101×10⁻¹⁴. A execução dos 16 quantis consumiu 1251,65 segundos sob carga concorrente.

O protótipo adicional que compartilha a decomposição espectral entre 16 vetores de dados teve aceleração de 1,67–1,79× e diferenças locais de log-integral ≤6,83×10⁻¹³. Isso mede custo de um kernel em três condições fixas; não constitui 16 posteriores globais nem validação de seus PITs.

O pacote preserva os JSONs históricos, inclusive seus hashes de fontes temporárias, e fornece fontes portáteis separadas. Dezesseis funções/classes matemáticas mantêm AST idêntica, exceto o import de YEAR; seis testes após a portabilidade verificam normalização e covariância conjunta da priori, truncamento da medida, Cholesky independente, lote versus escalar, limite de omissão e identidade do cache. A migração não foi apresentada como repetição da campanha completa.

