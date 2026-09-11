# FrozenCoefficientORF v2: revisão do loader

Fonte nova: `src/frozen_coefficient_orf_v2.py`. A fonte v1 foi preservada.
O v2 recebe coeficientes existentes, copia-os e valida a representação, sem
reajustar spline, executar integrais ORF, construir bancos ou avaliar logL.

## Contrato e memória

O construtor recebe **arrays NumPy já existentes**, inclusive `memmap`.
Listas não são convertidas implicitamente, pois isso criaria uma alocação
antes da conferência de orçamento. A API de consulta continua aceitando
vetores/listas e mantém `.nodes`, `.matrices`, `.coeff`, `.alpha`,
`.coordinate_name == 'beta'`, `.location(u)` e `__call__(u)`.

`loader_memory_estimate` examina apenas metadados. O construtor confere seu
resultado contra `maximum_owned_numeric_bytes` antes de copiar ou examinar
valores. Os arrays próprios são float64 para nós/coordenadas e complex128
para matrizes/coeficientes, contíguos e somente leitura depois da validação.

Para N nós, K frequências, P dimensões e t = min(tile, N):

- Arrays próprios persistentes: `16*N + 16*(N + 4*(N-1))*K*P*P` bytes.
- Buffers reutilizáveis: `41*t*K*P*P` bytes, correspondentes a dois tiles
  complexos, um real e um booleano. Vistas desses buffers servem também
  para coordenadas e larguras.
- Resultado de autovalores: até `8*t*K*P` bytes. Cada resultado é liberado
  antes da próxima chamada. Um único controle Bernstein existe por vez.

O limite do loader abrange a soma dessas três parcelas. O relatório fornece
também o pico numérico simultâneo estimado com os **bytes lógicos das entradas
do chamador**. Esse pico exclui os buffers internos de NumPy/LAPACK, overhead
Python, backing allocations maiores que suas vistas, descompressão, consultas
posteriores e bancos/native buffers. Essas parcelas exigem orçamento externo.
Nenhuma dessas estimativas é garantia de RSS.

Finitude, Hermiticidade, endpoints e Bernstein são verificados em tiles;
cada potência do coeficiente é processada separadamente. Todas as falhas
rejeitam a representação, sem clipping ou fallback.

## Continuidade

O padrão exige correspondência dos endpoints às matrizes com erro absoluto
≤1e-11, caracterizando somente a checagem C0 numérica. O guard prospectivo
`require_C1=True` compara derivadas laterais na coordenada **x = −β**, com
`C1_absolute_tolerance=1e-7` por padrão. Quando desligado, curvas toy C0
continuam aceitas. Paridade no limiar permanece um guard separado,
`require_threshold_parity=True`, com erro absoluto da derivada ≤1e-7.

## Verificação realizada

Comando: `VECLIB_MAXIMUM_THREADS=1 .venv/bin/python -B tmp/c08_runtime_design/test_frozen_coefficients_v2.py`

Os 14 testes pequenos passaram. Eles verificam compatibilidade bit a bit com
v1 em caso válido, isolamento das cópias, consultas/API, orçamento antes de
coerção/alocação/finitude, limites instrumentados das operações por tile,
falhas em tiles finais e nas fronteiras, Bernstein negativo entre endpoints
positivos, paridade opcional, e C1 opcional em polinômios analíticos e toy C0.
Não houve construção de banco real, integral ORF, likelihood ou inferência.

O log e o manifesto de hashes estão em `test_frozen_coefficients_v2.log` e
`loader_v2_review.json`. A integração com um runtime real e sua memória total
continuam sujeitas à revisão do responsável.
