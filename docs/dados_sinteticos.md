# Dados sintéticos e evidências executadas em C06

O pacote implementa a população tensorial descrita no contrato de comparações. O controle principal utiliza 10 direções fixas de Fibonacci, T=15 anos, canais n=1,2,3 e uma grade periódica de 392 pontos (cadência 13,9764 dias). Distâncias de 100–300 anos-luz e incertezas TOA de 100–500 ns estão enumeradas, sem sorteio oculto, nos três arquivos JSON. Essa geometria reduzida valida momentos; não é uma PTA observada ou representativa. O máximo fL/c é 60.

O vetor de estatísticas tem quatro bins angulares de pares Re, quatro Im e dois grupos de autos. Os pares são orientados a<b. A binagem é fixada pela geometria e pelos erros nominais, sem verdade injetada; os pesos de frequência são 1/3. A normalização usa uma lei de potência fiducial e a mediana dos erros nominais, conforme o JSON. O caso sem sinal continua com essa normalização fixa: seus canais normalizados não têm a mesma variância, e a compressão não garante uma grande redução da curtose.

## Execuções

| Caso | Seed | Realizações físicas e controles pareados | Maior discrepância em SE Monte Carlo | Pares ORF auditados | Tempo antes da serialização |
|---|---:|---:|---:|---:|---:|
| Massivo u=0,6 |691206|131072 cada|3,502|275|21,76 s|
| GR u=0 |691207|131072 cada|3,936|165|15,93 s|
| Apenas ruído branco |691208|131072 cada|3,187|165|15,96 s|

Os números se referem a 128 blocos de 1024 sorteios independentes, com limiar de regressão pré-fixado em 6 SE. A interpretação é acordo empírico de momentos nas três configurações, sem reivindicar um limite de confiança simultâneo. Os três casos foram executados simultaneamente, com outras tarefas concorrentes. Os tempos dependem dessa carga e de hardware/cache; geração e cálculo dos blocos de momentos custaram 1,65 s no caso massivo, 2,50 s em GR e 2,51 s no controle branco. JSON `null` nas amplitudes do controle significa amplitude física exatamente zero.

Todos os elementos de cada matriz usaram as mesmas resoluções C05: grossa(460,900,500,1000), fina(520,1000,600,1200), na ordem(lmax,nmu_harmonic,nmu_direct,nphi_direct), atol 1e-5 e rtol 1e-3. O máximo observado entre refinamento e comparação independente foi 3,1131e-13. O orçamento por par é 10 milhões de unidades de trabalho aproximadas e 64 MB de memória estimada. O teto agregado de 3 bilhões soma reservas conservadoras dos pares; a execução é sequencial e não interpreta a soma dos orçamentos de memória como memória residente.

No caso massivo, o menor autovalor de Γ foi 0,29512455, a maior parte imaginária absoluta 0,00430026, o menor autovalor de C normalizada 0,08354305 e a maior condição de C 4,3334. Nenhum autovalor foi recortado. Produtos escalares podem ser saturados em [-1,1] apenas para arredondamento após validar direções unitárias com tolerância 1e-12.

Os controles incluem a covariância completa dos coeficientes, inclusive os blocos entre canais, e sua pseudocovariância nula; médias e covariâncias de A/B físicas e normais; assimetria e curtose selecionadas. Onze testes portáveis também passaram. Eles incluem uma referência independente de Isserlis, reconstrução por FFT, suporte espectral, propagação geral de covariâncias e recusa de orçamento agregado antes da quadratura.

## Resultados que limitam a interpretação

No primeiro bin de autos massivo, a assimetria e a curtose excessiva teóricas são 1,02266 e 1,68314 no primeiro canal; depois da compressão,0,63238 e 0,66413. Os dados físicos recuperam esses valores dentro da incerteza Monte Carlo. O controle gaussiano recupera assimetria/curtose excessiva zero. Portanto, verificar a simulação gaussiana não autoriza declarar exata a likelihood normal de suas estatísticas quadráticas.

Na única injeção massiva, C_full muda a média B em até 0,60467 desvio-padrão marginal e a covariância B em 24,0167% na norma de Frobenius relativa. São diferenças condicionais de momentos, sem significado automático de viés de massa, KL ou cobertura. Em GR, C_beta coincide exatamente com B; C_full conserva um deslocamento por congelar fases. No controle branco sem sinal, as covariâncias previstas por todos os modelos coincidem mesmo que as ORFs sem peso de sinal difiram.

## Arquivos e reprodução

Cada pasta de resultados contém resumo JSON, auditoria completa por par e NPZ com 32 realizações físicas/controle. O NPZ conserva q normalizado, A por frequência, B, direções, distâncias em metros, frequências em hertz, escalas[s³], matrizes Γ/C e estimadores. Os parâmetros, seeds e hashes SHA-256 permitem regenerar os outros sorteios. A parte científica de C05 permanece importada sem modificação.

O adaptador que audita todos os pares é uma referência pequena. A campanha posterior deverá compartilhar coeficientes harmônicos entre pares, avaliar nós explícitos de massa e refinar separadamente a integração de parâmetros e a ORF. Nenhuma interpolação em massa foi aceita nesta etapa.

Para ampliar de modo transparente, a grade inicial prevista utiliza T=4,5/15 anos,12 pulsares,4 canais e distâncias 300–1000 anos-luz: max fL/c=888,89. Alterações em duração, número de canais ou distâncias devem verificar novamente esse produto, βfL/c, coerência entre posições próximas, orçamento e convergência. A geração CN não é a única parcela do custo.

Ainda não foram executadas inferência, SBC, cobertura condicional, sensibilidade às prioris,500 posteriors, médias sobre distâncias ou janelas/ajustes de temporização. Essas atividades pertencem aos marcos seguintes.

## Receitas

Execute `.venv/bin/python scripts/validar_simulador.py --check` para os 11 testes, a conferência de fontes/configurações e a regeneração das amostras pequenas. As três campanhas completas têm as receitas:

```bash
.venv/bin/python scripts/validate_moments.py --config configs/experiments/c06_moments.json --output tmp/repro_c06/massive
.venv/bin/python scripts/validate_moments.py --config configs/experiments/c06_moments_gr.json --output tmp/repro_c06/gr
.venv/bin/python scripts/validate_moments.py --config configs/experiments/c06_moments_noise_only.json --output tmp/repro_c06/noise_only
```

`configs/experiments/campaign_design.json` fixa a geometria, prioris e extensões previstas para inferência; seu estado é prospectivo. Os quatro artigos metodológicos acrescentados ao catálogo em C06 orientam a calibração futura. O download não equivale à implementação dos métodos descritos.

A figura `figures/C06/nao_normalidade.pdf` é reproduzida por
`MPLCONFIGDIR=tmp/matplotlib .venv/bin/python scripts/figuras_simulacao.py`.
Ela usa 65536 sorteios novos, seed 2026091066, sem reutilizar as amostras pequenas.
As alturas são contagens divididas pelo total de sorteios e largura do bin; a janela
[-4,7] não renormaliza a densidade. O JSON `results/C06/figure_summary.json` registra
contagens, cumulantes, frações fora da janela e hashes. Foram preservados 1035 autos
normais negativos em A e 11 em B. As cumulantes estimadas por k-statistics e os
momentos centrados nos valores populacionais têm definições distintas no registro.
