# Parecer independente — síntese C07 fechada, 500×5

**PASS no âmbito auditado.** A síntese reproduz as estatísticas, as decisões registradas e a máscara de resolução dos produtos compactos fechados. Não foram encontrados defeitos numéricos ou de inventário nas verificações executadas. Todos os500 dados de cada um dos cinco modelos,2500 alvos e15000 PITs foram conservados. As fontes e produtos ROOT permaneceram inalterados.

## Identidade e verificações

O fechamento foi comunicado por ROOT após os dois processos encerrarem com código0. Foram conferidos os SHAs informados:

- `campaign_complete.json`: `1daa0948e9d55f6537cd7c25870c609ea9e1c8019dc59dc8abea899ff6b2c9e2`.
- `campaign_plan.json`: `987804ca6b8aecb223e35975dfcfb308e64e90bb7a520cbf42ec9e2c7c83604c`.
- `results/C07/synthesis/summary.json`: `909ef28817342c19293fe9cb832bcf659dd480be5fd82c3708ee73b832cd4f9a`.
- `arrays.npz`: `2effb30fafb2db1ae6371952d933cb9f8be63bf2875cd8a55ea15188a39a4a4f`.

A auditoria principal contém **6202 verificações**. Usa NumPy/SciPy diretamente, sem importar os helpers ROOT. Recalculou os30 testes KS, médias, extremos, empates e histogramas20 dos PITs;125 eventos de cobertura, p-valores binomiais e intervalos Clopper–Pearson; as correções Holm das famílias93/62/15;15 comparações pareadas de cobertura e60 diferenças descritivas de quantis; e os envelopes de sensibilidade dos15000 PITs. Ambos os CSVs concordam com o resumo.

A maior diferença absoluta foi **1,4210854715202004×10⁻¹⁴**, em `log10` do limite de cauda DKW; a maior diferença dos intervalos mostrada no registro é7,77×10⁻¹⁶. Todas as decisões booleanas concordaram exatamente. O KS foi obtido também por `scipy.stats.kstest(..., method='exact')`; os limites CP superiores usaram a função de sobrevivência beta; o envelope de McNemar foi recalculado por total de discordâncias, sem copiar a grade bidimensional do helper ROOT. O retângulo continua sendo um superconjunto conservador das contagens possíveis.

O cálculo da rotina principal usou2,868211s CPU; o processo completo, com imports, encerrou em5,002s de parede com um thread numérico. RSS máximo113.557.504B. O contador CPU dessa rotina começa após os imports; esse detalhe não é apresentado como medida integral do processo.

## Reconstrução da resolução por função

Após autorização adicional de ROOT, foram lidos os **2500 JSONs e2500 NPZs compactos**, com SHA individual confrontado contra o inventário fechado da síntese. Nenhum raw foi aberto. A auditoria recalculou os flags dos204 contrastes entre réplicas e sete refinamentos a partir de diferenças/MCSE, com suas famílias510000/17500; os cortes de precisão.00335; a fórmula `max_weight/(1-max_weight)` e os dois controles de peso; e o limite de massa ponderada saturada10⁻¹². Reconstruiu a conjunção específica de cada função com seus contrastes, o denominador/logZ e os controles comuns, sem recorrer a `resolved_by_function`.

A máscara reconstruída é **idêntica nos15000 elementos** à síntese. A fórmula de retirada de um peso coincidiu exatamente. As contagens distintas são:

- **81 alvos** têm pelo menos um dos cinco flags numéricos globais falso.
- **50 alvos** têm ao menos um dos seis PITs inelegível para uma faixa numérica finita.
- **243 funções PIT** são `unresolved` e conservaram o intervalo completo[0,1].

Os81 alvos correspondem aos controles dos26 CDFs/limiares e demais verificações por alvo; a elegibilidade de um PIT é específica dessa função e não depende automaticamente dos20 cortes adicionais de quantis. Isso explica por que as três contagens não são intercambiáveis. Nenhum alvo ou PIT foi descartado.

| Modelo | Alvos com algum flag falso | Alvos com algum PIT unresolved | Funções PIT unresolved |
|---|---:|---:|---:|
| A0_CN | 4 | 3 | 18 |
| A_CN | 27 | 15 | 68 |
| B_CN | 10 | 6 | 31 |
| A_G | 25 | 16 | 71 |
| B_G | 15 | 10 | 55 |
| Total | **81** | **50** | **243** |

As ocorrências de causas podem se sobrepor; não se deve somar as linhas de causas para obter243. A tabela conta funções entre os2500 alvos:

| Causa de inelegibilidade | u | log10Agw | gamma | log10Ar | log10EFAC | logL | Total |
|---|---:|---:|---:|---:|---:|---:|---:|
| Precisão do CDF alto | 3 | 8 | 3 | 5 | 6 | 7 | 32 |
| Controle de peso | 37 | 37 | 37 | 37 | 37 | 37 | 222 |
| Massa ponderada saturada | 1 | 1 | 1 | 1 | 1 | 1 | 6 |
| Réplicas de logZ | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Refinamento de logZ | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Réplicas da própria função | 0 | 0 | 0 | 0 | 1 | 0 | 1 |
| Refinamento da própria função | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| **Funções unresolved únicas** | **39** | **43** | **39** | **39** | **41** | **42** | **243** |

A reconstrução consumiu11,966098s CPU, incluindo imports, e RSS120.651.776B; leu78.206.529B de JSON/NPZ compactos. A atribuição complementar por função, solicitada após esse resultado, consumiu3,687173s CPU/RSS39.387.136B. O total dessa auditoria adicional é15,653271s CPU, abaixo do teto30s. `causes_by_function.json` também conserva a decomposição por modelo.

## Leitura científica delimitada

Na família dos controles A0_CN/A_G/B_G houve **zero rejeição nominal após Holm**. Na família aproximada A_CN/B_CN houve **13 rejeições nominais**, das quais **10 persistem nas faixas de sensibilidade prefixadas**. As15 comparações pareadas tiveram oito rejeições nominais e duas persistentes nessas faixas, ambas referentes aEFAC. Os desvios mais destacados dos modelos aproximados aparecem em EFAC e na CDF dependente dos dados de logL.

Essas decisões pertencem ao experimento sintético, à geometria, às priors e às funções declaradas em C07. Não rejeitar os controles não demonstra correção universal nem substitui as validações do integrador. A persistência de uma rejeição é condicional aos intervalos de sensibilidade, que usam CLT/MCSE e a parcela determinística.002 observada no protocolo; não são certificados globais de erro. Os quantis permanecem descritivos quanto à precisão horizontal.

O parecer confirma a coerência aritmética e a rastreabilidade dos resultados publicados pela síntese. A validade física dos kernels/ORFs e das evidências externas pertence às auditorias próprias já vinculadas ao projeto; não houve nova ORF, likelihood, geração de dados ou posterior nesta revisão.

## Evidências reproduzíveis

- `audit_synthesis.py` e `closed500/review.json`: estatísticas independentes e comparação do resumo/CSVs.
- `audit_resolution.py`, `resolution500/review.json`, `hash_inventory.json` e `independent_resolved.npy`: máscara independente e inventário completo.
- `resolution_causes.py` e `resolution500/causes_by_function.json`: causas por função/modelo.
- `commands.sh`: comandos executados; `*.log` e `helper_toy.json`: registros de execução e controles sintéticos preliminares.
- `package_manifest.json`: lista explícita de arquivos e SHAs. O material em `PREPARACAO.md` registra o escopo prospectivo anterior ao sinal de fechamento.
