# Comparação Student/GMM sob o mesmo protocolo IID v1

**Os dois históricos permanecem sem aprovação completa.** A proposta GMM foi ajustada antes das novas amostras, usa nova seed907102101, mesma tabela553 e mesmos16alvos. A componente defensiva tem peso.15 e os pesos usam a densidade completa.

| Proposta | N por réplica | CDFs precisas /416 | PITs precisos /96 | Alvos com6PITs precisos /16 | Brackets A0d14 precisos /20 | Máxima MCSE |
|---|---:|---:|---:|---:|---:|---:|
| Student | 1024 | 10 | 10 | 0 | 0 | 0.053585 |
| Student | 8192 | 130 | 22 | 0 | 10 | 0.026385 |
| GMM | 1024 | 17 | 14 | 0 | 0 | 0.026802 |
| GMM | 8192 | 283 | 52 | 1 | 15 | 0.008519 |

A projeção por finalidade é descritiva: não elimina os20cortes de quantis do protocolo originalmente aplicado. Todos os20brackets foram compatíveis nas duas propostas/níveis; nenhum dos16alvos cumpriu o conjunto histórico completo. GMM8192 passa a guarda de dominância em16/16alvos, contra8/16emStudent8192. Não houve discordância nas famílias de replicações/refinamento de qualquer proposta; isso não garante precisão nem ausência de modos omitidos.

O maior erro de GMM8192 ocorre em A_CN,d4, na mediana de log10EFAC: .008519 (componente IID .004760; entre replicações .008519). O segundo é A_CN,d9, mediana de log10A_GW: .008364. A maior MCSE dentro dos seisPITs de cada alvo não precisa coincidir com o máximo dos26cortes.

## Planejamento sem as verdades

O novo leitor de planejamento examinou uma grade de9probabilidades nos5parâmetros e emlogL, sem carregar campos de verdade. Fixou os cortes usando1024e estimou o erro no8192independente. O máximo foi.008584, em A_CN,d4, corteQ75de logL. A regra de projeção1/√N sem margem pede aproximadamente54mil pontos por réplica e arredonda para65536; uma produção32768teria erro projetado≈.004292.

Foi recomendado aos agentes um próximo benchmark com níveis independentes16384/65536×4e tabela física refinada, condicionado ao congelamento do novo plano pelo ROOT. A margem2 foi mostrada somente como cenário mais conservador, não imposta retrospectivamente. A projeção não transfere precisão a uma nova tabela/proposta nem substitui verificação posterior.

A produção GMM553 consumiu32.98s no registro do produtor, sem incluir o ajuste da proposta. O leitor original levou3.73s e a versão portátil integrada3.55s. A reprodução portátil foi numericamente e logicamente idêntica em todos os campos estatísticos; diferenças de hash/caminho/tempo foram preservadas.

O desenho prospectivo de objetivos, produção sem verdades e envelopeECDF para todos500PITs está em`../PROPOSTA_PRODUCAO_POR_FINALIDADE.md`. Não há posterior SBC500 executada por este pacote.
