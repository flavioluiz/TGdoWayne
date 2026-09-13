# Reprodução científica

Este guia distingue regeneração das respostas e observações, integração de
posteriores, agregação estatística e apresentação gráfica. A situação atual
está em [auditoria_final.md](auditoria_final.md). O histórico das tentativas e
ajustes operacionais foi preservado em
[registro cronológico](historico_editorial/reproducao_c13_registro_cronologico.md).
C13 ainda não está encerrado: os comandos abaixo documentam as partes executadas,
sem converter uma síntese de arquivos existentes em reprodução da inferência.

## Ambiente e entradas

A base científica exportada é `v0.12.0`, commit
`587fb5b3e68cee3a311632fa371b11ab47b0467e`. As versões de Python, NumPy e SciPy
estão registradas em `results/C13/runtime.json`. A execução realizada reutilizou
o ambiente de bibliotecas do projeto e uma cópia isolada das entradas científicas;
não representa instalação em outro sistema operacional.

Para preparar um destino inexistente, a partir do repositório com seu histórico:

```sh
.venv/bin/python scripts/preparar_reproducao_c13.py --destination /private/tmp/tgwayne-reproducao --revision v0.12.0
```

A preparação exporta o commit, restaura as entradas C11 e recupera documentos
prospectivos pelo hash exigido por seus manifestos. Ela não executa a ciência.
Os scripts C13 novos devem ser copiados para a raiz exportada antes de usá-los.
As demais famílias têm restauradores próprios em `scripts/restaurar_*.py` e
manifestos de arquivos publicados. Os 74 ZIPs externos C10 são necessários à
reprodução escalar; seus downloads foram conferidos em
`results/C13/c10_external_archives.json`.

Três suplementos completam dependências ausentes das distribuições anteriores:

- `results/C13/portability_supplement/c08_window_and_publication.zip` e `manifest.json`;
- `c08_window_source_closure.zip` e `source_closure_manifest.json`;
- `c08_weak_map_closure.zip` e `weak_map_manifest.json`.

O restaurador `scripts/restaurar_manifesto_simples_c13.py` confere o ZIP e cada
membro, recusando substituir um arquivo de conteúdo diferente. As ligações
históricas adicionais estão nos recibos `*binding_restoration*.json` e
`historical_binding_restoration.json`. Restaurar esses vínculos não altera os
parâmetros científicos.

## Execução isolada

`scripts/executar_isolado_c13.py` recebe `--original-root`, `--clean-root`,
`--receipt`, o caminho relativo do script e seus argumentos. O script precisa
existir no destino; o recibo precisa ser novo. Caminhos históricos são
redirecionados para a cópia, e um controle negativo verifica que aberturas Python
da árvore científica original são recusadas. Essa proteção cobre E/S Python,
não processos externos ou um isolamento completo do sistema operacional.

Exemplo para a geração tensorial em saídas novas:

```sh
.venv/bin/python scripts/executar_isolado_c13.py \
  --original-root "$PWD" \
  --clean-root /private/tmp/tgwayne-reproducao \
  --receipt /private/tmp/tgwayne-reproducao/tmp/tensorial_orf_io.json \
  scripts/gerar_calibracao.py build-orfs \
  --output /private/tmp/tgwayne-reproducao/tmp/tensorial_nova \
  --construction-cache /private/tmp/tgwayne-reproducao/tmp/tensorial_orf_nova
```

Depois da construção, a ação `generate` do mesmo script usa a mesma saída.
`verify` regenera observações de um produto já existente. Os recibos `*_io.json`
retêm o script, seu hash e os argumentos efetivamente executados para as outras
famílias. Os nomes de destino nesses recibos identificam aquela execução; uma
repetição deve usar saídas novas e ajustar os argumentos dependentes.

## Cadeias de reprodução e evidências

| Família | Cadeia executada | Evidência principal em `results/C13` |
|---|---|---|
| Fundamentos, resposta e simulador | Regeneração e 19 + 23 + 11 testes | `c13_reproduzir_tg.py.json`, `c13_validar_orf.py.json`, `c13_validar_simulador.py.json` |
| Aplicação ampliada | Respostas → 596 observações → verossimilhanças → 10.728 posteriores → síntese | `c11_population_comparison.json`, `c11_synthesis_comparison.json` |
| Escalar | Respostas → 1.192 observações → 6.344 posteriores → síntese | `c10_full_generation_comparison.json`, `scalar_full_production_comparison.json`, `scalar_fresh_synthesis_comparison.json` |
| Integrais escalares arquivadas | Integração independente de 6.344 alvos e 2.500 eventos | `C10_production_audit.json` |
| Fisher escalar | Respostas adicionais → derivadas → matrizes de informação | `fisher_orf_comparison.json`, `fisher_derivatives_comparison.json` |
| Robustez | Respostas → observações → 25.956 posteriores; síntese ligada aos novos arquivos idênticos | `c09_nominal_inference_comparison.json`, `distance_posterior_replay/comparison.json`, `c09_synthesis_regenerated_binding.json` |
| Tensorial original | 503 respostas e 500 observações regeneradas; síntese dos 2.500 alvos arquivados | `c07_generation_comparison.json`, `c07_synthesis_comparison.json` |
| Dispersão fraca e duração | Respostas e momentos regenerados | `weak_physical_comparison.json`, `window_physical_comparison.json` |
| Referências de integração | Sete scripts e oito relatórios recalculados | `independent_integrals/comparison.json` |

A aplicação ampliada usa o script restaurado `tmp/c11_production_v1/run.py`,
seguido de `synthesize.py`. Sua execução isolada precisou de 3 GiB de limite RSS,
conforme `c13_memory_allowance.json`; somente esse limite operacional mudou.
Os arrays científicos e estados aleatórios coincidiram com os originais.
O script `autorizar_memoria_reproducao_c13.py` registra essa alteração na cópia.

Na produção escalar, os executores originais são
`gerar_populacao_escalar_c10.py --execute` e
`executar_campanha_escalar_c10.py --execute`. Os manifestos vinculam a geração à
produção: preservar os novos recibos antes de restaurar um recibo histórico
byte a byte para satisfazer uma ligação existente. A comparação de respostas
já demonstrou a igualdade dos dados; a produção e sua nova síntese passaram nas comparações integrais, com 11.392
arquivos de produção e dez arrays PIT idênticos.

A repetição da síntese C07 e dos testes SBC C09 não demonstra, sozinha, repetição
dos sorteios e de todas as integrações originais. A inferência bruta C07 está em execução (`c07_current_execution.json`); a C09
foi reexecutada e seus arquivos de posteriores coincidiram com os hashes das
entradas da síntese, conforme `c09_synthesis_regenerated_binding.json`.

## Experimentos acrescentados na revisão

O teste de timing usa `configs/experiments/c13_timing_projection.json`:

```sh
.venv/bin/python scripts/experimento_timing_c13.py --output /private/tmp/timing-novo
```

São 20.000 realizações por esquema temporal, com três ajustes pareados. A
covariância analítica é comparada à de séries simuladas e ajustadas uma a uma.
Para gerar as figuras canônicas, `scripts/figura_timing_c13.py` lê
`results/C13/timing_projection`. Matrizes, tabela e figuras foram reproduzidas;
os recibos ficam nessa pasta. A KL compara distribuições de dados, não posterior
e priori de massa. As campanhas anteriores permanecem periódicas.

Os contrastes condicionais usam os primeiros 50 IDs P16K8 e ruído fixado:

```sh
.venv/bin/python scripts/contrastes_condicionais_c13.py --clean-root /private/tmp/tgwayne-reproducao
.venv/bin/python results/C13/conditional_contrasts/verify_inverse.py --clean-root /private/tmp/tgwayne-reproducao
```

Esses scripts esperam os produtos regenerados em
`tmp/c13_population_reproduced_third` e `tmp/c13_synthesis_reproduced`, conforme
os argumentos da reprodução C11. A configuração está em
`configs/experiments/c13_conditional_contrasts.json`. São sensibilidades da
inversão de duas CDFs ampliadas verticalmente por 0,002, não intervalos de
confiança populacionais. O interpolador original está preservado em
`results/C13/conditional_contrasts/density_reference.py`, com hash registrado.

## Figuras, tabelas e PDFs

As apresentações históricas foram conferidas separadamente: 24 PDFs por pixels
a 120 dpi e cinco arquivos de tabelas por bytes. O inventário está em
`central_products_inventory.json`. Onze tabelas internas e 159 células foram
comparadas aos resultados e ao arredondamento exibido em `inline_tables_audit.json`.
Essas verificações não abrangem automaticamente adições posteriores.

`scripts/figuras_academicas_c13.py` desenha onze figuras com os mesmos dados e
intervalos, preservando os 53 arrays utilizados em
`figures/academicas/plot_values.npz`. A reprodução confirmou igualdade dos arrays
e dos pixels PNG (`academic_figures_reproduction.json`). As figuras e a tabela
de timing têm recibos próprios; a tabela condicional tem resultado e verificação
de inversão em `conditional_contrasts`.

`make pdf` compila a dissertação em `tmp/latex/dissertacao`. A cópia em
`output/pdf/conferencia` é uma prévia local, não um release. A inspeção integral
está em `final_pdf_visual_review.json`. O release v1.0.0 inclui seu próprio
PDF e manifesto; o arquivo baixado do GitHub deve coincidir com o hash publicado.

## Reprodução tensorial integral

A preparação resolveu as onze entradas pelos hashes originais e conferiu o
plano de 2.500 alvos e 901.130.000 avaliações. O binário nativo original foi
copiado para `tmp/c13_c07_native_reference`, com hash registrado em
`c07_native_reference.json`; esta execução não prova compilação independente.
O pacote PTA histórico tem oito módulos. Para preservar sua identidade sem
alterar a execução escalar simultânea, `c07_frozen_driver.py` carrega uma cópia
privada desse pacote e executa o controlador original sem modificações.
As identidades do runtime e do controlador coincidiram exatamente com o plano
publicado. `c07_current_execution.json` registra o término e a comparação
integral da campanha.

O inventário `current_products_inventory.json` lê o arquivo `.fls` da compilação
e confere os 34 produtos externos atuais: 28 figuras e seis arquivos de tabelas.
Arquivos históricos inalterados mantêm sua evidência; apresentações novas foram
comparadas aos PDFs regenerados por pixels a 120 dpi, e tabelas por bytes.

A verificação parcial `c07_partial_128.json` compara os primeiros 128 alvos da
inferência tensorial: 1.024 resumos de réplicas e 3.072 arrays descritivos iguais.
Os hashes de propostas diferem porque incluem tempo de execução; cada hash foi
validado antes de comparar os campos científicos. Essa conferência inicial
detecta divergências antes de terminar a campanha e não substitui a comparação
integral ao final.

## Inferência de robustez concluída

`reproduzir_inferencia_robustez_c13.py --clean-root DIRETORIO` executa os 24
lotes nominais, de autocontrole e de refinamento, em saída nova.
`comparar_inferencia_robustez_c13.py` compara as 22.957 linhas, incluindo a
substituição de uma posterior, e os 72 arrays de verossimilhanças salvos.

`reproduzir_distancias_posteriores_c13.py --clean-root DIRETORIO` preserva as
saídas anteriores de distância, executa as 12.145.500 avaliações e usa a rotina
original de integração em blocos. O produtor monolítico reproduz sua parada
histórica por memória depois de salvar os componentes; a recuperação separada
conclui as 3.000 posteriores. Os 15 arrays de componentes, as 13.500 referências
SciPy e todas as posteriores coincidiram. O atlas angular de distância é uma
entrada existente, não regenerada por esse executor.

Os recibos desse adaptador devem ser gravados dentro do diretório isolado e só
então copiados para o projeto. A primeira tentativa calculou os produtos mas
falhou ao finalizar os recibos fora desse diretório; a repetição corrigida e os
resultados originais foram preservados em `distance_posterior_replay`.

### Fechamento da inferência tensorial

`scripts/comparar_inferencia_tensorial_c13.py --clean-root /private/tmp/tgwayne-c13-clean-20260913`
exige o recibo terminal dos 2.500 alvos e compara propostas, oito réplicas por
alvo, diagnósticos, estados e arrays. Os vínculos de arquivos são verificados
localmente antes de normalizar os hashes derivados de tempos de execução.
A opção `--prefix 1152` foi executada com sucesso e constitui apenas uma
comparação parcial: 9.216 réplicas e 80.640 arrays. A execução sem essa opção
concluiu a comparação integral, conforme o resultado abaixo.

A leitura visual integral das 167 páginas da dissertação foi concluída;
`results/C13/final_pdf_visual_review.json` identifica o PDF atual e as páginas
reexaminadas individualmente após a última limpeza editorial.

Após a comparação integral, executar
`scripts/sintetizar_tensorial_reproduzido_c13.py --clean-root /private/tmp/tgwayne-c13-clean-20260913`.
O script usa o sintetizador original em isolamento, confere os vínculos de
proveniência em cada diretório e compara o JSON científico, os 14 arrays e os
dois CSVs. Sua execução concluiu com sucesso e está registrada em
`c07_fresh_synthesis_comparison.json`.

## Resultado final da reprodução tensorial

Concluída com os 2.500 alvos e 901.130.000 avaliações previstos.
`c07_inference_full_comparison.json` confirma 20.000 réplicas e 175.000 arrays
iguais. `c07_fresh_synthesis_comparison.json` confirma a síntese dos produtos
regenerados: 155 testes, 15 contrastes, 14 arrays e dois CSVs iguais.
As referências anteriores a verificações parciais descrevem o procedimento
realizado durante a execução; não representam pendências atuais.
