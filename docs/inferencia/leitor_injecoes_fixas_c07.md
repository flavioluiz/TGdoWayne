# Contrato prospectivo do leitor de injeções fixas

Este documento especifica a adaptação necessária ao leitor de posteriores. Não é um leitor executado. O produtor pode reutilizar o runtime C07 com a configuração n=96 e a tabela interpolada previamente aprovada pelo root; este pacote não construiu essa tabela nem um banco de momentos. A seleção deve ser `models=["A0_CN"]`, `targets=list(range(96))`. Os arrays das observações obedecem ao loader existente e o produtor continua sem desserializar `truth`.

## Metadados dos dados

| Campo | Forma | Uso |
|---|---|---|
| `truth` | 96×5 | Coordenadas físicas originais; NaN onde não existe verdade geradora |
| `truth_defined` | 96×5, bool | Autoriza diagnóstico de PIT/viés/cobertura daquele parâmetro |
| `coverage_parameter_defined` | 96×5, bool | Igual à máscara de verdade neste desenho |
| `log_likelihood_at_truth` | 96 | LogL CN com constantes completas nos 64 casos com sinal; NaN nos outros |
| `log_likelihood_at_truth_defined` | 96, bool | Autoriza o diagnóstico de logL na verdade |
| `structural_lower_boundary_pit` | 96×5, bool | Apenas u nas primeiras 32 linhas é verdadeiro |
| `scenario_index` | 96 | 0: u=0; 1: u=.995; 2: sem GW |
| `replicate_within_scenario` | 96 | 0…31, sem descarte |
| `target` | 96 | 0…95, coincidente com os targets A0 no runtime n=96 |
| `signal_present` | 96, bool | Duas primeiras séries verdadeiras; terceira falsa |

A covariância normalizada total, gravitacional e de ruído por cenário é preservada em `covariance_by_scenario`, `gw_covariance_by_scenario` e `noise_covariance_by_scenario`, formas 3×4×12×12. Não são consumidas pelo posterior: servem à rastreabilidade e à verificação do gerador.

## Estados por função

Cada diagnóstico posterior precisa separar três propriedades: **aplicável**, **estrutural exato**, **numericamente resolvido**. Uma máscara única de finitude não consegue representá-las.

1. **Aplicável e não estrutural:** avaliar a CDF pelos pesos IID e aplicar os controles numéricos próprios da função, como no protocolo prospectivo. Se não resolvida, preservar estimativa/flags e usar `[0,1]` como sensibilidade. Constantes amostrais não estruturais continuam não resolvidas.
2. **Aplicável e estrutural:** em u=0 sob a priori contínua em `[0,1]`, a posterior tem `F_u(0)=0` exatamente. Pode-se registrar PIT=0, erro MC=0 e intervalo `[0,0]`, com `structural_exact=True`. Não passar esse zero ao validador genérico que exige MCSE positiva, nem tratá-lo como cauda amostral não resolvida. Essa identidade decorre do suporte e da ausência de átomo posterior no extremo; não depende dos draws. Falhas de outros diagnósticos continuam registradas.
3. **Não aplicável:** nas últimas 32 linhas, u, log10_Agw, gamma_gw e o logL do vetor de verdade de cinco parâmetros permanecem NaN/`null` e recebem `applicable=False`, `status="NO_GENERATING_TRUTH"`. Não atribuir PIT0/.5, intervalo `[0,1]`, viés, cobertura ou p-valor. `[0,1]` representa uma integral existente mas não resolvida; aqui a quantidade não existe. Os parâmetros log10_Ar e log10_EFAC continuam aplicáveis.

Os dados sem sinal são ajustados futuramente pelo modelo com sinal e pela sua priori original finita. A ausência de sinal está fora do suporte dessa priori de amplitude logarítmica. A densidade de geração sob o ruído é finita, mas não é `L(theta_true)` da família de cinco parâmetros num ponto inexistente. Não usá-la como limiar do diagnóstico posterior de logL nem como evidência de um modelo nulo.

## Eventos de cobertura e síntese

Para u=0, `theta_true <= Q_p` tem cobertura estrutural 1 para p positivo e `[0,U90]` inclui sempre a verdade. O intervalo central `[Q05,Q95]` não inclui o extremo sob uma posterior contínua estritamente positiva no suporte interior. Esses fatos não são testes de calibração nominal .9 e devem ter rótulo estrutural.

Para os outros parâmetros/cenários aplicáveis, reportar contagens entre as 32 realizações e intervalos Clopper–Pearson pontuais de 95%, com possíveis faixas de sensibilidade quando a integral não for resolvida. Não exigir cobertura frequentista universal .9 para intervalos bayesianos em uma verdade fixa. Não aplicar KS uniforme aos PITs de injeções fixas, nem misturar essas linhas com as 500 realizações de priori contínua. Se um parâmetro não se aplica a todo um cenário, seu denominador de cobertura é **não aplicável**, e não zero sucessos em 32.

Os quatro quantis podem ser salvos descritivamente para todos os parâmetros ajustados, inclusive quando não existe verdade geradora. Por exemplo, o limite de massa sem GW pode ilustrar ausência de informação ou dependência da priori, mas não recebe escore de recuperação da massa. A precisão de CDF não certifica erro horizontal de quantil; manter as flags correspondentes separadas.

## Validações a executar na futura adaptação

- Conferir hashes dos dados/protocolo/configuração e correspondência inequívoca target→cenário→réplica.
- Nunca passar NaNs de verdade ao cálculo da likelihood, ao normalizador de coordenadas para treino ou ao checker genérico de CDF; avaliar apenas as coordenadas autorizadas.
- Conferir a recuperação das máscaras após serialização NPZ/JSON, com `null` no JSON e NaN com máscara no NPZ.
- Manter todos os 32 IDs de cada cenário, inclusive falhas numéricas e não aplicabilidade.
- Testar separadamente o evento estrutural u=0, uma cauda constante não estrutural e um campo sem verdade. Eles não podem receber o mesmo estado por conveniência.
- Não reaproveitar automaticamente a família numérica 510000/17500 da campanha500 para afirmar um novo controle familiar das injeções. O leitor fixo deve declarar antes dos posteriores sua própria multiplicidade/limiares para as funções aplicáveis, ou uma extensão explícita do protocolo aprovada pelo root.
