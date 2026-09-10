# C09 — Robustez a prioris, ruído e covariâncias

- **Commit planejado:** `feat: audita prioris covariancias e robustez dos limites`
- **Tag e release:** `v0.9.0`
- **Janela estimada:** 14–15.
- **Dependência:** C08 publicado e validado. As etapas anteriores permanecem incorporadas ao PDF.
- **PDF obrigatório:** `output/pdf/v0.9.0/dissertacao.pdf` — disponível após concluir o marco.
- **Conteúdo acumulado do PDF:** Resultados de robustez e informação dos dados concluídos.

## Objetivo

Determinar quanto dos limites resulta dos dados e quanto das escolhas de inferência.

## Trabalho que entra neste commit

1. Comparar prioris uniformes em massa e massa ao quadrado e logarítmica com corte inferior documentado.
2. Confrontar priori e posterior com métricas de informação e sensibilidade ao suporte.
3. Comparar covariância completa e diagonal, espectros alternativos e contaminantes monopolar/dipolar.
4. Quantificar variabilidade entre realizações do fundo e incertezas de distâncias relevantes.
5. Revisitar a escala h/T do benchmark MeerKAT sem confundir proximidade de quantis com ausência de informação.

## Arquivos e produtos esperados

- `configs/robustness/`
- `scripts/campanha_robustez.py`
- `results/C09/`
- `figures/robustez/`
- `latex/capitulos_dissertacao/08_robustez.tex`

Além desses arquivos, atualizar `project_status.json`, o painel do `README.md`, o estado dos capítulos,
`releases/v0.9.0/RELEASE_NOTES.md`, o PDF e o manifesto da versão. Diretórios científicos
previstos serão criados quando necessários; sua presença neste plano não significa que já existam.

## Critérios de conclusão

- [ ] Conclusões distinguem mudança de parametrização, suporte e informação efetiva.
- [ ] Não se declara que diagonalizar covariância é sempre conservador; a direção do efeito é medida.
- [ ] Limites e comparação de modelos são apresentados com hipóteses suficientes para reprodução.

## Validação exigida

Repetir cenários representativos com prioris e ruídos alternativos; verificar estabilidade numérica das métricas e evidências.

## Refinamento após a revisão C03

- Fatorial separado para covariância completa/diagonal e fixa/variável com parâmetros. Quando variável, incluir log-determinante e avaliar sua adequação probabilística. Medir empiricamente a direção do efeito; não pressupor conservadorismo.

- Distinguir informação da forma angular, da distribuição em frequência e do corte cinemático. Variar priori em massa mantendo constantes os demais elementos da análise; mudanças de medida requerem Jacobiano. Prioris logarítmicas possuem corte inferior próprio e não contêm massa zero.

- SBC e distribuições condicionais de limites são recalibradas para prioris e modelos representativos. Resultado Asimov não é apresentado como distribuição de limites obtida por realizações.

O [contrato metodológico da revisão](../../docs/literatura/ajustes_metodologicos.md) define A0/A/B/C. Estes requisitos integram os critérios de conclusão do marco, além dos itens anteriores.

## Risco e decisão de escopo

Se a massa não for identificável, reportar restrições condicionais e limitação informacional, sem transformar corte da priori em detecção ou limite universal.

## Fechamento e publicação

1. Concluir as tarefas e registrar as verificações efetivamente executadas nas notas do release.
2. Atualizar o estado e gerar o README; preparar a versão com o procedimento do [plano geral](../README.md#procedimento-de-fechamento-de-cada-marco).
3. Compilar e inspecionar o PDF completo. Resolver falhas antes de fazer o commit.
4. Incluir fontes, resultados pertinentes, plano atualizado, PDF e manifesto no **mesmo commit**.
5. Criar a tag `v0.9.0`, enviar commit e tag e conferir o PDF anexado ao GitHub Release.
6. Não considerar o marco publicado enquanto o download e seu SHA-256 não forem conferidos.

A aceitação científica é avaliada pelos critérios acima. O sucesso da compilação ou a existência de uma
tag, isoladamente, não significa que os experimentos estejam validados. Correções posteriores seguem a
regra de nova versão descrita no plano geral, preservando o histórico publicado.
