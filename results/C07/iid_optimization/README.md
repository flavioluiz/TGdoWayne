# Otimização dos diagnósticos IID, sem alteração do protocolo v1

O módulo `src/inference/iid_diagnostics.py` e todos os protocolos permanecem intactos. A implementação candidata está em `iid_optimized.py`; a referência continua obrigatória. Nenhum resultado histórico foi reclassificado.

## API para produção por alvo

```python
from inference.iid_optimized import TargetIIDContext, compare_brackets

# Um único alvo e nível, replicações IID independentes de igual comprimento.
context = TargetIIDContext(log_weights)       # shape (R, N), cópias próprias
pit_rows = context.cdf(parameter_values, cuts, mcse_target=.00335)
logl_rows = context.cdf(log_likelihood, logl_cuts, mcse_target=.00335)
quantiles = context.quantiles(parameter_values, [.05, .5, .9, .95])
weight_diagnostics = context.weights()
```

Valores têm shape `(R,N)`. A classe pode ser reutilizada nos cinco parâmetros, logL e cortes externos. `weights()` retorna uma cópia do resumo para impedir que sua edição corrompa o cache. Os dados e os cortes são validados e copiados em cada chamada; não há cache global, cache pela identidade de arrays mutáveis, alteração do módulo de referência ou RNG.

A classe não conhece verdades, IDs de alvo, hashes do raw ou resultados científicos. Não devolve `NUMERICALLY_APPROVED`. Um relatório externo deve combinar a finalidade declarada, identidade/target/hashes, validação de ORF/implementação, MCSE, concentração/caudas, constantes e demais controles antes de qualquer decisão de armazenagem ou liberação do raw. A classe não altera arquivos.

As funções com API v1 também estão disponíveis: `iid_cdf`, `replicated_cdf`, `weighted_quantiles`, `weight_summary`, `replicated_weights`, `compare_brackets`. A função de brackets aceita opcionalmente `context=` para reutilizar as normalizações; verifica que os pesos do contexto correspondem aos fornecidos. Sem contexto, cria um por alvo. Os40extremos e suas decisões continuam iguais ao protocolo.

## O que foi otimizado

Cada replicação e o conjunto agrupado normalizam os pesos apenas uma vez. Máscaras de peso positivo eNp_i ficam armazenadas. As duas formas de cálculo de logZ usadas no v1 para CDFs e evidência são mantidas separadas, inclusive na ordem das operações. A ordenação dos pesos para seus resumos permanece igual; calcular vários quantis de uma função em uma única chamada reutiliza a mesma ordenação.

A estimativa da CDF mantém o produto matricial original `p @ indicator`. A variância continua sendo `std(N*p*(I−Fhat),ddof=1)/sqrt(N)`. A redução agora usa um vetor contíguo por corte, evitando a grande matriz de influências e a redução por colunas. Não se introduziu expressão de prefixos potencialmente sujeita a cancelamento entre massas de cauda. O ganho veio da reutilização e da disposição dos temporários em memória, sem trocar o estimador.

A ordem de soma da variância pode produzir diferenças de arredondamento. Um controle sintético colocou a meta exatamente na MCSE v1 e encontrou uma mudança de flag de1ulp na primeira candidata. Esse fracasso e a fonte inicial foram preservados em `results/boundary_failure_initial.json` e `experimental_sources/iid_initial.py`.

Na candidata final, quando a MCSE está a≤10⁻¹² do limiar, ou uma variância extremamente pequena poderia mudar o estado numérico de um indicador misto, usa-se a redução matricial v1 original. O mesmo retorno à referência ocorre perto de uma desigualdade de bracket. **10⁻¹² controla somente a escolha de implementação; não aumenta a tolerância de aprovação.** A meta permanece .00335 e a decisão final usa o comparador original. Não é uma regra de parar ou modificar amostras.

Constantes continuam com MCSE operacional infinita e estado não resolvido; nenhuma cauda, peso extremo ou falha é descartada. ESS permanece um diagnóstico de concentração, sem equivalência com ensaios binomiais.

## Evidência e testes

- `results/diagnostics_final.json`: leitor completo nos16alvos e dois níveis16384/65536do piloto com tabela8336; inclui todos os26cortes, pesos,40extremos de referência por nível e famílias de replicações/refinamento.
- `results/comparison_final.json`: comparação de todos os campos estatísticos com o relatório v1; todos os flags coincidem, diferença máxima5,46×10⁻¹⁷. Foram excluídos apenas hashes/caminhos da implementação e tempo.
- `results/benchmark.json`: benchmark CPU pareado nos32casos alvo–nível, alternando a ordem referência/otimizado e medindo I/O separadamente.
- `results/toy/comparison.json`: reprodução da experiência conjugada e do controle de modo raro, mesmas sementes e critérios. As estimativas dosPITs são idênticas bit a bit; diferenças nas MCSEs ficam abaixo de1,91×10⁻¹⁷. Os sete critérios TOY e todos os flags continuam iguais.
- `test_optimized.py`:12testes, cobrindo matrizes IID, empates, constantes, zeros/underflow, pesos extremos e deslocamentos de logw, amostras pequenas/subnormais, quantis exatos, posse do cache, entradas inválidas e limiares de decisão de MCSE/brackets.

O leitor completo final levou15,73s, comparado a29,12s do registro v1, incluindo leitura e escrita. Essa comparação total usa execuções diferentes; o benchmark pareado por alvo isola melhor o ganho de cálculo. Os tempos não garantem a mesma aceleração sob outra plataforma, pressão de memória ou esquema de I/O. O experimento continua sendo um piloto de16alvos, sem SBC500 adicional.

## Comandos e integração

Executar a partir da raiz, com os caminhos explícitos do piloto:

```sh
.venv/bin/python -m unittest discover -s tmp/c07_iid_optimized -p test_optimized.py -v
PYTHONPATH=src .venv/bin/python tmp/c07_iid_optimized/benchmark.py
PYTHONPATH=src .venv/bin/python tmp/c07_iid_optimized/validate_toy_optimized.py
PYTHONPATH=src .venv/bin/python tmp/c07_iid_optimized/diagnose_optimized.py \
  --low tmp/c07_iid_gmm_approved/results/iid_N16384.npz \
  --high tmp/c07_iid_gmm_approved/results/iid_N65536.npz \
  --truth-logl tmp/c07_iid_gmm_approved/results/truth_likelihood.json \
  --reference results/C07/reference/quantiles/posterior_reference.json \
  --protocol configs/calibration/diagnostics_iid_8336_execution.json \
  --output tmp/c07_iid_optimized/results/diagnostics_reproduction.json
```

TOY e leitor recusam sobrescrever seus resultados; reproduzir em outra pasta/saída. O benchmark tem saída fixa, portanto preservar o JSON antes de repetir. Todos os scripts foram executados; não são apenas exemplos planejados.

Integração sugerida: copiar `iid_optimized.py` para `src/inference/iid_optimized.py`, portar imports dos testes e do leitor para esse módulo, preservar o v1. No leitor, trocar os três imports de `iid_optimized` por `inference.iid_optimized`; o restante da lógica estatística fica igual. O leitor temporário guarda contextos para os16alvos a fim de reproduzir o relatório completo. Na produção, usar um contexto por alvo/nível e liberá-lo depois de registrar o resumo, limitando memória.

A implementação depende das definições v1 e de NumPy/SciPy já fixados no projeto. Fontes e hashes dos resultados finais identificam ambas as implementações. A candidata inicial permanece como antecedente de uma falha de arredondamento, sem ser o módulo a integrar.
