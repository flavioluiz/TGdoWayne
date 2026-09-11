# Driver operacional fixed96, revisão 2

Entrega temporária concluída; nenhum arquivo versionado do produtor, runtime, ledger ou arquivador foi modificado. Não foram executados treino nem posteriores dos96dados. O único contato com a infraestrutura física na nova revisão foi o preflight do runtime existente, com dados96, a tabela8336 já validada e sem construir um banco de momentos.

## Mudanças delimitadas

- `src/inference/fixed_diagnostics_v2.py`: conserva os corpos numéricos do leitor v1. Muda o nome dos produtos para `diagnostic_target_XXXXXX.{json,npz}` e o status para `NUMERICAL_DIAGNOSTICS_COMPLETE`, aceito pelo arquivador genérico. O schema é `C07_FIXED_MASKED_IID_DIAGNOSTICS_v2_OPERATIONAL` e o scope é `FIXED_TRUTH96_NOT_SBC`. Máscaras, NaNs, distinção estrutural, MCSEs e denominadores permanecem iguais. Comparação AST dos cinco corpos de cálculo/validação confirma sua identidade.
- `scripts/run_fixed_campaign.py`: usa o `CampaignRuntime` e as funções ROOT de treino, produção, arquivo e liberação, sem variantes dessas31fontes. Reutiliza `Ledger`, lock exclusivo e verificação dos alvos concluídos de `scripts/run_calibration_campaign.py`. Seu pequeno laço mantém a mesma sequência por alvo: produção, diagnóstico mascarado, arquivo íntegro, liberação dos oito raws, registro imutável do alvo. O treino continua por blocos e há um único runtime por processo.
- `configs/fixed_campaign_prospective_v1.json`: n96 é determinado pela configuração experimental; seleciona somente A0, targets0…95. Os níveis16384/65536×4 e os budgets estão explícitos. Treino está `steps=null`, `approved=false`, e execução está desativada enquanto o root escolhe a proposta/comprimento finais. O driver é parametrizado pelo JSON e não escolhe esse comprimento.
- `configs/fixed_diagnostics_v1.json`: protocolo numérico anterior, sem mudança: famílias conservadoras19584/672. A revisão operacional não renomeia nem relaxa esse protocolo.

O leitor v1, seus testes/documentação e manifestos estão preservados em `archive/masked_reader_v1/`. O primeiro preflight do driver está em `archive/driver_preflight_v1/`; a revisão final acrescenta verificação de fontes/entradas antes do treino e antes de qualquer arquivo/liberação. Use o manifesto final, não atribua à execução anterior esses controles adicionais.

## Identidade, máscaras e arquivo

A CLI recebe `--generation` explicitamente. Não há argumento `--truth-logl`, nem um campo com esse nome usado para representar falsamente o manifesto de geração. O dado, seu hash, o manifesto de geração, o protocolo mascarado e as fontes do driver/leitor formam uma identidade canônica adicional ao runtime. A prévia verifica também o inventário declarado:64verdades definidas para os três parâmetros de GW,96para os dois de ruído,64logL-na-verdade e os três intervalos de32linhas.

O preflight lê somente observações e metadados; não desserializa `truth`. A leitura da verdade continua exclusiva de `diagnose_fixed_target`, mediante o arquivo explícito. `driver_provenance/<driver_identity>/` preserva fontes próprias, fonte do driver base, protocolo e manifesto de geração. O runtime preserva as fontes/configurações originais pelo seu mecanismo existente. Os hashes são verificados antes do trabalho e antes de arquivar cada alvo.

Antes de chamar `prepare_archive`, o driver exige o schema/escopo mascarado e a mesma SHA do manifesto de geração. Um diagnóstico da campanha500 ou um produto sem máscaras não atende esse contrato. O arquivador ROOT copia o JSON e NPZ completos, a proposta e os oito checkpoints/RNG, preservando também alvos numericamente não resolvidos. A decisão de liberar raws é de integridade e reprodutibilidade; não exige uniformidade, não elimina o alvo e não afirma calibração. O JSON do diagnóstico continua com `raw_release_authorized=false`; só o recibo separado do arquivador autoriza a etapa explícita de liberação.

Falhas interrompem a execução e ficam no ledger. A retomada confere fontes, entradas, artefatos arquivados e os custos reservados/consumidos; não repete alvos já arquivados e liberados. As máscaras e os NaNs permanecem no NPZ arquivado. CDFu0 estrutural exata mantém MCSE0; parâmetros sem verdade mantêm NaN/false; falhas de outros integrais permanecem registradas.

## Preflight executado

`results/fixed_operational_preflight_final.json` registra:

-96datasets e96targets A0; zero avaliações de likelihood.
-31.457.280 avaliações de produção planejadas nos dois níveis×4replicações; treino ainda sem comprimento escolhido.
-1.596.588.032bytes numéricos estimados pelo runtime NumPy; nenhum banco foi construído nesta etapa.
-37.552.128bytes estimados de raw por alvo; a estimativa conservadora do runtime para bloco16é600.834.048bytes, embora o driver use um alvo por vez no ciclo produção/arquivo/liberação.
-Execução não pronta: treino pendente e flag de execução falsa. A tabela existente foi lida para integridade/dimensões; não foi regenerada.

Comando executado, a partir da raiz:

```sh
PYTHONPATH=src .venv/bin/python tmp/c07_fixed_scenarios/scripts/run_fixed_campaign.py \
  --project-root . \
  --masked-module-path tmp/c07_fixed_scenarios/src/inference/fixed_diagnostics_v2.py \
  --experiment configs/calibration/fixed_experiment_v1.json \
  --data results/C07/fixed_scenarios/data.npz \
  --table results/C07/orf_interpolation/orf_table_pilot12x4.npz \
  --table-manifest results/C07/orf_interpolation/orf_table_manifest.json \
  --validation-config configs/calibration/pilot_initial.json \
  --run-config tmp/c07_fixed_scenarios/configs/fixed_campaign_prospective_v1.json \
  --protocol tmp/c07_fixed_scenarios/configs/fixed_diagnostics_v1.json \
  --truth-data results/C07/fixed_scenarios/data.npz \
  --generation results/C07/fixed_scenarios/generation.json \
  --output tmp/c07_fixed_scenarios/operational_preflight_output \
  --plan-file tmp/c07_fixed_scenarios/results/fixed_operational_preflight_final.json
```

Após copiar o script/módulo para a raiz, omitir `--project-root` e `--masked-module-path`; os caminhos default passam a ser os integrados. Copiar as duas configurações para `configs/calibration/`. O backend NumPy é o default; o C++ continua opcional e exige os mesmos argumentos explícitos `--native-library` e `--native-build-manifest` do runtime. Nenhuma compilação ou execução é implícita. O `--execute` só funciona quando a configuração congelada estiver habilitada e aprovada; não foi usado nesta entrega.

## Verificação

**36 testes passaram:**9da geração,10do leitor v1 preservado, os mesmos10contra v2 e7do driver operacional. Os testes do driver usam operações TOY em três IDs representativos0/32/64, por injeção explícita de operações na função interna; não passam pelo preflight obrigatório de96targets da CLI de produção e não constituem96posteriores. O teste usa os arquivadores `prepare_archive`, `verify_archive_receipt` e `release_raw` ROOT reais sobre arquivos TOY temporários.

Casos conferidos: arquivo íntegro com máscaras/NaNs e alvo não resolvido; remoção somente após recibo; retomada sem repetir alvo liberado; falha intermediária debitada ao ledger; schema incorreto impede arquivo e mantém os oito raws; alteração de geração antes do início impede qualquer treino; corrupção do snapshot impede retomada; inventário diferente dos96A0é rejeitado pelo preflight. O resultado completo está em `results/tests_operational_complete.json`.

Nenhum resultado de SBC, cobertura empírica ou inferência física decorre desses testes de operação. As famílias científicas93/62/15 da campanha500 continuam em sua síntese separada, que não deve aceitar o schema fixed96.
