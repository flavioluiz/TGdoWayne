# Integração da síntese fixed96

Copiar os três arquivos novos para caminhos ROOT:

| Arquivo deste pacote | Destino |
|---|---|
| `src/inference/fixed_synthesis.py` | `src/inference/fixed_synthesis.py` |
| `scripts/sintetizar_injecoes_fixas.py` | `scripts/sintetizar_injecoes_fixas.py` |
| `configs/fixed_synthesis_v1.json` | `configs/calibration/fixed_synthesis_v1.json` |

O módulo usa somente funções já existentes de integridade, arquivo, CP e
envelope de PIT. Não altera produtor, leitor mascarado, driver ou protocolo
IID. Os snapshots e identidades da campanha permanecem intactos.

Conservar também `PROTOCOLO.md`, `results/tests.json`, `tests/` e
`package_manifest.json`. O exemplo `results/toy_summary.json` é explicitamente
TOY e não deve ser apresentado como resultado dos96 dados. Os testes têm
dez casos; seus caminhos de fixtures atualmente usam a raiz e o pacote
temporário. Ao portar, ajustar somente esses caminhos de teste.

Quando a campanha96 tiver terminado, usar diretório de saída novo:

```sh
PYTHONPATH=src .venv/bin/python scripts/sintetizar_injecoes_fixas.py \
  --campaign tmp/c07_fixed_posterior96_v2 \
  --experiment configs/calibration/fixed_experiment_v1.json \
  --data results/C07/fixed_scenarios/data.npz \
  --generation results/C07/fixed_scenarios/generation.json \
  --numerical-protocol configs/calibration/fixed_diagnostics_v1.json \
  --scientific-protocol configs/calibration/fixed_scenarios_v1.json \
  --synthesis-config configs/calibration/fixed_synthesis_v1.json \
  --validation-evidence CAMINHO_DO_MANIFESTO_NUMERICO_REVISADO.json \
  --output results/C07/fixed_scenarios/synthesis_v1
```

O argumento de evidência é explícito e aceita o formato já usado na síntese500,
com entradas `role/path/sha256` para ORF, kernel e referência posterior.
Os limites de aplicabilidade dessa evidência devem constar no manifesto.
O leitor não constrói runtime, banco ORF ou verossimilhança e não requer raws
já retirados: confere seus hashes e os artefatos preservados nos recibos.

Para revisão antes de copiar os arquivos, usar o script temporário com
`--project-root . --module-path tmp/c07_fixed_synthesis/src/inference/fixed_synthesis.py`
e os caminhos temporários dos protocolos ainda não integrados. Executar a
CLI sobre campanha incompleta resulta em erro; não há opção de resumir
apenas os alvos aprovados.

Produtos: `summary.json` com todos os cenários/funções/quantis e proveniência,
`arrays.npz` com96×6 PITs, faixas/máscaras, quantis e IDs, e `README.md` curto.
Não há teste de uniformidade, filtro científico, gráfico com referência
uniforme ou afirmação de inferência/calibração concluída por haver um arquivo.
Uma figura posterior pode usar os intervalos condicionais destes produtos;
a tabela e os arrays completos são a fonte auditável.
