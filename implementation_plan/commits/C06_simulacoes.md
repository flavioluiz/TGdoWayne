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

- `src/simulation/`
- `configs/experiments/`
- `docs/dados_sinteticos.md`
- `results/C06/`
- `latex/capitulos_dissertacao/05_metodologia.tex`
- `requirements.txt ou arquivo de ambiente equivalente`

Além desses arquivos, atualizar `project_status.json`, o painel do `README.md`, o estado dos capítulos,
`releases/v0.6.0/RELEASE_NOTES.md`, o PDF e o manifesto da versão. Diretórios científicos
previstos serão criados quando necessários; sua presença neste plano não significa que já existam.

## Critérios de conclusão

- [ ] Realizações independentes recuperam momentos esperados dentro de incertezas Monte Carlo.
- [ ] Covariâncias são hermitianas/simétricas e positivas no domínio usado; unidades e resposta temporal são consistentes.
- [ ] As três análises recebem as mesmas realizações e o mesmo modelo físico de geração.

## Validação exigida

Verificar média, covariância, ausência de sinal, RG tensorial e casos massivos; reproduzir conjuntos a partir de configuração e semente.

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
