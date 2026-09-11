# Capítulo completo C09 para v0.8.5

`tmp/v085_chapter.tex` substitui o resumo curto inicial. Reúne **integralmente** o conteúdo científico de `fundamentos_robustez.tex` e `diagnosticos_robustez.tex`, com abertura de capítulo e nova seção detalhando as pendências D2/D3. Aproximadamente2514 palavras. Apenas estes dois arquivos temporários foram escritos nesta tarefa.

## Integração

- Destino natural: `latex/capitulos_dissertacao/08_robustez.tex`; inserir após capítulo7 na dissertação. Título curto de cabeçalho: `Robustez estatística`.
- Registrar C09 como parcial/em andamento; C10/C11 não estão concluídos. Texto é cumulativo até os resultados D1/D1b já calculados.
- Não incluir novamente os dois fragmentos-fonte em paralelo: seus conteúdos já estão concatenados.
- Figuras esperadas, mantidas com os caminhos dos fragmentos: `figures/robustez/prioris_suporte.pdf` e `figures/robustez/fisher_direcao.pdf`. ROOT cuidará dos arquivos e QA.
- Chaves `wang2024graviton` e `zhao2026` confirmadas na bibliografia oficial. Todas as referências internas c09 usadas estão definidas no texto concatenado.

## Ajustes de consistência

O conteúdo dos fragmentos foi mantido, com três ajustes locais de apresentação/precisão: explicitar suporte[0,1] no exemplo do Jacobiano v=u²; apresentar as três prioris/quantis em linhas separadas para reduzir risco de overflow; explicitar que a fórmula u=sqrt(1−β²) usa a frequência de referência1/T, sem atribuir essa escolha particular à análise publicada de Wang.

A seção final distingue D2 prospectivo (comparações pareadas nos mesmos dados) e D3 prospectivo (ruído/espectro/contaminantes/distâncias/variabilidade/calibração). Preserva a atualização de avanço por quantidade: cada função tem gate próprio, e falha de logL não pode ser convertida em PASS pela CDF de massa.18grupos/500realizações/126testes são **plano não executado de C09**, não resultados.

## Números conferidos nos recibos

- D1:325629 avaliações novas;9eventos da tabela resolvidos e5casos com orçamento esgotado.
- D1b:125000valores históricos verificados bit a bit,8099novos;4casos adicionais resolvidos.
- Combinado13/14tablePASS;ID10 pendente;14intervalos físicos[0,1].
- ID10:2399subdivisões;erro0.015034636784667647,meta0.002.
- CPU externa final D1b35.399674s e acumulado484.422282s,544316avaliações. Texto usa35,40s/484,42s. O supervisor interno possui alcance ligeiramente menor; não misturar essas medições.

Não executamos testes, compilação, ORFs, likelihoods, sorteios ou simulações. A leitura de JSONs/TeX e a escrita editorial são as únicas operações novas.

## Fontes consultadas e SHA256

- `latex/dissertacao.tex`: `3fa1e3f0d4ca52bcc492e5036c16fc6be782b7a7ee10d40800cfd66965d6c17e`
- `latex/chapters.json`: `709d57a820e1daf7dbf6650009d25b0d4d6c29bedd1c2e21304e1ab93237238d`
- `latex/referencias/referencias.bib`: `180af3c10fc1228a0326942d2dce616358a8a90ca15fc9aa92f88b0e4983fc16`
- `tmp/c09_ROOT/fundamentos_robustez.tex`: `f1f95b16d5f442a41463f3b613482e05899826b196a401fc8174847bc2d3e483`
- `tmp/c09_ROOT/diagnosticos_robustez.tex`: `0d1d3dcbeb21a779644a56913558402fbc510de3201e5c0ec3aa90000036fc6c`
- `tmp/c09_ROOT/D1_result_review_v1.json`: `402ff35774943d5928f10a688047eadf177cc9cf818592d2352a23022bebe87b`
- `tmp/c09_ROOT/D1b_result_review_v1.json`: `71c8e9f76c58d0d2ed35a68a1dd7038d0a52c2b79887d3273d802b8791383990`
- `tmp/c09_D1b_result_audit_v1/result.json`: `ef42692788c1608b18ca2519fb9e919f8c79658c1296b90b9e0dce81e56f94c2`
- `tmp/c09_D1b_execution_v1/worker/target_10.json`: `4a4f33d279bf6e46a1f2e2f3856f1215b73d64081320dc1adf1ab386565ddd27`
- `tmp/c09_D1b_execution_v1/execution_end.json`: `7e5d60d65e8be39d5881da8d0095bee64617bf17dae15328dd51c84312ba0083`
- `tmp/c09_ROOT/D2_design_review_v1.json`: `eaca77ab8a7ce8557d5240138025fee448a249e3ad889ef65a0d6c709f36393c`
- `tmp/c09_ROOT/D2_pure_component_review_v1.json`: `5c5c4358b1835e31eeb9a4e0d94625bcd0dbd314ab62842435764420888e4388`
- `tmp/c09_ROOT/DECISAO_AVANCO_FUNCIONAL.md`: `445c3b557b1edb989fd57f3262f1a6dccd49be630b097c2a24b53fa043edc627`
- `tmp/c09_execution_design/PROTOCOLO.md`: `25b694531c92868fc930a599ab008c69527893ba9419dc5ce4d3db80e1d1094c`
- `implementation_plan/commits/C09_prioris_covariancias.md`: `829e85f2483c973eb79240ac34e3e7dd5fc3769ad7e9b31fc67fb4b8c9d4ff94`

Texto entregue SHA256: `2a209538ea5d819e11860090b9d932ae12d4216826b533f32b441cf7a1989d8c`.
