# Piloto histórico de integração C07

Oito níveis de RQMC foram executados com 16 verdades contínuas e cinco análises.
As falhas numéricas são preservadas. Estes arquivos não constituem SBC500 nem
aprovação posterior. O relatório `historical_REPORT_BASELINE.md` descreve o
estado naquele ponto do desenvolvimento; suas tarefas prospectivas podem
ter sido superadas por outros resultados C07.

Os JSONs foram copiados byte a byte. `sources_at_integration/` conserva as
fontes ao encerrar a integração do pacote preparatório, incluindo a adição
posterior do preflight das sete verificações angulares diretas. Não se afirma
que essa fotografia corresponda à fonte exata de cada execução anterior.
A versão integrada foi novamente confrontada com referências independentes.

Dados/verdades e cache angular histórico ficam em `../fixtures/`; a
configuração original é `configs/calibration/pilot_initial.json`, e os
refinamentos estão em `configs/calibration/rqmc_refinements.json`.
Os grandes arranjos de pesos intermediários permanecem localmente em
`tmp/c07_integration/results/`, fora do Git. São reconstituíveis com as
configurações, sementes e comandos abaixo; não são tratados como amostras
posteriores IID. Os produtos JSON retêm as estimativas e comparações usadas.

Da raiz, a reprodução usa uma pasta nova e não sobrescreve o registro:

```sh
.venv/bin/python scripts/reproduzir_piloto_rqmc.py --dry-run
.venv/bin/python scripts/reproduzir_piloto_rqmc.py
.venv/bin/python scripts/reproduzir_piloto_rqmc.py --level-file configs/calibration/rqmc_refinements.json --skip-direct
```

A segunda chamada gera novamente os dados/ORFs; a terceira exige que as
checagens diretas já tenham sido concluídas. Não executar a campanha grande
apenas porque a reprodução do piloto terminou. Sementes, suporte e
probabilidade dos modelos são preservados, inclusive quando uma resolução
falha. Os testes de integração determinística e os diagnósticos MCMC estão
registrados separadamente.
