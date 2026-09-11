# Revisão C++ independente

Ler primeiro `REVIEW.md`: derivação, achados e contrato de integração. Nenhum arquivo do ROOT foi editado. Os fontes e binários auditados estão congelados em`sources/`, com manifests. Este pacote não compila automaticamente o kernel.

Resultados:

- `results/independent_fixtures.json`:480avaliações em matrizes aleatórias/rotações, cinco verificações matemáticas agregadas e dez grupos de negativas.
- `results/physical_review.json` e `physical_arrays.npz`:512pontos posteriores selecionados por seed e400pontos de fronteira/meio emtodos80alvos, recalculados com8336nós.
- `results/guarded_review.json`:34verificações do antecedente; confirmou alias de IDs do chamador.
- `results/owned_review.json`:os mesmos34controles no candidato final, incluindo isolamento de mutações; não há alias de IDs.
- `results/owned_physical_review.json`:candidato final repetiu os912valores físicos, todos bit a bit iguais ao kernel original.
- `results/environment.json`:ambiente, compilador disponível e formato arm64do binário; não inventa flags originais de compilação.

Reprodução a partir da raiz do projeto:

```sh
.venv/bin/python tmp/c07_cpp_review/independent_review.py
.venv/bin/python tmp/c07_cpp_review/physical_review.py
.venv/bin/python tmp/c07_cpp_review/guarded_review.py \
  --module tmp/c07_cpp_review/sources/native_owned.py \
  --output tmp/c07_cpp_review/results/owned_review_reproduction.json
.venv/bin/python tmp/c07_cpp_review/owned_physical_review.py
```

Para preservar todos os resultados, copiar o pacote para outra pasta temporária antes de repetir scripts cujas saídas têm nomes fixos. O ensaio físico leva cerca de55s principalmente na preparação do banco NumPy. Os testes pequenos levam poucos segundos. Não há novas amostras posteriores: os pontos do ensaio físico foram selecionados de um histórico e somente suas likelihoods foram reavaliadas na tabela correta.

Os scripts usam os módulos de referência e dados locais identificados nos hashes. O binário `.dylib` pertence ao ambiente arm64auditado; outra plataforma exige compilação controlada e repetição dos controles pertinentes. O ROOT pode portar as fixtures/testes para a suíte do repositório durante a integração, mantendo a referência NumPy.
