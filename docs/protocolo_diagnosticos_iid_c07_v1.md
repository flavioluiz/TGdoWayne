# C07: diagnóstico prospectivo de importância IID, versão 1

Este é um protocolo adicional para integração numérica por importância. Não substitui o protocolo MCMC v2 nem reclassifica seus pilotos. O arquivo `protocol_config.json` foi escrito antes da primeira leitura dos resultados IID pelo responsável por este diagnóstico. A produção de fundamentos usa quatro replicações independentes em cada nível, N=1024 e N=8192, e 16 alvos previamente escolhidos. Não há SBC PTA de 500 realizações neste pacote. A tabela ORF553 permanece sem aprovação física de sua interpolação.

## Distribuição e separação do ajuste

A proposta conjunta em cinco logits é uma mistura Student com ν=5, escalas de covariância 1 e 3 e probabilidades .75/.25. Parâmetros ajustados no aquecimento MCMC anterior ficam congelados. As novas produções usam sementes independentes desse ajuste, entre replicações e entre níveis. Condicional à proposta congelada, os pontos devem ser IID: escolhe-se o componente aleatoriamente a cada ponto e avalia-se a densidade **completa da mistura**. Uma alocação determinística por componente teria outra análise de variância e não está abrangida.

Com x_j=σ(z_j), θ_j=a_j+(b_j−a_j)x_j e priori uniforme normalizada na caixa, o volume da caixa cancela no produto priori–Jacobiano. O peso completo é

    log w = log L(θ;y) + Σ_j [log σ(z_j)+log σ(−z_j)] − log q_z(z).

Portanto Z=E_q w é a evidência absoluta sob a mesma medida dos dados e todas as constantes da verossimilhança. Um deslocamento arbitrário de logw preserva CDFs, mas desloca logZ; não é permitido para evidência sem restaurar a constante. Nenhum Bayes factor entre A0/A/B é definido aqui, pois os espaços de dados diferem. A densidade da proposta deve cobrir todo o suporte do alvo. A componente larga melhora a exploração, mas não demonstra por si só que os pesos têm variância finita ou que todos os modos foram visitados.

## CDF, influência e erro Monte Carlo

Para um corte t fixo, h_i=1[g(θ_i)≤t], p_i=w_i/Σw e F̂=Σp_i h_i. A variável de influência plug-in é

    ψ_i = (w_i / mean(w)) (h_i−F̂) = N p_i(h_i−F̂).
    se_IID² = sample_variance(ψ; ddof=1) / N.

Essa é uma aproximação delta para uma razão de médias IID. Ela inclui a covariância entre numerador e denominador, sem tratar a normalização como conhecida. O fator N/(N−1) é a correção de variância amostral adotada. Intervalos normais resultantes são assintóticos e exigem controle de caudas; não são exatos para N finito. A razão tem viés em amostra finita. Em particular, não se substitui N por ESS em Clopper–Pearson, teste binomial ou distribuição exata de ranks.

Calcula-se também um erro entre replicações. Para R blocos de mesmo N, Ẑ_r=mean(w_r), Ẑ_pool=mean_r Ẑ_r e F̂_pool é a razão de todas as amostras juntas. A influência de bloco é g_r=(Ẑ_r/Ẑ_pool)(F̂_r−F̂_pool); então se_R=sd(g_r)/√R. O erro operacional é max(se_IID,se_R). Com R=4, se_R é instável: seu uso é um controle adicional, não uma garantia. A média simples das CDFs auto-normalizadas dos blocos não é a CDF pooled e não substitui esse cálculo.

A meta de cada CDF é se≤.00335. Ela corresponde a aproximadamente um quarto de sqrt(.9×.1/500)=.013416, o erro entre realizações no cenário de cobertura nominal .9. São fontes de incerteza diferentes. Quantis empíricos ponderados usam a inversa esquerda da CDF ponderada; o erro da CDF em um corte escolhido pela mesma amostra é um diagnóstico local, não um intervalo simultâneo válido para um corte aleatório. Comparações formais entre níveis usam cortes fixados pelo nível independente menor; a análise é condicional a esses cortes. A referência externa emprega seus extremos fixos.

Para logL usa-se a CDF posterior de **log L(θ;y)** na mesma realização y, avaliada em log L(θ_verdade;y). Não se usa logw, logposterior, Jacobiano ou log(L/q). Um algoritmo que devolve a priori pode produzir ranks uniformes dos parâmetros; esse diagnóstico dependente dos dados continua necessário. Ranks obtidos por reamostrar os pontos ponderados não são ranks exatos de amostras independentes da posterior verdadeira. PITs SNIS carregam os erros descritos; testes KS ideais só servem como referência assintótica, e sua sensibilidade à incerteza de integração deve ser propagada na campanha futura.

Se todos os indicadores com peso positivo forem iguais, a fórmula devolve zero por construção. O relatório preserva `raw_delta_mcse=0`, mas marca `constant_indicator_unresolved`, erro operacional infinito e reprovação de precisão. Somente uma prova externa de integral constante pode alterar esse tratamento. Isso inclui valores saturados numericamente. Em u=0, cobertura de [0,U90] é estruturalmente 100%; não se exige 90% nesse ponto nem uniformidade de PITs para injeções fixas.

## Pesos, evidência e caudas

Registram-se ESS de concentração 1/Σp², exp(entropia), pmax, fração dos dez maiores e do 1% superior, amplitude de logw, pesos exatamente zero e underflows. O ESS não certifica precisão de uma função particular. Mantêm-se pesos brutos: não há truncamento, suavização Pareto, eliminação de outliers ou escolha de replicações convenientes.

Como guarda operacional prospectiva, pmax/(1−pmax)≤.00335. Esse limite controla superiormente quanto a remoção de um único ponto pode modificar qualquer CDF observada. É conservador e não limita modos ausentes. A massa normalizada de pontos cujas coordenadas expit saturaram é registrada separadamente pelo produtor; logits e log-Jacobianos originais não são truncados.

Para Ẑ, a MCSE relativa estimada é sqrt[(NΣp²−1)/(N−1)], também a MCSE delta de logZ. Calcula-se o análogo entre replicações usando Ẑ_r/Ẑ_pool. Registram-se nível, erro e concordância. Não se impõe a todos os alvos a antiga meta determinística .001 em logZ da cubatura. Tal meta histórica permanece inalterada, e uma comparação absoluta com evidência externa ficará restrita ao alvo com referência e constantes compatíveis. Z estável em quatro replicações não prova normalização correta se todas omitirem a mesma região.

A discussão de caudas baseia-se também no artigo primário de Vehtari et al., JMLR 25(72), 2024, §§2–3: pesos extremos podem impedir aproximação normal útil mesmo com grande amostra. Este pacote não implementa PSIS nem estima um k de Pareto; suas guardas observadas não devem ser chamadas de diagnóstico PSIS. Fonte: https://www.jmlr.org/papers/v25/19-556.html .

## Replicações, refinamento e multiplicidade

São preservados todos os alvos e todas as falhas. No benchmark de dois níveis, a família de estabilidade entre replicações contém todas as seis comparações pareadas por nível, alvo e CDF fixa (cinco verdades, vinte quantis de referência do nível menor e logL na verdade), mais os contrastes de logZ. Usa-se Bonferroni bilateral, α=.05 para a família completa. Para cortes estimados no nível menor, os contrastes desse mesmo nível são apenas descritivos; a família formal usa verdades/logL e, no nível maior, os vinte cortes independentes. Reportam-se as duas contagens explicitamente. Dois níveis são independentes; o contraste de refinamento usa sqrt(se_low²+se_high²), α=.05 em uma família separada de CDFs nas verdades/logL, cortes externos A0d14 e logZ. Comparar quantis escolhidos no nível menor com sua própria probabilidade nominal é descritivo, sem alegar corte fixo independente.

Essas duas famílias são controles distintos e não constituem uma garantia conjunta de 95%. Uma avaliação conjunta conservadora teria erro nominal no máximo .10 sob todas as hipóteses normais aproximadas; não se declara tal garantia em caudas problemáticas. Um nível adicional exige orçamento/seed e regra congelados antes de novas amostras; nenhum descarte seletivo de falhas.

Para A0_CN, realização14, os vinte brackets independentes têm 40 extremos. Mantém-se z=Φ⁻¹(1−.05/40)=3.02334144 e componente determinístico .002:

    F̂(lo) ≤ p + .002 + z se(lo),
    F̂(hi) ≥ p − .002 − z se(hi).

Exigem-se também largura horizontal≤.001 da priori, controles de refinamento da referência e MCSE≤.00335 nos extremos. O ponto médio não foi avaliado por cubatura; nunca se assume F(mid)=p. Diferenças diretas CDF_MC−CDF_cubatura nos extremos são descritivas e não criam uma segunda família de aprovação. As quatro probabilidades são .05/.5/.9/.95 em cinco parâmetros.

## Verificação independente antes de PTA500

O TOY conjugado tem posterior N(.4,.7²), priori N(0,1), likelihood normal com variância .49/.51 e observação .4/.51. CDF, evidência e CDF de logL têm formas analíticas. Executam-se 128 campanhas independentes com quatro replicações nos níveis1024/8192, com sementes congeladas em `protocol_config.json`. Comparam-se viés, dispersão empírica e RMS das MCSEs de influência, além da redução com N. São 1024 replicações TOY, não realizações de PTA.

O controle negativo usa alvo .95N(0,1)+.05N(12,1), proposta quase toda N(0,1) e defesa larga de probabilidade 10⁻⁶. A probabilidade alvo à esquerda de 6 é conhecida. Mesmo com ESS observado próximo de N e denominadores semelhantes entre replicações, o modo raro pode faltar. O teste deve preservar esse fracasso e a precisão não resolvida; não aumentar a defesa depois de ver resultados para apagar o controle.

As condições de variância da razão e sua expansão delta foram conferidas em Owen, capítulo9, §9.2, eqs.(9.8)–(9.9): https://artowen.su.domains/mc/Ch-var-is.pdf . Esse capítulo proíbe redistribuição eletrônica sem permissão; não foi copiado para o repositório. A derivação e o código aqui são próprios.
