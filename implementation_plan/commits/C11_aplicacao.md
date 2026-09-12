# C11 — Aplicação pública ou extensão simulada

- **Commit planejado:** `feat: aplica metodologia a produtos publicos ou benchmarks ampliados`
- **Tag e release:** `v0.11.0`
- **Janela estimada:** 19–20.
- **Dependência:** C10 publicado e validado. As etapas anteriores permanecem incorporadas ao PDF.
- **PDF obrigatório:** `output/pdf/v0.11.0/dissertacao.pdf` — disponível após concluir o marco.
- **Conteúdo acumulado do PDF:** Aplicação e limites observacionais documentados.

## Objetivo

Testar utilidade externa da metodologia com dados disponíveis ou um substituto simulado rigoroso.

## Trabalho que entra neste commit

1. Auditar acesso, licença, formato, informação em frequência e covariâncias dos produtos públicos escolhidos.
2. Se houver produtos suficientes, reproduzir um resultado publicado e aplicar a comparação validada.
3. Se faltarem produtos essenciais, registrar a limitação e ampliar simulações com características observacionais documentadas.
4. Preservar a origem dos dados, versões e receitas de aquisição, sem incluir dados restritos.
5. Comparar conclusões com literatura atualizada e explicitar a diferença entre aplicação e previsão.

## Arquivos e produtos esperados

- `docs/dados_publicos.md`
- `scripts/aplicacao_publica.py ou scripts/benchmark_observacional.py`
- `configs/application/`
- `results/C11/`
- `latex/capitulos_dissertacao/10_aplicacao.tex`

Além desses arquivos, atualizar `project_status.json`, o painel do `README.md`, o estado dos capítulos,
`releases/v0.11.0/RELEASE_NOTES.md`, o PDF e o manifesto da versão. Diretórios científicos
previstos serão criados quando necessários; sua presença neste plano não significa que já existam.

## Critérios de conclusão

- [x] A decisão de ramo é registrada antes de executar a análise e sustentada pela auditoria dos produtos.
- [x] Não se reconstrói artificialmente informação em frequência a partir de correlações já comprimidas.
- [x] Resultados simulados permanecem rotulados como simulação; uma nova restrição observacional exige dados e validação adequados.

## Validação exigida

Reproduzir benchmark independente e conferir rastreabilidade de dados, configurações e incertezas; atualizar testes afetados.

## Risco e decisão de escopo

A ausência de dados completos não bloqueia o artigo metodológico; restringe as alegações observacionais.

## Fechamento e publicação

1. Concluir as tarefas e registrar as verificações efetivamente executadas nas notas do release.
2. Atualizar o estado e gerar o README; preparar a versão com o procedimento do [plano geral](../README.md#procedimento-de-fechamento-de-cada-marco).
3. Compilar e inspecionar o PDF completo. Resolver falhas antes de fazer o commit.
4. Incluir fontes, resultados pertinentes, plano atualizado, PDF e manifesto no **mesmo commit**.
5. Criar a tag `v0.11.0`, enviar commit e tag e conferir o PDF anexado ao GitHub Release.
6. Não considerar o marco publicado enquanto o download e seu SHA-256 não forem conferidos.

A aceitação científica é avaliada pelos critérios acima. O sucesso da compilação ou a existência de uma
tag, isoladamente, não significa que os experimentos estejam validados. Correções posteriores seguem a
regra de nova versão descrita no plano geral, preservando o histórico publicado.

## Evidência de execução

Campanha: 596 realizações, 10728 posteriores. Auditoria de geração e 396 verificações de agregação aprovadas. Referências diretas: 18. Restauração: 106941 arquivos; 13 casos de componentes aprovados. Consulte `results/C11/statistical_audit.json`, `results/C11/reference_consolidation.json` e `docs/c11_reproducibilidade.md`. A conclusão científica não implica publicação: commit, tag e download do PDF ainda devem ser verificados no fechamento.
