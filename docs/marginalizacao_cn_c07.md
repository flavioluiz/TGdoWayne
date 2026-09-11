# Marginalização exata de uma escala comum no A0

O módulo `src/inference/scale_cn.py` reduz de quatro para três as coordenadas nuisance que precisam de quadratura em A0. A massa permanece contínua, e nenhuma ORF, priori ou constante da likelihood é substituída. Esta é uma redução algébrica do experimento C06/C07, seguida de validação numérica; não é uma campanha posterior concluída.

## Coordenadas, Jacobiano e suporte conjunto

Escreva `g=log10 A_gw`, `r=log10 A_red` e `t=log10 EFAC`. As três variáveis possuem prioris independentes uniformes nos intervalos originais G, R e E, de comprimentos `ΔG,ΔR,ΔE`. Defina

`a=g−t`, `b=r−t`, `s=10^t`.

A transformação inversa é `(g,r,e)=(a+t,b+t,t)`, com matriz Jacobiana triangular e determinante absoluto um. A inclinação γ não muda. Para valores fixos de a e b, o intervalo da escala é

`t_lo=max(E_lo,G_lo−a,R_lo−b)`,

`t_hi=min(E_hi,G_hi−a,R_hi−b)`.

Um ponto de razões só pertence ao suporte quando `t_hi>t_lo`. A densidade conjunta marginal correta é

`p(a,b)=(t_hi−t_lo)/(ΔG ΔR ΔE)`.

Ela não é uniforme em um retângulo, e a e b não são independentes: ambos contêm a mesma variável t. Em particular,

`Cov(a,b)=Var(t)=ΔE²/12`.

Para a priori congelada em C07, G=[−16,−14], R=[−17,−14,5] e E=[−log10 2,+log10 2]. O suporte projetado fica contido em `a∈[G_lo−E_hi,G_hi−E_lo]` e `b∈[R_lo−E_hi,R_hi−E_lo]`, mas a densidade deve continuar proporcional ao comprimento da interseção.

## Rosenblatt exata, sem rejeição

A primeira marginal é a diferença de duas uniformes: `a=g−t`. Sua densidade é

`p(a)=ℓ_a/(ΔG ΔE)`,

onde `ℓ_a=U_a−L_a`, `L_a=max(E_lo,G_lo−a)` e `U_a=min(E_hi,G_hi−a)`. Condicionalmente a a, t é uniforme em `[L_a,U_a]`, e r conserva sua uniforme original independente. Portanto,

`p(b|a)=(t_hi−t_lo)/(ΔR ℓ_a)`.

O produto das duas densidades recupera exatamente `p(a,b)`. O algoritmo usa uma inversa trapezoidal para a e **outra inversa condicional**, com posição e largura dependentes de a, para b. Usar duas marginais trapezoidais independentes seria incorreto.

A inversa necessária é a soma de `U(0,w1)+U(0,w2)`. Com `m=min(w1,w2)`, `M=max(w1,w2)` e `p0=m/(2M)`, sua função quantil é

- `sqrt(2mM p)`, para `p<p0`;
- `M p+m/2`, para `p0≤p≤1−p0`;
- `m+M−sqrt(2mM(1−p))`, para `p>1−p0`.

Para a, somam-se os intervalos de larguras ΔG e ΔE com origem `G_lo−E_hi`. Para b condicionado a a, as larguras são ΔR e ℓ_a e a origem é `R_lo−U_a`. Uma terceira uniforme gera γ em seu intervalo original. A API `.sample_ratio_prior(unit[N,3])` retorna colunas `(a,b,γ,t_lo,t_hi)`.

Como essa transformação já amostra a densidade marginal induzida, o integrando da quadratura reduzida é a **média condicional**

`L_bar(a,b,γ,u)= [1/(t_hi−t_lo)] ∫_(t_lo)^(t_hi) L(a+t,b+t,t,γ,u) dt`.

Usar apenas a integral sem dividir pelo comprimento contaria duas vezes o fator de volume. Uma alternativa equivalente, não usada pelo sampler, seria integrar sobre um retângulo de razões com integrando `∫L dt/(ΔG ΔR ΔE)` e densidade de proposta explícita, atribuindo contribuição nula fora do suporte.

## Integral fechada da CN própria

A geração atual satisfaz

`C_n(t)=s² C0_n=10^(2t) C0_n`.

`C0` usa `log10 A_gw=a`, `log10 A_red=b`, `EFAC=1`, a mesma inclinação γ e a mesma ORF dispersiva. Essa identidade exige que todas as parcelas de covariância sejam escaladas conjuntamente. Uma componente aditiva que não receba s² exige outra parametrização ou outra integral.

Se há K canais e Np pulsares, `M=K Np` conta as coordenadas complexas próprias. Defina

`χ=Σ_n q_n† C0_n^(-1) q_n`, `D=Σ_n log det C0_n`.

A likelihood completa é

`L(t)=π^(−M) exp(−D) 10^(−2Mt) exp[−χ10^(−2t)]`.

Para χ>0, faça `v=χ10^(−2t)`. Então `dt=−dv/(2 ln10 v)`, e

`I_t = π^(−M) exp(−D) χ^(−M)/(2 ln10) × ∫_(χ10^(−2t_hi))^(χ10^(−2t_lo)) v^(M−1) exp(−v) dv`.

A última integral é a diferença de gamas incompletas de ordem M. A função `cn_log_scale_integral(chi,logdet_c0,M,low,high,conditional_average=True)` conserva todas as constantes, incluindo `π^(−M)`, o determinante, `1/(2 ln10)` e, por padrão, o comprimento do intervalo condicional.

Para χ=0, o limite é elementar:

`I_t=π^(−M) exp(−D) [10^(−2M t_lo)−10^(−2M t_hi)]/(2M ln10)`.

Trocar para `τ=ln s` é equivalente, mas deve-se usar `dt=dτ/ln10`. Para a média condicional, tanto a integral quanto o comprimento do intervalo precisam estar na mesma coordenada. Esquecer esse fator muda a evidência absoluta.

## Avaliação estável e limites numéricos

O código utiliza diferenças de funções gama regularizadas quando bem condicionadas. Nas caudas, usa uma série positiva para a gama inferior ou o polinômio finito da gama superior de ordem inteira, evitando que probabilidades pequenas virem zero por underflow antes do logaritmo.

Foi encontrada e corrigida uma dificuldade adicional: χ extremamente pequeno, junto com um intervalo de escala estreito, provocava cancelamento entre logaritmos de probabilidades muito pequenos. Para `v_max≤0,1`, o módulo integra a série de `exp(−v)` contra a potência analítica. O resto é limitado uniformemente por `v_max^(j+1)/(j+1)!`; a soma só é aceita após o limite ficar abaixo da tolerância interna. Essa é uma avaliação numérica da mesma integral, sem alteração física de χ ou de seu suporte.

As verificações cobrem M=1,12,48, χ=0 e valores entre 10⁻²⁴⁰ e 10⁴, intervalos amplos e estreitos até 10⁻⁷ em t. Isso não certifica quaisquer dimensões, limites de escala ou valores que ultrapassem a faixa representável em ponto flutuante. Os dados próprios do C07 continuam no domínio explicitamente usado.

## CDFs condicionais e recuperação dos parâmetros originais

Depois de marginalizar t, ainda é possível recuperar suas distribuições posteriores. A CDF condicional é

`F_t(z|a,b,γ,u,q)=I(t_lo,min(z,t_hi))/I(t_lo,t_hi)`,

com zero abaixo de t_lo e um acima de t_hi. O módulo oferece `cn_conditional_scale_cdf(threshold,chi,M,low,high)`. No interior, essa é uma razão de integrais de gama truncada; as constantes de normalização cancelam somente depois de estarem consistentemente definidas.

Em uma quadratura posterior com pesos `W_j ∝ peso_prior_j × L_bar_j`, as CDFs dos parâmetros originais são recuperadas por

- `F_e(z)=Σ_j W_j F_t(z|j)/Σ_j W_j`;
- `F_g(z)=Σ_j W_j F_t(z−a_j|j)/Σ_j W_j`;
- `F_r(z)=Σ_j W_j F_t(z−b_j|j)/Σ_j W_j`.

Assim, os quantis de amplitude e EFAC não precisam usar indicadores duros dos valores de escala sorteados. A inclinação γ permanece uma marginal das três coordenadas numéricas e exige seu próprio controle de quadratura. Não basta mostrar que o quantil de massa ficou estável.

## Validação independente executada

O script `scripts/inference_checks/scale_cn.py` passou em:

1. **90 integrais** contra quadratura adaptativa direta na coordenada original t, com máximo erro absoluto de **8,18×10⁻¹⁰ no logaritmo da integral**. O integrando de referência é a expressão exponencial original, sem chamar funções gama.
2. **42 CDFs condicionais**, incluindo extremos, com máximo erro absoluto de **1,42×10⁻¹⁴**.
3. **Priori conjunta**, com oito scrambles de 131072 pontos: médias, covariâncias, reconstrução de um evento retangular nos parâmetros originais e três probabilidades conjuntas de (a,b) comparadas a uma integral independente sobre a escala original. O máximo foi **2,22 erros-padrão**. A covariância cruzada observada foi 0,03020622, contra 0,03020635 esperada; marginais independentes incorretas dariam zero.
4. **Likelihood física congelada C07**, em u=0,5, 16 pontos de razões e os dados 0, 9, 14: covariâncias concordaram com `C=s²C0` até 4,50×10⁻¹⁵ relativamente; as log-likelihoods completas concordaram até 4,10×10⁻¹². Doze integrais físicas adicionais concordaram com a quadratura direta até 5,69×10⁻¹⁴.

O relatório detalhado, sementes, hash do módulo e custo estão em `results/C07/validation/scale_cn.json`. Esses controles validam a redução; não aprovam a malha em massa, uma evidência final ou uma campanha de SBC.

## Integração com C07

Para um lote de N coordenadas reduzidas e R dados, calcular C0 uma vez por ponto, obter `χ[N,R]` e `D[N]`, e chamar a função com `D[:,None]`, `t_lo[:,None]`, `t_hi[:,None]`. Isso conserva o reuso de Cholesky entre os dados. A priori original é uniforme no cubo de entrada da Rosenblatt; uma proposta adaptada nesse cubo deve conservar a correção `1/q_cube`.

A redução pode ser combinada com a proposta defensiva já investigada, agora em três dimensões, mas qualquer ganho precisa ser medido com scrambles e níveis independentes. A marginalização de escala é uma forma de pré-integração, discutida metodologicamente por [Owen (2026), seção 5.8](https://arxiv.org/html/2608.17143v1). Não se assume que ela forneça automaticamente uma taxa de erro ou uma aceitação para esta PTA.

A extensão normal A/B/G está implementada separadamente em `src/inference/scale_gaussian.py` e `scale_kernel.py`, com os mesmos intervalos e a mesma priori conjunta. Sua derivação e validação estão em [marginalização normal](marginalizacao_normal_c07.md). A validação da escala não aprova automaticamente os posteriors completos.


Reprodução integrada:

```sh
.venv/bin/python scripts/inference_checks/scale_cn.py
```
