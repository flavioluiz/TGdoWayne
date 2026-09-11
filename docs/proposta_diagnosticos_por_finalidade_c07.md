# Proposta prospectiva: diagnóstico por finalidade e custo de produção

**Estado: proposta para uma nova produção, não emenda dos critérios históricos.** O protocolo IID v1, o protocolo MCMC v2 e os resultados de seus pilotos ficam intactos. Nenhum alvo histórico passa a ser aprovado por retirar critérios depois da execução. Esta separação especifica quais produtos futuros exigem cada quantidade e permite relatar resultados científicos e limitações numéricas sem confundi-los.

## O que são as26CDFs por alvo

Cada alvo corresponde a um modelo e uma realização. Há cinco parâmetros, não vinte: u, log10 A_GW, γ_GW, log10 A_r e log10 EFAC. O relatório piloto computa5CDFs nas respectivas verdades,1CDF de logL na verdade e20CDFs em cortes associados aos quatro quantis de cada parâmetro. Portanto26=5+1+5×4. Os últimos20são diagnósticos de quantis, não vinte PITs adicionais.

| Finalidade | Quantidades mínimas | Precisão e limites |
|---|---|---|
| Uniformidade SBC de parâmetros | 5PITs: F_j(θ_j,verdade\|y) | MCSE≤.00335 por função; componente determinístico .002 e sensibilidade simultânea |
| Controle de uso dos dados | 1PIT de logL(θ;y), na mesma verdade/dado | Mesma meta; não substituir por logw, logposterior ou densidade da proposta |
| Coberturas unilaterais em .05/.5/.9/.95 | Os mesmos5PITs de parâmetros | Evento F_j(θ_j,verdade)≤p sob posterior contínua; não requer20novasCDFs |
| Cobertura central90% | Os mesmos5PITs | Evento .05≤F_j(θ_j,verdade)≤.95; considerar ambiguidade dos intervalos de erro |
| Valor publicado de U90 para massa | Quantil Q_u(.9), sua incerteza horizontal e CDF local | MCSE da CDF≤.00335; a precisão horizontal não segue dessa condição sem inversão/controle da densidade |
| Medianas e intervalos marginais publicados | Somente os quantis efetivamente apresentados | Mesma distinção entre erro vertical e horizontal; calcular os20apenas se todos forem produtos do estudo |
| Benchmark externo A0_CN,d14 | Os20brackets e40CDFs nos extremos fixos | Preservar Bonferroni40unilaterais, componente .002 e largura horizontal .001 da priori |
| Evidência/Bayes factor, se relatado | Z completo e sua referência específica | Critério próprio, dados e medida compatíveis; não é condição adicional para uma análise que não relata evidência |

Os93testes da família correta podem continuar: por modelo são6testes de uniformidade,20coberturas unilaterais e5coberturas centrais. Todas essas coberturas se obtêm dos5PITs de parâmetros. Três controles corretos dão93hipóteses; os dois modelos aproximados dão62em família separada. Isso preserva as finalidades estatísticas sem exigir20integrais adicionais por alvo. A0_CN,A_G e B_G são controles da calibração; A_CN/B_CN podem apresentar falha científica de calibração mesmo quando a integração está precisa. Não se deve buscar uniformidade destes últimos ajustando critérios.

Para distribuições com átomos ou empates estruturais, a equivalência simples exige tratamento de CDF esquerda/direita e da convenção de quantil. A priori contínua em u não tem átomo em zero. Na experiência separada de injeção fixa u=0, [0,U90] contém a verdade por construção; sua cobertura é100%, sem teste de nominal90%. Injeções fixas não recebem teste geral de PIT uniforme.

## Planejamento sem acesso às verdades

O tamanho da produção pode depender dos dados observados e de um piloto independente da produção; não deve depender das verdades injetadas, dos seus ranks ou de uma decisão de uniformidade SBC. O ajuste da proposta usa somente y e seu alvo posterior. A etapa de planejamento recebe amostras/pesos/logL do piloto, hashes e IDs; sua interface não recebe `truth_unit` nem `truth_log_likelihood`.

Uma regra candidata é:

1. Congelar, antes de novos dados de produção, o tipo de proposta, orçamento do piloto, R, escada de N, margem de planejamento, máximo por alvo e máximo global. Reservar fluxos RNG distintos para ajuste, piloto de planejamento e produção.
2. Ajustar a proposta usando dados/aquecimento e congelá-la. Produzir o piloto independente para essa proposta; ele não entra no estimador final. Se o piloto motivar mudar a proposta, gerar outro piloto independente; todas as tentativas ficam registradas.
3. Sem ler verdades, estimar a maior MCSE da CDF de cada um dos cinco parâmetros e de logL ao longo dos cortes observados ordenados. Alternativamente, usar uma grade de probabilidades densa previamente fixada, identificando que o máximo vale apenas nessa grade. Incluir influência IID e entre replicações, concentração dos pesos e guardas de cauda. Os extremos onde os indicadores são estruturalmente constantes na amostra não provam precisão da cauda não visitada.
4. Se o piloto estiver numericamente regular, projetar N pela relação de planejamento N\_prod≈N\_pilot×(m×s\_max/.00335)², com margem m fixada previamente, por exemplo2. Arredondar para o próximo valor da escada, preservando R. A lei1/√N é uma projeção condicional ao regime de variância útil; não é um teorema para uma proposta problemática.
5. Congelar N e gerar produção nova, sem reutilizar o piloto. Não parar antecipadamente porque um PIT de verdade passou, e não aumentar seletivamente o comprimento segundo esses PITs. Encerrar no N fixado e avaliar todos os requisitos pertinentes.
6. Se a produção falhar em precisão, registrar falha/faixa incerta. Uma extensão deve obedecer a regra prospectiva previamente aprovada, com orçamento e tratamento de dependência explícitos; não escolher retrospectivamente um prefixo ou uma replicação favorável. Sob orçamento esgotado, a realização continua no denominador da campanha.

A margem2 é uma proposta operacional, não um limite probabilístico sobre a variância. Não está aplicada aos pilotos existentes. O ROOT deve congelar uma escada e o orçamento final após comparar os pilotos de propostas e antes de produzir a campanha; este documento não autoriza uma campanha nova. Uma escada candidata em potências de2 permite loteamento previsível, mas o teto global precisa ser calculado em avaliações de likelihood e armazenamento, considerando2500alvos.

Para a importância IID, é possível obter a variância plug-in em todos os cortes observados sem calcular uma matriz de indicadores N×N. Ordene os valores, acumule p_i e p_i². Com F=Σ_{x_i≤t}p_i e S₂(t)=Σ_{x_i≤t}p_i², a componente IID é

    se²(t) = N/(N−1) [S₂(t)(1−2F)+F²S₂(total)].

Para Rreplicações de mesmo N, P_r=Σ_{i em r}p_i e A_r(t)=Σ_{i em r,x_i≤t}p_i. A componente entre replicações pode ser computada por

    se_R²(t) = R/(R−1) Σ_r [A_r(t)−P_r F(t)]².

Essas identidades seguem das influências já usadas no código. Empates precisam ser acumulados juntos. O máximo ao longo dos cortes observados é um instrumento de planejamento sem verdades; não é uma banda uniforme garantida nem controla regiões que não apareceram no piloto. Uma implementação nova dessas varreduras exigirá testes independentes antes de entrar no controle de produção; ela não é apresentada aqui como funcionalidade já executada.

O denominador SNIS deve continuar incluído na influência de cada CDF. Seu logZ e a MCSE podem ser armazenados como diagnósticos de custo muito baixo. Isso não obriga a exigir MCSE(logZ)≤.001 em todos os alvos, quando evidência não será relatada. Mantém-se inalterado o critério .001 da referência de cubatura e sua validação específica.

## Todos os500resultados permanecem na análise

A campanha futura deve guardar para cada modelo/realização: estimativa dos6PITs, MCSE por função, componente determinístico, estado de caudas/concentração, orçamento efetivamente usado e motivo de qualquer precisão não resolvida. Não excluir realizações difíceis, nem reduzir o denominador a uma amostra selecionada de aprovados. É possível relatar uma diferença de calibração robusta nas aproximações e, ao mesmo tempo, reconhecer alvos com integração incerta.

Separar três estados: **resolvido numericamente**, **resultado científico incompatível com calibração ideal** e **conclusão inconclusiva por erro de integração**. Uma rejeição robusta de uniformidade em A_CN/B_CN não reprova o integrador por si só. Uma falha robusta em A0_CN/A_G/B_G requer investigação, pois esses controles são probabilisticamente corretos por construção sob suas hipóteses. Nenhuma ausência de rejeição prova calibração.

## ECDF dosPITs com envelope de sensibilidade

Para cada PIT, construir [L_i,U_i] pela estimativa±(ε_det+z×MCSE), limitada a[0,1], seguindo a família simultânea pré-fixada de15000PITs e α_MC=.01. São intervalos aproximados baseados em CLT, não intervalos exatos. O componente determinístico pode ser uma diferença de refinamento observada; deve manter esse rótulo. Quando a integração está não resolvida e nenhum limite adicional foi justificado, usar [0,1] conservadoramente, com flag explícita. Não substituir MCSE ausente por zero.

Com N=500fixo, o envelope induzido para a ECDF é

    G_lower(t) = (1/N) Σ_i 1[U_i≤t],
    G_upper(t) = (1/N) Σ_i 1[L_i≤t].

O desenho recomendado é uma curva em degraus para a ECDF nominal, diagonal t e área sombreada entre essas duas funções. Informar na legenda o número total500, a quantidade não resolvida, a meta .00335, a natureza aproximada do envelope e o erro de multiplicidade adotado. Se também houver banda amostral ideal de uniformidade, desenhá-la separadamente e identificá-la como referência ideal; não confundir incerteza entre realizações com erro numérico dentro de cada posterior.

As desigualdades da ECDF são exatas **condicionalmente aos intervalos conterem osPITs ideais**. A validade de tais intervalos é aproximada; o gráfico não transforma uma MCSE estimada em prova. Usar o envelope para verificar se a conclusão muda ao variar todos osPITs dentro de suas faixas. Uma realização sem informação sobre seuPIT amplia a faixa em até1/500; ela continua contabilizada.

Cobertura unilateral em p pode ser apresentada como intervalo de contagens: certamente cobertos=Σ1[U_i≤p]; possivelmente cobertos=Σ1[L_i≤p]. Para intervalo central[a,b], certamente cobertos têm L_i≥a e U_i≤b; possivelmente cobertos têm U_i≥a e L_i≤b. Reportar ambiguidade e a incerteza binomial entre as500realizações separadamente. Não somar MCSE de PIT em quadratura a um erro binomial de uma classificação descontínua.

O protocolo de multiplicidade dos testes científicos permanece pré-fixado. Pode-se aplicar os limites de sensibilidade de KS e dos p-valores já disponíveis para observar se a decisão de Holm é estável, sem procurar o extremo favorável. Se ela mudar, a conclusão fica inconclusiva ou recebe refinamento conforme a regra aprovada. Não há gráfico SBC500 neste pacote: os dados dessa campanha posterior ainda não foram executados aqui.
