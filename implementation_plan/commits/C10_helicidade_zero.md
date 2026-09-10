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

- [ ] A relação escalar é satisfeita no modelo e na resposta derivada; não se ajustam duas deformações do mesmo modo como independentes.
- [ ] Recuperação e falsos positivos são avaliados em injeções tensoriais e mistas.
- [ ] A interpretação não assume que o modelo completo se torne RG apenas com massa nula.

## Validação exigida

Derivação analítica independente, convergência de ORF, injeções e testes de identificabilidade em cenários selecionados.

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
