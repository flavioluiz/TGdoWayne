# Revisão independente dos limites de sensibilidade SBC

Data: 10/09/2026. Escopo: `src/inference/sbc_sensitivity.py` e os seis testes associados, congelados em `snapshot/`. Nenhum dado, verdade ou posterior da campanha PTA500 foi lido. A auditoria executa apenas exemplos algébricos pequenos. Fontes congeladas e SHA-256 constam de `results/audit.json`.

**Conclusão:** as fórmulas dos limites de ECDF, KS, cobertura binomial, Holm e McNemar são conservadoras no domínio pretendido. Há uma guarda de entrada que deve ser corrigida antes da integração pública e uma ressalva de interpretação do campo de rejeição possível. Os valores previstos pelo protocolo 93/62/15 e pelo envelope 15000/.01/.002 não provocam o defeito de entrada encontrado.

**Estado após comunicação ao root:** os itens F1 e F3 abaixo já foram corrigidos na árvore principal: a família agora exige inteiro ≥1, e a flag passou a `rejection_not_excluded_by_rectangular_bounds`. A auditoria preserva o snapshot anterior e os exemplos que motivaram as correções. F2 foi comunicado separadamente; o manifesto registra as duas versões, sem atribuir ao snapshot uma correção que não contém.

**Fechamento final:** F2 também foi corrigido pelo root com `Real/Integral`, rejeição de booleanos/arrays e normalização escalar. Doze controles negativos e um controle de serialização dos metadados passaram na versão final, conforme `results/final_guards.json`, que registra sua SHA-256. F1, F2 e F3 estão encerrados. A seção de achados permanece como histórico rastreável.

## Problemas concretos

1. **`coverage_bounds`, linhas 73–91: família não validada.** `family_size=.5` é aceito. Para 18 sucessos em 20 e probabilidade nominal .9, o intervalo pontual é `[.68301728598, .98765147283]`, enquanto o chamado simultâneo passa a `[.71738147511, .98193479691]`: fica mais estreito, pois usa `alpha/.5=.1`. Família deve ser inteiro positivo, sem `bool`; a guarda existente em `diagnostics._integer` já expressa esse contrato. Validar também `alpha` antes da divisão evita tipos/erros inconsistentes. A reprodução integral está no achado F1 do JSON.

2. **`pit_intervals`, linhas 33–41: controles escalares incompletos.** `deterministic_component=np.array([.002])` é aceito e o relatório devolve um `ndarray`, que falha na serialização JSON comum; `True` também é aceito como componente 1. Um vetor unitário `alpha_mc` termina em `TypeError` ao converter o quantil, em vez de uma rejeição explícita de domínio. Não muda o resultado dos controles escalares oficiais. Convém usar a mesma guarda de real escalar finito do módulo de diagnósticos e normalizar o metadado para `float`. Achado F2 registra as execuções, sem convertê-las em falha estatística.

3. **`holm_sensitivity`, linha 106: rejeição não excluída não significa existência física.** A aritmética está correta para o retângulo de p-valores marginais. O nome `rejection_for_some_permitted_pvalues` precisa ser entendido como “rejeição não excluída pelos limites marginais” ou “rejeição em algum vetor do retângulo relaxado”. Exemplo: se os únicos vetores conjuntamente admissíveis forem `(.026,.9)` e `(.06,.01)`, o primeiro teste tem p ajustado `.052` e `.06`, respectivamente, e não rejeita em nenhum deles. O canto inferior marginal `(.026,.01)` produz `.026` e rejeita, mas não é conjuntamente admissível. A flag de conservadorismo ajuda, porém não deve ser perdida no relatório agregado. Não é necessário alterar a fórmula nem os critérios. Achado F3 contém esse contraexemplo sem supor independência entre testes.

## Conferência matemática

**ECDF.** Se cada PIT verdadeiro satisfaz `L_i <= x_i <= U_i`, então, para todo t,

`sum 1[U_i <= t]/n <= F_n(t) <= sum 1[L_i <= t]/n`.

As buscas com `side='right'` preservam corretamente a inclusão nas igualdades e nos extremos 0/1. Usar `[0,1]` nos não resolvidos mantém todas as realizações no denominador. Os limites também se comportam corretamente para t fora de `[0,1]`.

**KS por estatísticas de ordem.** Ordenar separadamente os limites não exige que o mesmo índice permaneça pareado: da desigualdade coordenada a coordenada resulta `L_(i) <= x_(i) <= U_(i)`. Como

`D(x) = max_i {i/n - x_(i), x_(i) - (i-1)/n}`,

o limite inferior implementado é

`max(0, max_i[i/n-U_(i)], max_i[L_(i)-(i-1)/n])`,

e o superior é

`max(max_i[i/n-L_(i)], max_i[U_(i)-(i-1)/n])`.

Ambos são válidos. O superior é atingível por um dos vetores completos L ou U. O inferior pode ser frouxo: com n=1 e intervalo `[0,1]`, o código devolve 0, embora o menor KS possível seja .5. O campo `lower_statistic_bound_not_asserted_attainable=True` registra corretamente essa limitação. Não é defeito nem motivo para relaxar critérios. A sobrevivência `kstwo.sf(D,n)` decresce em D, portanto a inversão dos extremos dos p-valores está correta. “Exato” refere-se à distribuição KS finita sob PITs verdadeiros IID uniformes e contínuos; não transforma os intervalos SNIS em confiança exata.

**Cobertura.** Para os posteriores contínuos e estritamente crescentes no interior do suporte do recorte, `theta_true <= Q_p` equivale a `F(theta_true) <= p`, salvo questões de igualdade que têm probabilidade zero sob a priori contínua. As desigualdades inclusivas implementadas são coerentes. Cobertura central usa `p_low <= F <= p_high`; contagens certas/possíveis vêm de inclusão/interseção do intervalo de PIT com esse intervalo. Os p-valores binomiais bilaterais não são monotônicos na contagem, por isso enumerar todos os inteiros entre kmin e kmax é a escolha correta. As extremidades Clopper–Pearson crescem com k: o intervalo entre a extremidade inferior de kmin e a superior de kmax contém todos os intervalos admissíveis. A regra Bonferroni permanece válida para família inteira ≥1, independentemente da dependência entre testes. A união é uma propagação determinística condicionada à validade dos limites de PIT; sua cobertura global não é exata quando os limites de PIT são apenas assintóticos.

Esse módulo se destina à campanha de priori contínua. Não se deve interpretar a cobertura de `[0,U90]` numa injeção fixa `u=0` como teste binomial nominal .9: nesse cenário a cobertura é estruturalmente 1 e permanece no utilitário de injeções fixas separado.

**Holm.** A forma por testes fechados de Bonferroni é `p_adj,i = max_{S contendo i} min(1, |S| min_{j em S} p_j)`. Cada operação é monotônica nas coordenadas, provando que aplicar Holm aos cantos inferior/superior limita cada p ajustado mesmo com mudança de ordenação, empates e dependência. `upper_adjusted <= alpha` é suficiente para rejeição em todos os vetores admissíveis; `lower_adjusted > alpha` exclui rejeição. O caso intermediário não é uma conclusão de existência sob restrições adicionais de dependência, conforme F3.

**Pareamento e McNemar.** `cx & ~py` força discordância 10; `px & ~cy` permite 10; as fórmulas 01 são simétricas. Todo par de contagens atingível pertence ao retângulo e satisfaz `n10+n01 <= n`. A implementação inclui esse semiplano, podendo ainda admitir contagens não atingíveis; isso só amplia os extremos do p-valor. Por exemplo, um par forçadamente `(1,1)` e outro totalmente ambíguo permitem contagens reais `(0,0),(1,0),(0,1)`, enquanto o retângulo também admite `(1,1)`. O p-valor `min(1,2 BinomCDF(min(n10,n01); n10+n01,.5))` coincide com o bilateral exato para nulo .5, e discordância zero é corretamente tratada como p=1. Os limites da diferença média seguem de `cx <= X <= px` e `cy <= Y <= py`. O relatório externo deve conferir a igualdade e a ordem dos IDs antes de chamar o utilitário, que recebe apenas vetores booleanos e não tem como verificar identidade.

## Protocolo e execução independente

O envelope padrão corresponde a `z = Phi^{-1}(1-.01/(2*15000)) = 4.970830636716245` e semi-amplitude `.002 + z*MCSE`. Com MCSE=.00335, a semi-amplitude é aproximadamente .0186523; não é ±.002. Os pontos não resolvidos recebem `[0,1]` mesmo com MCSE NaN/infinita, e não são descartados. As estimativas PIT fornecidas ainda precisam ser finitas em `[0,1]`; se nem uma estimativa existir, o agregador deve tratar explicitamente esse caso sem fabricar um PIT. O rótulo assintótico do módulo está adequado.

As famílias científicas permanecem separadas: 93 testes nos controles, 62 nas aproximações, 15 contrastes pareados. Não há controle global de .05 para a união dessas três famílias. A família 15000/.01 do envelope numérico tampouco deve ser confundida com essas famílias científicas.

Verificações executadas:

- Os **6 testes originais** passaram.
- **325 caixas / 4585 atribuições**: KS e ECDF contra cálculo direto dos dois lados dos saltos, incluindo extremos/empates; nenhuma violação ou excesso de arredondamento.
- **80 caixas / 6480 vetores**: Holm contra enumeração independente de todos os testes fechados de Bonferroni; diferença máxima zero.
- **200 casos / 23310 atribuições**: eventos de cobertura e probabilidades binomiais pela soma direta de massas; intervalos CP por inversão numérica das caudas binomiais. Maior diferença residual de p-valor: `4.44e-16`.
- **729 padrões / 4096 atribuições pareadas**: enumeração de todos os estados impossíveis/ambíguos/certos em três pares; limites McNemar e da diferença média contiveram todos os resultados.

Reprodução: `.venv/bin/python tmp/c07_sbc_review/audit.py`. O script importa as fontes congeladas, não modifica o código raiz e salva `results/audit.json`. Essas verificações conferem o utilitário, não executam SBC da PTA nem avaliam verdades das 500 realizações.

## Definição prospectiva por função

Também foi lido `configs/calibration/sbc_synthesis_v1.json`, confrontado com o schema do pacote portátil, antes da produção posterior. A definição é coerente: precisão alta daquela CDF; guardas de pesos e saturação nos dois níveis; seis contrastes entre replicações em cada nível para aquela CDF e logZ; refinamento da CDF e logZ; referências independentes ORF/kernel/quadratura presentes. Os outros PITs não são necessários à precisão dessa função, e seus problemas devem continuar visíveis nos próprios resultados. Não há exigência de erro de evidência .001 em todos os alvos.

Isso preserva as famílias numéricas pré-definidas: no nível menor são `6 PITs × 6 pares + 6 pares logZ = 42`; no maior, `26 CDFs × 6 pares + 6 pares logZ = 162`. São 204 por alvo, 510000 na campanha. Refinamento: seis PITs+logZ = 7 por alvo, 17500 no total. Os vinte cortes escolhidos no nível menor geram controles adicionais de produtos de quantis no nível maior, sem se tornarem vinte novos PITs SBC.

**Cuidado concreto de integração:** o campo `pit_resolved` produzido por `campaign_diagnostics.py` significa apenas MCSE finita. A síntese deve construir explicitamente a flag mais forte `resolved_for_function`; não pode reutilizar apenas aquele campo, nem um `all_pass` global que reprovaria indevidamente todas as funções quando um único corte auxiliar falha. Em falha dos requisitos próprios, o intervalo é `[0,1]` e a realização permanece no denominador. As flags científicas de uniformidade nunca entram nessa decisão numérica.
