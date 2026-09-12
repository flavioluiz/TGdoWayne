# v0.11.0 — Simulações com posições celestes de catálogo

Entrega C11: dissertação cumulativa com auditoria dos produtos públicos e extensão
simulada P12K4/P16K8. As posições dos pulsares vêm do MeerKAT; distâncias, sinais e
ruídos são sintéticos. Nenhum TOA foi analisado.

- Benchmark da nova geometria aprovado após correção analítica apenas da diagonal;
  tentativas anteriores e tolerâncias preservadas.
- Piloto com 288 posteriores e 18 referências funcionais diretas concluído.
- Campanha com 596 realizações pareadas, 10728 posteriores e 20855232 avaliações
  de log-verossimilhança. Geração auditada a partir das sementes nominais.
- Agregação independente aprovada em 396 verificações. Todos os PITs de massa
  resolvidos nos critérios operacionais; eventos logL indeterminados conservados.
- Famílias Holm separadas: 42 testes corretos, sem rejeição persistente e com três
  indeterminações; 84 testes das aproximações, com uma rejeição persistente e uma
  indeterminação. A rejeição ocorre no PIT logL de A_CN em P12K4.
- Perda média de informação A_G→B_G: 0,06211 ± 0,00477 nat em P12K4 e
  0,10631 ± 0,00695 nat em P16K8; barras são um erro Monte Carlo da média nas
  500 realizações da priori. As 96 verdades fixas não entram nessas médias.
- 106941 arquivos lógicos restaurados e conferidos em diretório separado;
  três testes agregadores, com 13 casos, passaram também nas fontes restauradas.
  Oito ZIPs novos e dois anteriores estão versionados no repositório.

A validação funcional é finita e a inferência mantém ruídos conhecidos. Ausência
de rejeição não demonstra equivalência. Não há restrição observacional de massa.
A restauração comprova integridade e testes de componentes, não a reexecução
integral dos caches físicos em outro diretório. Consulte `docs/c11_reproducibilidade.md`.

Próximos marcos: C12/v0.12.0, discussão, conclusões e manuscrito; C13/v0.13.0,
auditoria final de reprodução e do documento. Não há submissão de artigo.
