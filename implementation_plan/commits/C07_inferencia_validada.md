# C07 — Inferência de referência e calibração

- **Commit planejado:** `feat: valida inferencia com frequencia explicita`
- **Tag e release:** `v0.7.0`
- **Janela estimada:** 10–12.
- **Dependência:** C06 publicado e validado. As etapas anteriores permanecem incorporadas ao PDF.
- **PDF obrigatório:** `output/pdf/v0.7.0/dissertacao.pdf` — disponível após concluir o marco.
- **Conteúdo acumulado do PDF:** Métodos estatísticos e validação básica concluídos.

## Objetivo

Estabelecer uma inferência confiável antes de medir os efeitos das aproximações.

## Trabalho que entra neste commit

1. Implementar a verossimilhança em frequência e parâmetros comuns de massa, espectro e ruído.
2. Incluir RG como hipótese separada e registrar suportes das prioris e tratamento de canais abaixo do limiar.
3. Comparar integração de baixa dimensão com o amostrador utilizado sempre que possível.
4. Executar injeções e calibração baseada em simulação (SBC), além de cenários fixos de interesse.
5. Definir métricas, incertezas Monte Carlo e regras de parada da campanha principal.

## Arquivos e produtos esperados

- `src/inference/`
- `scripts/calibrar_inferencia.py`
- `configs/calibration/`
- `results/C07/`
- `latex/capitulos_dissertacao/06_validacao.tex`

Além desses arquivos, atualizar `project_status.json`, o painel do `README.md`, o estado dos capítulos,
`releases/v0.7.0/RELEASE_NOTES.md`, o PDF e o manifesto da versão. Diretórios científicos
previstos serão criados quando necessários; sua presença neste plano não significa que já existam.

## Critérios de conclusão

- [ ] Amostragem e evidências, quando usadas, têm diagnósticos de convergência e verificações independentes.
- [ ] SBC é compatível com a distribuição de referência dentro da incerteza amostral; eventuais falhas são investigadas.
- [ ] Cobertura em parâmetros fixos é reportada como diagnóstico, sem presumir cobertura frequentista nominal universal para intervalos bayesianos.
- [ ] O número de repetições sustenta a precisão declarada; 500 realizações dão cerca de 1,3 ponto percentual a p=0,9.

## Validação exigida

SBC, recuperação de injeções, comparação com quadratura e repetição de cadeias/sementes independentes; testes sob ausência de sinal.

## Refinamento após a revisão C03

- Implementar referência A0 e controle A de mesma família probabilística que será usada em B/C. Retê-los separados para medir o efeito da aproximação de verossimilhança antes da campanha de compressão.

- SBC sorteia parâmetros da priori; cobertura em valores fixos e P–P condicionais são experiências distintas, com denominadores e incertezas reportados. Tratar massa zero, limite superior unilateral e censura pelo suporte cinemático. Uma previsão Asimov dimensiona recursos, mas não valida cobertura.

- Campanha possui controles com mesma família de verossimilhança e estimadores antes/depois da compressão. Divergências A0–A não são atribuídas a perda de frequência.

O [contrato metodológico da revisão](../../docs/literatura/ajustes_metodologicos.md) define A0/A/B/C. Estes requisitos integram os critérios de conclusão do marco, além dos itens anteriores.

## Risco e decisão de escopo

Não atribuir ao efeito da compressão um viés causado por amostragem inadequada, verossimilhança incorreta ou parâmetro não identificável.

## Fechamento e publicação

1. Concluir as tarefas e registrar as verificações efetivamente executadas nas notas do release.
2. Atualizar o estado e gerar o README; preparar a versão com o procedimento do [plano geral](../README.md#procedimento-de-fechamento-de-cada-marco).
3. Compilar e inspecionar o PDF completo. Resolver falhas antes de fazer o commit.
4. Incluir fontes, resultados pertinentes, plano atualizado, PDF e manifesto no **mesmo commit**.
5. Criar a tag `v0.7.0`, enviar commit e tag e conferir o PDF anexado ao GitHub Release.
6. Não considerar o marco publicado enquanto o download e seu SHA-256 não forem conferidos.

A aceitação científica é avaliada pelos critérios acima. O sucesso da compilação ou a existência de uma
tag, isoladamente, não significa que os experimentos estejam validados. Correções posteriores seguem a
regra de nova versão descrita no plano geral, preservando o histórico publicado.
