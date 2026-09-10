# Contrato estatístico de C06 e das comparações posteriores

O produto executado em C06 é um simulador e uma verificação de momentos. A tabela abaixo define análises futuras; sua presença não indica que posteriors, SBC ou cobertura já foram calculados.

| Análise | Dados recebidos | Família probabilística | Modelo da resposta |
|---|---|---|---|
| A0 | Todos os coeficientes complexos `q_n` | CN própria exata no experimento periódico declarado | `Γ(f_n; f_g,L)` completa |
| A | Estatísticas quadráticas reais por frequência, incluindo Re/Im de pares e autos | Normal multivariada com momentos exatos; aproximação da distribuição física | Mesma resposta completa de A0 |
| B | `W A`, com W fixado antes dos sorteios | Normal com `W μ_A` e `W Σ_A Wᵀ` | Mesma resposta completa |
| C_full | Exatamente o mesmo vetor observado de B | Normal com média **e** covariância recalculadas | `Γ(f_ref; f_g,L)` em todos os canais: congela β e as fases |
| C_beta | Exatamente o mesmo vetor observado de B | Normal com média **e** covariância recalculadas | β=`β(f_ref)` fixo, fases `2π f_n L/c` preservadas |
| Controle G | Vetor normal gerado diretamente com os momentos de A; e sua compressão fixa | Normal exata por construção | Mesmas previsões das análises A/B/C correspondentes |

## Experimento probabilístico e unidades

Para frequências positivas `f_n=n/T`, gera-se independentemente `q_n~CN(0,C_n)`, com

`C_n = P_gw(f_n) Γ_n + diag[r_a² P_red(f_n) + 2 (EFAC σ_a)² Δt]`.

A matriz C é o espectro unilateral de resíduos `[s³]`; a pseudocovariância é `E[q_n q_mᵀ]=0`. O coeficiente de série de Fourier é `a_n=q_n/√(2T)` e

`r(t)=√(2/T) Re Σ_n q_n exp(+i 2π f_n t)`.

Logo `[q]=s^(3/2)` e `[r]=s`. O espectro de lei de potência é

`P(f;A,γ)=A²/(12π² f_piv³) (f/f_piv)^(-γ)`;

`f_piv=1/ano juliano` fixa a amplitude e difere de `f_ref=1/T`, utilizado na aproximação da resposta. Para ruído branco regularmente amostrado, o PSD unilateral é `2 σ² Δt`; o teste de reconstrução cobre os modos positivos de uma grade ímpar completa. Os exemplos de três canais guardam apenas essa banda; não constituem ruído branco independente no tempo em toda a grade.

A geração CN usa fator de Cholesky, com partes real e imaginária independentes de variância 1/2 antes da transformação. O módulo não recorta autovalores para corrigir uma matriz inválida. O controle G utiliza coordenadas normais dos mesmos sorteios latentes e tem exatamente a média e covariância de A; trata-se de outro experimento, e a associação dos sorteios não garante redução de variância Monte Carlo.

Os espectros são divididos por escalas positivas fixadas no arquivo de configuração antes da injeção. O vetor salvo é `q_normalized=q/√(fixed_scale)`. As estatísticas construídas desse vetor são adimensionais. As escalas e os parâmetros usados para defini-las são registrados, diferem da verdade injetada e permanecem constantes em toda avaliação de parâmetros.

## Estatísticas e covariância

Os pares são orientados por `a<b`, e cada bin utiliza pesos uniformes fixados pela geometria. Os grupos de autos são definidos pelas incertezas TOA nominais, sem EFAC ajustado ou potências observadas. Escrevendo `y_i=q†H_i q`, os H são hermitianos: para Re de um par, `H_ab=H_ba=1/2`; para Im de `q_a q_b*`, `H_ab=+i/2`, `H_ba=-i/2`. O fator de binagem multiplica esses elementos.

Para uma CN própria,

`μ_i=tr(H_i C)`, `Σ_ij=tr(H_i C H_j C)`.

Não há fator dois nessa fórmula complexa. Um teste independente constrói a covariância dos pares por Isserlis: para `X_ab=q_a q_b*`,

`K_ab,cd=Cov(X_ab,X_cd*)=C_ac C_db`,

`J_ab,cd=Cov(X_ab,X_cd)=C_ad C_cb`.

As covariâncias Re/Re, Im/Im, Re/Im, Im/Re são, respectivamente, `Re(K+J)/2`, `Re(K-J)/2`, `Im(J-K)/2`, `Im(J+K)/2`. Partes imaginárias de pares não são descartadas; a auto imaginária, identicamente nula, não é adicionada à likelihood.

Com canais independentes e pesos `w_n`, `μ_B=Σ_n w_n μ_n` e `Σ_B=Σ_n w_n² Σ_n`. Para janelas que acoplam canais, o módulo fornece a operação geral `W Σ Wᵀ`; a fórmula em blocos independentes deixa de ser aplicável.

A cumulante de ordem r de um projetor escalar é `(r−1)! tr[(HC)^r]`. Em particular, o campo gaussiano não torna suas potências e produtos quadráticos gaussianos. A curtose excessiva de uma projeção não degenerada é `6 Σ λ_j⁴/(Σ λ_j²)²`, estritamente positiva. Para um único canal, é ao menos `6/N_p`. A/B físicas precisam de calibração própria. O controle normal G permite separar efeitos da compressão na família normal da inadequação dessa família às estatísticas físicas.

## Domínio, convenções e dependência dos parâmetros

Usam-se direções Terra→pulsar, `β=√(1−(f_g/f)²)`, `y=2π fL/c` e a ORF C05 com termos Terra/pulsar completos. `Γ_ab=Γ_ba*` e `Γ(-f)=Γ(f)*`. A geração por covariância absorve o sinal global comum da resposta de redshift; o sinal relativo dos espectros cruzados complexos e a convenção de Fourier permanecem explícitos.

O recorte previsto inicialmente é `u=f_g T∈[0,1]`, preservando todos os canais viajantes. Não se removem observações ao variar u. Não há aqui um modelo para um componente evanescente. Distâncias e frequências são fixas; médias que destruam coerência precisam ser definidas e validadas em outra etapa.

C_full pode diferir de B mesmo em u=0, porque congela a fase dos pulsars. C_beta coincide exatamente com B em u=0. Não se deve interpretar C_full exclusivamente como erro de aproximar a dispersão. O espectro, o ruído e a normalização fixa continuam dependentes dos seus parâmetros usuais em todas essas análises; congela-se somente o componente declarado da resposta.

Os cinco parâmetros previstos são `(u,log10 A_gw,γ_gw,log10 A_red,log10 EFAC)`. A inclinação vermelha e um padrão relativo de amplitude podem ser fixados e registrados em um primeiro recorte. Massa, amplitude e inclinações não são identificáveis por decreto: as campanhas devem testar degenerações, sensibilidade à priori e dependência efetiva dos posteriors dos dados. A priori uniforme em u, uniforme em u² e log-uniforme com corte positivo são medidas distintas. Um limite de massa próximo ao quantil da priori não constitui sensibilidade demonstrada.

## Janela e campanhas futuras

O experimento atual define uma série periódica com modos positivos independentes, sem ajuste de temporização, irregularidade amostral ou janela que misture frequências. Essas hipóteses são uma definição geradora explícita, não uma afirmação de que coeficientes observados de PTA real sejam independentes. Se uma transformação produzir pseudocovariância P≠0, a covariância real de `(Re q,Im q)` será

`(1/2) [[Re(C+P), Im(P−C)], [Im(P+C), Re(C−P)]]`.

O pacote oferece essa conversão, mas não implementa janelas, ajustes ou uma likelihood CN imprópria. As fórmulas quadráticas próprias não podem ser transferidas sem correção a esse caso.

SBC exige parâmetros sorteados da priori; cobertura condicional exige injeções fixas e novos dados. São verificações diferentes. A comparação A–B só pode receber interpretação sobre informação depois que a família probabilística for calibrada ou que sua falha seja explicitamente quantificada. C06 não executou nenhuma dessas campanhas, nem realizou um teste de 500 posteriors. As realizações independentes usadas para erros Monte Carlo de momentos não simulam segmentos independentes de uma mesma PTA.
