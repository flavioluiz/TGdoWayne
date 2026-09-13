# Reprodução final — em andamento

A auditoria final separa restauração de arquivos, repetição dos cálculos físicos,
reconstrução das estatísticas e comparação das figuras e tabelas. Um resultado de
restauração ou de teste de componentes não fecha a reprodução populacional.

## Ambiente isolado

`scripts/preparar_reproducao_c13.py --destination <diretório-novo>` exporta a base
científica comprometida na tag v0.12.0 por `git archive`, restaura os arquivos C11
com verificação de SHA-256 e recupera do histórico os documentos prospectivos
exatos exigidos pelos manifestos. Não copia resultados não versionados do diretório
de trabalho. Um diretório já existente é recusado.

Os scripts científicos são executados sem edição por
`scripts/executar_isolado_c13.py`. O adaptador redireciona caminhos absolutos
históricos para a cópia isolada; os bytes e hashes dos arquivos ficam intactos.
Um gancho de auditoria recusa aberturas Python que ainda apontem para a árvore
científica original, com um controle negativo registrado antes de cada execução.
As dependências do ambiente Python são reutilizadas. Isso é uma auditoria de E/S
Python, não um isolamento completo do sistema operacional nem a instalação das
bibliotecas em uma máquina independente.

## Evidência obtida e pendências

- Exportação do commit 587fb5b3e68cee3a311632fa371b11ab47b0467e.
- Restauração de 106.941 arquivos lógicos em dez arquivos ZIP, com hashes conferidos.
- Plano prospectivo C11 recuperado do primeiro commit pelo SHA-256 exigido pelo
  manifesto original; a edição posterior de encerramento não alterou a ciência.
- Reexecução da população C11, comparações numéricas completas, síntese posterior,
  demais campanhas e conferência de figuras/tabelas: ainda não concluídas.

O estado exato de cada execução fica nos recibos em `results/C13`. A dissertação
não recebe a narrativa operacional descrita neste arquivo.

## Verificações já executadas no diretório isolado

Passaram 19 testes e o registro simbólico dos fundamentos, 23 testes da resposta
angular e 11 testes do simulador, incluindo regeneração dos dados salvos de três
campanhas. Esses controles não substituem a reprodução das inferências populacionais.

A primeira execução da população parou na ligação ao documento prospectivo; a
segunda parou no limite de memória, antes de gerar observações. Os recibos foram
preservados. `autorizar_memoria_reproducao_c13.py` cria uma autorização específica
para reprodução com 3 GiB, alterando exclusivamente `RSS_bytes_candidate` no
configurador da cópia isolada. O arquivo original do repositório não é alterado.
O código científico, sementes, população, malhas e tolerâncias permanecem iguais.

## Reprodução completa da população C11

A terceira execução terminou com sucesso. A comparação integral encontrou
15.614 arquivos NPZ com 18.630 arrays, todos idênticos bit a bit aos arquivos da
campanha publicada; os estados aleatórios também foram reproduzidos. Foram
recalculadas 20.855.232 avaliações de verossimilhança e 596 observações.
Os recibos são `c11_population_execution.json`, `c11_population_io.json` e
`c11_population_comparison.json`, em `results/C13`.

O recálculo das 10.728 posteriores e da síntese estatística terminou; a comparação
integral está descrita abaixo.

A reconstrução independente das 1.192 observações escalares passou no diretório
isolado: 500 nulas, 500 da priori conjunta e 192 de recuperação. As verdades
foram reproduzidas exatamente; o maior desvio escalado dos dados foi
4,0878 × 10⁻¹⁶. Essa verificação reutiliza as respostas nodais arquivadas e
não constitui reexecução das respostas físicas nem da inferência escalar.

As integrais escalares dos 6.344 alvos e 2.500 eventos foram reconstruídas
independentemente a partir dos valores armazenados. O maior desvio em log Z
foi 7,11 × 10⁻¹⁵; o maior resíduo de CDF de quantil, 2,74 × 10⁻¹⁴.
A síntese escalar, seus arrays PIT, a auditoria de Fisher e a síntese SBC da
robustez coincidiram exatamente com os produtos publicados.

Também foi reexecutada a reconstrução independente de todas as 5.396 observações
da robustez, com operadores quadráticos branqueados. O resultado científico
coincidiu exatamente com o registro publicado; apenas CPU e RSS diferiram.
Recibos de referência restaurados após a comparação mantêm suas ligações de hash
para auditorias subsequentes; as novas evidências estão em `results/C13`.

## Síntese posterior da aplicação ampliada concluída

As 10.728 posteriores dos 18 grupos foram recalculadas a partir das
verossimilhanças regeneradas. Todos os valores JSON dos registros posteriores,
os hashes dos dados de entrada, as famílias SBC e as estatísticas de recuperação
coincidiram exatamente. Os hashes das fontes também coincidiram; diferenças
permitidas restringem-se às raízes dos caminhos, ao recibo operacional da
produção e ao tempo de execução. Consulte `c11_synthesis_comparison.json`.
Não há execução C11 pendente desta reprodução.

## Síntese tensorial original

Os 125.233 arquivos do pacote compacto foram restaurados em um novo destino.
O script original revalidou todos os 2.500 alvos e recalculou a síntese: 155 testes,
15 contrastes pareados e 243 PITs não resolvidos. Os 14 arrays, ambos os CSVs e
todos os valores do relatório coincidiram com os publicados. A comparação
normalizou exclusivamente a raiz absoluta dos caminhos, inclusive nas chaves
do inventário de fontes, sem excluir nenhum campo numérico.
Recibos: `c07_restoration.json`, `c07_synthesis_io.json` e
`c07_synthesis_comparison.json`. A inferência desde os sorteios brutos não é
reivindicada por essa repetição da síntese.

## Regeneração física escalar e da robustez

A geração escalar foi repetida desde as respostas físicas: 1.000 nós de massa,
30.000 matrizes ORF e 1.192 observações. Os sete arquivos NPY/NPZ coincidiram
byte a byte (`c10_full_generation_comparison.json`). Também passaram nove testes
simbólicos e dez verificações físicas da base harmônica. Isso complementa a
reconstrução independente das integrais, mas não equivale à reexecução de toda a
produção posterior escalar.

Na robustez, os 84 trabalhadores originais foram reexecutados individualmente
sob o adaptador de E/S. Todos os arquivos de respostas coincidiram byte a byte;
o total foi 240,26 segundos de CPU e 264,37 segundos de parede. A comparação
está em `c09_truth_responses_reproduced.json`. A agregação dessas respostas e
as partes restantes da reprodução permanecem sujeitas à auditoria final.

## Figuras e tabelas regeneradas

`conferir_figuras_tabelas_c13.py` executou dez geradores originais no diretório
isolado. Treze PDFs científicos foram comparados por rasterização a 120 dpi,
com igualdade exata de todos os pixels. Cinco arquivos de tabelas coincidiram
byte a byte. Isso evita interpretar datas de criação dos PDFs como divergências
científicas. As entradas numéricas retidas são distintas da prova de regeneração
das campanhas; ambas as evidências precisam ser consideradas. O inventário
`central_products_inventory.json` enumera os demais produtos externos incluídos
no LaTeX e mantém as verificações não executadas como pendentes.

## Conclusão da regeneração dos produtos gráficos externos

Os 29 produtos externos alcançáveis a partir do LaTeX atual foram conferidos:
24 figuras tiveram igualdade exata de pixels a 120 dpi, e cinco arquivos de
tabelas tiveram igualdade byte a byte. Os recibos são `figure_table_replay.json`,
`remaining_figures_replay.json` e `window_figures_replay.json`. As tabelas escritas
diretamente nos capítulos exigem uma conferência separada.

A tentativa inicial da descrição C07 detectou a ausência de um recibo de
publicação exigido por hash; ela não foi tratada como sucesso. Foi criado o
suplemento `results/C13/portability_supplement/c08_window_and_publication.zip`
com 150 arquivos (cerca de 1,8 MB). Os relatórios e arrays do mapa de janelas
coincidem com os hashes do registro C08 já publicado, e o recibo de publicação
coincide com a ligação do G0 arquivado. O suplemento contém também o gerador
original do mapa e seu controle de autorização. Seu manifesto registra cada
arquivo, tamanho e SHA-256. Os releases anteriores permanecem intactos; a
reprodução dessas partes passa a depender explicitamente desse suplemento C13.

O suplemento foi restaurado no diretório isolado antes de repetir os geradores.
As figuras de dispersão fraca, descrição pareada, contraste pareado, prioris,
Fisher analítico e geometria também coincidiram. O controlador executado foi
preservado em `results/C13/remaining_figures_driver.py`, com caminhos históricos
registrados; os recibos de E/S registram cada gerador e seus argumentos.

## Tabelas internas e agregação física da robustez

`auditar_tabelas_internas_c13.py` conferiu dez tabelas e 143 valores,
recalculando seleções, máximos e contagens a partir dos arquivos de resultados.
Cada célula é comparada à precisão decimal exibida; o limite conservador
1,85e-8 é explicitamente identificado como arredondamento superior. Isso
verifica a transcrição, não constitui outra inferência.

Os 164 testes de componentes de inferência passaram no diretório isolado.
A agregação física da robustez foi repetida com os 84 lotes recém-gerados: os
1.765 nós novos e três reutilizados produziram o mesmo `truth_responses.npz`,
byte a byte; os campos científicos do recibo coincidiram exatamente. Somente
CPU e memória diferiram. Recibos: `inference_components_io.json` e
`c09_response_merge_comparison.json`.

## Reprodução física do mapa de duração e janela

O controlador original e seus 43 trabalhadores foram executados no diretório
isolado, com os limites originais, terminando em 59,16 segundos de CPU. Todos
os 79 arrays, os relatórios científicos e os controles harmônicos coincidiram
exatamente. A comparação está em `window_physical_comparison.json`.

O fechamento das dependências exigiu mais dois arquivos de fontes, arquivados
em `portability_supplement/c08_window_source_closure.zip`, com manifesto.
A primeira tentativa parou antes de executar trabalhadores porque o controlador
original exige o conjunto exato de módulos PTA de sua época. Sete módulos
adicionados depois foram temporariamente movidos dentro da cópia isolada,
sem alteração dos arquivos do projeto, e restaurados após o sucesso. A lista
e seus hashes estão em `window_namespace_adjustment.json`. O controlador foi
executado diretamente na raiz isolada; os trabalhadores usam essa mesma raiz,
sem a interceptação individual de E/S aplicada à campanha C09.

## Dispersão fraca e controles independentes de integração

Os 13 trabalhadores originais do mapa de dispersão fraca terminaram com os
limites originais, em 17,28 segundos de CPU. Todos os 99 arrays, os relatórios
científicos e os restos da expansão coincidiram exatamente. O suplemento
`c08_weak_map_closure.zip` preserva 73 arquivos de fontes, entradas e produtos
de referência; cada arquivo é inventariado por SHA-256. A comparação é
registrada em `weak_physical_comparison.json`.

Sete scripts em `scripts/inference_checks/` foram reexecutados no diretório
isolado: integrais CN e gaussianas, caudas com 70 dígitos, guardas, cálculo
de verossimilhança e novas respostas de referência. Os oito relatórios
coincidiram exatamente nos valores científicos, normalizando exclusivamente
o prefixo dos caminhos e seis campos de medição de tempo. As novas evidências
e os recibos de E/S estão em `results/C13/independent_integrals/`. Os relatórios
históricos foram restaurados na cópia isolada após a comparação para conservar
as ligações de hash de verificações posteriores.

A produção posterior escalar completa foi iniciada pelo executor original,
com seu plano inalterado, 6.344 alvos e limite de 7.200 segundos de CPU. O
recibo de tempo da geração histórica foi restaurado depois da regeneração
numérica idêntica, preservando o recibo novo em C13. A comparação integral
ainda aguarda o término da produção.
# Reprodução das derivadas de Fisher no fechamento

No diretório isolado, os 60 vínculos de entrada de
`results/C10/fisher_v4/plan.json` foram verificados antes da execução. O diretório
publicado foi preservado em `tmp/c13_fisher_v4_published`; o novo diretório
`results/C10/fisher_v4` recebeu somente o plano original. Executou-se
`scripts/fechar_fisher_escalar_c10.py --execute` pelo adaptador
`scripts/executar_isolado_c13.py`, com o limite original de 60 segundos de CPU.

O arquivo `derivatives.npz` reproduzido é idêntico byte a byte; o relatório
completo é exatamente igual excluindo somente o campo operacional `CPU`.
Foram recalculados oito pontos, três níveis harmônicos e dez passos de
diferenças finitas. As respostas ORF usadas nesse cálculo foram arquivadas;
esta execução não é uma regeneração dessas respostas. Evidências:
`results/C13/fisher_derivatives_comparison.json` e
`results/C13/fisher_derivatives_io.json`.

Em seguida, `scripts/reproduzir_orf_fisher_c13.py`, copiado para o diretório
isolado e executado pelo mesmo adaptador, regenerou as respostas adicionais
usadas por Fisher: 82 massas, três resoluções, cinco casos e duas polarizações,
totalizando 2.460 matrizes. O executor extrai o bloco de respostas físicas do
script histórico de refinamento e não executa seus cálculos de derivadas
superados. Usa os mesmos núcleos numéricos e confere os vínculos do plano.
O NPZ inteiro coincidiu byte a byte, em 0,79 segundo de CPU, dentro do limite
original de 60 segundos. Recibos: `results/C13/fisher_orf_comparison.json` e
`results/C13/fisher_orf_io.json`. A igualdade dos arquivos de resposta liga
essa verificação à reprodução das derivadas, sem exigir nova execução das
mesmas derivadas apenas para trocar arquivos idênticos.

## Experimento sintético de projeção de timing

A configuração completa está em `configs/experiments/c13_timing_projection.json`.
Em uma cópia com saída ainda inexistente, executar:

```sh
.venv/bin/python scripts/experimento_timing_c13.py
.venv/bin/python scripts/figura_timing_c13.py
```

A primeira rotina exige uma pasta nova e produz `results/C13/timing_projection`;
para uma repetição local sem substituir o resultado, usar `--output` com outra
pasta. A figura lê o resultado canônico. A reprodução isolada usou os mesmos
scripts e configuração, pelo adaptador `executar_isolado_c13.py`. O arquivo
`matrices.npz` foi idêntico, assim como os relatórios científicos excluindo
somente CPU. As duas figuras coincidiram por rasterização e a tabela coincidiu
byte a byte. Os recibos estão nessa pasta de resultados.

O experimento tem dois esquemas temporais e três ajustes pareados, com 20.000
realizações por esquema. A covariância temporal analítica é confrontada com
ruído e modos Fourier gerados separadamente; cada série recebe e ajusta seu
modelo determinístico de timing por mínimos quadrados. O critério de
concordância das 816 entradas de covariância foi definido na configuração
antes da execução. A KL adicional compara distribuições gaussianas de dados,
não posteriores de massa. As campanhas anteriores de inferência permanecem
experimentos periódicos e não foram reinterpretadas como dados pós-ajuste.

## Complementos da primeira revisão científica

Os contrastes condicionais usam os primeiros 50 IDs da população P16K8,
selecionados antes dos contrastes, com parâmetros auxiliares fixados.
A configuração é `configs/experiments/c13_conditional_contrasts.json`.
Após a reprodução da população e de sua síntese, executar
`scripts/contrastes_condicionais_c13.py --clean-root DIRETORIO_ISOLADO` e
`results/C13/conditional_contrasts/verify_inverse.py --clean-root DIRETORIO_ISOLADO`.
Os intervalos são sensibilidades numéricas da inversão de duas CDFs ampliadas
verticalmente por 0,002; não são intervalos de confiança populacionais.
A cópia `density_reference.py` preserva o interpolador da campanha original;
seu hash e os hashes das entradas constam do resultado.

`scripts/figuras_academicas_c13.py` produz onze figuras de apresentação a partir
das sínteses originais, com fontes maiores e painéis divididos. O arquivo
`figures/academicas/plot_values.npz` retém os 53 arrays efetivamente desenhados;
a reprodução isolada confirmou igualdade dos valores e dos pixels PNG.
Os relatórios de figuras históricas continuam documentando as apresentações
anteriores, e não devem ser confundidos com a verificação dessas novas figuras.
