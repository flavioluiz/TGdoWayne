# Verificador MCMC v2 otimizado, para revisão

Não altera o método, os limiares ou arquivos versionados. A implementação candidata está em `mcmc_optimized.py`; importa o módulo estável `src/inference/mcmc_diagnostics.py`, preserva suas funções públicas auxiliares e substitui apenas `target_diagnostics` por execução com reutilização explícita. Não usa monkey-patching, cache global, RNG ou threads.

Mudanças de custo:

- Escores normais dos ranks são calculados uma vez por parâmetro e reutilizados em Rhat e ESS bulk.
- A ordenação original é reutilizada para quantis e para calcular os ranks dos desvios absolutos; estes formam duas sequências monotônicas, aproveitadas pela ordenação estável.
- Indicadores/ESS dos cortes .05/.95 são reutilizados nos resumos de cauda e de quantis.
- Interpolação linear dos quantis usa os valores já ordenados; o cálculo em lote dos limites beta elimina partições repetidas.
- Entradas são validadas uma vez e copiadas para memória contígua por alvo. Os caches existem somente durante esse cálculo.

Fórmulas de autocovariância, Geyer, MCSE, tamanho de lote, folding, empates e flags de falha são as mesmas de v2. Optou-se pela reutilização antes de acrescentar FFTs em lotes maiores: o perfil mostrava custo importante também na ordenação/partição e validação repetidas.

## Verificação concluída

Seis testes específicos passaram: comprimentos pares/ímpares, empates, cadeias constantes/presas, diferentes escalas, ranks e quantis contra as funções de referência e contrato de entradas. Comparou-se **toda a saída detalhada** nos 80 alvos do piloto Student277, prefixo de 4.096 passos, mais seis casos difíceis completos de 16.384 passos e o caso constante B_Gd14 do piloto139: **87 comparações**.

Todas as decisões, estados e listas de falhas coincidiram. Em 86/87 casos, todos os campos foram exatamente iguais. Num caso, houve dois arredondamentos: `4,55e−13` no ESS usado para erro de um quantil e `1,11e−16` no extremo do intervalo; ambos abaixo da tolerância absoluta pré-fixada `1e−12`. Não houve alteração de CDF, Rhat ou decisão nesse caso. Detalhes em `results/roundoff.json`.

O ganho mediano pareado foi **2,23×** no conjunto e **2,14×** nos casos completos. Na campanha de comparação, o código estável somou 21,44 s e o candidato 9,46 s. A ordem foi alternada previamente; esses custos dependem do ambiente e da carga concomitante. Resultados e hashes estão em `results/benchmark.json`.

Da raiz:

```sh
.venv/bin/python -m unittest discover -s tmp/c07_mcmc_optimized -p test_optimized.py -v
.venv/bin/python tmp/c07_mcmc_optimized/benchmark.py
.venv/bin/python tmp/c07_mcmc_optimized/audit_roundoff.py
```

Para integração, copiar o candidato para um módulo distinto em `src/inference/` e adaptar apenas os caminhos dos testes/scripts. Manter o módulo estável disponível como referência. Os testes originais das funções auxiliares continuam pertinentes; os seis novos exercitam diretamente a execução otimizada. `benchmark.py` usa fixtures locais históricas, sem gerar ou aprovar uma campanha SBC500.

Os diagnósticos científicos dos pilotos permanecem os produzidos pelo verificador estável. Ganho de execução não constitui aprovação da posterior, da ORF ou de cobertura estatística.
