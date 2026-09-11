# Pacote temporário C07: inferência contínua e piloto numérico

**Estado: piloto real de 16 realizações; critérios de convergência ainda em avaliação. Não é SBC500, resultado observacional ou conclusão sobre massa do gráviton.** Os níveis iniciais revelaram falhas numéricas e são preservados. Nenhum arquivo versionado foi alterado por este pacote.

O experimento usa 12 pulsares numa esfera de Fibonacci, quatro coeficientes positivos de Fourier independentes em `n/T`, duração de 4,5 anos e distâncias de 300–1000 anos-luz. A configuração integral e as sementes foram escritas em `config.json` antes dos dados. As cinco coordenadas contínuas são `u=f_g T`, `log10_Agw`, `gamma_gw`, `log10_Ar` e `log10_EFAC`. O índice vermelho intrínseco é fixado em 4. Os dados e as verdades estão em `results/data.npz`; a configuração tem seu SHA256 registrado nesse arquivo. A grade temporal periódica tem 118 amostras, com cadência efetiva `T/118`; o experimento retém somente quatro modos e não implementa ajuste temporal ou janela irregular.

A conversão física é `m_g c² = h u/T`, aproximadamente `2,91×10⁻²³ u eV` para essa duração. O limite superior `u=1` é uma escolha explícita de suporte da priori para preservar os quatro canais propagantes; não é um limite observacional obtido pelo piloto.

## Famílias probabilísticas

| Coluna | Dados | Verossimilhança | Interpretação |
|---|---|---|---|
| A0_CN | Coeficientes complexos completos | CN própria, um coeficiente por frequência | Referência física exata do experimento idealizado |
| A_CN | Quadráticas angulares da mesma realização | Normal com média/covariância exatas | Família aproximada; calibração pode falhar mesmo com integração exata |
| B_CN | Compressão fixa das mesmas quadráticas | Normal com momentos comprimidos corretamente | Família aproximada; A–B não isola perda de informação quando a família falha |
| A_G | Controle normal pareado, com mesmos momentos | Normal exata | Separa o erro numérico da aproximação distributiva |
| B_G | Compressão fixa do controle A_G | Normal exata | Estuda compressão dentro de uma família correta |

Os controles G compartilham variáveis normais latentes com CN, mas são experimentos distintos com as distribuições marginais declaradas. Não há segmentos fictícios independentes de PTA. Os bins e pesos foram fixados pela geometria e pelos erros nominais, sem usar a verdade ou a potência observada. `C_full` e `C_beta` serão acrescentados posteriormente; não foram avaliados neste piloto.

As PSDs residuais físicas têm unidades de s³. O cálculo usa `q'=q/sqrt(s_k)` e `C'=C/s_k`, com `s_k` positivo fixado por um modelo de referência anterior à injeção. As densidades armazenadas são relativas a esses dados adimensionais. A mudança de medida adicionaria uma constante independente de parâmetros à log-densidade dos dados físicos; ela cancela nas comparações de resolução e nas razões de evidências entre modelos definidos sobre os mesmos dados. A compressão de frequências opera sobre as quadráticas adimensionais, com pesos1/4 fixos.

## Integração e controles

`src/inference_pilot.py` implementa verossimilhanças em lote, quadratura contínua em massa e integração Sobol embaralhada nos quatro nuisances. As ORFs são calculadas em cada massa solicitada: não há interpolação de ORF ou prior discreta. A densidade marginal de massa é aproximada por segmentos lineares positivos; a CDF é integrada e invertida continuamente dentro dos segmentos. Essa aproximação exige refinamento e não torna a posterior física exata.

As CDFs dos nuisances são aproximações de quadratura com interpolação dos pontos médios de probabilidades acumuladas ponderadas. Não são amostras da posterior. Os erros de quantis são avaliados por refinamento e scrambles independentes. A concentração dos pesos, rotulada como ESS de quadratura, é somente um diagnóstico numérico, sem interpretação de ESS de amostras IID.

Os níveis iniciais variam separadamente 33→65 massas, 512→2048 pontos Sobol por scramble e conjuntos independentes de quatro scrambles. `adaptive_levels.json` adiciona pontos na camada `u→1`, definida por valores explícitos de `beta_1`; os pesos continuam sendo larguras em `du`, preservando a priori. Os níveis seguintes comparam 65→129 nós de base e 2048→8192 nuisances, sem alterar dados, verdades, prioris, critérios ou famílias.

Todas as matrizes ORF solicitadas passam comparação harmônica em duas resoluções. Sete entradas predefinidas também são comparadas com integração direta independente, incluindo o primeiro e o quarto canais, `u=0`, `u=0,5` e `u=1`. Isso é convergência interna de todas as matrizes com checagens independentes esparsas; não é certificação independente de cada entrada por quadratura direta. O orçamento é estimado antes de cada cálculo. Não há correção de autovalores por clipping.

Precisão histórica sobre recursos: o primeiro conjunto de sete verificações diretas usou resoluções explícitas, mas precedeu a adição do preflight específico dessas verificações. A memória conservadora foi auditada posteriormente (cerca de570MB no maior caso). A reprodução atual verifica orçamento próprio de1bilhão de unidades de trabalho e700MB antes de executar esse conjunto; o preflight harmônico já existia desde a primeira tabela. As estimativas são proxies, não limites medidos de RSS.

## Reprodução da raiz do repositório

```sh
.venv/bin/python tmp/c07_integration/run_staged.py tmp/c07_integration/tests/test_kernel.py
.venv/bin/python tmp/c07_integration/run_staged.py tmp/c07_integration/scripts/validate_quadrature.py
.venv/bin/python tmp/c07_integration/run_staged.py tmp/c07_integration/scripts/run_pilot.py
.venv/bin/python tmp/c07_integration/run_staged.py tmp/c07_integration/scripts/run_pilot.py --level-file tmp/c07_integration/adaptive_levels.json --skip-direct
.venv/bin/python tmp/c07_integration/run_staged.py tmp/c07_integration/scripts/compare_levels.py
```

O harness importa os módulos públicos C05 e os módulos temporários C06. Os resultados existentes são preservados; usar outra pasta em `--output` para uma reprodução independente. A opção `--skip-direct` exige um registro de checagens diretas já existente. Os tempos com cache reutilizado são identificados no relatório e não representam geração de tabelas do zero.

O rascunho de campanha500 apenas prepara o contrato e a estimativa de memória; ele bloqueia a execução enquanto estiver marcado como não convergido:

```sh
.venv/bin/python tmp/c07_integration/run_staged.py tmp/c07_integration/scripts/run_pilot.py --config tmp/c07_integration/campaign500_draft.json --output tmp/c07_integration/results/campaign500 --dry-run
```

## Validação e limites de interpretação

Os cinco testes independentes cobrem PSD física, momentos por traços diretos, densidade CN comparada com normal real de dimensão24, densidade normal comparada com SciPy e CDF/quantis contínuos de uma densidade linear analítica. A referência de quadratura5D usa distribuição normal truncada fatorizada com normalização e quantis analíticos. O pacote anterior `tmp/c07_design` contém ainda referência independente de massa+amplitude TT em dimensão2 por Gauss–Legendre e quadratura adaptativa; a geometria dessa referência é propositalmente pequena. Isso não substitui validação independente das posteriores físicas de cinco parâmetros.

Além dos PITs dos parâmetros, o piloto calcula a CDF posterior de `log L(theta; dados)` na verdade injetada e a mesma quantidade sob uma implementação negativa que ignora os dados e devolve a priori. Não se declara uniformidade com16 realizações. Falhas numéricas atuais impedem usar diferenças de calibração para julgar a família estatística. O nível de integração não será aprovado por uma mera aparência uniforme dos ranks.

As evidências são comparadas somente entre resoluções do mesmo experimento e mesma família. Razões de normalizações A0/A/B não são fatores de Bayes válidos: essas análises podem usar dados de dimensões diferentes. Testar um modelo RG pontual contra massa contínua requer calcular ambas as evidências na mesma família, com prioris próprias e validação específica da razão.

Com priori contínua, `P(u=0)=0`. A cobertura de `[0,U90]` em verdade fixa `u=0` é100% por construção, e não deve ser cobrada como90%. Cenários de fronteira, nulo sem sinal, identificabilidade e futura seleção de modelos permanecem explicitamente separados de SBC sob a priori.
