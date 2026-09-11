# C08 — Resultados sobre compressão em frequência

- **Commit planejado:** `feat: quantifica efeitos da compressao em frequencia`
- **Tag e release:** `v0.8.0`
- **Janela estimada:** 12–14.
- **Dependência:** C07 publicado e validado. As etapas anteriores permanecem incorporadas ao PDF.
- **PDF obrigatório:** `output/pdf/v0.8.0/dissertacao.pdf` — disponível após concluir o marco.
- **Conteúdo acumulado do PDF:** Primeiro capítulo de resultados científicos concluído.

## Objetivo

Responder à pergunta principal comparando perda de informação e aproximação do modelo comprimido.

## Trabalho que entra neste commit

1. Executar as três análises sobre as mesmas injeções: frequência explícita, compressão consistente e frequência de referência.
2. Comparar limites de massa, forma das posteriores, viés e evidências somente quando calibradas.
3. Medir discrepância em unidades do ruído, incluindo Delta C^T Sigma^-1 Delta C.
4. Mapear regimes por f_g T, espectro, duração, janela e sinal/ruído.
5. Produzir figuras e tabelas diretamente dos resultados e registrar casos em que a aproximação é adequada.

## Arquivos e produtos esperados

- `scripts/campanha_compressao.py`
- `configs/compression/`
- `results/C08/`
- `figures/compressao/`
- `latex/capitulos_dissertacao/07_resultados_compressao.tex`

Além desses arquivos, atualizar `project_status.json`, o painel do `README.md`, o estado dos capítulos,
`releases/v0.8.0/RELEASE_NOTES.md`, o PDF e o manifesto da versão. Diretórios científicos
previstos serão criados quando necessários; sua presença neste plano não significa que já existam.

## Critérios de conclusão

- [ ] A diferença entre compressão e modelagem aproximada é isolada com controles compartilhados.
- [ ] Conclusões incluem incerteza Monte Carlo, convergência e condições de validade.
- [ ] Um resultado nulo inclui limites quantitativos para efeitos que a campanha conseguiria detectar.

## Validação exigida

Comparações pareadas, repetição de cenários centrais, controles não dispersivos e inspeção dos casos próximos ao limiar.

## Refinamento após a revisão C03

- Executar A/B/C nas mesmas realizações e comparar também com A0 em cenários centrais. Relatar separadamente A0–A, A–B e B–C, segundo o contrato de comparações aprovado em C06.

- Evidências devem preservar normalizações e ser comparadas como fatores de Bayes entre hipóteses no mesmo espaço de dados. Não subtrair evidências absolutas de A e B como se fossem um único fator de Bayes.

- Definir se C troca a ORF somente na média ou também na covariância do sinal. Uma troca somente na média mantendo massa dispersiva na covariância é ablação explicitamente denominada; a análise de frequência única completa deve aplicar a escolha consistentemente. Não alterar ao mesmo tempo o suporte dos canais sem uma experiência própria.

- Mapa de validade quantitativo em massa, espectro e sinal/ruído inclui diferença de limites, calibração, erro Monte Carlo e erro numérico. Posterior mais estreita ou mera diferença entre Gaussian e Whittle não satisfaz a pergunta principal.

O [contrato metodológico da revisão](../../docs/literatura/ajustes_metodologicos.md) define A0/A/B/C. Estes requisitos integram os critérios de conclusão do marco, além dos itens anteriores.

## Risco e decisão de escopo

Se não houver efeito relevante, o produto será o domínio de validade; não escolher apenas cenários favoráveis à hipótese de viés.

## Fechamento e publicação

1. Concluir as tarefas e registrar as verificações efetivamente executadas nas notas do release.
2. Atualizar o estado e gerar o README; preparar a versão com o procedimento do [plano geral](../README.md#procedimento-de-fechamento-de-cada-marco).
3. Compilar e inspecionar o PDF completo. Resolver falhas antes de fazer o commit.
4. Incluir fontes, resultados pertinentes, plano atualizado, PDF e manifesto no **mesmo commit**.
5. Criar a tag `v0.8.0`, enviar commit e tag e conferir o PDF anexado ao GitHub Release.
6. Não considerar o marco publicado enquanto o download e seu SHA-256 não forem conferidos.

A aceitação científica é avaliada pelos critérios acima. O sucesso da compilação ou a existência de uma
tag, isoladamente, não significa que os experimentos estejam validados. Correções posteriores seguem a
regra de nova versão descrita no plano geral, preservando o histórico publicado.
