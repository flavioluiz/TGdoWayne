# Resultado do experimento de cubatura C07

Obtivemos uma referência determinística parcial para **A0, realização 14**:
evidência, quantis de massa e CDFs nuisance nos 20 cortes congelados passam
pelas comparações realizadas. A integração por painéis que inclui os cortes
das CDFs resolveu o problema que persistia ao usar somente os painéis dos
limites da priori. Nenhuma aprovação dos quantis completos nuisance, das 16
realizações, dos modelos A/B/G ou da campanha de 500 é inferida deste resultado.

## Resultado quantitativo

Todos os cálculos abaixo usam a mesma realização física CN, priori contínua
original e ORFs exatas nos 139 nós congelados de massa. Os quantis correspondem
às probabilidades `[.05,.5,.9,.95]`.

| Comparação de nuisance | `|Δlog Z|` | Maior `|ΔCDF|` nos 20 cortes | Estado dos itens testados |
|---|---:|---:|---|
| CDF condicional, 12→20 | 3,69×10⁻⁶ | 2,84×10⁻² | Falha nas CDFs |
| CDF condicional, 20→32 | 2,50×10⁻⁹ | 4,65×10⁻³ | Falha nas CDFs |
| Caixas truncadas, 20³→32×20×12 | 1,61×10⁻⁹ | 1,18×10⁻⁴ | Passa evidência e cortes de CDF |

As CDFs condicionais da primeira rota são matematicamente corretas, mas cada
corte introduz novas quebras nas razões de amplitude. O segundo cálculo muda
a partição da integral para alinhar essas quebras, preservando a medida da
priori e a normalização. Na massa fixa `u=.5`, aumentar a primeira rota para
64³ reduz sua diferença para a segunda rota 32³ a aproximadamente 3,11×10⁻⁴.

A referência fina tem

```
log Z                 = -76.08009859732175
log BF(livre/fixo u=0) ≈  0.13199552
quantis de u          ≈ [0.056934997, 0.538761018, 0.913334114, 0.956976003].
```

Os dígitos guardados permitem comparação numérica; não são uma declaração
de erro absoluto na evidência. O teste de resolução da massa domina a
comparação de ordens nuisance:

| Neste alvo, malha 75→139 | Diferença |
|---|---:|
| `log Z` | 1,96×10⁻⁵ |
| Quantil de massa, máximo | 3,79×10⁻⁵ da largura da priori |
| CDF de massa, máximo em 201 pontos | 5,28×10⁻⁵ |
| CDF nuisance, máximo nos 20 cortes | 9,42×10⁻⁶ |

Essa comparação foi refeita com os valores deste experimento, sem transferir
a aprovação anterior da malha em uma integração RQMC diferente. As tolerâncias
originais continuam `ΔlogZ≤.001`, `ΔPIT≤.002` e `Δquantil≤.001` da largura
da priori. O teste de quantis completos nuisance ainda não foi executado.

As 20 CDFs, seus numeradores condicionais por massa e todos os hashes estão
em `results/A0_d14_GL32_20_12_full_truncated_cdf.json`. A ordem dos parâmetros
segue `[log10 Agw, gamma_gw, log10 Ar, log10 EFAC]`; cada grupo contém os quatro
cortes de quantis anteriores e o corte do PIT, devidamente rotulados no JSON.

## Comparação com RQMC e custo

O nível anterior `endpoint_129_13_independent` (mesmos 139 nós, 8192 nuisances
por scramble e quatro scrambles) deu `logZ=-76.07655264480616`, com erro padrão
relativo estimado de 0,00715. Sua diferença de aproximadamente −0,003546 em
relação à referência determinística fica dentro desse erro estimado, mas
excede a meta numérica de 0,001. Esse nível já falhara nas próprias comparações;
não era uma referência absoluta. Não se afirma um viés de RQMC a partir disso.

| Regra completa | Pontos dos integrandos | Tempo de parede observado |
|---|---:|---:|
| CDF condicional 12, 139 massas | 4.863.888 | 18,94 s |
| CDF condicional 20, 139 massas | 17.514.000 | 57,53 s |
| CDF condicional 32, 139 massas | 60.208.128 | 205,06 s |
| Caixas truncadas 20³, 139 massas | 210.168.000 | 546,83 s |
| Caixas truncadas 32×20×12, 139 massas | 201.761.280 | 623,57 s |

Na primeira rota, as ordens de gamma reais são 27/35/47, pois ela insere os
cortes de CDF de gamma e distribui a ordem entre os painéis. A segunda rota
conta 20 numeradores e um denominador, cada qual com sua caixa e painéis.
Os tempos foram medidos com carga concorrente; não se conclui que a regra
com menos pontos seja universalmente mais lenta. As matrizes de ORF são
lidas de cache, não recalculadas por ponto. Os limites de pontos foram
verificados antes das execuções; cada integral completa truncada ficou abaixo
do teto declarado de 500 milhões. A estimativa de arranjos densos em memória
está em `resource_estimate.json`; não é uma medida de RSS.

## Verificações independentes

* Kernel espectral versus Cholesky: 972 casos, máximo `|ΔlogL|=3,37×10⁻¹¹`,
  erro relativo de `χ≤4,67×10⁻¹³`, erro de `logdet≤4,84×10⁻¹³`.
* Priori conjunta: normalização e momentos, inclusive `Cov(a,b)=Var(t)`,
  reproduzidos até arredondamento. Controles em 41 caixas incluem larguras
  truncadas menores que a largura da escala.
* Função exponencial separável: integral transformada contra produto de quatro
  integrais elementares originais, erro relativo≤3,17×10⁻¹⁴; CDFs originais
  contra expressão fechada, erro absoluto≤1,78×10⁻¹⁵.
* Regra anisotrópica versus 32³ em `u=0,.5,1`: maior diferença de CDF≤7,95×10⁻⁶
  nos cortes testados. Em `u=1`, a diferença foi≤1,35×10⁻⁹.
* Nenhum recorte de autovalor: os pequenos autovalores negativos por
  arredondamento permanecem no cálculo; todos os denominadores espectrais
  foram positivos. Seus mínimos constam nos resultados.
* A omissão de pesos minúsculos só na rota condicional tem soma posterior
  explicitamente registrada (~10⁻¹⁸), muito menor que suas falhas de CDF.
  A rota por caixas truncadas não omite essas contribuições.

## Entrega e próximos limites

`DERIVACAO_CUBATURA.md` contém a medida, painéis, integração da escala e o
atalho espectral; `INTEGRACAO.md` descreve as interfaces e o trabalho restante.
`results/comparison.json` é o resumo reproduzível; a figura diagnóstica fica
em `results/convergence_diagnostic.pdf` e `.png`. Fontes, configuração, dados,
cache por massa e cortes têm hashes nos JSONs.

O passo seguinte para usar esta referência em C07 é calcular quantis nuisance
pela CDF contínua com intervalos de precisão em largura de suporte e validar
as demais realizações/modelos. A decomposição espectral pode ser compartilhada
por vários dados A0, mas essa extensão ainda não foi implementada. Todos os
arquivos deste pacote permanecem em `tmp/`; nenhum commit, push ou arquivo
versionado foi alterado por esta subtarefa.
