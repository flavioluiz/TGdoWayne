# Tabela ORF do piloto12×4

`orf_table_pilot12x4.npz` é a tabela fina usada pela inferência:8.336 nós contínuos em massa e matrizes complexas Gamma de dimensão `(8336,4,12,12)`. O arquivo contém somente `nodes` e `matrices`; pesa42.670.838 bytes. Sua assinatura física e SHA256 estão em `orf_table_manifest.json`.

A interpolação deve usar `EvenThresholdCubicORF(..., coordinate='beta')`: cúbica em `−sqrt((1−u)(1+u))`, derivada zero no limiar beta=0 e condição not-a-knot no outro extremo. Todos os controles Bernstein passaram a tolerância PSD de−1e−12; não houve fallback, recorte de autovalores ou jitter. A priori continua uniforme emu. O pacote exige a geometria, frequências e domínio de prioris congelados em `configs/calibration/pilot_initial.json`; não autoriza reutilização arbitrária em outros experimentos.

A validação final em `dense_local_validation.json` compara4.169 e8.336 nós. Máximo erro absoluto de logL:4,93e−6 em82.240 pontos posteriores;8,82e−4 em4.096 pontos novos da priori;2,10e−4 em333.360 testes nos nós novos;1,95e−5 em11.520 testes associados a144 massas off-grid independentes. A tabela fina versus ORFs calculadas diretamente nessas massas teve máximo2,57e−7. O critério.001 foi mantido. Esses testes finitos não são uma prova analítica de erro global, nem validam um posterior por si.

O refinamento local foi motivado por falhas preservadas das tabelas anteriores, incluindo a primeira malha uniforme8193. Adicionou142 nós, concentrados em beta≤.001953125 e na vizinhança do intervalo474 da malha4097. A nova validação usou uma semente independente. Os relatórios anteriores permanecem no pacote para explicar a decisão.

`cache_inventory.json` registra cada nó e origem local, digest do arquivo e da matriz, erro de construção e backend. Cada matriz empacotada foi comparada bit a bit com sua entrada de cache validada. Os milhares de arquivos de cache e os checkpoints não precisam ser versionados. `executed_sources/` preserva os bytes das fontes verificadas e a versão1 do construtor que produziu a tabela uniforme original; os caminhos internos são históricos.

A receita portátil usa os módulos integrados em `src/inference/` e deve ser chamada da raiz do repositório. Sem `--execute`, mostra somente o preflight:

```sh
.venv/bin/python tmp/c07_sampler/delivery/rebuild_orf_table.py \
  --cache tmp/rebuild_orf_cache \
  --output tmp/rebuilt_orf_table.npz
```

Para reconstruir, acrescente `--execute`. O orçamento separado é de60 trilhões de multiplicações reais,768MiB de arrays de construção e10.000 nós; o preflight prevê49,63 trilhões para os8.336 nós. A construção uniforme original levou31,3min na máquina deste projeto; reconstrução completa depende de CPU/BLAS. O script não sobrescreve saída existente. Metadados e diferenças de BLAS podem alterar o SHA do NPZ reconstruído, por isso a verificação científica confronta matrizes e assinatura dentro da tolerância, preservando também os hashes de ambas as execuções.

A receita reconstrói a tabela e verifica os nós; reproduzir os confrontos de likelihood requer os scripts de validação e o fixture piloto, ambos identificados no manifesto. O coarse é um subconjunto exato de4.169 nós da fine; seus índices são emitidos pela receita, dispensando outro arquivo grande no repositório.
