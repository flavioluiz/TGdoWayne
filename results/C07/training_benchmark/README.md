# Medição do treino completo com backend nativo

Os seis casos concluíram 8192 passos por quatro trajetórias, seleção fixa de
2048 estados por alvo e EM de quatro componentes. Nenhuma verdade foi lida.
Os dados existentes serviram somente ao benchmark de engenharia: as
trajetórias adaptativas não são apresentadas como amostras posteriores.

| Alvos por lote | Workers | MH completo | LogL e dispatch, incluídos no MH | EM | MH + EM |
|---:|---:|---:|---:|---:|---:|
| 16 | 1 | 22.305 s | 8.052 s | 4.958 s | 27.263 s |
| 16 | 4 | 28.970 s | 14.429 s | 4.915 s | 33.884 s |
| 16 | 6 | 34.443 s | 19.917 s | 4.941 s | 39.384 s |
| 64 | 1 | 58.941 s | 21.852 s | 19.789 s | 78.730 s |
| 64 | 4 | 57.190 s | 19.257 s | 19.643 s | 76.833 s |
| 64 | 6 | 61.172 s | 23.430 s | 19.982 s | 81.154 s |

Dentro de cada tamanho de lote, os estados selecionados, metadados e parâmetros
EM foram idênticos bit a bit entre 1/4/6 workers. A agenda de RNG por alvo e
trajetória é a do produtor portátil, preservada na cópia integral de 51 módulos.
Só a avaliação determinística é distribuída aos workers. Os 80 pontos de
ancoragem, incluindo u=0/1 e todas as famílias, diferiram do kernel NumPy em
no máximo 1.10e−11 em logL. Esta é uma checagem complementar, sem substituir
a auditoria ampla do backend realizada pelo root.

A construção compartilhada demorou 55.02 s. O trabalho de treino compreendeu
7865280 avaliações de logL, mais 560 âncoras nativas e 80 NumPy, abaixo do teto
de dez milhões. Os 240 ajustes EM atingiram exatamente seu teto declarado.
Todas as fontes congeladas e entradas permaneceram inalteradas. O artefato
nativo foi associado à receita de compilação e ao C++ pelos hashes, preservados
em `native_provenance/`.

Recomendação local: 64 alvos por lote de treino, quatro workers para o nativo;
um worker é quase equivalente nesse tamanho (diferença de apenas 2.4%, sujeita
à carga compartilhada). Em lotes de 16, um worker foi claramente melhor.
O número de workers da produção IID em lotes grandes deve ser configurado
separadamente. Não se deve transferir o throughput de 428 mil logL/s do IID
para a sequência adaptativa do treino.

Quarenta lotes completos de 64 cobririam os 2500 alvos de 500 dados × cinco
famílias em cerca de 51.22 minutos, incluindo EM e contando o último lote
parcial como completo. Com 16 alvos, a mesma extrapolação é 71.34 minutos.
O lote de 64 contém aproximadamente a proporção equilibrada das famílias;
o de 16 contém os casos difíceis selecionados do piloto e é menos equilibrado.
São projeções locais, sem garantia de tempo real ou aprovação estatística de
novos treinos. Critérios de convergência continuam necessários em cada alvo.

O pico de RSS Darwin foi 3257303040 bytes, ou aproximadamente 3.034 GiB.
Ele excede em 36.08 MB os 3 GiB nominais usados no orçamento de arrays do
benchmark. Esse orçamento não era um limite garantido de RSS. Recomenda-se
registrar 4 GiB de margem para construção e execução, e continuar medindo.
Não houve alteração de covariância, clipping ou mudança de algoritmo por memória.

O plano portátil atual produz níveis independentes de 16384 e 65536 pontos
por quatro réplicas: são 819.2 milhões de logL de produção, além de cerca de
81.92 milhões do treino. Isso acrescenta 25% ao custo anteriormente apresentado
somente para o nível final. O orçamento total deve também incluir diagnóstico,
I/O e eventuais falhas registradas. Lote de treino 64 não obriga manter 64
posteriores brutas simultaneamente: separar esse tamanho da quota ativa de
produção evita ultrapassar o orçamento de armazenamento.

Entradas e resultados: `config.json`, `execution_manifest.json`,
`frozen_source_manifest.json`, `executed_sources/`, `run.log`,
`results/benchmark_summary.json` e `results/cost_projection.json`.
`run_benchmark.py` reproduz os seis casos; `analyze_benchmark.py` faz apenas
a extrapolação explícita dos resultados já completos.
