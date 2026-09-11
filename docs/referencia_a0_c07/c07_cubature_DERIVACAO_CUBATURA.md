# Cubatura determinística auxiliar de C07: A0, realização 14

Este pacote é um experimento numérico temporário. Usa a realização de índice
zero-based 14, dados/prioris já congelados de C07, quatro frequências e 12
pulsares. Não constitui uma campanha de SBC, inferência observacional ou
aprovação das 16 realizações. A pergunta é se a integração determinística de um
alvo difícil fornece uma referência útil para as regras RQMC em avaliação.

## Transformação e medida

Sejam `g=log10 Agw`, `r=log10 Ar`, `t=log10 EFAC`, e `γ=gamma_gw`. Os intervalos
originais são `G=[−16,−14]`, `R=[−17,−14.5]`,
`E=[−log10 2,+log10 2]` e `S=[3,5.5]`. A densidade conjunta é a constante
`1/V`, com `V=ΔG ΔR ΔE ΔS`. Fazemos

```
a=g−t, b=r−t;   g=a+t, r=b+t;   |J|=1.
tlo(a,b)=max(E0,G0−a,R0−b)
thi(a,b)=min(E1,G1−a,R1−b).
```

A integração da escala é `I(a,b,γ,u)=∫[tlo,thi] L dt`. A integral restante
é `∫ I da db dγ du / V`. **Não** se divide `I` por `thi−tlo` nesta cubatura.
Esse divisor só pertence à média condicional usada ao amostrar a densidade
marginal das razões pelo Rosenblatt. A priori contínua em `u` continua uniforme
em `[0,1]`.

Invertemos a ordem aninhada sugerida para `b→a`, usando Fubini sobre a mesma
região de volume finito e integrando uma função não negativa. Os painéis são:

```
b: extremos R0−E1,R1−E0; quebras R0−E0,R1−E1.
Para b fixo: tL=max(E0,R0−b), tH=min(E1,R1−b).
a: extremos G0−tH,G1−tL; quebras G0−tL,G1−tH.
```

Ordenar os quatro valores distintos em cada linha também cobre larguras de
`G` ou `R` menores que o intervalo de escala. Isso é necessário nas CDFs, cujos
numeradores usam caixas truncadas. Em geral são três painéis em `b` e três em
`a`; coincidências de quebras removem um painel de largura zero. Os nós GL
ficam estritamente dentro dos painéis e têm pesos positivos. Usam-se limites
da escala exatos, sem diferenças de raízes do Rosenblatt perto de bordas.

Controles independentes em `validate_cubature.py` verificam a normalização,
momentos e `Cov(a,b)=Var(t)`. Duas marginais independentes das razões não
reproduziriam essa covariância. `validate_truncation.py` verifica 41 caixas,
incluindo intervalos mais estreitos que `E`, com controles polinomiais e
`exp(0.13 g−0.27 r+0.7 t+0.21 γ)`. A referência desta última função é o produto
de quatro integrais elementares nas coordenadas originais, sem a transformação.

## Integração exata da escala

Os dados de C07 já usam a normalização fixa por frequência; os mesmos fatores
permanecem em todas as comparações. Para o modelo proper-CN,

```
C_k(t)=10^(2t) C0_k,
M=K Np=48,
χ=Σ_k q_k† C0_k^−1 q_k,
D=Σ_k log det C0_k,
log L=−M log π−D−2M ln(10)t−χ 10^(−2t).
```

Para `χ>0`,

```
I_t = exp(−D) π^(−M) χ^(−M)/(2 ln 10)
      × ∫[χ 10^(−2thi), χ 10^(−2tlo)] v^(M−1) exp(−v) dv.
```

A função `cn_log_scale_integral(...,conditional_average=False)` vem do pacote
independente `tmp/c07_scale/`, onde foi confrontada com quadratura direta na
escala original. O caso `χ=0`, caudas que sofrem underflow nas funções gama e
intervalos estreitos têm tratamentos explícitos nesse módulo. Os termos de
normalização completos da densidade CN são mantidos. Evidências de dados CN e
de observáveis quadráticos com medidas diferentes não são comparadas entre si.

## Reuso espectral da covariância

Para `b` fixo, a parcela diagonal estritamente positiva é

```
N_k(b)=diag[Pr_k(b) red_p² + Pw_k(EFAC=1) σ_p²],
C0_k=N_k+Pgw_k(a,γ) Γ_k.
N_k^(−1/2) Γ_k N_k^(−1/2)=U_k diag(λ_ki) U_k†,
z_k=U_k† N_k^(−1/2) q_k.
```

Logo,

```
χ = Σ_ki |z_ki|² / [1+Pgw_k(a,γ) λ_ki],
D = Σ_kp log N_kpp + Σ_ki log[1+Pgw_k(a,γ) λ_ki].
```

Cada decomposição é reutilizada por todos os nós `a,γ` daquele `b`. Isso troca
uma fatoração complexa 12×12 por nó por somas escalares. Nenhum autovalor é
recortado: os denominadores devem permanecer positivos; seus mínimos e os
autovalores mínimos são registrados. Autovalores negativos da ordem do erro
de arredondamento podem aparecer no setor de posto reduzido e continuam no
cálculo. O teste com Cholesky cobre `u=0,0.5,sqrt(1−0.001²),1`, bordas e
interiores das razões e extremos/interior de `γ` (972 casos).

As unidades/fatores espectrais são exatamente os de `covariance_batch` no
piloto: espectros de resíduos em s³ antes da normalização fixa, frequências
em Hz, ano juliano, amplitudes sem dimensão e EFAC sem dimensão. Não se
reintroduz uma normalização dependente dos parâmetros.

## Duas formas de avaliar CDFs

1. **CDF condicional da escala:** para um corte `z`, integramos a escala até
   `min(thi,z)` para `t`, `min(thi,z−a)` para `g`, ou `min(thi,z−b)` para `r`.
   Os cortes em `γ` dividem explicitamente os painéis de `γ`; não se integra
   seu indicador descontínuo com uma única regra GL. Esta rota reutiliza `χ,D`,
   mas introduz novas quebras nas razões. Por isso sua evidência pode convergir
   antes das CDFs. O código registra uma omissão opcional de contribuições
   minúsculas **somente nas CDFs**: toda contribuição entra na evidência e a
   soma efetivamente omitida fornece um limite absoluto posterior do erro da
   CDF da regra finita. A regra declarada usa diferença de 40 no logaritmo em
   relação ao maior peso já visto; não serve como justificativa de convergência.
2. **Numeradores por caixas originais truncadas:** truncar, por exemplo,
   `G1→z` calcula a mesma integral `g≤z`, agora com os painéis alinhados a todas
   as trocas dos limites da escala. O código integra a caixa pequena com sua
   densidade uniforme normalizada e multiplica por `V_pequena/V_original`.
   Isso é apenas uma forma de computar o numerador com a densidade original,
   não uma troca de priori. Não há omissão de contribuições nessa rota.

Os 20 cortes são congelados antes destas execuções: para cada nuisance, os
quatro quantis estimados pelo nível independente anterior de RQMC e a verdade
injetada para diagnóstico PIT. As verdades não escolhem a proposta, a malha de
quadratura ou a realização. A realização 14 foi selecionada pelos problemas
de convergência previamente registrados. Comparar CDFs em 20 cortes não
certifica um erro uniforme em todo o suporte nem o erro dos quantis.

## Massa, recursos e escopo da referência

A malha é a união de 129 nós uniformes em `u` com a camada
`u=sqrt(1−β²)`, `β=[0,.0002,.0005,.001,.002,.005,.01,.02,.05,.1,.15]`: 139
nós distintos. Lê-se a ORF exata já calculada em cada nó, do cache congelado
do piloto, com hash e assinatura. A função de acesso se recusa a calcular um
nó ausente; não escreve no cache de outro agente. A assinatura e as verificações
originais de duas resoluções não são promovidas a um certificado universal de
quadratura angular. Nenhuma interpolação de ORF é usada.

A integral em massa usa trapézios da marginal positiva e quantis/CDFs da
densidade linear por trechos. Isso aproxima uma priori/marginal contínua;
não introduz massas discretas a priori. A comparação 75→139 pode ser feita
usando um subconjunto dos mesmos valores para cada nova marginal. O resultado
anterior de RQMC não é transferido automaticamente para este alvo.

O preflight conta nós antes de executar. A rota inicial limita 150 milhões
por ordem; as duas execuções completas com numeradores truncados têm teto de
500 milhões cada. Estimativas foram medidas em `u=0.5`: regras 12³/20³/32³,
20 numeradores mais denominador, custaram aproximadamente 0,64/2,08/7,00 s.
A regra anisotrópica `(nb,na,nγ)=(32,20,12)` custou 2,32 s e foi comparada
com 32³ nesse mesmo dado e massa antes de executar os 139 nós. Tempos são de
parede, em máquina com outros processos; são medidas de carga, não benchmarks
universais. O processo guarda somente lotes de um `b`, não toda a grade de
covariâncias. A memória dos arranjos densos de trabalho cresce como
`O(3 na nγ K Np)`, mais os caches de 139 matrizes 4×12×12 (~1,3MB complexos).
`resource_estimate.json` registra uma estimativa conservadora dos arranjos
numéricos, calculada pela geometria dos lotes. Não mede RSS nem inclui a memória
do interpretador e bibliotecas. O limite obrigatório dos scripts é o número de
pontos; a estimativa de memória é um diagnóstico separado.

Os critérios permanecem: `|ΔlogZ|≤.001`, `|ΔPIT|≤.002` e diferenças de
quantis≤`.001` da largura da priori. Um resultado que só testa evidência,
CDFs em cortes finitos e quantis de massa deve dizer expressamente que os
quantis completos dos nuisances não foram certificados. Não se roda a
campanha de 500 com base neste pacote.

## Reprodução

Usar o Python do ambiente do workspace e o harness que fixa os módulos de
C06/C07 usados no piloto:

```sh
.venv/bin/python tmp/c07_cubature/run_staged.py tmp/c07_cubature/validate_cubature.py
.venv/bin/python tmp/c07_cubature/run_staged.py tmp/c07_cubature/validate_truncation.py
.venv/bin/python tmp/c07_cubature/run_staged.py tmp/c07_cubature/cubature.py --orders 12 20 32
.venv/bin/python tmp/c07_cubature/run_staged.py tmp/c07_cubature/truncated_cdf.py --orders 20 --maximum-points 500000000
.venv/bin/python tmp/c07_cubature/run_staged.py tmp/c07_cubature/anisotropic_experiment.py --orders 32 20 12
```

Os scripts preservam arquivos de resultado existentes em vez de sobrescrever
evidência de uma execução. Remover resultados para uma repetição é uma decisão
explícita; os hashes das fontes da execução original permanecem nos JSONs.
