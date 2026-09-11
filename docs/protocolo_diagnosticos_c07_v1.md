# Diagnósticos prospectivos de C07

Protocolo v1, 10/09/2026, escrito antes dos sorteios TOY deste pacote. Os parâmetros numéricos estão em `configs/calibration/diagnostics_v1.json`, cujo SHA-256 será registrado nos resultados. **Nenhuma campanha PTA de 500 realizações foi executada aqui.** O piloto PTA histórico de 16 realizações tem problemas de integração documentados e não recebe teste conclusivo de calibração por este pacote.

## Experimentos e decisão estatística

Em SBC, sortear independentemente 500 vetores contínuos da priori declarada e, para cada vetor, novos dados do experimento correspondente. A0_CN recebe os coeficientes físicos; A_CN/B_CN recebem estatísticas quadráticas/compressões do mesmo sorteio; A_G/B_G recebem outro experimento, normal, pareado por variáveis latentes. A dependência entre análises da mesma réplica é admitida. A independência exigida é entre réplicas. Os cinco parâmetros são `u, log10_Agw, gamma_gw, log10_Ar, log10_EFAC`.

O PIT do parâmetro j é `F_j(theta_j_true | y)`. A quantidade dependente dos dados é

`P_{theta~posterior(.|y)}[log L(theta;y) <= log L(theta_true;y)]`.

Usa-se o **mesmo dado y**, a mesma família probabilística e a log-verossimilhança completa, inclusive normalizações dependentes dos parâmetros. Não usar log-posterior, razão de importância `log(L/q)` ou avaliação em novos dados. Constantes independentes de theta cancelam na ordenação; isso não autoriza omitir determinantes dependentes de theta.

Sob um modelo e algoritmo corretos, a verdade condicional ao dado tem a distribuição posterior; portanto PITs de quantidades contínuas, inclusive dependentes do dado, são uniformes. Isso não implica uniformidade sob uma verdade fixa. A abordagem vem de [Talts et al., v2](https://arxiv.org/abs/1804.06788v2) e da escolha de quantidades sensíveis discutida por [Modrák et al., v3](https://arxiv.org/abs/2211.02383v3). Usar a log-verossimilhança amplia o diagnóstico, mas um teste específico não prova a correção integral de toda posterior.

## Pré-requisitos numéricos e integridade

Antes da interpretação SBC, concluir verificações independentes e os refinamentos do integrador. O booleano de aprovação é fornecido explicitamente por documento externo de revisão; não é inferido de PITs aparentemente uniformes. Exigir valores finitos, PIT em [0,1], quantis monotônicos, 500 IDs únicos e as cinco análises completas. Não recortar PITs, substituir NaNs ou eliminar seletivamente réplicas difíceis. Falhas interrompem o relatório conclusivo; registrar todas e repetir a campanha ou a inferência conforme regra de parada prévia, conservando dados/sementes quando a mudança for exclusivamente numérica.

Os níveis atuais verificam diferenças de PIT de 0,002 e quantis de 0,001 da largura da priori. Diferença entre duas resoluções não é uma prova de erro absoluto abaixo desses valores. O utilitário mostra a sensibilidade do p-valor KS à variação `D±0,002`, explicitamente sem transformá-la em garantia certificada. Se uma conclusão depender dessa escala, aprofundar integração; não escolher posteriormente um teste menos sensível.

CDFs obtidas por quadratura são contínuas aproximadas, não ranks de amostras IID. Se o método passar a usar amostras posteriores, criar protocolo específico para ranks discretos, empates e autocorrelação. No protocolo atual, contar valores exatamente 0/1 e empates; não acrescentar jitter para melhorar uniformidade. Na presença de uma estatística com átomos, usar PIT randomizado com uma fonte uniforme independente pré-especificada e CDF esquerda/direita, ou outro teste apropriado; o KS contínuo deste pacote não é aprovado para essa alteração.

## Hipóteses e multiplicidade predefinidas

Nível familiar `alpha=0,05`; teste de uniformidade primário KS bilateral de uma amostra, distribuição nula contínua exata de tamanho finito. Estatística calculada por `max(max(i/N-u_(i)), max(u_(i)-(i-1)/N))`. O utilitário usa sua distribuição finita no SciPy; testes independentes comparam com `scipy.stats.kstest(method='exact')`. Não ajustar uma distribuição uniforme aos próprios PITs. [Documentação oficial KS](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.kstest.html).

Para cada análise, são 31 hipóteses: seis PITs; 20 probabilidades `Pr(theta_j <= Q_p)=p`, para cinco parâmetros e `p=.05,.50,.90,.95`; cinco coberturas centrais `Pr(Q_.05 <= theta_j <= Q_.95)=.90`. O teste das contagens é binomial bilateral exato. O intervalo `[0,U90]` para u duplica o teste de Q_.90 em SBC com suporte não negativo e não entra duas vezes.

- **Família correta:** A0_CN/A_G/B_G, total **93 hipóteses**, correção Holm conjunta. Uma rejeição exige investigação numérica/modelo; não atribuir automaticamente a ruído Monte Carlo. Não rejeitar significa compatibilidade na resolução estatística disponível, não certificação de equivalência.
- **Família aproximada:** A_CN/B_CN, total **62 hipóteses**, Holm separado. Rejeição pode ser efeito da família de verossimilhança, mesmo com posterior aproximada integrada precisamente. A–B não deve ser interpretada como perda isolada de informação quando essa família falhar.
- **Controle negativo de dados ignorados:** cinco PITs de parâmetros sob a priori, comuns às análises, mais um PIT de logL sob a priori por análise: **10 hipóteses**, Holm separado. Parâmetros sozinhos podem passar por construção. Este controle mede sensibilidade do diagnóstico; não o inclui na família dos algoritmos que se deseja aprovar.
- **Contrastes pareados primários:** cobertura central de 90% para cinco parâmetros nos pares A_CN–B_CN, A_G–B_G e A0_CN–A_CN: **15 testes McNemar exatos**, Holm separado. As famílias respondem perguntas distintas; não anunciar FWER global de 5% ao unir todas as conclusões. Uma única alegação global exigiria correção adicional predefinida.

Holm controla FWER dentro de cada família mesmo com testes dependentes; nenhuma independência entre modelos, parâmetros ou quantis é pressuposta. A comparação dos modelos usa as mesmas réplicas. Os testes não serão escolhidos ou seus limiares relaxados após observar resultados. Se múltiplas geometrias tiverem campanhas completas, registrá-las como famílias separadas com conclusões condicionais ou incorporar previamente todas as hipóteses à família conjunta; não reunir observações não identicamente distribuídas numa contagem binomial sem justificar o experimento.

## Cobertura, incerteza Monte Carlo e N=500

Para k coberturas em N réplicas IID, reportar k/N, erro MC `sqrt(p_hat(1-p_hat)/N)` e intervalo binomial exato de Clopper–Pearson de 95%. Em k=0 ou N, o erro plug-in é zero, mas o intervalo exato continua não degenerado; nunca concluir certeza apenas desse erro. Reportar também intervalo simultâneo Bonferroni usando o tamanho da família (93 ou 62), conservador e distinto dos p-valores Holm. [Teste e intervalo exatos no SciPy](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.binomtest.html).

Em N=500 e p=.9, o erro MC sob a hipótese é **0,013416**, ou 1,34 ponto percentual. Para p=.5, é 2,24 pontos; para p=.05/.95, 0,975 ponto. O JSON de exemplo registra bandas centrais binomiais exatas e intervalos, evitando confundir banda de contagem sob p conhecido com intervalo para p desconhecido. O fato de um resultado ficar a menos de dois erros MC de .9 não substitui multiplicidade e análise de dependência.

Para duas coberturas pareadas, `d_r=I_r(X)-I_r(Y)` tem erro MC `sd(d)/sqrt(N)`. O McNemar exato condiciona ao total de discordâncias: sob igualdade das coberturas, a direção de discordância é Binomial(n_discord,.5). Não somar variâncias como se os métodos fossem independentes. O pacote fornece também intervalo t aproximado da média e um intervalo Hoeffding conservador para a diferença binária; não chama o primeiro de intervalo exato. Se não houver discordâncias, p=1 e intervalo t degenerado não provam igualdade populacional: o intervalo conservador permanece com largura positiva.

Diferenças de medianas, larguras e erros quadráticos podem usar a mesma função de média/erro MC pareados, com intervalos t **descritivos**. Sem hipótese extra sobre distribuições e N, não são testes exatos. Não subtrair log-evidências A0/A/B para formar fatores de Bayes: os dados e suas dimensões diferem.

## Injeções fixas, fronteiras e ausência de informação

Cada cenário fixo tem sua própria verdade e N, sem mistura com SBC. Não aplicar KS-uniforme a seus PITs. Coberturas de intervalos bayesianos são reportadas como propriedades condicionais estimadas; nem os modelos corretos têm cobertura frequentista nominal garantida em cada theta.

Em `u=0` e suporte `[0,1]`, `[0,U90]` contém a verdade em todas as realizações admissíveis: cobertura **100% estrutural**, e não 90%. Um intervalo de caudas iguais `[Q05,Q95]` para uma posterior contínua pode excluir u=0 em todas as realizações. Esses dois fatos não demonstram defeito numérico. No extremo u=1, o limite U90 de uma posterior contínua em [0,1] também pode nunca cobrir a fronteira superior. Reportar esses cenários e a distribuição de U90; não ajustar o critério depois de vê-los.

Massa zero com sinal tensorial e ausência de sinal são cenários distintos. Uma amplitude exatamente nula não pertence ao prior de amplitude logarítmica finita: o gerador de ausência de sinal deve ser explicitamente definido como experimento fora desse suporte ou hipótese pontual própria. CDF marginal uniforme quando não há informação não demonstra sensibilidade à massa. A razão de evidências entre RG pontual e massa contínua exige validação própria e dados/medidas idênticos; não é aprovada por este pacote.

O algoritmo negativo retorna a priori independentemente de y. Em SBC, `F_prior(theta_true)` é uniforme e as coberturas dos quantis da priori são nominais. Portanto, além da logL, registrar distância dos quantis posteriores aos quantis da priori, largura e resposta a dois dados deliberadamente distintos. Igualdade de apenas quatro quantis é um aviso, não prova de identidade de distribuições. Uma posterior igual à priori pode ser correta em um experimento sem informação: o controle negativo deve ser demonstrado em um modelo informativo previamente definido.

## Validação TOY, independente da PTA

Configuração fixada antes da execução: 4.096 réplicas, cinco dimensões, `theta~N(0,I)` e `y|theta~N(theta,0,3² I)`, seed 707209106. O prefixo de 500 será relatado também, escolhido antecipadamente, sem procurar uma subsequência favorável. A posterior exata é `N(m,vI)`, `v=(1+1/sigma²)^(-1)`, `m=v*y/sigma²`.

Para qualquer candidato `theta'~N(a,s²I)`, a CDF de logL na verdade é

`sf_ncx2(||y-theta_true||²/s²; df=5, nc=||y-a||²/s²)`.

Essa identidade permite avaliar o algoritmo exato e o algoritmo-priori sem amostragem posterior. A fórmula é conferida em dimensão um por probabilidades de caudas normais e quadratura adaptativa independente, e a posterior é conferida integrando produto priori×likelihood. Tolerância determinística **1e-10**. O controle logL-priori deve rejeitar após multiplicidade a .05; uma eventual rejeição do controle exato é relatada, nunca eliminada por trocar seed, e não serve como teste unitário determinístico.

Uma segunda demonstração usa `u~Uniforme(0,1)`, `y|u~N(u,.15²)`, posterior normal truncada analítica, 500 réplicas por verdade fixa `u∈{0,.05,.5,1}`, seed 707209107. Serve somente para conferir cobertura de fronteira e utilitários. Não modela ondas gravitacionais, não calibra o integrador PTA, não valida ORFs e não constitui SBC500 da dissertação.

## Entradas e integração futura

Preservou-se a ordem histórica: `pit[M,N,5]`, `quantiles[M,N,5,4]`, `data_dependent_loglikelihood_pit[M,N]`, `ignored_data_prior_loglikelihood_pit[M,N]`, `truth[N,5]`. Métodos e parâmetros são explicitamente nomeados. Cada índice de réplica é o mesmo nos cinco modelos; ao combinar arquivos, conferir hash/configuração, sementes, IDs e ordem. O adaptador não faz interseção silenciosa de réplicas.

`src/inference/diagnostics.py` implementa os utilitários sem dependência do pipeline PTA. `scripts/validar_diagnosticos_toy.py` e seus resultados ficam rotulados TOY. `scripts/diagnose_campaign.py` somente lê produtos de inferência já concluídos e requer um documento explícito de aprovação numérica, N planejado e resultados completos. O presente pacote não cria esse documento de aprovação para a PTA e não altera `tmp/c07_integration/`.
