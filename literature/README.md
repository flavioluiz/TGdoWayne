# Acervo de artigos

Biblioteca local de apoio à pesquisa, com corte bibliográfico em **11/09/2026** e suplemento metodológico em **12/09/2026**: **38 PDFs**, **69.513.382 bytes** (69,51 MB decimais) e **857 páginas**. Todos os arquivos foram baixados e conferidos; o grau de leitura varia e está registrado por referência. O download de um PDF não equivale a sua leitura integral, reprodução ou validação científica.

O [catálogo](catalog.json) registra título, autores, revisão, datas, URL primária, licença identificada na fonte, caminho local, tamanho e SHA-256. Nos 35 registros arXiv, a revisão é fixada por identificador `vN`. Dois documentos dos sites dos autores e um PDF editorial JMLR têm mês documental e SHA-256 explícitos, pois seus URLs não identificam revisões numeradas. Novas cópias devem entrar em atualização explícita do catálogo. O TG original fornecido pelo usuário permanece em [TG_Wayne.pdf](../TG_Wayne.pdf), fora desta coleção de artigos baixados.

## Reconstituir ou verificar o acervo

A partir da raiz do repositório, com Python 3 e acesso HTTPS às fontes primárias:

```sh
python3 scripts/download_papers.py
```

O comando usa `literature/catalog.json` e baixa somente arquivos ausentes para `literature/papers/`. Cópias existentes são verificadas; uma divergência de tamanho ou SHA-256 termina com erro e preserva o arquivo existente. Uma resposta HTML ou outro conteúdo que não seja PDF não é aceita. O catálogo não é atualizado silenciosamente durante o download.

Verificação inteiramente local, sem acesso à rede:

```sh
python3 scripts/download_papers.py --verify
```

Para um catálogo alternativo ou checkout diferente:

```sh
python3 scripts/download_papers.py --catalog literature/catalog.json --root . --verify
```

O verificador exige a revisão explícita no URL arXiv e o caminho padronizado. Para o relatório do autor e o PDF editorial, exige URL primário HTTPS, mês documental, descrição da versão e bytes fixados por SHA-256; o registro editorial também identifica o periódico e o ano. Se o arXiv regenerar um PDF da mesma revisão, os bytes poderão mudar: registrar a divergência, conferir a fonte e atualizar o catálogo em um novo commit justificado. Não desativar a verificação para aceitar bytes desconhecidos.

## Cópias locais e redistribuição

Os PDFs de terceiros em `literature/papers/` ficam **fora do Git**. São versionados o catálogo, esta documentação e a receita de obtenção. Os releases deste projeto contêm os PDFs produzidos pelo próprio projeto, não uma republicação automática dos artigos consultados.

Nos registros arXiv, a coluna de licença reproduz o identificador e o link apresentados para a cópia baixada. No relatório do autor, não foi identificada licença explícita de reutilização. Não substitui os termos da licença, nem atribui a licença do repositório ao texto de terceiros. Uma cópia editorial pode ter licença diferente: por exemplo, o catálogo de Franciolini et al. referencia o preprint local com licença arXiv, separadamente dos dados de sua publicação em periódico.

A escolha de guardar PDFs localmente não afirma que todas as licenças proíbam redistribuição. Qualquer redistribuição futura exige conferir a licença da versão exata e suas condições. As categorias `arXiv nonexclusive-distrib` e `arXiv assumed-1991-2003` não são convertidas em licenças Creative Commons por este projeto.

## Arquivos disponíveis

Os nomes abaixo são relativos a `literature/papers/`; os links “fonte” abrem os PDFs primários, pois as cópias locais não são hospedadas no GitHub.

| Arquivo local | Artigo | Páginas | Licença indicada | PDF primário |
|---|---|---:|---|---|
| `gr-qc_0409041v1.pdf` | Polarization states of gravitational waves with a massive graviton | 11 | [arXiv assumed-1991-2003](http://arxiv.org/licenses/assumed-1991-2003/) | [fonte](https://arxiv.org/pdf/gr-qc/0409041v1) |
| `gr-qc_9705051v2.pdf` | Mass for the graviton | 12 | [arXiv assumed-1991-2003](http://arxiv.org/licenses/assumed-1991-2003/) | [fonte](https://arxiv.org/pdf/gr-qc/9705051v2) |
| `1810.09316v1.pdf` | The Exact Amplitudes of Six Polarization Modes for Gravitational Waves | 27 | [arXiv nonexclusive-distrib 1.0](http://arxiv.org/licenses/nonexclusive-distrib/1.0/) | [fonte](https://arxiv.org/pdf/1810.09316v1) |
| `1011.4266v3.pdf` | Quantum Aspects of Massive Gravity II: Non-Pauli-Fierz Theory | 17 | [arXiv nonexclusive-distrib 1.0](http://arxiv.org/licenses/nonexclusive-distrib/1.0/) | [fonte](https://arxiv.org/pdf/1011.4266v3) |
| `1011.1232v2.pdf` | Resummation of Massive Gravity | 4 | [arXiv nonexclusive-distrib 1.0](http://arxiv.org/licenses/nonexclusive-distrib/1.0/) | [fonte](https://arxiv.org/pdf/1011.1232v2) |
| `1109.3515v2.pdf` | Bimetric Gravity from Ghost-free Massive Gravity | 12 | [arXiv nonexclusive-distrib 1.0](http://arxiv.org/licenses/nonexclusive-distrib/1.0/) | [fonte](https://arxiv.org/pdf/1109.3515v2) |
| `2108.05344v3.pdf` | Detecting the Stochastic Gravitational Wave Background from Massive Gravity with Pulsar Timing Arrays | 28 | [CC BY 4.0](http://creativecommons.org/licenses/by/4.0/) | [fonte](https://arxiv.org/pdf/2108.05344v3) |
| `2310.07469v1.pdf` | Constraining the Graviton Mass with the NANOGrav 15-Year Data Set | 6 | [CC BY 4.0](http://creativecommons.org/licenses/by/4.0/) | [fonte](https://arxiv.org/pdf/2310.07469v1) |
| `2310.12138v1.pdf` | The NANOGrav 15-year data set: Search for Transverse Polarization Modes in the Gravitational-Wave Background | 11 | [CC BY 4.0](http://creativecommons.org/licenses/by/4.0/) | [fonte](https://arxiv.org/pdf/2310.12138v1) |
| `2407.04464v2.pdf` | On the overlap reduction function of pulsar timing array searches for gravitational waves in modified gravity | 14 | [CC BY 4.0](http://creativecommons.org/licenses/by/4.0/) | [fonte](https://arxiv.org/pdf/2407.04464v2) |
| `2507.02059v2.pdf` | Do Pulsar Timing Datasets Favor Massive Gravity? | 7 | [CC BY 4.0](http://creativecommons.org/licenses/by/4.0/) | [fonte](https://arxiv.org/pdf/2507.02059v2) |
| `2506.07679v2.pdf` | Spatial Correlation between Pulsars from Interfering Gravitational-Wave Sources in Massive Gravity | 11 | [CC BY 4.0](http://creativecommons.org/licenses/by/4.0/) | [fonte](https://arxiv.org/pdf/2506.07679v2) |
| `2607.14790v1.pdf` | Probing Graviton Mass with MeerKAT PTA and SKA--PTA Forecasts | 12 | [CC BY-NC-ND 4.0](http://creativecommons.org/licenses/by-nc-nd/4.0/) | [fonte](https://arxiv.org/pdf/2607.14790v1) |
| `2603.19020v2.pdf` | GWTC-4.0: Tests of General Relativity. II. Parameterized Tests | 43 | [CC BY 4.0](http://creativecommons.org/licenses/by/4.0/) | [fonte](https://arxiv.org/pdf/2603.19020v2) |
| `2603.03165v1.pdf` | Testing gravitational wave polarizations with LISA | 113 | [arXiv nonexclusive-distrib 1.0](http://arxiv.org/licenses/nonexclusive-distrib/1.0/) | [fonte](https://arxiv.org/pdf/2603.03165v1) |
| `2507.09543v2.pdf` | Distinguishing gravity theories with networks of space-based gravitational-wave detectors | 9 | [arXiv nonexclusive-distrib 1.0](http://arxiv.org/licenses/nonexclusive-distrib/1.0/) | [fonte](https://arxiv.org/pdf/2507.09543v2) |
| `2509.08273v1.pdf` | New test of modified gravity with gravitational wave experiments | 30 | [CC BY 4.0](http://creativecommons.org/licenses/by/4.0/) | [fonte](https://arxiv.org/pdf/2509.08273v1) |
| `2505.24695v1.pdf` | Likelihoods for Stochastic Gravitational Wave Background Data Analysis | 25 | [arXiv nonexclusive-distrib 1.0](http://arxiv.org/licenses/nonexclusive-distrib/1.0/) | [fonte](https://arxiv.org/pdf/2505.24695v1) |
| `2604.23384v2.pdf` | Forecasting graviton-mass constraints from the full covariance of PTA-astrometry ORF estimators | 23 | [CC BY-NC-ND 4.0](http://creativecommons.org/licenses/by-nc-nd/4.0/) | [fonte](https://arxiv.org/pdf/2604.23384v2) |
| `2306.13593v4.pdf` | Testing gravity with cosmic variance-limited pulsar timing array correlations | 9 | [arXiv nonexclusive-distrib 1.0](http://arxiv.org/licenses/nonexclusive-distrib/1.0/) | [fonte](https://arxiv.org/pdf/2306.13593v4) |
| `1210.0584v2.pdf` | Accelerating pulsar timing data analysis | 9 | [arXiv nonexclusive-distrib 1.0](http://arxiv.org/licenses/nonexclusive-distrib/1.0/) | [fonte](https://arxiv.org/pdf/1210.0584v2) |
| `2408.10122v2.pdf` | A novel probe of graviton dispersion relations at nano-Hertz frequencies | 19 | [CC BY 4.0](http://creativecommons.org/licenses/by/4.0/) | [fonte](https://arxiv.org/pdf/2408.10122v2) |
| `1804.06788v2.pdf` | Validating Bayesian Inference Algorithms with Simulation-Based Calibration | 19 | [arXiv nonexclusive-distrib 1.0](http://arxiv.org/licenses/nonexclusive-distrib/1.0/) | [fonte](https://arxiv.org/pdf/1804.06788v2) |
| `2211.02383v3.pdf` | Simulation-Based Calibration Checking for Bayesian Computation: The Choice of Test Quantities Shapes Sensitivity | 50 | [CC BY 4.0](http://creativecommons.org/licenses/by/4.0/) | [fonte](https://arxiv.org/pdf/2211.02383v3) |
| `2508.11814v4.pdf` | Simulation-based validation of Bayes factor computation | 54 | [CC BY-NC-SA 4.0](http://creativecommons.org/licenses/by-nc-sa/4.0/) | [fonte](https://arxiv.org/pdf/2508.11814v4) |
| `2502.03279v2.pdf` | Posterior SBC: Simulation-Based Calibration Checking Conditional on Data | 25 | [CC BY 4.0](http://creativecommons.org/licenses/by/4.0/) | [fonte](https://arxiv.org/pdf/2502.03279v2) |
| `2608.17143v1.pdf` | Randomized quasi-Monte Carlo integration | 20 | [arXiv nonexclusive-distrib 1.0](https://arxiv.org/licenses/nonexclusive-distrib/1.0/) | [fonte](https://arxiv.org/pdf/2608.17143v1) |
| `owen_zhou1998.pdf` | Safe and effective importance sampling — relatório de junho de 1998 | 34 | Reutilização não identificada na cópia consultada | [fonte do autor](https://artowen.su.domains/reports/seis.pdf) |
| `2608.13991v1.pdf` | On the Acceleration of Pulsar Timing computations using Normalising Flows and Parallelisation | 15 | [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) | [fonte](https://arxiv.org/pdf/2608.13991v1) |
| `1903.08008v5.pdf` | Rank-normalization, folding, and localization: An improved R-hat for assessing convergence of MCMC | 26 | [arXiv nonexclusive-distrib 1.0](https://arxiv.org/licenses/nonexclusive-distrib/1.0/) | [fonte](https://arxiv.org/pdf/1903.08008v5) |
| `vehtari2024psis.pdf` | Pareto Smoothed Importance Sampling | 58 | [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) | [fonte editorial](https://jmlr.org/papers/volume25/19-556/19-556.pdf) |

| `1712.00012v2.pdf` | Generalized massive optimal data compression | 6 | [arXiv nonexclusive-distrib 1.0](http://arxiv.org/licenses/nonexclusive-distrib/1.0/) | [fonte](https://arxiv.org/pdf/1712.00012v2) |
| `1107.3797v2.pdf` | A note on insufficiency and the preservation of Fisher information | 12 | [arXiv nonexclusive-distrib 1.0](http://arxiv.org/licenses/nonexclusive-distrib/1.0/) | [fonte](https://arxiv.org/pdf/1107.3797v2) |
| `2406.11954v2.pdf` | Spatial and Spectral Characterization of the Gravitational-wave Background with the PTA Optimal Statistic | 24 | [CC BY 4.0](http://creativecommons.org/licenses/by/4.0/) | [fonte](https://arxiv.org/pdf/2406.11954v2) |
| `2509.07090v1.pdf` | Mapping the Gravitational-wave Background Across the Spectrum with a Next-Generation Anisotropic Per-frequency Optimal Statistic | 23 | [CC BY 4.0](http://creativecommons.org/licenses/by/4.0/) | [fonte](https://arxiv.org/pdf/2509.07090v1) |
| `2307.04680v4.pdf` | Unveiling the Graviton Mass Bounds through Analysis of 2023 Pulsar Timing Array Data Releases | 7 | [CC BY-NC-ND 4.0](http://creativecommons.org/licenses/by-nc-nd/4.0/) | [fonte](https://arxiv.org/pdf/2307.04680v4) |
| `2506.13866v1.pdf` | Beyond diagonal approximations: improved covariance modeling for pulsar timing array data analysis | 14 | [arXiv nonexclusive-distrib 1.0](http://arxiv.org/licenses/nonexclusive-distrib/1.0/) | [fonte](https://arxiv.org/pdf/2506.13866v1) |

## Relação com a revisão bibliográfica

O acervo inicial de C03 tinha 22 artigos e 452 páginas. C06 acrescenta quatro referências
metodológicas de calibração e evidências bayesianas para apoiar a etapa inferencial.
As versões de preprint e as datas de publicação editorial são registradas separadamente.
C07 acrescenta duas referências de agosto de 2026, sobre RQMC e aceleração
computacional em PTAs, referências sobre diagnósticos de MCMC e de amostragem por importância
e um relatório histórico sobre amostragem por importância. A cópia de Owen–Zhou é de junho de 1998,
precursora do artigo JASA de 2000; o catálogo não a apresenta como PDF editorial.

A análise crítica e os limites da busca constam de [protocolo](../docs/literatura/protocolo_busca.md), [matriz de originalidade](../docs/literatura/matriz_originalidade.csv) e [decisão do recorte](../docs/literatura/decisao_recorte.md). Os códigos externos inspecionados são descritos na [auditoria de códigos](../docs/literatura/auditoria_codigos.md); essa inspeção não implica que tenham sido executados.

Metadados e hashes preservam a rastreabilidade das cópias; não certificam a correção dos artigos. O estado atual da dissertação e o PDF mais recente estão no [README principal](../README.md).

A [atualização computacional C07](../docs/literatura/atualizacao_computacional_c07.md)
registra a leitura recente e uma tentativa de obter o erratum NANOGrav de 2026,
cujo PDF não foi recebido. Fontes sem PDF não entram na contagem acima.

A [auditoria dirigida de 11/09/2026](../docs/literatura/atualizacao_20260911/REPORT.md)
acrescenta seis antecedentes sobre estimadores PTA por frequência, covariância da janela,
priori de velocidade e informação de Fisher. A matriz passa de 17 para 23 entradas.
Os seis PDFs foram copiados para esta biblioteca e conferidos localmente; os caminhos
`tmp` no pacote de entrega preservam a proveniência anterior à integração.

## Suplemento metodológico C10

Em 12/09/2026 foi acrescentada a cópia pública de *Exactness of quadrature formulas*, de Lloyd N. Trefethen, para apoiar os testes de integração aninhada. A cópia `exactnessRev2.pdf` do autor está fixada por SHA-256; não é apresentada como idêntica à revisão arXiv v1.
