# C04 — Fundamentos teóricos e reprodução do TG

- **Commit planejado:** `feat: valida fundamentos e reproduz polarizacoes do TG`
- **Tag e release:** `v0.4.0`
- **Janela estimada:** 3–5.
- **Dependência:** C03 publicado e validado. As etapas anteriores permanecem incorporadas ao PDF.
- **PDF obrigatório:** `output/pdf/v0.4.0/dissertacao.pdf` — disponível após concluir o marco.
- **Conteúdo acumulado do PDF:** Fundamentos e reprodução analítica concluídos.

## Objetivo

Construir uma base teórica verificável para o modelo de propagação e as polarizações.

## Trabalho que entra neste commit

1. Reconstruir equações e convenções dos capítulos 4–6 e do apêndice do TG, com unidades explícitas.
2. Derivar R_0i0j para ondas planas não nulas e explicitar limites da classificação E(2).
3. Impor vínculos de Visser linear e Fierz–Pauli; derivar a relação entre deformações transversal e longitudinal da helicidade zero.
4. Comparar resultados gerais com Hyun et al. e separar estabilidade dinâmica de contagem cinemática.
5. Expandir as checagens preliminares com derivação simbólica geral e exemplos numéricos documentados.

## Arquivos e produtos esperados

- `latex/capitulos_dissertacao/03_fundamentos.tex`
- `src/polarizacoes/`
- `scripts/reproduzir_tg.py`
- `tests/test_polarizacoes.py`
- `results/C04/`

Além desses arquivos, atualizar `project_status.json`, o painel do `README.md`, o estado dos capítulos,
`releases/v0.4.0/RELEASE_NOTES.md`, o PDF e o manifesto da versão. Diretórios científicos
previstos serão criados quando necessários; sua presença neste plano não significa que já existam.

## Critérios de conclusão

- [ ] Convenções, normalizações e limites são reproduzíveis; identidades são demonstradas, não inferidas só de pontos numéricos.
- [ ] Simetrias de Riemann, Bianchi, perturbação de coordenadas, postos e relação escalar passam nas condições especificadas.
- [ ] Divergências em relação ao TG são explicadas por aproximação, unidade ou convenção, com referência à equação original.

## Validação exigida

Comparação independente entre derivação analítica/simbólica e cálculo tensorial; limites massivo, nulo e de limiar; aritmética exata quando aplicável.

## Risco e decisão de escopo

Não usar a formulação histórica como prova de uma teoria não linear estável, nem pressupor que o limite de massa nula com fontes reproduza RG automaticamente.

## Fechamento e publicação

1. Concluir as tarefas e registrar as verificações efetivamente executadas nas notas do release.
2. Atualizar o estado e gerar o README; preparar a versão com o procedimento do [plano geral](../README.md#procedimento-de-fechamento-de-cada-marco).
3. Compilar e inspecionar o PDF completo. Resolver falhas antes de fazer o commit.
4. Incluir fontes, resultados pertinentes, plano atualizado, PDF e manifesto no **mesmo commit**.
5. Criar a tag `v0.4.0`, enviar commit e tag e conferir o PDF anexado ao GitHub Release.
6. Não considerar o marco publicado enquanto o download e seu SHA-256 não forem conferidos.

A aceitação científica é avaliada pelos critérios acima. O sucesso da compilação ou a existência de uma
tag, isoladamente, não significa que os experimentos estejam validados. Correções posteriores seguem a
regra de nova versão descrita no plano geral, preservando o histórico publicado.
