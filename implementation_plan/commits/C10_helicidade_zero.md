# C10 — Extensão com helicidade zero vinculada

- **Commit planejado:** `feat: avalia helicidade zero de Fierz Pauli em PTAs`
- **Tag e release:** `v0.10.0`
- **Janela estimada:** 16–18.
- **Dependência:** C09 publicado e validado. As etapas anteriores permanecem incorporadas ao PDF.
- **PDF obrigatório:** `output/pdf/v0.10.0/dissertacao.pdf` — disponível após concluir o marco.
- **Conteúdo acumulado do PDF:** Extensão de polarizações e seu domínio avaliados.

## Objetivo

Conectar o resultado principal às polarizações adicionais sem introduzir amplitudes escalares incompatíveis com os vínculos.

## Trabalho que entra neste commit

1. Construir a resposta do modo de helicidade zero de Fierz–Pauli e sua combinação de deformações transversal e longitudinal.
2. Tratar amplitudes tensorial e escalar como parâmetros de população sob hipóteses explícitas.
3. Validar limites e normalizações antes de repetir um subconjunto da campanha de compressão.
4. Medir degenerescências entre massa, amplitude escalar, espectro e ruído.
5. Delimitar a extensão no artigo de acordo com a precisão e os recursos disponíveis.

## Arquivos e produtos esperados

- `src/pta/scalar_fp.py`
- `tests/test_scalar_fp.py`
- `configs/scalar/`
- `results/C10/`
- `latex/capitulos_dissertacao/09_helicidade_zero.tex`

Além desses arquivos, atualizar `project_status.json`, o painel do `README.md`, o estado dos capítulos,
`releases/v0.10.0/RELEASE_NOTES.md`, o PDF e o manifesto da versão. Diretórios científicos
previstos serão criados quando necessários; sua presença neste plano não significa que já existam.

## Critérios de conclusão

- [x] A relação escalar é satisfeita no modelo e na resposta derivada; não se ajustam duas deformações do mesmo modo como independentes.
- [x] Recuperação e falsos positivos são avaliados em injeções tensoriais e mistas.
- [x] A interpretação não assume que o modelo completo se torne RG apenas com massa nula.

## Validação exigida

Derivação analítica independente, convergência de ORF, injeções e testes de identificabilidade em cenários selecionados.

## Refinamento após a revisão C03

- Derivar a resposta completa de Fierz–Pauli a partir dos vínculos e do desvio de frequência incluindo observadores, e confrontá-la com Liang–Trodden v3 Eq.(22). Confrontar também as combinações escalares de Bernardo–Ng/PTAfast, compatibilizando teoria e amplitude. A presença de um vínculo transversal/longitudinal por si só tem antecedentes.

- Distinguir a amplitude de população da normalização da polarização e da eficiência de excitação pela fonte. Equipartição e desacoplamento no limite sem massa não são impostos silenciosamente. Declarar se a população é fenomenológica ou derivada de modelo de fonte.

- Subconjunto escalar conserva os controles A0/A/B/C de C06–C09, incluindo covariância. Testar o limite tensorial ao zerar a amplitude escalar; não exigir que o modelo completo de Fierz–Pauli se reduza a RG apenas fazendo a massa tender a zero.

O [contrato metodológico da revisão](../../docs/literatura/ajustes_metodologicos.md) define A0/A/B/C. Estes requisitos integram os critérios de conclusão do marco, além dos itens anteriores.

## Risco e decisão de escopo

Se a extensão não puder ser validada no prazo, documentar o resultado parcial e a redução de escopo; o artigo tensorial permanece o núcleo, e o marco não pode ser descrito como validação escalar concluída.

## Fechamento e publicação

1. Concluir as tarefas e registrar as verificações efetivamente executadas nas notas do release.
2. Atualizar o estado e gerar o README; preparar a versão com o procedimento do [plano geral](../README.md#procedimento-de-fechamento-de-cada-marco).
3. Compilar e inspecionar o PDF completo. Resolver falhas antes de fazer o commit.
4. Incluir fontes, resultados pertinentes, plano atualizado, PDF e manifesto no **mesmo commit**.
5. Criar a tag `v0.10.0`, enviar commit e tag e conferir o PDF anexado ao GitHub Release.
6. Não considerar o marco publicado enquanto o download e seu SHA-256 não forem conferidos.

A aceitação científica é avaliada pelos critérios acima. O sucesso da compilação ou a existência de uma
tag, isoladamente, não significa que os experimentos estejam validados. Correções posteriores seguem a
regra de nova versão descrita no plano geral, preservando o histórico publicado.

## Evidência de conclusão C10

Campanha: 1192 observações, 6344 análises, sem descarte; auditoria em
`results/C10/production_audit/audit.json`, síntese em
`results/C10/population_synthesis/results.json`, Fisher em
`results/C10/fisher_audit/audit.json`. Treze testes de componentes passaram
no workspace e com referências restauradas. O capítulo 9 apresenta os
resultados e as limitações; a conclusão do marco é condicional e não afirma
validação uniforme do contínuo, boa recuperação em todas as células ou
reanálise observacional. A restauração completa e a distribuição dos ZIPs
são descritas em `docs/c10_restauracao_producao.md`.
