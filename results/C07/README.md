# C07 — evidências em desenvolvimento

**Estado:** componentes verificados; a inferência de produção e a calibração PTA ainda não estão concluídas. O release publicado mais recente é C06. A presença destes arquivos não aprova C07.

| Diretório ou arquivo | Conteúdo e alcance |
|---|---|
| `fixtures/` | Dezesseis dados do piloto e matrizes angulares nos nós originais; cópias exatas com inventário |
| `validation/` | Referências independentes de verossimilhanças e integrais condicionais; checagens diretas esparsas de ORF |
| `toy/` | Modelo normal conjugado com posterior analítica, 4096 repetições e prefixo de 500; não é uma PTA |
| `mcmc_toy/` | Processos IID e AR(1), erros de CDF e dependência dos postos; não é uma campanha de inferência PTA |
| `pilot_initial/` | Histórico RQMC e amostragem por importância que não satisfez os critérios de produção |
| `pilot_mcmc_history/` | Três pilotos MCMC com tabelas ainda não aprovadas e precisão insuficiente; falhas preservadas |
| `reference/` | Cubatura independente de A0 na realização 14; referência de quantis/evidência com receitas portáveis |
| `mcmc_optimization/` | Equivalência e desempenho dos diagnósticos de cadeias |
| `generator_review_history/` | Revisão independente do gerador em experimento pequeno; inclui falhas e correções preservadas |
| `iid_toy/` | Razões auto-normalizadas com solução analítica e controle negativo de modo raro |
| `orf_interpolation/` | Tabela final com 8336 nós, controles de paridade/PSD/refinamento e referência em massas independentes |
| `iid_pilot_history/` | Comparação Student/GMM em ORF553; falhas e estimativas de custo preservadas |
| `pilot_iid_approved/` | Piloto de 16 alvos com ORF8336 e416/416 CDFs precisas no nível 65536×4 |
| `prior_predictive/` | 500 observações novas e 503 nós diretos de verdade/âncoras; geração reproduzida, sem inferência concluída |
| `data500_independent_review/`, `truth_interpolation500/` | Reprodução independente dos 500 dados e confronto de 2500 valores de logL nas verdades com ORFs diretas |
| `native_review_history/`, `portable_inference/`, `iid_optimization/` | Kernel nativo, implementação portátil e equivalência dos diagnósticos; controles de normalização e propriedade dos arrays |
| `integrated_engineering/`, `cold_tail_review/` | Ensaio integrado que falhou em 15 dos 416 cortes de CDF; investigação de caudas e reprodução de arquivos preservadas |
| `proposal_broadening/`, `wide16_review/` | Proposta ampliada fixada antes da produção; ensaio independente com 416/416 cortes precisos no nível alto |
| `integrated_wide3/`, `campaign_driver/` | Três alvos de engenharia e executor completo com registro de custos, sementes, identidades e retirada verificável dos arquivos brutos |
| `fixed_scenarios/`, `fixed_operational/`, `fixed_synthesis_review/` | 96 injeções fixas geradas e verificadas, executor com máscaras e síntese condicional testados; posteriores ainda pendentes |
| `sbc_delivery/`, `sbc_sensitivity_review/` | Síntese estrita e análise de sensibilidade numérica verificadas em controles sintéticos; não são resultados SBC dos 500 dados físicos |
| `compact_archive_review/` | Ferramenta de arquivamento e restauração, conferida byte a byte no ensaio integrado de três alvos |
| `validation_evidence.json` | Ligações e hashes das evidências independentes usadas pela síntese; integridade não equivale a aprovação científica automática |
| `component_validation.json` | 164 testes curtos e hashes das evidências, incluindo o transporte fixed96 e os geradores de figuras e tabelas; não aprova a campanha posterior |

O piloto é definido por `configs/calibration/pilot_initial.json`; a produção usa
`prior_predictive_500_v1.json` e `campaign_500_execution_v1.json`. Os protocolos
científicos e numéricos permanecem separados. Os cenários fixos foram registrados
em `fixed_scenarios_v1.json` antes da geração, hoje preservada em
`fixed_scenarios/`; a inferência dessas injeções ainda está pendente.

## Verificar e reproduzir

```sh
make check-inference-components
.venv/bin/python scripts/reproduzir_piloto_rqmc.py --dry-run
```

O primeiro comando executa os testes curtos e confere relatórios e hashes. A reconstrução das integrais condicionais utiliza os scripts em `scripts/inference_checks/`; os dois controles analíticos são reproduzidos por `scripts/validar_diagnosticos_toy.py` e `scripts/validar_diagnosticos_mcmc_toy.py`. Esses comandos escrevem seus relatórios no diretório correspondente; executá-los conscientemente ao atualizar uma evidência. Tempos de parede podem variar com a máquina e a carga.

O piloto RQMC completo tem receita própria no script; não se deve confundir sua reprodução com a aprovação de seus resultados. Os arquivos históricos conservam a identificação das fontes temporárias usadas naquela fase. Novas execuções devem usar destinos separados e identificar suas fontes integradas.

O empacotador `scripts/compactar_calibracao.py` conserva o escopo dos experimentos.
O modo padrão exige os 2500 alvos da campanha principal; `--fixed96` exige
exatamente as 96 injeções A0, sua geração e os diagnósticos com máscaras.
`--engineering` aceita apenas um ensaio explicitamente identificado dessa forma.
Todos os modos exigem conclusão do executor e preservam os alvos não resolvidos,
as receitas RNG e os recibos de retirada dos arquivos brutos. O empacotamento
não valida a posterior nem transforma as injeções fixas em SBC.

## Distinções necessárias

1. Concordância entre duas ordens de uma integral condicional não garante a convergência da integral externa da posterior.
2. Convergência da evidência não garante a dos quantis. As CDFs introduzem limites de integração adicionais que precisam ser resolvidos.
3. Matrizes ORF verificadas em nós discretos não aprovam sua interpolação. Esta deve conservar a estrutura física e resolver as oscilações das fases dos pulsares.
4. Taxa de aceitação, Rhat ou um piso de ESS não substituem uma meta de erro Monte Carlo dos resultados efetivamente reportados.
5. Os benchmarks que repetem dezesseis dados em quinhentas colunas medem custo computacional. Não são quinhentas realizações independentes.
6. A0_CN, A_G e B_G utilizam as famílias corretas de seus experimentos; A_CN e B_CN aproximam as estatísticas quadráticas físicas por normais. Falhas dessas aproximações não são automaticamente efeitos de compressão.

O capítulo `latex/capitulos_dissertacao/06_validacao.tex` permanece em elaboração. Sua inclusão no PDF cumulativo, com resultados de produção e diagnóstico, ocorrerá no fechamento validado do marco.
