# Leitor C07 por alvo

`inference.campaign_diagnostics.diagnose_target` recebe um runtime com a mesma
identidade da produção, relatório do alvo, pasta raw, arquivo de verdade,
protocolo e destino explícitos. A execução é read-only quanto aos dados/verdades;
gera somente JSON/NPZ novos, sem alterar a proposta ou iniciar inferência.

A opção obrigatória `truth_loglikelihood_path` referencia o JSON produzido por
`scripts/calcular_logl_verdades.py`, com status
`DIRECT_ORF_TRUTH_LOGL_DIAGNOSTIC_ONLY`, `models`, `shape`,
`log_likelihood[model][datum]`, `data_sha256` e `config_sha256`. A geometria direta
usada para gerar as observações também define a log-verossimilhança na verdade.
O leitor não constrói o banco e não avalia esse ponto pela ORF interpolada.

`diagnose_calibration_target.py` oferece os mesmos argumentos de identidade do
produtor, mais `--production`, `--raw`, `--truth-data`, `--truth-logl`, `--protocol`
e `--output`. Escolha explicitamente um `--target` ou um `--block`. A quantidade
de dados não é hardcoded; a configuração prospectiva500 define2.500 alvos. Um
protocolo separado de engenharia deve usar o número total de alvos selecionados,
mesmos níveis e campos, sem alterar os limiares de precisão.

O NPZ inclui20quantis,26CDFs por nível, PIT6, MCSE e flags, pesos, logZ e erros,
204contrastes de replicações e7de refinamento, além de suas especificações.
`replication_specification[:, :]` tem colunas `(level, measure, replica_a,
replica_b)`: measures0–25 seguem verdade+quatro cortes por parâmetro, depois
logL verdade;26 representa logZ. Índices PIT são `[0,5,10,15,20,25]`.
Os primeiros42contrastes pertencem ao nível menor;162ao maior. O refinamento
segue cincoPITs,logL-PIT,logZ. Isso permite reconstruir verificações por função.

`pit_resolved` indica indicador e MCSE resolvidos, sem afirmar precisão ou
validação externa. `pit_precision_pass` é separado. `weight_deletion_guard_by_level`,
`saturated_weight`, `replication_pass/resolved` e `refinement_pass/resolved`
permitem à síntese construir seu `resolved_for_function` mais forte. Não propagar
a falha de outra função para todos osPITs. O envelope de sensibilidade e famílias
científicas93/62/15 permanecem no protocolo de síntese. Neste leitor, as famílias
numéricas são510.000replicações/17.500refinamentos, alpha=.05 cada.

A massa normalizada de linhas saturadas por `expit` tem limite prospectivo1e−12;
não se exige ausência de linhas. Guardas de pesos e precisão preservam v1. Uma
constante devolve MCSE infinito e unresolved, nunca um passe por MCSE zero.
Nenhuma observação ou alvo é removido. Não há certificado de cauda não observada.

O JSON emitido tem status `NUMERICAL_DIAGNOSTICS_COMPLETE`, todos os hashes,
flags e `raw_release_authorized=false`. A etapa operacional `archive` pode
preservar esse resultado e autorizar retirar raws temporários inclusive para
alvos não resolvidos, mantendo os resultados completos e a receita RNG. Essa
etapa não equivale a aprovação da calibração científica.

Verificação: três testes de núcleo contra v1, fronteiras constantes e unidades;
um teste integrado de producer→reader com hashes e logL direta, que proíbe
chamar o kernel interpolado; todos passam. Comparação real A0d14 nos dois níveis
reproduziu52CDFs e flags, máximo erro1,8648e−17,26/26precisas no nível maior.
O relatório está em `results/real_reader_A0d14.json`. Esses testes são engenharia;
nenhuma das500posteriores foi calculada por este leitor.
