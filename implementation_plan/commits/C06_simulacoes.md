# C06 — Metodologia de simulação e dados sintéticos

- **Commit planejado:** `feat: cria simulador de PTA e desenho experimental`
- **Tag e release:** `v0.6.0`
- **Janela estimada:** 9–10.
- **Dependência:** C05 publicado e validado. As etapas anteriores permanecem incorporadas ao PDF.
- **PDF obrigatório:** `output/pdf/v0.6.0/dissertacao.pdf` — disponível após concluir o marco.
- **Conteúdo acumulado do PDF:** Metodologia e desenho experimental documentados.

## Objetivo

Gerar observações controladas que permitam atribuir diferenças à compressão e à modelagem.

## Trabalho que entra neste commit

1. Definir geometrias sintéticas, duração, canais, janela observacional, espectro e modelos de ruído.
2. Gerar realizações de resíduos ou estimadores espectrais com covariância conhecida e sementes registradas.
3. Implementar estimadores comprimidos com pesos explícitos e guardar os dados em frequência antes da compressão.
4. Planejar a grade em f_g T, sinal/ruído, espectro e distância; medir custo com 10–30 pulsares antes de ampliar.
5. Fixar ambiente, configurações e convenções de armazenamento; versionar amostras pequenas e receita dos conjuntos grandes.

## Arquivos e produtos esperados

- `src/pta/simulation.py`, `src/pta/statistics.py` e `src/pta/geometry.py` (pacote compartilhado com C05)
- `configs/experiments/`
- `docs/dados_sinteticos.md`
- `results/C06/`
- `latex/capitulos_dissertacao/05_metodologia.tex`
- `requirements.txt ou arquivo de ambiente equivalente`

Além desses arquivos, atualizar `project_status.json`, o painel do `README.md`, o estado dos capítulos,
`releases/v0.6.0/RELEASE_NOTES.md`, o PDF e o manifesto da versão. Diretórios científicos
previstos serão criados quando necessários; sua presença neste plano não significa que já existam.

## Critérios de conclusão

- [x] Realizações independentes recuperam momentos esperados dentro de incertezas Monte Carlo.
- [x] Covariâncias são hermitianas/simétricas e positivas no domínio usado; unidades e resposta temporal são consistentes.
- [x] As três análises recebem as mesmas realizações e o mesmo modelo físico de geração.

## Validação exigida

Verificar média, covariância, ausência de sinal, RG tensorial e casos massivos; reproduzir conjuntos a partir de configuração e semente.

## Refinamento após a revisão C03

- Implementar estimadores angulares por frequência e sua compressão, com pesos, tratamento de pares, unidades e covariância documentados. Guardar a estatística anterior à compressão. Fixar os pesos antes de avaliar parâmetros; quando aprendidos dos dados, repetir sua construção em cada realização. Pesos calculados com a verdade injetada são controle idealizado, não análise observacional realizável.

- `docs/contrato_comparacoes.md`, especificando A0/A/B/C; dados de entrada; família probabilística; médias; covariâncias; normalização; suporte espectral; `f_ref`; pesos e variáveis que mudam em cada contraste.

- Mesma binagem angular atua na estatística e na previsão. Propagação dos momentos pelo operador é verificada contra realizações. Gaussianidade de estimadores quadráticos não é presumida pelo fato de o campo gerador ser gaussiano.

O [contrato metodológico da revisão](../../docs/literatura/ajustes_metodologicos.md) define A0/A/B/C. Estes requisitos integram os critérios de conclusão do marco, além dos itens anteriores.

## Risco e decisão de escopo

Se uma análise completa de resíduos exceder os recursos, adotar estimadores espectrais validados, registrando o alcance dessa simplificação.

## Fechamento e publicação

1. Concluir as tarefas e registrar as verificações efetivamente executadas nas notas do release.
2. Atualizar o estado e gerar o README; preparar a versão com o procedimento do [plano geral](../README.md#procedimento-de-fechamento-de-cada-marco).
3. Compilar e inspecionar o PDF completo. Resolver falhas antes de fazer o commit.
4. Incluir fontes, resultados pertinentes, plano atualizado, PDF e manifesto no **mesmo commit**.
5. Criar a tag `v0.6.0`, enviar commit e tag e conferir o PDF anexado ao GitHub Release.
6. Não considerar o marco publicado enquanto o download e seu SHA-256 não forem conferidos.

A aceitação científica é avaliada pelos critérios acima. O sucesso da compilação ou a existência de uma
tag, isoladamente, não significa que os experimentos estejam validados. Correções posteriores seguem a
regra de nova versão descrita no plano geral, preservando o histórico publicado.

## Registro de execução

Concluídos os três controles: massa positiva, GR e ruído branco sem sinal. Cada caso usa 131072 realizações físicas e controles normais pareados, com sementes fixas. Onze testes passaram e os 605 pares necessários às matrizes foram auditados pela interface C05. A covariância e as cumulantes recuperadas mantêm explícita a não normalidade dos estimadores. Os mesmos dados comprimidos alimentam as previsões de B/C_full/C_beta; A conserva os canais, e A0 conserva os coeficientes.

O desenho adota um experimento periódico de Fourier sem ajuste de temporização. A referência de custo utiliza dez pulsares; a extensão prospectiva usa 12 e quatro canais. A configuração declara prioris e recursos. Não foram executadas posteriors ou SBC neste marco. O pacote foi concentrado em `src/pta/` para reutilizar a resposta validada, sem alterar os cinco módulos científicos de C05.

Evidências: `results/C06/`, `docs/dados_sinteticos.md`, `docs/contrato_comparacoes.md` e `docs/validacao_v0.6.0.md`.
