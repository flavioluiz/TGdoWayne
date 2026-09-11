# C07: protocolo prospectivo para posterior obtida por MCMC

Versão 2, 10/09/2026. Complementa `docs/protocolo_diagnosticos_c07_v1.md` e o pré-registro do amostrador `tmp/c07_sampler/PREFLIGHT.md`. Não substitui as famílias probabilísticas, os dados ou os critérios determinísticos. `configs/calibration/diagnostics_mcmc_v2.json` foi gravado antes dos experimentos TOY deste pacote e antes de examinar novas cadeias PTA. O módulo de diagnósticos é separado do amostrador e não o implementa. **Não aprova nem executa SBC500.**

## Contrato com o amostrador

Quatro cadeias com fluxos aleatórios independentes por alvo. Inícios dispersos dentro do suporte, sem usar a verdade injetada. Adaptação de escala/covariância somente no aquecimento; descartar todo aquecimento e congelar a proposta na produção. Para coordenadas `x_j=(theta_j-a_j)/(b_j-a_j)` e `z_j=logit(x_j)`, a priori uniforme requer o termo `sum_j(log x_j+log(1-x_j))` na densidade em z. O fator constante da largura cancela no MH, mas não transforma log-posterior em log-verossimilhança. Guardar esta última separadamente para SBC.

Matrizes ORF interpoladas devem passar verificações de Hermiticidade, PSD e precisão, com resolução independente. Preservar PSD por convexidade é necessário, mas não prova precisão da likelihood. Erro amostral de `|delta logL|≤.001` em pontos de validação não é uma garantia uniforme no suporte. Comparar posteriores produzidas com tabelas refinadas e preservar falhas, inclusive caudas. O orçamento ou uma taxa de aceitação plausível não certificam o resultado.

Formato público: `(draw,chain,param)`, sem embaralhar a dimensão temporal; piloto legado `(draw,target,chain,param)`, `target=model*16+replica`, com modelos `A0_CN,A_CN,B_CN,A_G,B_G`. Os parâmetros são `u,log10_Agw,gamma_gw,log10_Ar,log10_EFAC`. A API usa coordenadas normalizadas da priori, portanto tolerância horizontal .001 tem a mesma interpretação nos cinco parâmetros. As verdades físicas usam os limites do JSON original. Guardar IDs, hashes dos dados/fontes/configuração/tabela, seeds, aceitação, duração, aquecimento, número efetivo de passos e motivos de falha.

## Convergência e precisão são verificações distintas

Para cada parâmetro e para a log-verossimilhança, dividir cada cadeia em duas metades; se o comprimento for ímpar, descartar apenas a observação central. Calcular ranks conjuntos, com rank médio em empates, e escores normais

`z=Phi^{-1}((rank−3/8)/(S+1/4))`.

Usar `Rhat=max(Rhat_rank_split,Rhat_rank_folded_split)`, sendo folding o desvio absoluto da mediana conjunta. Exigir **Rhat≤1.01**, **ESS bulk≥400** e **ESS tail≥400**. ESS bulk usa os escores normais; ESS tail é o mínimo dos ESS dos indicadores abaixo dos quantis .05 e .95. Estes pisos são diagnósticos de mistura, não metas suficientes de precisão. Cadeias constantes ou presas não passam. A discussão e os limites vêm de [Vehtari et al., v5, §2 e §4.1–4.3](https://arxiv.org/abs/1903.08008v5).

ESS usa autocovariâncias por FFT com divisor N, variância dentro/entre cadeias e truncamento positivo e monotônico dos pares de autocorrelação. Para calcular erros neste pacote, adota-se conservadoramente `ESS_precision=min(ESS,S)`; o ESS sem esse teto permanece disponível, pois anticorrelação pode legitimamente produzir ESS>S. Não se substitui S por ESS e se declara que os passos viraram independentes.

Para um corte t, calcular o indicador `I(theta≤t)` e a CDF empírica. Estimar `MCSE_ESS=sqrt(p_hat(1−p_hat)/ESS_I)`. Conferir por médias de lotes não sobrepostos, sem concatenar cadeias; usar `b=ceil(sqrt(N))` observações por lote e registrar sobras. Adotar o maior dos dois erros. Exigir pelo menos 16 lotes completos por cadeia e `b≥5 max(1,tau_I)` para considerar essa comparação utilizável. A regra é um controle prático pré-fixado, não prova de independência dos lotes.

Exigir **MCSE≤.00335** nos 20 quantis marginais (.05/.50/.90/.95), nas cinco verdades e no corte `logL(theta_true;y)`. Monitorar também Rhat/ESS de logL; lp em coordenadas logit pode ser diagnosticado adicionalmente, mas não substitui logL no PIT. Os limiares implicam, aproximadamente, ESS 22.277 no corte p=.5, 8.020 em p=.9 e 4.233 em p=.05. Não há exigência universal de um milhão de amostras efetivas.

Se um indicador vale sempre zero ou sempre um, seu MCSE não é registrado como zero: **precisão não resolvida**. Não substituir por um intervalo binomial “exato com n=ESS”. O protocolo do piloto não introduz um envelope alternativo após observar esses casos. Fronteiras estruturais conhecidas do suporte, como u=0, serão declaradas separadamente na etapa de injeções fixas.

Para quantis, usar ESS do indicador e propagar os quantis da `Beta(ESS*p+1,ESS*(1−p)+1)` pela inversa da CDF empírica. A metade da largura correspondente a ±1 sigma é uma estimativa de MCSE. Não exige estimativa de densidade por KDE, mas a cobertura do intervalo de erro ainda é aproximada para MCMC finito. Fonte: [Vehtari et al., §4.4, pp.11–12](https://arxiv.org/pdf/1903.08008v5).

## Referência independente e componentes determinísticos

Mantêm-se os critérios históricos de refinamento **.002 em PIT** e **.001 da largura da priori em quantis**, sempre identificando quando são diferenças observadas entre resoluções, não limites absolutos demonstrados. O ruído Monte Carlo é acrescentado separadamente; não se exige que duas produções finitas difiram por menos desses números sem considerar MCSE.

Para a realização A0_CN d14, confrontar todos os 20 cortes da cubatura independente. A referência deve fornecer `q_ref,p` e a incerteza de `F(q_ref)−p`. Uma tolerância horizontal de quantil não pode ser somada a uma CDF sem mapa/densidade ou outra justificativa. Com erro determinístico de CDF `epsilon_det`, a comparação primária é

`|F_hat_MC(q_ref)−p| ≤ epsilon_det + z_(1−.05/(2*20))*MCSE_MC(q_ref)`.

A mesma família contém os 20 cortes, não vinte famílias escolhidas depois. Exigir simultaneamente o teto de MCSE. A concordância de quantis, usando intervalo MC horizontal ampliado por .001, é registrada como diagnóstico descritivo; não se acrescenta uma segunda família de rejeições sem corrigir a multiplicidade. Cada quantil conserva sua MCSE em unidades normalizadas/físicas.

Para duas produções **independentes**, a diferença de CDF tem erro `sqrt(se1²+se2²)`. Produções com números aleatórios comuns exigem covariância explícita ou erro pareado; prefixo e cadeia completa não são independentes. O critério de referência não valida evidências: MH não fornece a normalização marginal como subproduto. Evidência, quando pertinente, permanece sob cubatura própria e dados idênticos.

Examinar checkpoints de comprimento N e 2N declarados no amostrador; não selecionar o prefixo que passou. Monitorar estabilidade dos ESS, MCSEs, lotes e quantis. Mudança de tabela, proposta ou regra produz versão nova identificada. Se falhar ao alcançar o teto de recursos, registrar insuficiência e decidir novo orçamento antes de continuar; não chamar o teto de convergência. Nenhuma seleção ou abandono de réplicas SBC difíceis é permitida.

## PIT empírico, ranks discretos e dependência

O PIT ideal continua `F(theta_true|y)` e, para a quantidade dependente dos dados, `P[logL(theta;y)≤logL(theta_true;y)|y]`. Usar o mesmo y, a likelihood completa e o alvo correspondente. O estimador MCMC é uma proporção correlacionada com MCSE; não é uma CDF contínua conhecida sem erro. O KS contínuo finito permanece uma referência **ideal**, não um teste exato da saída MCMC aproximada.

Para L amostras posteriores genuinamente intercambiáveis com a verdade, `R=#(theta_l<theta_true)` é uniforme discreto em 0…L. Havendo empates, posicionar a verdade aleatoriamente entre os empatados; então `(R+U)/(L+1)`, com U uniforme independente, tem nula contínua uniforme. Essa propriedade requer intercambiabilidade: jitter, thinning arbitrário ou substituir L por ESS não a restauram para uma cadeia autocorrelacionada. A utilidade de ranks SBC e o papel da dependência estão em [Talts et al., v2](https://arxiv.org/abs/1804.06788v2); a função deste pacote explicita a hipótese e não a certifica.

O protocolo primário usa CDF empírica com incerteza propagada, conservando todas as amostras para eficiência. Histograma de ranks de passos correlacionados pode ser exibido apenas com ressalva ou nula simulada específica. Selecionar uma única observação por cadeia independente é uma alternativa de baixa resolução, válida somente se os estados marginais já representarem a posterior; não é adotada como prova de convergência. O TOY estacionário deste pacote demonstra que jitter não corrige autocorrelação mesmo com marginais normais corretas.

A uniformidade contínua também exige uma estatística sem átomos. Uma log-verossimilhança constante num experimento sem informação não deve ser submetida mecanicamente ao KS contínuo; nesse caso, a randomização depende das CDFs esquerda/direita corretas, como no protocolo v1.

## Propagação para SBC500 e controles

Conservar as famílias v1: 93 hipóteses dos controles corretos A0_CN/A_G/B_G; 62 das aproximações A_CN/B_CN; dez do controle que devolve a priori; quinze contrastes pareados de cobertura. Holm é aplicado separadamente; não há alegação de FWER global .05 ao juntar todas as famílias. A precisão binomial de cobertura .9 em N=500 é `sqrt(.9*.1/500)=.013416`, ou 1,34 ponto percentual. A meta .00335 reduz o erro de inferência por réplica, mas não elimina viés, autocorrelação residual ou incerteza na classificação de cobertura.

Além do relatório nominal, propagar intervalos de erro dos PITs: `p_hat±(epsilon_det+z*MCSE)`, truncados ao domínio probabilístico. Para uma campanha principal de 5 modelos×500 réplicas×6 quantidades, fixar família de 15.000 intervalos de Monte Carlo e erro familiar .01 por Bonferroni. São intervalos CLT aproximados, não limites rigorosos uniformes; a componente determinística continua dependendo da evidência de refinamento. Outras quantidades/controles têm famílias próprias pré-identificadas. Não reutilizar o intervalo pontual .95 como simultâneo de milhares de resultados.

O utilitário fornece limites de sensibilidade para a estatística KS e seus p-valores sobre todos os PITs contidos nesses intervalos. Para cobertura de `theta_true≤Qp`, classificar como certamente coberto se o limite superior de PIT≤p e possivelmente coberto se o limite inferior≤p; reportar contagens mínima/máxima e número ambíguo. Intervalos centrais usam a mesma lógica com ambos os cortes. Aplicar Holm aos extremos de p-valores para verificar estabilidade da decisão; não procurar o extremo favorável. As bandas podem ser largas: se a conclusão muda dentro delas, declarar precisão insuficiente ou refinar segundo a regra previamente documentada.

Não adicionar o MCSE de inferência em quadratura ao erro binomial da cobertura como se a classificação não fosse descontínua. Reportar separadamente a incerteza binomial entre réplicas, a estimativa Monte Carlo dentro de cada posterior e a sensibilidade determinística. A ausência de rejeição sob bandas largas não certifica calibração.

O controle que retorna a priori permanece obrigatório: os PITs dos parâmetros podem ser uniformes enquanto o PIT de logL detecta dados ignorados. Mantêm-se o modelo TOY analítico e os cenários de ausência de informação. Injeções fixas não recebem teste PIT-uniforme; em u=0, `[0,U90]` tem cobertura 100% estrutural, não nominal 90%. Nenhuma alteração MCMC resolve essas distinções estatísticas.

## Validação e proveniência

`tests/test_mcmc_diagnostics.py`: FFT versus produtos diretos, escores/ranks/empates, divisão temporal, cadeias deslocadas/com escalas distintas/constantes, transformação afim do erro de quantil, soma quadrática para produções independentes e limites de sensibilidade conferidos por enumeração amostral. `scripts/validar_diagnosticos_mcmc_toy.py`: IID e AR(1) estacionário com marginal N(0,1), ESS teórico da média e do indicador em zero, 128 repetições de CDF e comparação de ranks IID versus correlacionados. As seeds e tolerâncias foram pré-fixadas; os resultados são **TOY, não calibração da PTA**. A primeira execução encontrou apenas uma falha de serialização de `numpy.bool_`; foi corrigida, sem mudar critérios ou seeds.

Vehtari v5 foi baixado em `literature/papers/1903.08008v5.pdf`, 26 páginas, SHA registrado em `literature/catalog.json`; leitura dirigida §2, §3.2 e §4.1–4.4. Licença arXiv nonexclusive-distrib/1.0: manter cópia local/catalogada, **não pressupor permissão de redistribuição no git**. A documentação Stan 2.39 foi consultada como apoio; as definições implementadas seguem o artigo primário. Nenhum código externo de diagnósticos foi copiado.

## Extensão prospectiva reservada: Rao–Blackwellização

Se indicadores extremos ou mistura persistirem, uma extensão posterior poderá usar `g_t(psi)=Pr(theta_j≤t|psi,y)` e calcular a mesma CDF por `E[g_t(psi)|y]`, integrando condicionalmente escalas/amplitudes. Isso preserva o alvo somente com a medida/priori/Jacobiano e a likelihood completos. As rotinas condicionais de escala já existentes no projeto oferecem um possível ponto de partida; este pacote não as implementa nem as aprova.

O MCSE deverá usar a variância espectral ou médias de lotes da função `g_t` efetivamente amostrada, **não** a variância Bernoulli `p(1−p)`. Redução de variância marginal não dispensa a análise de autocorrelação. A integração condicional recebe orçamento determinístico próprio, preservando a meta global. Um valor condicional constante devido a underflow não prova resolução de uma cauda. LogL pode admitir integração condicional, mas deve manter a mesma quantidade dependente dos dados. Essa extensão exige testes analíticos e registro da versão antes de novas cadeias; não reclassifica retroativamente os pilotos 139 ou 277, nem altera os critérios usados nos relatórios deste pacote.

## Integração no repositório

O módulo está em `src/inference/mcmc_diagnostics.py`. O pré-registro do amostrador e os dois pilotos citados acima são preparatórios; suas falhas ficam preservadas em `results/C07/pilot_mcmc_history/`. As amostras grandes permanecem no diretório temporário, com hashes nos relatórios; os resultados históricos não são reclassificados após mudanças no amostrador. O comando TOY integrado foi executado novamente e os números comparados com o pacote preparatório.
