# Verificação do pacote e pilotos históricos

Estado: utilitários verificados, **pilotos ainda não aprovados; SBC500 não executada**. As tabelas ORF dos dois pilotos requerem aprovação independente; a tabela139 foi explicitamente reprovada por refinamento. Assim, a comparação abaixo é de diagnósticos computacionais de alvos aproximados, não uma comparação final de resultados físicos.

## Testes independentes

Quatorze testes unitários passaram. Num TOY normal estacionário com AR(1), rho=.8, quatro cadeias e 32.768 passos por cadeia, o ESS estimado da média foi 93,76% do valor teórico; o ESS do indicador em zero foi 96,20%. Para o indicador, a autocorrelação exata no lag k é `(2/pi)asin(rho^k)`, distinta da autocorrelação da média. Em 128 experimentos baratos independentes, a razão entre dispersão empírica das CDFs e MCSE médio quadrático foi 1,119, dentro do intervalo pré-fixado [.7,1.3]. Esses testes conferem estimadores, não a amostragem PTA.

O TOY de ranks usou 2.048 experimentos, 64 amostras por experimento e seed 707210912. Os ranks randomizados IID apresentaram D_KS=.01165, p=.941; os ranks de AR(1) estacionário rho=.95 apresentaram D=.13247, p=8,49e−32. Ambas as fontes têm marginal N(0,1) correta; a dependência torna inválida a nula intercambiável dos ranks de todas as observações. O jitter não corrige esse problema. Os p-valores foram relatados sem trocar seeds nem tornar a não rejeição um teste unitário.

## Pilotos com quatro cadeias

Cada piloto contém 16 dados fixos×5 métodos, 4.000 passos de aquecimento e 16.384 passos de produção por cadeia. Nenhuma amostra foi criada por este pacote. O segundo usa Student-t/RW e tabela277; o primeiro usa o algoritmo inicial e tabela139.

| Diagnóstico | Inicial139 | Student277 |
|---|---:|---:|
| Alvos que passam Rhat/ESS mínimos | 59/80 | 68/80 |
| Alvos que passam todos os critérios MC | 0/80 | 0/80 |
| Rhat máximo | 1,02782 | 1,03397 |
| ESS bulk mínimo | 173,21 | 78,66 |
| ESS tail mínimo | 48,55 | 19,56 |
| CDFs acima de MCSE .00335 | 1.755/2.080 | 1.195/2.080 |
| Indicadores constantes não resolvidos | 1 | 0 |
| Lotes insuficientes frente a tau | 828 | 227 |
| Maior MCSE finito | .03149 | .04938 |
| Mediana dos MCSEs finitos | .00547 | .00367 |
| Percentil90 dos MCSEs finitos | .01123 | .00700 |

O maior MCSE do primeiro piloto não é finito: um indicador constante foi mantido não resolvido. A mediana/percentil desse piloto usam os 2.079 valores finitos. Tempos observados dos cálculos de diagnóstico foram aproximadamente 60 e 63 segundos; não confundir com os custos de geração, registrados nos metadados dos amostradores (aproximadamente 114 e 219 segundos para estas execuções).

Os gargalos mudaram. No inicial, A_CN d12 apresenta MCSE .03149 na CDF da verdade de logAgw e tau estimado 1.161; no quantil05, tau≈1.350. O indicador constante ocorre em B_G d14, logAr na verdade. No Student277, A0_CN d11 apresenta logAr Q05 com MCSE .04938, tau≈3.350, Rhat1,03397 e ESS tail≈20; logL na verdade do mesmo alvo tem MCSE .04069. A_G d4 também mantém medianas de amplitudes com MCSE≈.022. Não selecionar apenas os casos difíceis conhecidos antes: d11 mostra por que o protocolo exige todos os alvos.

Esses tau/MCSEs extremos são estimativas sob mistura deficiente, não previsões certificadas do custo de convergência. A melhora global da proposta não resolve automaticamente caudas, nem permite extrapolar linearmente o comprimento necessário a partir de um único checkpoint.

## Consequências

Conservar os limiares e todas as realizações. Refinar a representação ORF e o algoritmo conforme o protocolo, com avaliação exata das razões MH e proposta congelada na produção. Se uma extensão condicional/Rao–Blackwell for adotada, validar suas integrais e medir MCSE da função condicional própria; não substituir indicador constante por erro zero. O protocolo reserva essa possibilidade sem a implementar ou reaprovar retroativamente os pilotos.

Os 20 cortes de A0_CN d14 podem ser comparados à cubatura quando a referência independente estiver completa. O pacote contém a API e os critérios, mas **não executou essa comparação sem receber a referência**. O piso de Rhat/ESS desse alvo passou no piloto inicial, o que não elimina suas falhas de precisão CDF.

Artefatos rastreáveis: `toy_summary.json`, `test_summary.json`, `pilot139_diagnostics.json`, `pilot277_student_diagnostics.json`, `pilot_comparison.json`; todos os resultados primários têm seeds/fontes/configuração ou hashes dos seus insumos. `null` em campo numérico dos relatórios indica valor não finito preservado por estado explícito de falha, não um valor omitido do critério.
