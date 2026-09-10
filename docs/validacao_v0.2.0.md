# Validação de C02 / v0.2.0

Data: 10 de setembro de 2026. PDF cumulativo: 12 páginas A4.

## Escopo conferido

- Introdução com motivação, continuidade TG2003/artigo2004, pergunta, hipótese, objetivos,
  escopo e organização da dissertação. As alegações de novidade são explicitamente condicionais.
- Distinção entre frequência explícita, compressão consistente e frequência de referência;
  controle separado de distribuição dos estimadores, covariância e informação espectral.
- Capa com identificação provisória solicitada; assunto e versão do PDF corretos.
- Quadro editorial: introdução concluída, demais capítulos planejados. Nenhum resultado estatístico
  futuro é apresentado como executado.
- Dezessete chaves de citação presentes na bibliografia e resolvidas na compilação.
- Compilação pdfLaTeX/Biber concluída sem citações indefinidas ou caixas Overfull.
- Todas as 12 páginas renderizadas com Poppler e revisadas, incluindo equações, tabelas, sumário e referências.

## Revisão do fluxo

Uma revisão independente identificou e motivou a correção de dois problemas: a etapa seguinte
aparecia como não iniciada apesar da pesquisa em andamento; e a verificação de capítulos não
exigia correspondência nos dois sentidos entre capítulo concluído e marco concluído.
A versão inclui estado explícito de etapas em andamento e essa verificação recíproca.
Os scripts conferem README, metadados, estado dos capítulos, inclusão dos capítulos concluídos
e hashes antes da publicação.

## Ensaios dos controles de publicação

Em uma cópia temporária independente da entrega, a verificação aceitou os arquivos íntegros
e rejeitou três perturbações controladas: capítulo ainda planejado em um marco concluído;
capítulo concluído removido dos comandos de inclusão; e PDF alterado após gerar o manifesto.
Nos dois primeiros ensaios, os hashes das entradas modificadas foram atualizados para confirmar
que o bloqueio vinha da consistência editorial e não apenas da comparação de hashes.

## Arquivo inspecionado

SHA-256: `3708a44c0f01012655f7c28bc0944170418c0741865c798699304f8d7aa433f1`.

Os avisos herdados do template não impediram a compilação e foram avaliados pela inspeção visual.
A validação editorial não substitui a futura revisão detalhada C03 nem valida qualquer inferência PTA.
