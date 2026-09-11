# Descrição pareada dos 500 dados publicados no C07

Produto descritivo separado da inferência C08 em andamento. Reutiliza exclusivamente os resumos C07 publicados em v0.7.1; não lê raws posteriores nem gera novas realizações, ORFs ou verossimilhanças. A leitura do NPZ de geração é limitada ao membro `truth` para conferir as 500 verdades originais.

## Resultado e domínio

Foram preservados os 2.500 alvos = cinco modelos × 500 dados, com inventário sem duplicatas e correspondência exata `target=model_index*500+datum`. Os três contrastes seguem **nova análise menos anterior**: A_CN−A0_CN, B_CN−A_CN e B_G−A_G. Cada um contém os 20 quantis (cinco parâmetros × probabilidades .05/.5/.9/.95) e as cinco larguras Q95−Q05. As diferenças são medidas em frações da largura da priori; para u essa largura vale um.

| Contraste | Média ΔQ95(u) | Mediana ΔQ95(u) | Média Δlargura90(u) | Mediana Δlargura90(u) |
|---|---:|---:|---:|---:|
| A_CN−A0_CN | +0,00129627 | +0,00059191 | −0,00244222 | −0,00007491 |
| B_CN−A_CN | +0,00540219 | −0,00126587 | +0,01147399 | +0,00213229 |
| B_G−A_G | +0,00477127 | −0,00060590 | +0,00652160 | +0,00137018 |

Esses números descrevem os valores calculados, sem precisão horizontal certificada para os quantis. Não demonstram viés populacional, equivalência ou materialidade de um pequeno deslocamento. A média e a mediana de ΔQ95 têm sinais distintos em dois contrastes, de modo que a média isolada também não descreve todos os dados. Não foram criados intervalos de confiança, MCSE de síntese, testes de hipótese ou filtros a partir desses valores.

Bins fixos de verdade: u em [0,.5), [.5,.9), [.9,1], com 243/208/49 casos; gamma em [3,4.25), [4.25,5.5], com 233/267 casos. As seis células cruzadas têm 117/126, 92/116 e 24/25 casos, respectivamente. O último intervalo inclui seu endpoint superior. São grupos dos mesmos dados, sem novos denominadores de Monte Carlo e sem combinar as células como réplicas independentes.

## Guardas mantidas

Nenhum caso foi removido. `summary.json` registra, por modelo, par e bin, as flags herdadas de resolução dos PITs por função e a precisão das CDFs nos cortes escolhidos no LOW independente, além dos ESS/pesos máximos HIGH salvos. A matriz de CDFs nos cortes LOW **não** é uma matriz de erros horizontais dos quantis HIGH. As flags por função não são rebatizadas como aprovação integral de todos os testes do alvo.

| Modelo | Dados com os seis PITs resolvidos | Dados com precisão CDF nos 20 cortes LOW |
|---|---:|---:|
| A0_CN | 497/500 | 498/500 |
| A_CN | 485/500 | 482/500 |
| B_CN | 494/500 | 495/500 |
| A_G | 484/500 | 484/500 |
| B_G | 490/500 | 492/500 |

## Produtos e seleção de figuras

- `load_c07_results.py`: leitor que confere SHA, publicação final G0/v0.7.1, dados/config/geração, inventário 2500, shapes, prioris, unidades e 500 verdades. Não reaudita nem reabre os 2.500 diagnósticos; parte da síntese já auditada e vinculada por SHA.
- `design.json`: contrastes, grupos, estatísticas e limites descritivos definidos antes da geração destes produtos.
- `results/paired_values.csv`: 1.500 linhas, uma por par/dado, com as 25 diferenças, verdade u/gamma e flags herdadas.
- `results/descriptive_bins.csv`: 900 linhas de estatísticas para global, bins marginais e células cruzadas. Percentis empíricos descrevem a distribuição entre os casos e não são intervalos de confiança da média.
- `results/paired_arrays.npz`: arrays completos das diferenças e guardas originais, sem amostras posteriores.
- `results/summary.json`: resumos globais, guardas por par/bin, proveniência e hashes dos produtos.
- **Figura selecionada 1:** `results/paired_quantiles_widths.pdf` e `.svg`.
- **Figura selecionada 2:** `figures_v2/paired_mass_bins.pdf` e `.svg`.
- `descriptive_review.json`: 60 médias com direção comparadas à síntese C07, erro exatamente zero; 225 recomposições das médias pelos bins, erro máximo 2,78e−17; inspeção dos dois PNGs selecionados.

A primeira versão `results/paired_mass_bins.*` tinha rótulos nas margens cortados; foi preservada, mas não deve ser portada para o PDF. A versão selecionada foi renderizada do CSV inalterado por `plot_mass_bins_v2.py`; somente layout e casas decimais da anotação mudaram. O gráfico global utiliza o estilo tipográfico C07 e não contém barras de erro.

## Proveniência

Síntese original `results/C07/synthesis/summary.json`: SHA **909ef28817342c19293fe9cb832bcf659dd480be5fd82c3708ee73b832cd4f9a**. Arrays originais: SHA **2effb30fafb2db1ae6371952d933cb9f8be63bf2875cd8a55ea15188a39a4a4f**. Dados: **63679c96852f3c0aa1e25c8a3f087c0646ceb22cd7701758491cabdd42ac0103**. Configuração: **f22b0a8cd7c86e477365ea02d3b37a836458d44285b0abd323bccd174c89fdfa**.

O leitor confere esses arquivos também no manifesto publicado v0.7.1, cuja identidade é validada pelo recibo de download mencionado em G0. O recibo G0 documenta a liberação histórica de recursos; não é consultado como medidor da carga atual. A execução descritiva consumiu 2,51 s de CPU e RSS máximo 139.198.464 B; o desenho dos gráficos não envolve cálculos PTA. No campo histórico `physical_or_posterior_arrays_read` da proveniência, “posterior” significa os raws de amostras: os arrays compactos de quantis foram explicitamente lidos conforme autorizado.

Reprodução em diretório novo:

```sh
VECLIB_MAXIMUM_THREADS=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv/bin/python tmp/c08_c07_descriptive_v1/summarize.py --repository . --output DIRETORIO_NOVO
```

`plot_mass_bins_v2.py` referencia explicitamente o CSV congelado para a correção de layout. Os fontes executados e a primeira falha sintática, anterior a qualquer leitura científica, permanecem preservados. `delivery_manifest.json` contém hashes e a lista de porte sugerida. O ROOT decide a integração e o texto final; este pacote não encerra C08.
