# C12 — Auditoria da narrativa científica

A revisão integra introdução, resumo, revisão bibliográfica, aplicação, discussão,
conclusões e manuscrito. Os capítulos científicos previamente publicados são
conservados com seu histórico; C13 fará a reprodução final em ambiente limpo.

## Alegações centrais

O script `scripts/auditar_narrativa_c12.py` confere 23 alegações e registra as
entradas por SHA-256 em `results/C12/narrative_audit.json`:

- C07: 243 PITs não resolvidos e dez rejeições persistentes nas aproximações.
- C09: 25956 posteriores, 39 contrastes, 126 testes SBC, dez indeterminações;
  834 PITs de massa e 2287 eventos não resolvidos no conjunto completo.
- C10: 6344 posteriores, onze rejeições persistentes nas aproximações e uma
  indeterminação na família correta.
- C11: 10728 posteriores, famílias 42/84, decisões 0/3 e 1/1, médias pareadas
  de KL e erros Monte Carlo arredondados conforme a síntese auditada.
- C_beta usa beta_1(u) e C_full usa B do canal 1 na mesma massa. Doze casos
  massa/canal são confrontados diretamente com o código executado.

A auditoria detectou uma descrição errada das aproximações na versão anterior,
corrigida e explicada em `docs/c12_errata_v0110.md`. Não foram alterados dados,
tolerâncias ou resultados para obter concordância com o texto.

## Delimitação das conclusões

A discussão responde aos seis objetivos na matriz de rastreabilidade. Distingue
reprodução histórica, contribuição metodológica proposta e resultado numérico.
Calibração não é tratada como prova de aprendizagem, não rejeição não é tratada
como equivalência, e metadados públicos não são tratados como análise de TOAs.
Fisher local e inferência condicional não são chamados de posterior plenamente
marginalizada. Os intervalos numéricos continuam sendo operacionais e finitos.

## Bibliografia e figuras

Os dois antecedentes mais próximos foram reconferidos em suas páginas primárias
arXiv; os PDFs já constam no acervo local, com hashes registrados no recibo
`results/C12/nearest_literature_check.json`. A checagem dirigida não representa
uma busca exaustiva nova. O manuscrito cita também resposta dispersiva e a
metodologia SBC. A figura inglesa usa as mesmas entradas auditadas da figura C11.

Compilação, referências internas e limites das caixas são verificados pelos
scripts de construção. A inspeção dos PDFs verifica a composição visual; ela
não substitui os benchmarks físicos e as auditorias de dados anteriores.
