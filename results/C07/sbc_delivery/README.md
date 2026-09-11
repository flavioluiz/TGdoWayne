# Entrega da síntese C07

Dois scripts portáveis, sem framework novo:

- `scripts/sintetizar_calibracao.py`: valida o inventário e produz síntese condicional.
- `scripts/figuras_calibracao.py`: produz18 painéis para os modelos de referência e12 para as aproximações, em PDF/SVG.

A síntese exige caminhos explícitos: `--diagnostics`, `--production`,
`--experiment`, `--data`, `--truth-logl`, `--config`, `--numerical-protocol`,
`--validation-evidence`, `--scientific-protocol` e `--output`. O destino deve ser
novo. O modo principal exige exatamente2.500 IDs únicos,500 em cada modelo, sem
interseção silenciosa ou descarte. `--toy64` é uma exceção explícita de teste,
rotulada no relatório e nas figuras; não aceita64 dados como campanha 500.

Conferências: schema/target/datum/modelo; identidade de runtime única; hashes de
produtores, dados, configuração, protocolo, logL direta e todos os NPZ; oito
replicações nos dois níveis; verdade e transformação às unidades da priori;
quantis monotônicos e conversão física; especificação exata204, 7 refinamentos,
flags coerentes com erros e multiplicidade. `resolved_by_function` é recalculado
a partir dos resultados de cada função e de logZ, preservando falhas de outros
PITs separadamente. O leitor não lê raws retirados nem cria posteriors ausentes.

O manifesto de evidências tem `entries` com `role`, `path`, `sha256`; caminhos
relativos são resolvidos a partir da pasta do manifesto. São obrigatórios os
papéis `orf_interpolation`, `likelihood_kernel` e `external_posterior_reference`.
`whole_flow_review` e demais evidências podem ser adicionados. Campos de revisão,
falhas e limitações são preservados como declarações. Verificar presença e hash
é uma conferência de proveniência: não há aprovação automática por booleanos ou
pela aparência da curva de calibração. Conclusões permanecem condicionais à
revisão independente dessas evidências.

Produtos: `summary.json`, `arrays.npz`, `README.md`, `tests.csv` e
`paired_central90.csv`. Conservam famílias 93/62/15, testes nominais e limites de
sensibilidade separadamente. Quantis são descritivos: MCSE de CDF não certifica
precisão horizontal. A faixa numérica usa 0,002 + z×MCSE, alphaMC 0,01 / família 15.000;
não resolvidas recebem [0,1]. DKW descreve a amostragem IID ideal e é desenhada
separadamente, com ajuste à família científica pertinente. Nenhum passe de KS
transforma uma falha numérica em integração aprovada.

```sh
python scripts/figuras_calibracao.py \
  --summary RESULTADOS/summary.json --arrays RESULTADOS/arrays.npz \
  --output RESULTADOS/figures
```

A validação usa um TOY64 independente: prior uniforme por transformaçãoPhi de
normal latente, observação normal, posterior conjugada exata e logL-PIT por
qui-quadrado não central. MCSE 1e-8 e os papéis de evidência são fixtures explícitos
de interface, sem reivindicação de precisão ou ORFs PTA. Cinco testes passam,
incluindo 155 p-valores contra SciPy, guardas de inventário/identidade/hash/verdade/specs
e separação do modo 500. Os PDFs finais de QA em `results/toy_figures_v2` foram
renderizados com Poppler e examinados integralmente, sem truncamentos ou sobreposições.
As figuras do TOY são exemplos de formato, não resultados da pesquisa PTA.

`integration_manifest.json` lista os arquivos de código/documentação para copiar.
Os 320 diagnósticos sintéticos de teste, caches de fontes e renders PNG permanecem
somente em tmp. Não copiar automaticamente esses arquivos para resultados científicos.
