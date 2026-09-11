# Configuração final fixed96: política ampla, sem posteriores executados

Entrega de 10/09/2026. A configuração nova é
`configs/fixed_campaign_execution_v2.json`, SHA256
`bdabf4d94a0c33a7d392d711bbc7cb66cb5c425f5d08ea47910bb3f6f296d8b0`.
A configuração desabilitada v1 e o pacote operacional v2 anterior permanecem
intactos. Nenhuma fonte ROOT foi editada.

Os96 alvos são somente A0_CN, IDs0…95, dados de32 injeções em cada cenário:
u=0, u=0,995 e ausência exata de sinal GW. A regra prospectiva usa8192 passos
frios×4 cadeias, seleção de2048 pontos para EM de quatro componentes, seguida
de `0,75 GM(C)+0,10 GM(9C)+0,15 Student_5_global`. A ampliação é parametrizada
por `training.gaussian_broadening={wide_total_probability:0.10,
variance_multiplier:9}`. Não há novo ajuste após observar diagnósticos.

As sementes907120101 para treino e907120102 para produção têm namespaces
distintos da campanha500, do ensaio wide16 e da geração dos96 dados. Os níveis
IID são16384/65536×4, com seleção de cortes pelo nível menor e diagnóstico
prospectivo pelo maior. A configuração está habilitada, mas a CLI permanece
em modo preflight sem `--execute`; nenhum posterior foi executado nesta entrega.

O preflight final (`results/fixed_execution_v2_preflight.json`) está pronto:
3.146.112 avaliações de treino incluindo inicialização e31.457.280 de produção,
total34.603.392 sob os limites originais16M/40M/60M. A memória numérica estimada
com NumPy é1.596.588.032 bytes, raw por alvo37.552.128 bytes e estimativa
conservadora do bloco16 de600.834.048 bytes; preservados os tetos4GiB/1GiB.
O cálculo de preparação efetuou zero avaliações de likelihood, não
desserializou verdades, não construiu banco e reutilizou a tabela8336 existente.

Confirmei por identidade dos objetos Python que `run_fixed_campaign.py`
importa diretamente ROOT `CampaignRuntime`, `campaign_training.train_block`,
`campaign_iid.produce_target/release_raw` e `campaign_archive.prepare_archive`.
O runtime inclui `proposal_broadening` em seu manifesto quando a configuração
contém a opção. O treino ROOT aplica a transformação antes de gerar o novo
hash de conteúdo e preserva o ajuste original num campo próprio; nenhum JSON
com identidade herdada do ensaio temporário é reutilizado. O leitor mascarado
final mantém o status `NUMERICAL_DIAGNOSTICS_COMPLETE`, o schema
`C07_FIXED_MASKED_IID_DIAGNOSTICS_v2_OPERATIONAL` e scope
`FIXED_TRUTH96_NOT_SBC`, compatíveis com o arquivador genérico e distintos da500.

Os36 testes existentes passaram novamente em0,51s: geração, valores
indefinidos, u=0 estrutural, identidade numérica v1/v2, arquivo, interrupção,
retomada e fontes. Os testes de operação são TOY; não geram96 posteriores.
O relatório `results/fixed_execution_v2_verification.json` contém também os
hashes ROOT efetivamente conferidos e a prova de que não houve construção.

## Integração mínima

1. Copiar o leitor `src/inference/fixed_diagnostics_v2.py` e o driver
   `scripts/run_fixed_campaign.py` do pacote para os caminhos homônimos ROOT;
   são os mesmos bytes já entregues no pacote operacional v2.
2. Copiar `configs/fixed_campaign_execution_v2.json` e o protocolo intacto
   `configs/fixed_diagnostics_v1.json` para `configs/calibration/`.
3. Repetir o preflight abaixo nos caminhos finais: identidade muda por caminhos
   e backend selecionado. Confirmar96A0, treino8192, níveis e zero logL.
4. Na execução efetiva, usar diretório próprio vazio e a mesma CLI com
   `--execute`; retomar somente com `--execute --resume`, mesmas fontes,
   configurações, sementes e backend. Manter todos os alvos, flags e máscaras.

Não substituir o argumento explícito `--generation` por um falso `--truth-logl`.
CDFs indefinidas continuam NaN/false; somente o caso estrutural demonstrado
u=0 tem CDF0 e MCSE0. As20 CDFs auxiliares de quantis continuam em todos os
posteriors. Famílias conservadoras19584/672 permanecem; contagens efetivas
planejadas17664/512 são registradas separadamente. Arquivo e liberação de raws
dependem de recibo íntegro, preservando também alvos numericamente não resolvidos.

Comando de preparação após integração:

```sh
PYTHONPATH=src .venv/bin/python scripts/run_fixed_campaign.py \
  --experiment configs/calibration/fixed_experiment_v1.json \
  --data results/C07/fixed_scenarios/data.npz \
  --table results/C07/orf_interpolation/orf_table_pilot12x4.npz \
  --table-manifest results/C07/orf_interpolation/orf_table_manifest.json \
  --validation-config configs/calibration/pilot_initial.json \
  --run-config configs/calibration/fixed_campaign_execution_v2.json \
  --protocol configs/calibration/fixed_diagnostics_v1.json \
  --truth-data results/C07/fixed_scenarios/data.npz \
  --generation results/C07/fixed_scenarios/generation.json \
  --output tmp/c07_fixed_posterior96_v2
```

Esse comando não executa treino nem posteriores. O backend nativo pode ser
selecionado explicitamente pelos mesmos `--native-library` e
`--native-build-manifest` da campanha500, com threads fixadas antes do preflight.
O arquivo da biblioteca, fontes e receita entram na identidade; não trocar
backend em uma retomada. Não modificar fontes importadas enquanto a500 está
rodando. A conclusão dos96 deverá ser relatada como injeções fixas e estudos de
limite/cobertura definidos por cenário, sem ser somada ao SBC500.
