# Integração editorial cumulativa C08 — mapas concluídos

Entregue para integração pelo ROOT, sem modificar os fontes oficiais. O capítulo consolidado é `07_resultados_compressao.tex`. Ele reúne o argumento de processamento de dados, as definições de B/C_beta/C_full, a expansão em dispersão fraca, o mapa de duração/janela e o mapa G2 que inclui u=1.

**Estado científico:** os resultados apresentados são mapas de médias/covariâncias em parâmetros fixos e métricas entre as normais reais definidas por esses momentos. A inferência C08 posterior ao C07 é um produto separado em execução. Este pacote não aprova o marco C08, não declara SBC32, não atribui viés de massa às discrepâncias de momentos e não transfere a aprovação de um mapa finito a um domínio contínuo.

## Alterações científicas/editoriais

1. Ambas as tabelas agora mostram d_mu². As figuras históricas de deslocamento da média mostram d_mu=sqrt(d_mu²); os arquivos foram preservados e as legendas explicitam a diferença. O arquivo `mean_shift_metric_p_squared.pdf` tem nome histórico, mas o gráfico é da raiz, conforme o escritor original.
2. A expansão de C_beta−B preserva o sinal negativo −u²(1−k⁻²)D_k/2, com y_k fixo. A primeira variação da covariância contém os dois termos da regra do produto para CN própria, sem fator 2 gaussiano real adicional. Sinal e ruídos são mantidos em C_GR,k.
3. A ilustração de frequências efetivas agora exige tanto Gamma_GR quanto D independentes do canal. Apenas D comum não basta para fatorar a parcela da covariância composta pelo sinal se Gamma_GR,k ainda variar com as fases.
4. A comparação C_beta→C_full é pequena no mapa T/janela até u=.995; essa conclusão é explicitamente limitada. No mapa adicional em T=4.5 e retangular, seu KL máximo em u=1 é 1.384104..., e não ~3e−4. Não há contradição: os domínios são diferentes.
5. No endpoint u=1, beta_ref=0 nas duas aproximações, enquanto B tem beta=0 somente em k=1. Os demais canais de B mantêm sqrt(1−k⁻²). A expressão analítica de Gamma em beta=0 retém as fases de pulsar.
6. Hann significa somente a projeção complexa linear nos quatro modos positivos do processo periódico bandlimited definido. O operador correto nas unidades normalizadas é D^(-1/2) S D^(1/2). Não se assume TOA irregular, janela arbitrária ou ajuste do modelo de temporização. A covariância entre frequências é preservada; a pseudocovariância zero é própria desta projeção.
7. A guia u⁴ e as razões de restos são descritivas. Duas razões com denominadores abaixo da guia de roundoff continuam sem valor; a guia não é um limite matemático de erro. C_full−B não é forçado a uma expansão sem termo constante em u².

## Arquivos de entrega

- `07_resultados_compressao.tex`: capítulo integrado, 503 linhas; usa cinco PDFs existentes. Não incluir também os dois antigos trechos separados, pois duplicaria as seções.
- `claims.json`: 18 grupos de afirmações numéricas/formais, com valores completos, localização e SHA de cada fonte. Valores percentuais do capítulo são 100 vezes as frações dos CSVs. Os máximos de cada coluna são independentes.
- `port_manifest.json`: lista exata de 48 arquivos, origem→destino, função, tamanho e SHA. Total aproximado de 12.31 MB decimais; inclui fontes do capítulo, cinco PDF e cinco SVG, resumos, momentos salvos, verificações finitas e fontes históricas pertinentes.
- `input_inventory.json`: identidade dos arquivos consultados/portáveis, inclusive os três trechos anteriores e a bibliografia existente.
- `metadata_review.json`: 74 hashes conferidos, todos coincidentes; checagem textual de rótulos/citações, sem teste físico.
- `consolidar_texto.py` e `inventariar_evidencias.py`: receita editorial e inventário, sem importar os calculadores físicos.

Os caminhos de figuras seguem o plano C08: `figures/compressao/mapa_janela/` e `figures/compressao/g2_fraca/`. Os caminhos dos `includegraphics` são relativos ao diretório `latex/`, conforme os capítulos existentes. O ROOT pode adaptar o destino dos resultados ao seu inventário geral, preservando os bytes e registrando a correspondência; os caminhos internos dos manifestos históricos não foram reescritos.

## Mínimo de evidência e limites de replay

O manifesto separa o texto, os resumos/CSVs, as figuras e a evidência física já produzida. `complete.json`, `moments_00/report.json`, `moments_00/arrays.npz` dos dois mapas e os registros de refinamento sustentam as contagens e permitem examinar os momentos salvos. A extensão fraca mantém também `weak_remainders.json`. Os resumos e os escritores originais explicam a conversão desses valores em tabelas e figuras. Os registros prospectivos preservam o domínio e os critérios, mesmo com estado histórico anterior à autorização; não reinterpretar esse estado como resultado de execução.

Esse é um conjunto mínimo de publicação/auditoria dos resultados editoriais, **não um pacote autônomo de replay das quadraturas**. A reexecução inalterada dos executores históricos requer sua árvore de fontes, autorizações, caches de ORF e entradas referidas por hash, tratada pelo inventário global do ROOT. Não são necessários os bancos densos C_beta/C_full para ler/reproduzir os resumos a partir dos momentos salvos; tampouco a existência desses bancos aprova a inferência dos mapas.

## Conferências realizadas nesta tarefa

Leitura científica das fórmulas e domínios; conferência de tabelas por leitura dos CSVs; comparação de hashes registrados; inventário de citações/rótulos. O capítulo não tem rótulos duplicados. As sete chaves bibliográficas já existem em `latex/referencias/referencias.bib`; a única referência externa de capítulo é `chap:validacao`, existente no capítulo C07.

Não foram executados ORFs, verossimilhanças, simulações, testes numéricos, compilação LaTeX ou renderização de figuras. Os registros históricos das figuras são preservados, inclusive o estado `PENDING_VISUAL_REVIEW` em `figures.json` do G2; esta tarefa não o converte em aprovação visual. O ROOT realizará compilação e inspeção cumulativas antes do commit/release.

## Relação com o plano C08

O pacote atende à preparação teórica e aos mapas de duração, janela, espectro e relação sinal/ruído no desenho finito de vértices. Não satisfaz sozinho os critérios inferenciais de comparação pareada de limites, quantificação de erro Monte Carlo ou sensibilidade a resultados nulos. Os sete contrastes e o protocolo posterior prospectivo comunicados pelo ROOT não foram transformados em resultados neste texto. A integração posterior deve manter separados os 24 casos representativos, os oito de estresse e os resumos descritivos das 500 realizações.
