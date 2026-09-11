# C07: dados de 96 injeções fixas, sem posteriores

Pacote temporário concluído em 10/09/2026. Usa integralmente os cenários e seeds de `configs/calibration/fixed_scenarios_v1.json`, sem reutilizar as realizações contínuas de priori. A aprovação da produção posterior continua separada; este pacote só construiu dois nós de ORF, gerou observações e verificou sua reprodução.

| Linhas/targets A0 | Cenário | Seed PCG64 | Verdade |
|---|---|---|---|
| 0–31 | massa zero, sinal presente | 707309101 | `(0,-15,13/3,-15.5,0)` |
| 32–63 | próximo do limiar cinemático | 707309102 | `(.995,-15,13/3,-15.5,0)` |
| 64–95 | contribuição gravitacional ausente | 707309103 | `(indefinido,indefinido,indefinido,-15.5,0)` |

O conjunto tem a mesma geometria C07: 12 pulsares, quatro canais, T=4,5 anos, distâncias 300–1000 anos-luz, mesma escala fixa, mesmo ruído e mesmos estimadores. A configuração experimental lista os cinco modelos para satisfazer o contrato do runtime, mas a seleção de posterior futura é exclusivamente `A0_CN`, targets 0…95. Os controles gaussianos são salvos com os mesmos normais latentes para compatibilidade do loader; nenhum deles é selecionado para ajuste neste experimento.

## Arquivos e evidências

- `src/inference/fixed_generation.py`: geração determinística, covariância sem GW por construção, máscaras de verdade e do logL na verdade.
- `scripts/gerar_injecoes_fixas.py`: comandos `preflight`, `build-orfs`, `generate`, `verify`, sem sobrescrever produtos existentes.
- `configs/fixed_experiment_v1.json`: n=96 e os cinco modelos do runtime; conserva o modelo físico de `pilot_initial.json`.
- `configs/fixed_generation_v1.json`: orçamento prospectivo de no máximo três nós e checagens diretas explícitas.
- `results/data.npz`: 96 observações e metadados numéricos.
- `results/orf_construction.json`: fontes, orçamento, resoluções, erros e seis confrontos diretos.
- `results/generation.json`, `verification.json`: hashes, seeds, execução e regeneração bit idêntica.
- `results/executed_sources/`: cópias dos scripts, módulos e configurações usados efetivamente.
- `tests/test_fixed_generation.py`, `results/tests.json`: nove verificações aprovadas, incluindo covariância sem sinal independente, logL CN contra solução matricial completa, streams por cenário, máscaras e loader.
- `CONTRATO_LEITOR_FIXED.md`: adaptação necessária ao leitor de posteriores, ainda não implementada nem executada aqui.

SHA-256 de `data.npz`: `834d95fa2a4c6854ac7cb129255769edca4cc4d563d3db99d8c821e69db78a80`.

Somente **u=0 e u=.995** foram construídos, usando as resoluções harmônicas grossa/fina do C07 e checando dois pares no primeiro canal e um no quarto canal, em cada massa. Não houve construção de banco interpolador ou acesso à tabela 8336. Diferença harmônica máxima: **7,59393e−13**, abaixo de 1e−8; diferença direta máxima: **5,02433e−15**, abaixo de 1e−7. São checagens no domínio explicitamente calculado, sem certificação universal da quadratura. O maior produto de fase é 5585,05361.

Construção e checagens diretas: **24,17 s**. Geração das 96 observações: **0,032 s**. Os limites prospectivos foram respeitados: 2 de no máximo 3 nós, 11.907.653.184 multiplicações reais estimadas de no máximo 20 bilhões, 548.007.296 bytes numéricos estimados de no máximo 805.306.368. A quadratura direta teve proxy 602.727.312 de no máximo 1 bilhão e memória estimada 570.013.120 de no máximo 700 milhões de bytes. São estimativas de recursos, não medições de RSS. A execução usou NumPy/SciPy fixados pelo projeto e `VECLIB_MAXIMUM_THREADS=2`.

No cenário sem GW, a matriz gravitacional é um array de zeros exatos e não há chamada à ORF. A covariância total é exclusivamente ruído vermelho+branco. Não se substitui amplitude zero por um log finito, não se usa massa fictícia e não se calcula `logL(theta_true)` do modelo com sinal usando um vetor inexistente de cinco parâmetros. `truth[64:96,:3]` e `log_likelihood_at_truth[64:96]` contêm NaN com máscaras falsas. Esses NaNs são metadados científicos deliberados; q e ambos os observáveis são finitos.

## Reprodução e integração

Exemplo executado no diretório raiz, preservando produtos anteriores:

```sh
PYTHONPATH=src VECLIB_MAXIMUM_THREADS=2 .venv/bin/python \
  tmp/c07_fixed_scenarios/scripts/gerar_injecoes_fixas.py preflight \
  --project-root . \
  --experiment tmp/c07_fixed_scenarios/configs/fixed_experiment_v1.json \
  --protocol configs/calibration/fixed_scenarios_v1.json \
  --generation-config tmp/c07_fixed_scenarios/configs/fixed_generation_v1.json \
  --output tmp/c07_fixed_scenarios/results \
  --implementation-path tmp/c07_fixed_scenarios/src/inference/fixed_generation.py
```

Na primeira execução, repetir com `build-orfs`, depois `generate`, depois `verify`. Os produtos presentes já passaram por esses comandos. `verify` não altera os dados e grava um recibo novo; para repetir a revisão de um produto já verificado, conservar o recibo anterior e escolher outro diretório de reprodução. O gerador recusa sobrescrever observações ou manifestos existentes. A construção só faz quadratura direta nos dois nós necessários; `validate_direct=False` do construtor genérico evita adicionar seus nós-âncora, sendo seguido pelas seis verificações diretas específicas e obrigatórias deste pacote.

Mapeamento proposto de integração:

| Pacote | Raiz |
|---|---|
| `src/inference/fixed_generation.py` | mesmo caminho |
| `scripts/gerar_injecoes_fixas.py` | mesmo caminho |
| `configs/fixed_experiment_v1.json` | `configs/calibration/fixed_experiment_v1.json` |
| `configs/fixed_generation_v1.json` | `configs/calibration/fixed_generation_v1.json` |
| `results/` | `results/C07/fixed_scenarios/` |
| teste | `tests/test_fixed_generation.py`, ajustando apenas os caminhos do pacote para os caminhos integrados |

Após integração, omitir `--implementation-path`: o script importa `inference.fixed_generation`. Os argumentos dos três JSONs e do destino permanecem explícitos. A troca de caminhos das fontes/configurações exige uma nova reprodução integrada e um novo manifesto; não atribuir ao arquivo original hashes de fontes portadas. Os snapshots preservam os bytes efetivamente executados aqui.

Os 32 experimentos por cenário são um diagnóstico grosseiro de estresse: o desvio binomial em cobertura populacional .9 é 0,05303 e o máximo é 0,08839. Não são SBC de priori contínua e não herdam a precisão 1,34 ponto percentual da campanha separada N=500. Não houve treino, produção de amostras posteriores, PIT calculado de posterior, cobertura empírica, teste de uniformidade ou fator de Bayes neste pacote.
