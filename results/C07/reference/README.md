# Pacote portátil da referência A0, dado 14

Pronto para integração independente em C07. Não edita C05, C06 ou arquivos já versionados. O resultado científico delimitado é a referência determinística de A0 para um dado congelado; não aprova o piloto inteiro, qualquer interpolador ORF ou SBC de 500 realizações.

## Arquivos para integrar

- `src/inference/reference_*.py`: módulos novos; imports do modelo, ORF, escala CN e quadratura apontam para `inference.*` já integrado. `reference_paths.py` resolve a raiz pela configuração congelada ou por `TGWAYNE_REFERENCE_ROOT`.
- `scripts/reference_a0.py`: entrada explícita para etapas de cálculo.
- `tests/test_portable_reference.py`: seis testes numéricos/contratuais portáveis. No teste que usa os denominadores históricos, o caminho definitivo é selecionado quando o diretório temporário do pacote não existe.
- `results/C07/reference/cubature/`: resultados históricos da cubatura, copiados byte a byte.
- `results/C07/reference/quantiles/`: os 16 quantis concluídos, resumo e `posterior_reference.json` com forma (5,4) para quantis e (5,4,2) para intervalos/CDFs.
- `results/C07/reference/history/cdf_cache/`: numeradores por massa dos controles e dos extremos, com fontes históricas; úteis para auditoria e reintegração dos subconjuntos.
- `docs/REFERENCIA_QUANTIS_CONCLUIDA.md`: resultado final e limites. Os demais documentos preservam a derivação e a evolução da investigação.
- `validation/`: seis testes com imports da raiz e comparação AST dos 16 símbolos matemáticos migrados; não substituem as validações científicas históricas.

Os arquivos de resultados anteriores preservam suas referências às fontes originais e seus hashes. Não reescrever esses campos para sugerir que os resultados vieram da versão portada. `port_manifest.json` distingue fontes antigas e novas. Os caminhos internos de origem antigos podem conter caminhos absolutos ou temporários, mas o código novo não depende deles para calcular.

## Entradas e saídas

Entradas definitivas: `configs/calibration/pilot_initial.json`, `results/C07/fixtures/pilot_data.npz`, `results/C07/fixtures/orf_cache/` e `results/C07/pilot_initial/endpoint_129_13_independent.json`. O leitor ORF exige os nós existentes, valida os metadados/matrizes e não calcula nós ausentes. A assinatura física fica a mesma. A priori selecionada é conferida explicitamente antes da CDF de alta precisão.

Novos cálculos escrevem somente em `results/C07/reference/reproduced/`. Os denominadores históricos de `results/C07/reference/cubature/` são utilizados explicitamente pelo construtor CDF; sua origem integra a chave de cache. O novo cache incorpora também dados, configuração, fontes matemáticas, orçamento de omissão, tamanho de lote e assinatura física. Os caches temporários históricos são preservados à parte e não são reutilizados como se tivessem a nova identidade.

Após copiar os arquivos para os destinos correspondentes, executar a partir da raiz:

```sh
PYTHONPATH=src .venv/bin/python -m unittest discover -s tests -p test_portable_reference.py
PYTHONPATH=src .venv/bin/python scripts/reference_a0.py cubature --orders 12 --mass 0 0.5 1 --no-cdf
PYTHONPATH=src .venv/bin/python scripts/reference_a0.py anisotropic --orders 32 20 12 --mass 0.5
```

Campanhas completas são explícitas e custam mais. Os comandos abaixo são instruções de reprodução, não campanhas adicionais já executadas:

```sh
PYTHONPATH=src .venv/bin/python scripts/reference_a0.py truncated --orders 20
PYTHONPATH=src .venv/bin/python scripts/reference_a0.py anisotropic --orders 32 20 12
PYTHONPATH=src .venv/bin/python scripts/reference_a0.py quantiles
PYTHONPATH=src .venv/bin/python scripts/reference_a0.py export
```

Os orçamentos originais de pontos são mantidos: cubatura geral 150 milhões, CDF truncada 1,5 bilhão, anisotrópica 500 milhões, cada avaliação de CDF 12 milhões e lote de no máximo 16 massas. Esses números limitam pontos, não RSS. A redução de custo de CDF usa um limite explícito sobre nós omitidos; a aprovação entre resoluções ainda precisa ser verificada.

Durante o desenvolvimento, `run_staged.py` injeta apenas o caminho dos novos submódulos em `inference.__path__`; ele não é necessário na integração definitiva. O gerador desse pacote (`finish_port.py`) também é apenas ferramenta temporária e não deve ser integrado como produto científico.
