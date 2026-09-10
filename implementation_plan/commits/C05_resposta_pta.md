# C05 — Resposta de PTA e correlações validadas

- **Commit planejado:** `feat: implementa e valida resposta dispersiva de PTA`
- **Tag e release:** `v0.5.0`
- **Janela estimada:** 6–8.
- **Dependência:** C04 publicado e validado. As etapas anteriores permanecem incorporadas ao PDF.
- **PDF obrigatório:** `output/pdf/v0.5.0/dissertacao.pdf` — disponível após concluir o marco.
- **Conteúdo acumulado do PDF:** Formulação da resposta e validação de ORFs concluídas.

## Objetivo

Obter a resposta observacional tensorial necessária à inferência da massa.

## Trabalho que entra neste commit

1. Derivar resíduos a partir do desvio de frequência dos pulsos, incluindo termos da Terra e do pulsar.
2. Implementar ORFs dispersivas com convenções de direção, fase, normalização e autocorrelações explícitas.
3. Comparar integração angular direta com um segundo método ou expressão analítica compatível.
4. Reproduzir limites aplicáveis de Liang–Trodden e Cordes et al. e o limite tensorial Hellings–Downs.
5. Mapear custo e convergência com frequência, distância e proximidade do limiar.

## Arquivos e produtos esperados

- `src/pta/response.py e src/pta/orf.py`
- `tests/test_orf.py`
- `configs/benchmarks_orf/`
- `results/C05/`
- `latex/capitulos_dissertacao/04_resposta_pta.tex`

Além desses arquivos, atualizar `project_status.json`, o painel do `README.md`, o estado dos capítulos,
`releases/v0.5.0/RELEASE_NOTES.md`, o PDF e o manifesto da versão. Diretórios científicos
previstos serão criados quando necessários; sua presença neste plano não significa que já existam.

## Critérios de conclusão

- [x] As curvas de referência coincidem dentro do erro numérico estimado após compatibilizar normalizações.
- [x] Tolerâncias iniciais propostas: erro relativo 10^-3 fora dos zeros e absoluto 10^-5 na normalização adotada; ajustes devem ser justificados antes da campanha.
- [x] A convergência é demonstrada também nos regimes difíceis; frequências evanescentes e limiar não geram raízes reais artificiais.

## Validação exigida

Refinar quadratura e precisão; comparar métodos independentes e limites conhecidos. Reportar erro absoluto junto ao relativo e seu impacto frente ao ruído.

## Refinamento após a revisão C03

- Fixar Liang–Trodden arXiv:2108.05344v3 (24/07/2026) e Cordes et al. arXiv:2407.04464v2 como versões dos benchmarks. Registrar equação, normalização, unidades e ramo de velocidade em cada configuração; revisão posterior ao artigo original não é uma nova medição.

- Documentar a resposta geral incluindo termos temporais da métrica e quatro-velocidades dos observadores; verificar sua redução tensorial. Deixar a implementação da população escalar para C10, sem transplantar fórmulas antigas de códigos sem comparação com a revisão consultada.

- A normalização não é refixada em cada massa de modo a absorver inadvertidamente o sinal dispersivo. Autocorrelação e coincidência angular de pulsares distintos são tratadas separadamente.

O [contrato metodológico da revisão](../../docs/literatura/ajustes_metodologicos.md) define A0/A/B/C. Estes requisitos integram os critérios de conclusão do marco, além dos itens anteriores.

## Risco e decisão de escopo

Se termos oscilatórios impedirem convergência, usar método apropriado e limitar explicitamente o domínio validado antes de prosseguir à inferência.

## Fechamento e publicação

1. Concluir as tarefas e registrar as verificações efetivamente executadas nas notas do release.
2. Atualizar o estado e gerar o README; preparar a versão com o procedimento do [plano geral](../README.md#procedimento-de-fechamento-de-cada-marco).
3. Compilar e inspecionar o PDF completo. Resolver falhas antes de fazer o commit.
4. Incluir fontes, resultados pertinentes, plano atualizado, PDF e manifesto no **mesmo commit**.
5. Criar a tag `v0.5.0`, enviar commit e tag e conferir o PDF anexado ao GitHub Release.
6. Não considerar o marco publicado enquanto o download e seu SHA-256 não forem conferidos.

A aceitação científica é avaliada pelos critérios acima. O sucesso da compilação ou a existência de uma
tag, isoladamente, não significa que os experimentos estejam validados. Correções posteriores seguem a
regra de nova versão descrita no plano geral, preservando o histórico publicado.

## Evidências do marco concluído

- Derivação e convenções em `latex/capitulos_dissertacao/04_resposta_pta.tex` e `docs/pta/validacao_orf.md`.
- Implementação própria em `src/pta/`, com domínio comum, resolução explícita e aceitação por refinamento.
- 23 testes aprovados; 58 casos de campanha com comparação independente, autos, coerência e zeros HD.
- `configs/benchmarks_orf/c05.json` e `results/C05/checked_benchmark_results.json` fixam as configurações, recursos, erros e hashes.
- Figura vetorial reproduzível em `figures/C05/orf_limites.pdf`.
- Domínio delimitado antes da inferência: fases até `2*pi*1000.125+1`; aprovação empírica por ponto, sem extrapolação silenciosa.
