# Proposta de mestrado

## Massa do gráviton e polarizações de ondas gravitacionais em PTAs: efeitos da compressão em frequência e validação estatística

**Área:** Gravitação, astrofísica e física computacional.  
**Duração proposta:** 24 meses.  
**Base histórica:** Wayne Leonardo Silva de Paula, *Estados de polarização de ondas gravitacionais com gráviton massivo*, ITA, 2003.  
**Data da pesquisa bibliográfica:** 10 de setembro de 2026.  
**Natureza deste documento:** proposta preliminar apoiada em leitura do TG, busca bibliográfica dirigida e checagens cinemáticas reproduzíveis. O ineditismo do recorte deverá ser confirmado na revisão inicial; os resultados científicos da dissertação ainda não foram produzidos.

## 1. Resumo

Propõe-se investigar a confiabilidade da inferência da massa do gráviton e de polarizações adicionais de ondas gravitacionais com redes de temporização de pulsares, conhecidas como PTAs. O trabalho dará continuidade à análise de polarizações apresentada no TG de Wayne, incorporando a descrição exata de ondas dispersivas, vínculos de teorias de spin 2 massivo e métodos contemporâneos de inferência estatística. A pergunta central será quanto a compressão da informação em frequência, a escolha das distribuições a priori e as aproximações na resposta dos pulsares modificam limites de massa e a capacidade de distinguir polarizações.

O estudo partirá de resultados recentes sobre NANOGrav, MeerKAT e perspectivas para SKA. Serão construídas simulações com parâmetros conhecidos, comparando análises que preservam a frequência com análises comprimidas. A validação incluirá reprodução de resultados analíticos, convergência numérica, recuperação de sinais injetados, calibração estatística e comparação entre informação anterior e posterior aos dados. O resultado esperado é um conjunto reproduzível de critérios de validade e de sensibilidade, com potencial para um artigo metodológico em gravitação. Uma conclusão de que as aproximações são adequadas, ou de que os dados ainda não distinguem os modelos, também será cientificamente relevante se acompanhada de limites quantitativos.

## 2. O que o TG oferece e o que precisa ser atualizado

O núcleo aproveitável encontra-se nos capítulos 4 a 6 e no apêndice Maple:

- **Capítulo 4, páginas impressas 22–25:** equações linearizadas da teoria de Visser, conservação e propagação dispersiva, especialmente as equações (4.14)–(4.22).
- **Capítulo 5, páginas 27–38:** formalismo de tetradas, aproximação quase nula, classificação E(2), equações (5.58)–(5.61) e matriz das componentes elétricas do tensor de Riemann.
- **Capítulo 6, páginas 39–42:** comparação entre faixas de frequência e sugestão de maior relevância de efeitos massivos em baixas frequências.
- **Apêndice A, páginas 43–51:** procedimento computacional que pode ser reconstruído e verificado em ferramentas atuais.

O resultado central já foi publicado por de Paula, Miranda e Marinho em *Classical and Quantum Gravity* **21**, 4595–4606 (2004). Assim, reproduzir as seis polarizações ou simplesmente atualizar os números do TG constitui uma etapa de formação e reprodução, mas não a contribuição original de um novo artigo. [Artigo derivado do TG](https://arxiv.org/abs/gr-qc/0409041).

Há quatro distinções fundamentais para o mestrado:

1. **Onda massiva e aproximação quase nula.** Usar uma tetrada nula é permitido; o problema é aplicar relações simplificadas que pressupõem propagação nula fora de seu domínio. Hyun, Kim e Lee já desenvolveram expressões exatas para polarizações nulas e não nulas e discutiram limitações de trabalhos anteriores, incluindo a referência de 2004. Uma nova derivação, isoladamente, não seria inédita. [Hyun et al., 2019](https://arxiv.org/abs/1810.09316).
2. **Deformações observáveis e graus de liberdade.** A matriz simétrica $R_{0i0j}$ possui seis componentes, mas os vínculos de uma teoria podem relacioná-las. Um campo de Fierz–Pauli massivo em quatro dimensões tem cinco graus de liberdade; sua helicidade zero pode produzir deformações transversal e longitudinal relacionadas. Isso difere de assumir seis amplitudes independentes. [Liang e Trodden, 2021](https://arxiv.org/abs/2108.05344).
3. **Consistência da teoria.** O termo massivo não Fierz–Pauli da formulação histórica exige atenção ao modo escalar com sinal cinético inadequado, o *ghost*. A contagem geométrica de polarizações não demonstra estabilidade. O modelo de Visser será uma referência histórica; o modelo físico de comparação será o setor linear de Fierz–Pauli, com discussão de seu domínio e de sua relação com construções modernas. A estabilidade não linear de dRGT ou Hassan–Rosen não pode ser transferida automaticamente para Visser. [Visser](https://arxiv.org/abs/gr-qc/9705051), [análise de teoria não Fierz–Pauli](https://arxiv.org/abs/1011.4266), [dRGT](https://arxiv.org/abs/1011.1232), [Hassan–Rosen](https://arxiv.org/abs/1109.3515).
4. **Amplitude de curvatura e detectabilidade.** Comparar coeficientes que multiplicam perturbações métricas não substitui calcular excitação pela fonte, resposta instrumental e ruído. A hipótese de componentes métricas com amplitudes semelhantes, explicitada no artigo de 2004, não é uma previsão geral sobre fontes astrofísicas. A classificação E(2), o tipo algébrico de Petrov e o número de graus de liberdade também devem ser apresentados como conceitos distintos.

Uma auditoria inicial deverá fixar convenções de sinal, normalização das tetradas, distinção entre $h_{\mu\nu}$ e sua versão de traço invertido, unidades e a definição de massa nas equações (4.17)–(4.22). As tabelas do capítulo 6 devem ser recalculadas com unidades explícitas. Não é necessário presumir que todas as diferenças sejam erros físicos; algumas podem decorrer de notação ou normalização.

## 3. Literatura recente que define a oportunidade

| Trabalho | Resultado ou alcance relevante | Consequência para a proposta |
|---|---|---|
| [Wu et al., CQG, 2024](https://arxiv.org/abs/2310.07469) | Analisa massa do gráviton com NANOGrav 15 anos. Distingue a comparação entre modelos da informação associada à frequência mínima. | Separar informação dos dados de restrições cinemáticas é parte central da análise. |
| [NANOGrav, ApJL, 2024](https://arxiv.org/abs/2310.12138) | Busca correlações escalares transversais; não encontra evidência significativa a favor de sua inclusão. | Um sinal correlacionado não basta para identificar uma polarização adicional. |
| [Cordes et al., CQG, 2025; preprint de 2024](https://arxiv.org/abs/2407.04464) | Examina funções de redução de sobreposição, distâncias finitas e corrige um resultado analítico no regime relevante para gravidade massiva. | É referência de validação; incluir distâncias finitas não constitui novidade por si só. |
| [Choi e Kahniashvili, preprint, 2025](https://arxiv.org/abs/2507.02059) | Considera dispersão e polarizações adicionais em correlações de NANOGrav e CPTA; reporta melhora de ajuste. | Melhor ajuste não equivale a detecção: é preciso considerar complexidade, covariâncias e calibração. |
| [Wu, Bi e Huang, PRD, 2025](https://arxiv.org/abs/2506.07679) | Estuda interferência entre fontes e variabilidade das correlações no setor tensorial massivo. | A variabilidade entre realizações do fundo precisa entrar nos testes de robustez. |
| [Zhao e Wang, preprint de julho de 2026](https://arxiv.org/abs/2607.14790) | Analisa MeerKAT 4,5 anos com correlações angulares comprimidas, explora modelos de ruído e faz previsões para SKA. | É o ponto de partida mais recente encontrado para o recorte principal. |
| [LVK, GWTC-4.0, versão de julho de 2026](https://arxiv.org/abs/2603.19020) | Reporta limite de massa e discute efeitos de priori e de modelagem nos testes de dispersão. | Oferece contexto observacional e exemplos da necessidade de validar inferências de massa. |

O detalhe particularmente útil está na seção III do trabalho de Zhao e Wang: como os produtos observacionais são comprimidos em frequência, os autores adotam $f_{\mathrm{ref}}=1/T$ para relacionar massa e velocidade. A análise também utiliza uma verossimilhança diagonal por não dispor da covariância completa dos produtos publicados e limita a priori pela condição de velocidade real nessa frequência. São hipóteses explicitadas pelos autores que podem ser investigadas por simulação. [Texto completo, seção III](https://arxiv.org/html/2607.14790v1).

A lacuna candidata é **quantificar, com dados simulados e calibração estatística, como a compressão em frequência e essas escolhas afetam limites de massa quando a resposta é dispersiva, incluindo posteriormente uma contribuição de helicidade zero fisicamente vinculada**. A busca realizada não estabelece prioridade absoluta sobre esse recorte. Nos dois primeiros meses deverão ser examinados códigos, suplementos e trabalhos que citam essas referências.

Também existem apresentações de maio de 2026 de [Chris Choi sobre NANOGrav](https://indico.global/event/16413/contributions/153867/) e de [Marcus Bosca e colaboradores sobre EPTA](https://indico.global/event/16413/contributions/153709/). Elas indicam pesquisa em andamento e possível concorrência temática; apresentações de congresso têm status distinto de artigos revisados por pares.

## 4. Comparação entre possíveis projetos

| Linha | Implementação e validação | Avaliação para 24 meses |
|---|---|---|
| **Inferência de massa com PTAs: compressão em frequência e vieses** | Simulação, resposta dispersiva, comparação entre métodos e calibração por injeções. | **Recomendada.** Pergunta estreita, referências de 2026 e resultado útil mesmo sem nova detecção. |
| Polarizações exatas e consistência de teorias massivas | Álgebra simbólica, vínculos e comparação com Fierz–Pauli. | Excelente primeiro capítulo. Para artigo próprio precisa superar resultados conhecidos, especialmente os de 2019. |
| Polarizações em LISA ou LISA–Taiji | Resposta interferométrica, formas de onda e inferência. | Alternativa se houver orientação especializada. Há trabalhos extensos de 2026; o recorte deve ser muito específico. |
| Correlações de três pontos para polarizações escalares | Derivação de resposta e simulação de fundos não gaussianos. | Mais exploratória e teórica; maior risco para mestrado. Deve ficar como alternativa, não ser somada ao projeto principal. |

Para LISA, os pontos de partida atuais incluem [Akama et al., preprint de março de 2026](https://arxiv.org/abs/2603.03165) e [Mu e Guo, PRD, 2026](https://arxiv.org/abs/2507.09543). Para correlações de três pontos, [Jiménez Cruz, Sánchez e Tasinato, PRD, 2026](https://arxiv.org/abs/2509.08273) propõem um diagnóstico de polarizações escalares sob hipóteses específicas de média sobre polarizações. Uma extensão para ondas massivas precisaria verificar dispersão, homogeneidade, estacionariedade e condições de ressonância; um fundo gaussiano tem bispectro nulo e não pode ser usado para prometer esse sinal.

A extensão cosmológica de Visser sugerida no TG também tem antecedentes diretos, inclusive de seus colaboradores: [conservação de energia-momento](https://arxiv.org/abs/0710.1077) e [aplicação cosmológica](https://arxiv.org/abs/0907.5190). Ela demandaria um problema novo e uma análise de estabilidade mais ampla, sendo menos indicada como primeira escolha neste caso.

## 5. Pergunta, hipótese e objetivos

**Pergunta principal:** em quais condições substituir a resposta dependente da frequência por uma resposta avaliada em $f_{\mathrm{ref}}$ preserva a inferência da massa do gráviton, e quando isso altera limites, evidências entre modelos ou a identificação de uma componente escalar?

**Hipótese de trabalho:** como a dispersão depende de $m_g^2/f^2$, a adequação dessa substituição depende do espectro, da janela temporal, dos pesos dos estimadores, do ruído e da proximidade do limiar de propagação. Ela pode ser suficiente em alguns regimes e produzir perda de informação ou viés em outros. A hipótese não pressupõe o sinal ou o tamanho do efeito.

**Objetivo geral:** construir e validar uma comparação reproduzível entre inferência com frequência explícita e inferência comprimida para ondas gravitacionais massivas em PTAs.

**Objetivos específicos:**

1. Reproduzir o núcleo cinemático do TG e explicitar sua relação com teorias massivas contemporâneas.
2. Implementar a resposta tensorial dispersiva com termos da Terra e do pulsar, controlando os limites analíticos.
3. Construir simulações nas quais o espectro, a massa, a geometria e o ruído sejam conhecidos.
4. Medir o efeito da compressão espectral, das escolhas a priori e da covariância entre estimadores.
5. Estender um subconjunto dos testes para tensor mais helicidade zero de Fierz–Pauli, respeitando a relação entre deformações escalar transversal e longitudinal.
6. Produzir um artigo sobre critérios de validade, informação efetivamente fornecida pelos dados e consequências para testes futuros.

## 6. Formulação e implementação

### 6.1. Modelo de propagação

Adotar explicitamente

$$\omega^2=c^2k^2+\left(\frac{m_gc^2}{\hbar}\right)^2,\qquad
f_g=\frac{m_gc^2}{h_{\mathrm P}},\qquad
\beta(f)=\frac{ck}{\omega}=\sqrt{1-\left(\frac{f_g}{f}\right)^2}.$$

Aqui $h_{\mathrm P}$ é a constante de Planck. A velocidade de grupo é $v_g=c\beta$; a velocidade de fase é $v_{\mathrm{ph}}=c/\beta$. Essa distinção precisa ser preservada no cálculo dos fatores de resposta. Para $f<f_g$, o modo livre não é uma onda viajante com número de onda real.

A etapa inicial trabalha no regime linear sobre fundo plano, apropriado para estudar a resposta local e a propagação na linha de visada Terra–pulsar. A geração cosmológica e a distribuição das amplitudes serão hipóteses especificadas, não previsões completas de dRGT. Fierz–Pauli será utilizado como referência linear de um campo massivo saudável. Isso não equivale a resolver a emissão por binárias em uma teoria não linear nem o mecanismo de Vainshtein.

### 6.2. Polarizações e vínculos

Calcular diretamente $E_{ij}=R_{0i0j}$ a partir de $h_{\mu\nu}$. Para Fierz–Pauli, impor os vínculos de transversalidade quadridimensional e traço nulo. Para a helicidade zero, na convenção

$$p_b=R_{0x0x}+R_{0y0y},\qquad p_l=R_{0z0z},$$

o benchmark linear de onda plana resulta em

$$\frac{p_l}{p_b}=-\left(\frac{f_g}{f}\right)^2.$$

Essa relação será uma verificação da implementação. Ela não é a fórmula de um escalar genérico em qualquer teoria. Tampouco implica que todas as amplitudes adicionais sejam universalmente suprimidas por $m_g^2/f^2$. A intensidade excitada depende do modelo e da fonte.

### 6.3. Resposta e correlações de PTA

Derivar a variação de frequência dos pulsos e integrá-la para obter os resíduos de temporização. A matriz de marés local, isoladamente, não constitui a resposta de uma PTA. Para cada polarização independente $A$, construir $\mathcal R_a^A(f,\hat\Omega,L_a;m_g)$, incluindo os termos da Terra e do pulsar, e então

$$\Gamma_{ab}^{A}(f)=\mathcal N_A\int d^2\hat\Omega\,
\mathcal R_a^{A}(f,\hat\Omega)\mathcal R_b^{A*}(f,\hat\Omega).$$

Fixar e documentar $\mathcal N_A$, as convenções espectrais e o tratamento das autocorrelações. Comparar integração angular direta com um segundo método ou limite analítico. Usar as expressões de [Liang e Trodden](https://arxiv.org/abs/2108.05344) e as correções aplicáveis de [Cordes et al.](https://arxiv.org/abs/2407.04464) como benchmarks, após compatibilizar normalizações.

O limite de Hellings–Downs será exigido no setor tensorial apropriado. Não se deve exigir que o modelo massivo completo com amplitudes escalares arbitrárias se torne RG apenas tomando $m_g\to0$; o limite com fontes e o desacoplamento dos setores adicionais exigem tratamento próprio.

### 6.4. Comparação central

Construir, a partir das mesmas realizações simuladas:

- **Análise com frequência explícita:** modelo de covariância ou espectros cruzados dependentes de $f$, usando uma mesma massa em todas as frequências.
- **Análise comprimida consistente:** aplicar ao modelo os mesmos pesos, janela e compressão utilizados nos estimadores simulados.
- **Análise com frequência de referência:** substituir a dependência relevante por uma avaliação em $f_{\mathrm{ref}}$, reproduzindo uma aproximação controlada.

Esquematicamente, a previsão comprimida correta tem a forma

$$\langle\widehat C_{ab}\rangle=\int df\,W_{ab}(f)S_h(f)\Gamma_{ab}(f;m_g),$$

em que $W_{ab}$ inclui o estimador e a observação. Em geral, isso não coincide com retirar $\Gamma_{ab}(f_{\mathrm{ref}};m_g)$ da integral. Não existe uma frequência efetiva universal independente do espectro e dos pesos. A extensão com várias polarizações deve somar espectros e respostas dos setores independentes.

Essa comparação separa a perda causada pela compressão da perda causada por aproximar incorretamente o modelo comprimido. Também permite avaliar covariância completa e diagonal sem pressupor que ignorar correlações seja sempre conservador.

### 6.5. Experimentos numéricos e inferência

Começar com PTAs sintéticas de 10–30 pulsares, duração de 4,5 e 15 anos e uma seleção controlada de geometrias, cadências e ruído. Esses tamanhos são escolhas de planejamento e poderão ser ajustados após medir o custo computacional. Comparar espectro em lei de potência com um espectro de baixa frequência modificado; acrescentar sinais comuns monopolar e dipolar como testes de robustez.

Explorar massas pela razão adimensional $f_gT$ e pela posição do limiar nos canais observados. Se um canal estiver abaixo de $f_g$, modelar a ausência da contribuição viajante daquele setor. Não excluir automaticamente todo o modelo por causa de um canal sem sinal confirmado. Uma mistura entre setores massivos e não massivos exige suporte espectral separado.

Para massa positiva, comparar escolhas a priori uniformes em $m_g$ e em $m_g^2$, e uma escolha logarítmica com corte inferior explicitado. Incluir RG como hipótese separada: uma priori contínua em $\log m_g$ não contém o ponto $m_g=0$.

As amplitudes dos setores tensorial e escalar serão parâmetros de população especificados. As deformações transversal e longitudinal do mesmo modo escalar deverão permanecer correlacionadas. Os modos vetoriais e a análise integral de uma segunda PTA serão extensões condicionais ao progresso.

### 6.6. Dados e ferramentas

Usar Python com álgebra simbólica e rotinas numéricas verificáveis. Para uma eventual análise completa de resíduos, aproveitar o [ENTERPRISE, mantido pelo NANOGrav](https://github.com/nanograv/enterprise), em vez de reconstruir toda a infraestrutura de temporização. Fixar versões e sementes aleatórias.

Os [dados públicos do NANOGrav](https://nanograv.org/science/data) e os produtos documentados pelos artigos servirão como referências. Antes da etapa observacional, verificar quais produtos contêm informação em frequência e covariâncias. Correlações angulares já comprimidas não permitem recuperar informação espectral perdida.

O artigo principal poderá ser concluído com simulações e benchmarks. A aplicação a dados públicos será realizada se houver produtos adequados e tempo, declarando as limitações de qualquer compressão ou covariância indisponível. Uma análise completa dos resíduos não será substituída por um ajuste de pontos de uma figura.

## 7. Plano de validação e critérios de sucesso

| Nível | Verificação | Critério de planejamento |
|---|---|---|
| Matemático | Simetrias de Riemann, identidade de Bianchi, vínculos e relação escalar | Igualdades simbólicas ou aritmética exata em benchmarks. |
| Físico | Limites tensorial sem massa, quase nulo e próximo ao limiar | Recuperar resultados pertinentes, explicitando setores e convenções. |
| Numérico | Integração angular e truncamentos espectrais | Tolerância inicial de $10^{-3}$ nas ORFs, com erro absoluto perto de zeros; ajustar para ficar abaixo do erro estatístico relevante. |
| Inferência | Recuperar massa e amplitudes injetadas | Medir viés normalizado, largura dos intervalos e estabilidade entre amostradores ou execuções. |
| Calibração | Injeções com parâmetros sorteados da priori e testes em pontos fixos | Verificar calibração sob a priori; medir separadamente cobertura em parâmetros fixos, sem exigir que cobertura bayesiana seja nominal em todo ponto. |
| Detecção | Realizações de RG com ruído e fundos alternativos | Calibrar a distribuição do fator de Bayes ou estatística escolhida sob a hipótese nula. |
| Informação | Comparar priori e posterior | Medir contração, divergência de informação quando apropriada e dependência dos limites com o suporte da priori. |
| Robustez | Mudar espectro, ruído, distâncias e covariâncias | Apresentar quais conclusões resistem e onde a aproximação falha. |

Para cobertura, um conjunto de 500 realizações teria incerteza binomial aproximada de 1,3 ponto percentual em torno de 90%. Esse número é um alvo de planejamento para cenários selecionados, não uma promessa de executar toda a grade com 500 repetições. Taxas de falso positivo da ordem de 1% requerem amostras maiores ou intervalos de incerteza explicitamente largos.

Será útil medir o erro do modelo em unidades do ruído, por exemplo $\Delta\mathbf C^\mathsf T\Sigma^{-1}\Delta\mathbf C$, além de erros relativos nas ORFs. Isso aproxima a discussão da consequência observacional: uma discrepância matemática grande em um canal pouco sensível pode ter efeito estatístico pequeno.

## 8. Checagens preliminares já executadas

Foi implementado o script [`scripts/checagens_preliminares.py`](../../scripts/checagens_preliminares.py), que usa somente a biblioteca padrão de Python. A saída está em [`checagens_preliminares.json`](checagens_preliminares.json). Ele verifica cinemática; não implementa a análise estatística proposta.

### 8.1. Escala de frequência

O estudo LVK de 2026 reporta $m_g\leq1{,}92\times10^{-23}\,\mathrm{eV}/c^2$ a 90% de credibilidade em seu teste de dispersão. Seu modelo pressupõe sinal descrito suficientemente bem por polarizações tensoriais; esse valor não é um limite universal para toda teoria ou mistura de modos. [GWTC-4.0, análise de dispersão e tabela 5](https://arxiv.org/pdf/2603.19020).

Usando esse valor apenas como benchmark, obtém-se $f_g=4{,}6425\times10^{-9}\,\mathrm{Hz}$:

| Frequência de referência | $x=(f_g/f)^2$ |
|---|---:|
| $10^{-8}$ Hz, faixa de PTA | $2{,}1553\times10^{-1}$ |
| $10^{-7}$ Hz, faixa de PTA | $2{,}1553\times10^{-3}$ |
| $10^{-4}$ Hz, referência de baixa frequência para LISA | $2{,}1553\times10^{-9}$ |
| $100$ Hz, interferometria terrestre | $2{,}1553\times10^{-21}$ |
| $3000$ Hz, referência do TG para detector ressonante | $2{,}3948\times10^{-24}$ |

Esses números justificam investigar dispersão local em PTAs. **Não são razões universais de amplitudes adicionais nem previsões de detectabilidade.** Tampouco eliminam testes interferométricos de dispersão: pequenos efeitos podem acumular fase ao longo da propagação.

Para o benchmark histórico do artigo de 2004, $m_gc^2=4{,}4\times10^{-22}$ eV e $f=1{,}1\times10^{-7}$ Hz, encontra-se $x=0{,}93547$, $v_g/c=0{,}2540$ e $(c/v_g)^2-1\simeq14{,}50$. Isso mostra que esse exemplo não está em regime quase nulo. É uma checagem de consistência de aproximação, não uma nova descoberta sobre polarizações.

### 8.2. Vínculos e matriz de marés

Foram calculados postos de matrizes com aritmética racional exata em quatro configurações de frequência e número de onda. Nos três casos massivos, os vínculos linearizados considerados deixam seis amplitudes no modelo histórico e cinco em Fierz–Pauli, com postos respectivos seis e cinco no mapa para $R_{0i0j}$. No caso nulo testado, o posto observável é dois. Foram verificadas a relação escalar acima, simetrias de Riemann, Bianchi e anulação da curvatura de uma perturbação de coordenadas linear.

Isso valida os benchmarks implementados, não demonstra estabilidade, acoplamento a fontes ou recuperação não linear da RG.

### 8.3. Informação a priori no benchmark de MeerKAT

Com $T=4{,}5$ anos julianos, a escolha $m_{\max}c^2=h_{\mathrm P}/T$ corresponde a $2{,}9123\times10^{-23}$ eV. Uma priori uniforme entre zero e esse máximo já possui percentil de 90% igual a $2{,}6210\times10^{-23}$ eV, antes de observar dados.

Os limites de 90% reportados por Zhao e Wang são $2{,}10$, $2{,}58$ e $2{,}25\times10^{-23}\,\mathrm{eV}/c^2$ nas três configurações. A comparação aritmética, particularmente para a configuração ER, motiva medir quanto a posterior realmente acrescenta à priori. **Essa proximidade, por si só, não prova que a inferência seja inválida ou que os dados não contenham informação.** Serão necessárias distribuições completas e testes controlados. [Fonte dos limites e da escolha a priori](https://arxiv.org/html/2607.14790v1).

Para reproduzir as checagens, na raiz do projeto:

```bash
python3 scripts/checagens_preliminares.py
```

## 9. Cronograma de 24 meses

| Meses | Atividade | Entrega e decisão |
|---|---|---|
| 1–2 | Revisão dirigida, atualização até a data de início e comparação com trabalhos de 2026 | Matriz de originalidade; fixação definitiva da pergunta. |
| 3–5 | Reconstrução do TG, polarizações exatas e vínculos de Fierz–Pauli | Caderno de derivação e benchmarks públicos. |
| 6–8 | Resposta tensorial de PTA e ORFs | Implementação validada em limites conhecidos. |
| 9–11 | Simulações e comparação das três formas de análise | Primeiro mapa de erros e custo computacional. |
| 12–15 | Calibração, priori versus posterior, covariância e espectros | Resultado principal sobre inferência de massa. |
| 16–18 | Subconjunto tensor mais helicidade zero; testes de robustez | Avaliação da identificação de polarizações. Se necessário, manter esse resultado como extensão delimitada. |
| 19–21 | Aplicação pública viável ou ampliação dos testes simulados; redação do artigo | Manuscrito completo e código documentado. |
| 22–24 | Submissão, dissertação e defesa | Artigo submetido, dissertação e material reproduzível. |

Pressupõe-se formação em relatividade, métodos matemáticos e programação. A análise integral de resíduos de uma PTA se beneficia de orientação ou colaboração com experiência em temporização. O estágio inicial pode ser executado em uma estação de trabalho; campanhas estatísticas devem ser dimensionadas após benchmarks e podem exigir recursos institucionais.

## 10. Produto publicável e limites de escopo

**Título provisório do artigo:** *Frequency compression and prior sensitivity in pulsar-timing tests of massive gravitational waves*.

Uma contribuição publicável poderá consistir em:

- critérios quantitativos para empregar uma frequência efetiva sem alterar materialmente a inferência;
- medição de viés, perda de informação ou falsa preferência por um modelo em cenários fisicamente especificados;
- demonstração de como uma componente escalar vinculada modifica esses resultados;
- benchmarks abertos e validação independente que permitam reproduzir a conclusão.

O manuscrito deve distinguir claramente resultados novos de reproduções. A aceitação dependerá da originalidade efetivamente confirmada, da qualidade da validação e da relevância dos efeitos encontrados. *Classical and Quantum Gravity* e *Physical Review D* são alvos temáticos plausíveis, como mostram os antecedentes citados; a escolha final depende do resultado e da orientação.

Se a compressão se mostrar adequada, o artigo poderá apresentar seu domínio de validade e limites superiores para o viés. Se a revisão encontrar trabalho idêntico, o recorte deverá migrar cedo para a extensão escalar ou para outro mecanismo concreto de perda de informação. O projeto não deve se expandir simultaneamente para cosmologia completa, emissão não linear de binárias, LISA, SKA e bispectro.

**Recomendação:** preservar do TG a ligação entre polarizações, massa e baixas frequências, e transformar essa base em um mestrado de validação teórica e numérica dos testes atuais com PTAs. O diferencial candidato está na confiabilidade e na informação das inferências, e não na redescoberta de modos de polarização já conhecidos.
