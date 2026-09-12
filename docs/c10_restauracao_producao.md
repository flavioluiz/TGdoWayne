# Restauração da campanha escalar C10

A campanha concluiu 6.344 análises sem descarte. O arquivo
`results/C10/production_reproducibility/manifest.json` descreve 110.257
arquivos lógicos, incluindo dependências reutilizadas. A restauração em
diretório separado conferiu todos os arquivos e seus SHA-256; o recibo está
em `restore_validation.json` no mesmo diretório.

Os 74 ZIPs novos somam 2.094.635.328 bytes e são distribuídos como anexos da
[v0.10.0](https://github.com/flavioluiz/TGdoWayne/releases/tag/v0.10.0).
O catálogo `distribution.json` registra nomes, URLs, tamanhos e hashes.
Os ZIPs da pré-produção e os manifestos permanecem no histórico Git.
Essa separação respeita o [limite de 2 GiB por push](https://docs.github.com/en/get-started/using-git/troubleshooting-the-2-gb-push-limit)
sem dividir o commit científico em versões intermediárias.

Após clonar e preparar o ambiente Python:

```bash
python3 scripts/restaurar_preproducao_c10.py --destination .
python3 scripts/baixar_producao_c10.py
python3 scripts/restaurar_producao_c10.py --destination .
make check-scalar
```

O download verifica tamanho e SHA-256 antes de aceitar cada arquivo.
O restaurador reconstitui partes ordenadas e recusa sobrescrever arquivos
diferentes. Omitir `--destination` executa somente a verificação dos ZIPs.
Nenhum desses comandos repete observações, ORFs ou posteriores físicos.

A auditoria numérica está em `results/C10/production_audit/audit.json`;
a síntese e os 71 testes prospectivos estão em
`results/C10/population_synthesis/results.json`. Os scripts de auditoria
e síntese preservam suas saídas e recusam sobrescrevê-las; para repetir a
análise, use uma cópia de trabalho separada e preserve o resultado anterior.

A concordância das representações numéricas não é um certificado uniforme
da likelihood física. Os PITs e fatores de Bayes não resolvidos permanecem
na síntese, conforme o capítulo 9.
