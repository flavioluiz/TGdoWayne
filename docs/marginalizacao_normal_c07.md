# Integral condicional da escala para A/B/G

Estado: **redução algébrica e referência numérica validadas; produção posterior e SBC não executados por este pacote**. As verificações foram reexecutadas com os módulos integrados em `src/inference/` e os módulos C05/C06 publicados de `src/pta/`.

## Coordenadas e medida da priori

Usamos exatamente a transformação de `src/inference/scale_cn.py`:

\[
t=\log_{10}s,\quad a=\log_{10}A_{\rm gw}-t,\quad
b_r=\log_{10}A_{\rm red}-t.
\]

A Jacobiana nas coordenadas logarítmicas é1. Os limites de t são a interseção dos três intervalos originais de amplitude/EFAC. O mapa de Rosenblatt `LogAmplitudeBox.sample_ratio_prior` devolve `(a,b_r,gamma,t_lo,t_hi)` e já amostra a densidade marginal induzida das razões. Portanto o integrando posterior é a **média condicional** `∫ L(t) dt/(t_hi−t_lo)`. Não se substitui essa priori por uma caixa independente em `(a,b_r)` e não se conta duas vezes o comprimento condicional.

## Coeficientes suficientes

Com todas as parcelas residuais escaladas conjuntamente, `C(t)=s² C0`. As estatísticas quadráticas normais usadas por A/B/G satisfazem

\[
\mu(t)=s^2\mu_0,\qquad\Sigma(t)=s^4\Sigma_0.
\]

Para cada dado y, somando os blocos independentes quando necessário, definimos

\[
\chi=y^T\Sigma_0^{-1}y,\quad
\ell=\mu_0^T\Sigma_0^{-1}y,\quad
c=\mu_0^T\Sigma_0^{-1}\mu_0,\quad
D=\sum_k\log\det\Sigma_{0,k}.
\]

`d` conta as coordenadas **reais**, valendo40 para A (quatro frequências, dez estatísticas) e10 para B. A dimensão complexa48 de A0 não deve ser usada aqui. O coeficiente linear `ell` pode ser negativo. A consistência exige `chi≥0`, `c≥0` e `ell²≤chi*c`; se `chi=0`, então `ell=0`.

A log-verossimilhança normalizada é

\[
\log L(t)=-2d\ln(10)t
-\tfrac12\{\chi10^{-4t}-2\ell10^{-2t}+c+D+d\log(2\pi)\}.
\]

`GaussianScaleKernel.coefficients` usa as médias lineares e covariâncias quadráticas já pré-computadas em componentes espectrais por massa. Ele precisa apenas das Choleskys das pequenas matrizes A/B para obter os coeficientes acima. Não recalcula Cholesky em cada nó de escala. O operador de compressão e todos os log-determinantes são preservados.

## Integral unidimensional e limites de erro

Escrevendo `z=10^(−2t)`, temos `dt=−dz/(2 ln10 z)` e

\[
I_t=\frac{\exp[-(D+c+d\log(2\pi))/2]}{2\ln10}
\int_{z_{\rm lo}}^{z_{\rm hi}}
 z^{d-1}\exp[-\chi z^2/2+\ell z]\,dz,
\]

onde `z_lo=10^(−2 t_hi)` e `z_hi=10^(−2 t_lo)`. O expoente da potência é `d−1` na **integral**; a log-verossimilhança considerada como função de z contém `d log z`. Seus modos diferem por essa unidade. O código usa a potência correta em cada situação.

O log-integrando de I_t é côncavo em z positivo:

\[
f''(z)=-(d-1)/z^2-\chi\le0.
\]

O modo positivo de `p log z−chi z²/2+ell z`, com `p=d−1`, é obtido pela raiz da quadrática e limitado ao intervalo. Para coeficiente linear negativo é usada a forma racionalizada `2p/(sqrt(ell²+4p chi)−ell)`. Para `chi=ell=0`, a integral original em t é calculada pelo limite exponencial analítico, incluindo a média condicional.

A implementação usa `z=z_lo(1+x)` e `x_max=expm1(2 ln10 Δt)` para preservar intervalos estreitos. Diferenças de log-integrando em relação ao modo são calculadas com `log1p` e produtos fatorizados; não se subtraem exponenciais já subfluxadas. Caudas além de uma queda de40 unidades de logdensidade são separadas. A concavidade fornece limites superiores explícitos por tangentes exponenciais, calculados até os extremos originais. O restante é integrado por duas ordens de Gauss–Legendre,32 e64 nos testes, e a soma de refinamento relativo e limite relativo das caudas deve ficar abaixo10⁻⁸. Não há refinamento silencioso; ordens insuficientes e orçamento excedido geram erro claro.

Essa tolerância se refere à quadratura e às caudas. A aritmética final de ponto flutuante é reportada separadamente por uma estimativa conservadora de magnitude, que não é uma prova de erro total. Em caudas com logdensidade perto de−5×10⁸, o erro absoluto final testado contra70 dígitos chegou a2,98×10⁻⁷, compatível com poucas unidades da representação double. Essas caudas não devem ser descritas como tendo precisão relativa global10⁻⁸. O chamador deve propagar o diagnóstico ao erro da integral posterior.

## CDFs condicionais e diagnóstico dependente dos dados

`gaussian_conditional_scale_cdf` calcula a razão de integrais entre `t_lo` e o limiar, com0/1 fora do suporte. As CDFs dos parâmetros originais usam os limiares `z`, `z−a` e `z−b_r` para EFAC, amplitude GW e amplitude vermelha, respectivamente, e são promediadas com pesos da likelihood marginalizada. Isso permite reduzir a variância dos indicadores de escala, sem gerar uma posterior discreta.

`gaussian_conditional_loglike_cdf` calcula `P(log L(t)≤limiar)` usando que o conjunto acima do limiar é um intervalo. Seus extremos são encontrados continuamente; as duas caudas usam a CDF condicional da escala. Esse cálculo usa a log-verossimilhança normalizada do **mesmo dado**, incluindo constantes e determinante. A opção `under_prior=True` usa a distribuição uniforme condicional de t e fornece a componente do controle que ignora os dados. Ela não usa `log(L/q)` de importance como estatística de calibração.

As CDFs das razões/índice e da massa, e a normalização externa em três dimensões, ainda requerem validação. Integrar exatamente a escala não certifica automaticamente a posterior inteira. Caixas originais truncadas por um limiar são uma alternativa para tratar as mudanças de painéis das CDFs; a normalização deve continuar sendo a da priori completa.

## Evidência de validação

Os scripts e JSONs são reprodutíveis; números abaixo não são resultados de SBC.

| Verificação | Resultado |
|---|---|
| 162 casos contra quadratura adaptativa na coordenada original t | Erro máximo de log-integral2,91×10⁻¹¹ quando a referência fica acima de−10⁵; extremos avaliados separadamente |
| Limites analíticos: dado zero e d=2, inclusive chi=10⁹ | PASS, sem underflow da integral antes de tomar log |
| 12 caudas contra integração direta com70 dígitos | Erro absoluto máximo2,98×10⁻⁷ em logdensidades próximas de−5×10⁸ |
| Densidades multivariadas normais do SciPy e22 CDFs de escala | Erro máximo de integral3,56×10⁻¹⁵ e CDF6,33×10⁻¹⁵ |
| Reconstrução A/B/G da likelihood física existente,16 razões ×3 massas ×3 escalas ×64 dados/modelos | Diferença absoluta máxima4,66×10⁻⁹ nas caudas; tolerância relativa2×10⁻¹¹ preservada |
| 9 conjuntos de integrais físicas, comparados ao kernel original com quadratura direta em t96→192→384→768 | Erro máximo3,20×10⁻¹⁰; refinamento final da referência5,61×10⁻¹⁰ |
| CDF de logL sob posterior/priori condicional | Confronto com bracketing escalar e integração direta; resultados em `results/C07/validation/validation_kernel.json` |
| Entradas inconsistentes, regra insuficiente e preflight de orçamento | Sete rejeições esperadas passaram |

A referência direta com96 nós em t falhou em algumas caudas: um erro de0,0016 foi encontrado e o refinamento192 ainda não bastou em outro caso. Isso foi corrigido refinando a referência até768, preservando a exigência de convergência. O valor da nova integral não foi ajustado para concordar com a referência insuficiente. A quadratura adaptativa double também emitiu aviso de arredondamento nas caudas extremas; o confronto com70 dígitos está preservado para resolver essa limitação.

## Custo e reprodução integrada

Na reprodução integrada, oito pontos de razões e as 16 realizações salvas custaram 0,0145 s para coeficientes e integrais normais A/B. O mesmo cálculo com 500 colunas obtidas por repetição desses dados custou 0,201 s. São medidas curtas sob carga concorrente, sem ganho universal inferido e **sem 500 novas realizações**. O custo adicional por dado impede presumir que marginalizar a escala acelere toda a campanha.

O orçamento conjunto A+B é verificado antes dos coeficientes. Lotes limitam os arranjos de nós. Os JSONs preservam estimativas de refinamento, caudas, arredondamento e custos. Quatorze dos 162 casos da referência adaptativa emitiram avisos de arredondamento, agora registrados individualmente em `reference_warnings`. A comparação independente com 70 dígitos permite avaliar as caudas extremas; os avisos não são convertidos em evidência de precisão inexistente.

```sh
.venv/bin/python scripts/inference_checks/scale_gaussian_guards.py
.venv/bin/python scripts/inference_checks/scale_gaussian_integral.py
.venv/bin/python scripts/inference_checks/scale_gaussian_high_precision.py
.venv/bin/python scripts/inference_checks/scale_gaussian_kernel.py
```

As saídas ficam em `results/C07/validation/`. Nenhum comando inicia produção posterior ou SBC. As funções fundamentais estão em `src/inference/scale_gaussian.py`; o adaptador físico está em `src/inference/scale_kernel.py`.
