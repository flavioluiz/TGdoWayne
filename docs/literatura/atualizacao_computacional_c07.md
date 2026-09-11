# Atualização computacional e rastreamento de versões

Corte em 10/09/2026. As páginas lidas, versões e SHA-256 dos PDFs estão no
[catálogo](../../literature/catalog.json). Este suplemento acompanha a C07;
não altera retrospectivamente o conteúdo do release C03.

## Alternativa computacional recente

Dwivedi, Shah e Tahbildar (14/08/2026) comparam POCOMC, PTMCMCSampler e
`parallel_bilby` em simulações PTA. Há ruídos cromáticos/acromáticos e processos
comuns; parâmetros brancos são fixados na etapa comum. O exemplo HD com
POCOMC usa um nó de 48 threads e cerca de dez horas. A comparação HD com
PTMCMCSampler não terminou no limite de dez dias do cluster. Os apêndices
comparam posteriores e números de partículas. São testes de desempenho,
sem equivalência direta à nossa geometria, inferência conjunta ou calibração.
[Preprint v1, seções 3–4 e apêndices](https://arxiv.org/abs/2608.13991v1).

Nossa decisão é avaliar qualquer alternativa por custo total, suporte,
normalização, repetições independentes e concordância com referências
numéricas. Gráficos de contorno semelhantes não substituem SBC. A escolha
de um método mais rápido depende de manter o mesmo alvo estatístico e de
quantificar sua precisão. Fluxos normalizantes são uma opção futura; nenhum
pacote desse estudo foi instalado ou executado nesta leitura.

Nota de leitura: na p.2, a Eq.8 omite a inversa interna de Woodbury; a Eq.9
divide pelo determinante interno, em vez de multiplicar. A Eq.5 apresenta
uma raiz dimensionalmente problemática. São inconsistências da apresentação
consultada, sem inferência sobre o código utilizado.
[PDF v1](https://arxiv.org/pdf/2608.13991v1).

## Correção do temperamento paralelo

O [PR58 oficial](https://github.com/nanograv/PTMCMCSampler/pull/58), incorporado
em 21/10/2025, corrige a sobrescrita sequencial de posições e log-likelihoods
durante trocas de cadeias. Buffers separados preservam os valores de origem.
O merge é `f3ea987f95aa78926cd48cc9a3760b8a1f503b7a`. A página apresenta um
controle com verossimilhança gaussiana. Isso identifica uma correção concreta;
não certifica todos os usos do pacote. Não foi estabelecida a revisão do
amostrador utilizada no preprint acima, portanto não se presume a presença
ou ausência dessa correção em seus benchmarks.

O erratum de Agazie et al., publicado online em 31/07/2026, refere-se ao
estudo NANOGrav de 2023 sobre binárias de buracos negros supermassivos.
O resumo editorial relata dois erros de software, pequenas alterações de
posteriores e manutenção das conclusões centrais. Também declara que outras
análises NANOGrav15, incluindo a evidência de fundo, não foram afetadas.
Esse é o alcance declarado pelos autores; não se generaliza a todos os
resultados PTA ou a limites de massa. O PDF não foi obtido: a resposta à
tentativa de download não era PDF. Não se atribui mecanismo ao segundo erro
com base apenas no resumo.
[Metadados e resumo editoriais](https://api.crossref.org/works/10.3847/2041-8213/ae8764).

## Consequência para a aplicação com dados públicos

O [KDE NANOGrav v2.0.0](https://zenodo.org/records/21844115), de 07/08/2026,
publica posteriors espectrais corrigidos e referencia o PR58 e o erratum.
O registro declara exceções às reexecuções, incluindo dois produtos que não
foram refeitos. A aplicação precisa identificar o produto específico e sua
versão, preservando essas exceções. Densidades espectrais e frequências não
fornecem, por si sós, os coeficientes complexos observados ou sua covariância
conjunta. O KDE isolado não reconstrói a comparação A0/A/B/C proposta aqui.

O [registro de fontes sem PDF](fontes_sem_pdf.json) preserva a tentativa
mal-sucedida do erratum. Ele não integra a contagem do acervo baixado. A
investigação de viabilidade observacional permanece separada da execução
das simulações e da validação inferencial.

## Erro de amostragem por importância

Vehtari et al. discutem pesos extremos, diagnóstico de caudas e a variância
de estimadores auto-normalizados. A Eq.5 é uma referência para a fórmula
de influência usada nos nossos testes com sorteios independentes. Um ESS
alto calculado sobre pesos observados não garante que regiões importantes
tenham sido visitadas. O artigo foi acrescentado ao acervo como PDF editorial
de 2024, com leitura dirigida. A suavização PSIS não foi implementada neste
projeto; seus resultados não são atribuídos aos nossos pesos brutos.
[JMLR25(72), pp.1–8](https://jmlr.org/papers/v25/19-556.html).
