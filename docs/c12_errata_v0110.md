# Correções editoriais de v0.11.0 incorporadas em C12

A seção “Desenho executado e alcance” da v0.11.0 descreveu C_beta como velocidade relativa igual a um e
C_full como resposta no limite sem massa. Essa descrição estava incorreta.
O arquivo executado `tmp/c11_pilot16_candidate_v2/semantics.py`, preservado nos
arquivos reproduzíveis da tag, define:

- B: beta_k(u) = sqrt(1 - (u/k)^2), com fase y_k.
- C_beta: beta_1(u) = sqrt(1 - u^2), com fase y_k.
- C_full: resposta B do canal 1, na mesma massa u, com fase y_1.

Assim, as duas aproximações conservam a dependência da massa. A configuração,
os caches, as verossimilhanças e as auditorias foram executados com essas
semânticas. A correção atinge a narrativa, não exige novas simulações e não
altera os números reportados. O capítulo de aplicação e o manuscrito C12
passam a explicitar as fórmulas. A tag v0.11.0 permanece imutável.

Outra correção: menções no estado editorial às próximas versões indicaram
C13/v0.13.0. O plano original sempre definiu C13/v1.0.0, que permanece a meta.
