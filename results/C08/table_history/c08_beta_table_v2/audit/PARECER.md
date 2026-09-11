# Parecer independente sobre o preflight C_beta v2

Escopo: leitura de `PREFLIGHT.md`, `preflight.json`, `preflight_corrected.py`
e da evidência v1 pertinente; pequenas verificações algébricas e aritméticas.
Nenhuma quadratura, likelihood, campanha ou reconstrução de spline foi
executada. As fontes e os resultados existentes foram preservados.

Não foi encontrada contradição matemática ou erro de orçamento no plano.
Este parecer não constitui aprovação científica, resultado de gate ou
autorização de construção. A autorização posterior informada pelo agente
responsável é independente deste parecer.

## Constatações

- As malhas propostas têm 9153/9185/9185 nós nos canais 2–4. Os patches
  têm 1089/1121/1121 nós, retendo todos os nós antigos. O encontro é um
  nó existente nos quatro canais, inclusive o canal ROOT preservado.
- Há 36 massas históricas na região. As 72 massas novas são distintas
  entre si e das 143 históricas; 21 estão no patch. São 64 sorteios e oito
  âncoras geométricas, não 72 sorteios aleatórios.
- O ledger existente reproduz exatamente o baseline: 48.508.435.951.296
  produtos reais, 878.592 logL e 2.051.757.104 unidades angulares.
  As parcelas novas conferem: 440.505.844.992 produtos, 516.096 logL
  (73.728 históricos + 442.368 novos) e 5.844.792 unidades angulares.
- A união C1 é coerente com a preservação dos coeficientes externos.
  Os coeficientes usam **x = −β**; o clamp deve usar dΓ/dx, ou o negativo
  de dΓ/dβ. Nas curvas antigas dos canais 2–4, os limites no encontro
  diferem no máximo 5,6×10⁻¹⁷ em valor e 3,6×10⁻¹⁵ em derivada.
- A conversão β→u→β tem arredondamento: o encontro representado é
  β = 0.015624999999998222. Quadraturas e checagens diretas devem usar
  β efetivo recuperado de u, mantendo o y físico e o kernel congelado.
  Dimensionar as ordens por βy não é, por si só, uma prova de convergência.
- Todos os 143 caches históricos existem, têm formas (64, 32) para
  fine/oráculo e possuem uma identidade de construção, um hash de nuisances
  e um hash de observações comuns. Isso verifica consistência dos metadados;
  não substitui a ligação criptográfica completa às matrizes e ao kernel.
- Os hashes publicados dos inputs do preflight e de sua própria fonte
  conferiram na auditoria.

## Condições a implementar antes dos gates

1. Verificar os controles Bernstein da spline reconstruída e da subdivisão
   comum. PSD nos nós não garante PSD entre eles. A classe antiga possui
   fallback linear automático, que pode quebrar C1; a reconstrução deve
   rejeitar falhas, sem clipping nem fallback. Os fine v1 registrados não
   tiveram fallback.
2. Congelar o ledger baseline, os caches históricos, `validation_matrices.npz`
   e o kernel, além das fontes e entradas já listadas. O reuso externo requer
   igualdade bit a bit das matrizes efetivamente usadas e dos polinômios
   pertinentes, identidade das nuisances/observações e a mesma normalização.
3. Manter liberação de arrays por etapas e medição de RSS. A soma informada
   de matrizes, coeficientes comuns e maior base/buffers é 1.020.342.208 bytes,
   inferior a 1 GiB, mas não inclui todas as alocações transitórias.

Os limiares e o diagnóstico reprovado da v1 continuam intactos. O novo fine
ainda precisa passar os gates registrados; este trabalho apenas auditou o
plano e sua evidência de entrada.

`PARECER.json` contém o resumo verificável. `input_hashes.json` registra os
hashes individuais dos artefatos substantivamente consultados e dos 143
caches lidos; a separação mantém o resumo curto.
