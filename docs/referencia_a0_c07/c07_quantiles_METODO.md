# Referência de quantis nuisance, A0 dado 14

Este experimento continua a cubatura em `tmp/c07_cubature/`. O objetivo é
fechar os quantis `.05,.5,.9,.95` dos quatro nuisances originais, mantendo
as regras `(nb,na,nγ)=20³` e `32×20×12` e as prioris originais. Continua sendo
uma referência selecionada de um único alvo A0, independente do novo sampler.

## Localização e bracket final

Os cortes antigos e suas CDFs já calculadas definem uma interpolação monótona
para propor o primeiro ponto. Só os quatro cortes de quantis anteriores são
usados nessa etapa; as coordenadas verdadeiras dos PITs não escolhem os novos
cortes. A localização usa 27 massas (17 uniformes mais a camada final), como
um controle relativo ao numerador antigo:

```
F_est(c)=F_139(c0)+[N_27(c)−N_27(c0)]/Z_139.
```

O mesmo denominador e a mesma família de dados são usados em todos os termos.
A aproximação da malha menor **não** recebe uma aprovação automática; ela
apenas escolhe um centro que será testado novamente. Passos de Newton/secante
são limitados e os cortes são fixados antes de cada avaliação.

Em torno do centro propomos `[lo,hi]` com largura `0.0009 Δ`, onde `Δ` é a
largura da priori do parâmetro. Cada extremo é calculado independentemente nas
duas regras nuisance com 139 massas. Os numeradores por massa permitem repetir
a integral com o subconjunto de 75 massas, sem novas avaliações da likelihood.
Para **cada** uma das quatro combinações exige-se

```
F_upper(lo) < p < F_lower(hi).
```

`F_lower/F_upper` incluem o limite explícito de omissão descrito abaixo. Se
todas as verificações passarem, o ponto médio tem erro de localização de no
máximo `0.00045 Δ` dentro dos brackets, e a diferença entre os quantis das
regras comparadas fica limitada pela largura comum `0.0009 Δ`. As diferenças
entre estimativas interpoladas linearmente também são registradas, sem
substituir o teste dos extremos. Se um bracket falhar, o centro é corrigido
pelas CDFs recém-calculadas; após quatro tentativas há falha explícita.

Esses são brackets para as CDFs numéricas comparadas. A convergência entre
quadraturas não é um teorema de erro absoluto universal da posterior exata.
Essa distinção permanece explícita nos arquivos de resultado.

## Limite das contribuições dispensadas

Para cada nó `(a,b,γ,u)`, a função na escala é a mesma CN normalizada:

```
log L(t)=−Mlogπ−D−2Mln(10)t−χ10^(−2t).
t_peak=clip[log10(χ/M)/2, tlo, thi].
0 ≤ I_t=∫L(t)dt ≤ (thi−tlo)L(t_peak).
```

Para `χ=0`, o máximo fica em `tlo`. Isso fornece um limite superior antes de
chamar as funções gama incompletas. Uma chamada pode ser dispensada somente
se o seu limite, já incluindo peso GL, peso de massa e fator de volume da
priori completa, for menor que `Z ε/Nmax`, com `ε=10⁻¹²` e `Nmax` o limite
superior do número de nós. A soma dos limites efetivamente dispensados é
registrada. Portanto a integral da regra finita está no intervalo entre a
soma calculada e a soma calculada mais esse limite. O erro de omissão da CDF
é separado do erro de quadratura e do arredondamento das funções gama.

O denominador de cada regra vem da execução anterior **sem omissão**, com
hash. A positividade dos pesos permite também reconstruir limites válidos
na submalha de massa de 75 nós. Não se substitui likelihood ou priori por
zero em uma região sem contabilizar a contribuição máxima possível.

`validate_bound.py` confrontou 60 integrais independentes na escala original
com o máximo analítico e os 20 numeradores congelados sem omissão. O maior
erro de CDF foi `1.31×10⁻¹⁴`, e o maior limite de contribuição dispensada
foi `1.30×10⁻¹⁴`; a tolerância de comparação inclui arredondamento separado.

## Lotes e recursos

O núcleo espectral anterior é vetorizado sobre oito massas por lote, com
limite explícito de 16. A matriz de ORF em cada massa continua sendo a exata
do cache; não existe interpolação nesse cálculo. Denominadores espectrais
são verificados e nenhum autovalor é recortado. A maior alocação principal
é proporcional a `J×(3na nγ)×K×Np`; lotes evitam materializar todas as massas
e todos os cortes juntos.

Em um teste pareado de 32 integrais (oito massas e quatro cortes), resultados
e limites coincidiram bit a bit com o núcleo escalar. Tempos foram 1,49 s
escalar e 0,99 s em lotes; o ganho medido ficou entre 1,46 e 1,55 por corte.
Isso é uma medida local sob carga, não uma estimativa de campanha universal.
Cada CDF tem limite de 12 milhões de nós verificado antes da execução. O caso
usual requer 64 CDFs finais, além das localizações; quatro tentativas por
quantil limitam também o pior número de reavaliações. Nenhuma campanha de
16 ou 500 realizações é executada aqui.

Os resultados são gravados por CDF e por quantil. O cache guarda cortes,
numeradores e limites por massa, ordens, denominadores e assinatura da fonte.
Uma execução interrompida pode reutilizar essas CDFs sem refazer sua integração.
Os parâmetros efetivos desta execução são congelados: orçamento de omissão
`10⁻¹²`, lote 8, quatro quantis por nuisance, até cinco passos de localização
e quatro tentativas de bracket. Generalizações do cache precisam incluir
novos parâmetros de execução em sua assinatura.

## Reprodução

```sh
.venv/bin/python tmp/c07_quantiles/run_staged.py tmp/c07_quantiles/validate_bound.py
.venv/bin/python tmp/c07_quantiles/run_staged.py tmp/c07_quantiles/validate_batch.py
.venv/bin/python tmp/c07_quantiles/run_staged.py tmp/c07_quantiles/quantiles.py
```

Resultados anteriores são preservados. O script interrompe diante de uma
falha de bracket em vez de afrouxar a tolerância. Os arquivos temporários
não alteram os módulos `src/inference` integrados pelo coordenador.
