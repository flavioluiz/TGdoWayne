# C04 — Derivação geral e auditoria do TG (subsídio para integração)

Estado: **derivação cinemática e implementação verificadas**, integradas ao marco C04. O PDF cumulativo apresenta as demonstrações e a auditoria de normalização.

## 1. Convenções e domínio

Usamos η=diag(+1,−1,−1,−1), índices gregos 0…3 e índices espaciais 1…3. A perturbação é **covariante**:

\[
g_{\mu\nu}=\eta_{\mu\nu}+\operatorname{Re}[H_{\mu\nu}e^{-i\omega t+ikz}],\qquad
q_\mu=(-\omega,0,0,k),\qquad q^\mu=(-\omega,0,0,-k).
\]

As amplitudes de Fourier podem ser complexas; para um campo métrico real, a frequência negativa contém o conjugado da positiva. As dimensões dos espaços de amplitudes abaixo são dimensões lineares em uma frequência, não uma contagem duplicada de estados pela separação artificial entre seno e cosseno. O benchmark de ImΨ4 usa C=1 real e fase comum para fixar a convenção.

Aqui c=1. A fase descreve propagação no sentido +z para ω,k>0. Trocar simultaneamente o sinal de q não altera os resultados quadráticos de curvatura. Se apenas k muda de sinal, os termos mistos e a tetrada adaptada à direção também devem mudar. H^{00}=H00, H^{ij}=Hij e H^{0i}=−H0i. O traço é H=H00−H11−H22−H33. O traço invertido é H̄μν=Hμν−ημνH/2, com H̄=−H e Hμν=H̄μν−ημνH̄/2 em quatro dimensões.

A frequência angular ω não é f em hertz. Em coordenadas x⁰=ct, substituir ω do cálculo por ω_SI/c. Então

\[
\omega_{\rm SI}^2=c^2k^2+(m_gc^2/\hbar)^2,\quad
\beta=ck/\omega_{\rm SI}=v_g/c,\quad
v_{\rm fase}=c/\beta,\quad f_g=m_gc^2/h_{\rm P}.
\]

Definimos Δ=ω²−k² e Σ=ω²+k². As parametrizações abaixo são válidas para **ω≠0 e k real**; Σ>0 neste domínio. O setor massivo viajante tem Δ>0, com 0≤|k|/|ω|<1. O limiar k=0 não é singular na álgebra; nele há oscilação espacialmente homogênea e não há uma direção de propagação fisicamente privilegiada. Δ=0, ω≠0, é tratado diretamente. O ponto q=0 e campos estáticos ω=0 não pertencem a essa parametrização e não devem ser avaliados por divisão por zero. Frequências abaixo de f_g exigem k imaginário: não são ondas viajantes homogêneas e não serão incluídas em uma ORF de ondas viajantes pela simples continuação dessas fórmulas.

A convenção de Riemann é

\[
R^\alpha{}_{\beta\gamma\delta}
=\partial_\gamma\Gamma^\alpha{}_{\delta\beta}-\partial_\delta\Gamma^\alpha{}_{\gamma\beta}+O(H^2).
\]

Ela é **oposta à saída do apêndice Maple do TG** para o tensor totalmente covariante. Em particular, nosso R0x0x=+ω²Hxx/2, enquanto o TG, p. impressa 44, apresenta −ω²A11/2. Com η=(+---), a aceleração relativa nessa convenção é a^i=c²R0i0j ξ^j, usando componentes espaciais euclidianas. Quem adotar a matriz S de força do TG com a^i=−c²Sijξ^j deve usar **Sij=−R0i0j**. Não combinar um sinal de Riemann de uma convenção com a equação de desvio geodésico de outra. Postos, quocientes escalares e erros relativos aqui estudados não dependem do sinal global.

## 2. Curvatura sem pressupor propagação nula

A derivação pelo símbolo de Christoffel dá

\[
R_{\alpha\beta\gamma\delta}^{(1)}
=\frac12(H_{\alpha\delta,\beta\gamma}+H_{\beta\gamma,\alpha\delta}
-H_{\alpha\gamma,\beta\delta}-H_{\beta\delta,\alpha\gamma}).
\]

Para uma única amplitude de Fourier, cada segunda derivada é −qμqν. Retirando o fator de fase, a matriz elétrica Eij=R0i0j fica

\[
E=\frac12\begin{pmatrix}
\omega^2H_{11}&\omega^2H_{12}&\omega^2H_{13}+\omega kH_{01}\\
\omega^2H_{12}&\omega^2H_{22}&\omega^2H_{23}+\omega kH_{02}\\
\omega^2H_{13}+\omega kH_{01}&\omega^2H_{23}+\omega kH_{02}&
\omega^2H_{33}+2\omega kH_{03}+k^2H_{00}
\end{pmatrix}.
\]

Este resultado não usa equação de campo, relação de dispersão, tetrada nula ou gauge. Há seis componentes geométricas possíveis, não necessariamente seis amplitudes físicas independentes. O teste simbólico calcula as mesmas 256 componentes de Riemann por duas rotas: fórmula acima e Γ linearizado seguida de derivada/contração. Verifica ainda antissimetria em ambos os pares, troca de pares, Bianchi algébrico, Bianchi diferencial de Fourier e curvatura nula para Hμν=qμξν+qνξμ.

## 3. Visser linear: seis amplitudes e parametrização regular

A condição da Eq. (4.14) do TG é

\[
q^\mu\bar H_{\mu\nu}=0.
\]

No modelo histórico ela é um vínculo associado à equação de campo e à conservação assumida; **não é uma liberdade de gauge disponível para remover modos de uma teoria massiva**. Uma transformação infinitesimal de coordenadas continua tendo curvatura linear nula, mas em geral não preserva a equação massiva nem esses vínculos.

Escolha as amplitudes livres

\[
A=H_{00},\quad D=H_{33},\quad B=H_{22},\quad C=H_{12},\quad
V_x=H_{13},\quad V_y=H_{23}.
\]

As quatro equações, resolvidas sem dividir por Δ ou k, fornecem

\[
H_{01}=-\frac{k}{\omega}V_x,\quad H_{02}=-\frac{k}{\omega}V_y,
\quad H_{03}=-\frac{\omega k}{\Sigma}(A+D),\quad
H_{11}=-B-\frac{\Delta}{\Sigma}(A+D).
\]

Isso remove a divisão intermediária por k usada na página 48 do apêndice do TG e permite tomar o limiar k=0 de modo regular. O menor do sistema de vínculos nas colunas (H01,H02,H03,H11) é −ω²Σ/2. Portanto, para qualquer ω≠0 e k real, o posto dos quatro vínculos é exatamente quatro e sua nulidade é seis. Não se trata de inferência a partir de amostras racionais.

Com essas amplitudes,

\[
E_V=\frac12\begin{pmatrix}
-\omega^2 B-\omega^2\frac\Delta\Sigma(A+D)&\omega^2C&\Delta V_x\\
\omega^2C&\omega^2B&\Delta V_y\\
\Delta V_x&\Delta V_y&\frac\Delta\Sigma(\omega^2D-k^2A)
\end{pmatrix}.
\]

Defina as coordenadas observáveis

\[
\mathbf p=(p_b,p_l,p_+,p_\times,p_x,p_y)
=(E_{11}+E_{22},E_{33},E_{11}-E_{22},E_{12},E_{13},E_{23}).
\]

O determinante de ∂p/∂(A,D,B,C,Vx,Vy) é

\[
\det J_V=\frac{\omega^6\Delta^4}{32\Sigma}.
\]

Assim, o mapa de amplitudes para curvatura tem posto seis para Δ≠0 no domínio adotado. Para Δ=0 os termos escalar e vetorial se anulam **nas famílias de amplitudes métricas limitadas**, restando E11=−ω²B/2, E22=ω²B/2, E12=ω²C/2 e posto dois. A nulidade do mapa de marés restrito é quatro.

Uma base alternativa com todas as seis amplitudes espaciais livres envolve H00=−H33−(Σ/Δ)(H11+H22), que é singular no limite nulo. A singularidade é da parametrização; ela alerta também que manter H11+H22 fixo enquanto Δ→0 pode exigir amplitudes métricas ilimitadas. Por isso, a afirmação sobre posto no caso exatamente nulo não pode ser aplicada sem qualificação a qualquer família de soluções massivas.

## 4. Fierz–Pauli: cinco amplitudes e um setor escalar

Em vácuo plano, para massa não nula, a divergência e o traço da equação de Fierz–Pauli impõem

\[
q^\mu H_{\mu\nu}=0,\qquad H=0.
\]

É possível ver a diferença em uma normalização das equações compatível com nosso sinal de Riemann: Gμν^(1)−μ²(Hμν−ημνH)/2=0. Sua divergência implica ∂μHμν=∂νH; esta relação anula R^(1), e o traço então força H=0 para μ²≠0. A equação restante é (□+μ²)Hμν=0. Esse raciocínio não vale dividindo por μ² quando μ=0. A teoria massless tem simetria de gauge e precisa ser tratada como tal.

Na parametrização anterior, o quinto vínculo equivale a

\[
A=\frac{k^2}{\omega^2}D,\quad H_{03}=-\frac k\omega D,
\quad H_{11}=-B-\frac\Delta{\omega^2}D.
\]

O menor dos cinco vínculos nas colunas (H00,H01,H02,H03,H11) vale −ω⁴; a dimensão das amplitudes sujeitas aos vínculos é cinco no domínio ω≠0. Para Δ≠0, o menor de cinco componentes observáveis (pb,p+,p×,px,py) relativamente a (B,C,Vx,Vy,D) vale ω⁴Δ³/16. Portanto, o posto elétrico é cinco. A contagem tem duas amplitudes tensoriais, duas vetoriais e uma escalar quando interpretada no campo massivo de spin dois.

As componentes escalares satisfazem identicamente

\[
p_b=-\frac\Delta2D,\qquad p_l=\frac{\Delta^2}{2\omega^2}D,
\qquad p_l+\frac\Delta{\omega^2}p_b=0.
\]

A identidade polinomial é preferível à razão onde pb=0. Quando pb≠0,

\[
\boxed{\frac{p_l}{p_b}=-\left(1-\frac{k^2}{\omega^2}\right)=-(1-\beta^2).}
\]

A normalização adotada para breathing é a **soma** E11+E22. Se alguém define breathing como uma única componente transversal, aparece um fator dois: isso não altera a física. A relação vale para todo campo que satisfaz esses vínculos; para isolar a helicidade zero, também se exige E11=E22 e C=Vx=Vy=0, isto é, B=−ΔD/(2ω²).

No limite de amplitudes métricas finitas, pb,pl e os termos vetoriais tendem a zero, e o mapa no ponto k=ω tem posto dois e núcleo de dimensão três. **Isso não demonstra continuidade física com RG para fontes.** Por exemplo, a família D=−2ω²/Δ, B=1 e C=Vx=Vy=0 satisfaz os vínculos para toda Δ≠0 e produz

\[
H_{\rm esc}=\begin{pmatrix}
-2k^2/\Delta&0&0&2\omega k/\Delta\\
0&1&0&0\\
0&0&1&0\\
2\omega k/\Delta&0&0&-2\omega^2/\Delta
\end{pmatrix},\quad
E_{\rm esc}=\operatorname{diag}(\omega^2/2,\omega^2/2,-\Delta).
\]

A curvatura breathing não desaparece nesse limite, mas a métrica não permanece limitada. A família ilustra matematicamente a não uniformidade; **não é uma afirmação de validade do regime linear até Δ=0**, nem uma derivação autônoma da descontinuidade vDVZ ou de sua resolução por mecanismos não lineares. Excitação, normalização canônica, acoplamento a fontes e estabilidade requerem análise dinâmica própria.

## 5. Auditoria explícita da Eq. (5.60) e do apêndice

A transcrição literal da Eq. (5.60) foi codificada separadamente da fórmula fatorada. Nas amplitudes métricas do apêndice, ela simplifica exatamente para

\[
\Psi_4^{\rm TG}=\frac{(\omega+k)^2}{8}
\left[-2B-\frac\Delta\Sigma(A+D)+2iC\right].
\]

Essa expressão foi reproduzida por contração tensorial independente usando n=(1,0,0,−1)/√2 e m=(0,1,i,0)/√2, escolhendo a orientação complexa que dá o sinal positivo de ImΨ4 impresso no TG. Como R_TG=−R_aqui, a definição −R_TG(n,m,n,m) equivale a R_aqui(n,m,n,m). Isso verifica a álgebra da Eq. (5.60); o problema não é simplesmente chamá-la de “cálculo errado de curvatura”. A identificação de um subconjunto de escalares de uma tetrada nula com a matriz física sob relações nulas é que exige cuidado quando k≠ω.

Também se obtêm as formas reduzidas das demais expressões impressas:

\[
\Psi_2^{\rm TG}=\frac\Delta{12\Sigma}(\omega^2D-k^2A),\quad
\Psi_3^{\rm TG}=\frac{\Delta(\omega+k)}{8\omega}(V_x+iV_y),\quad
\Phi_{22}^{\rm TG}=-\frac{\Delta(\omega+k)^2}{8\Sigma}(A+D).
\]

As relações de Ψ2 e Ψ3 com o tensor de Weyl usadas no capítulo 5 são explicitamente aproximadas, com termos O(ε), e o apêndice efetivamente calcula projeções de **Riemann**. Fora do domínio nulo, a projeção de Riemann que o código chama de Ψ2 ou Ψ3 não deve ser identificada automaticamente com o escalar de Weyl correspondente. Ψ4 é uma exceção: para a contração nmnm, os termos de Ricci da decomposição se anulam pela nulidade e ortogonalidade da tetrada.

Para o benchmark puro cruzado A=D=B=Vx=Vy=0 e C=1, obtém-se ImΨ4_TG=(ω+k)²/4 enquanto E12_exato=ω²/2 em nossa convenção. A conversão calibrada no limite nulo é ImΨ4_TG/2. Seu quociente com a resposta exata é

\[
\mathcal R_T(\beta)=\frac{\operatorname{Im}\Psi_4^{\rm TG}/2}{E_{12}}
=\frac{(1+\beta)^2}{4},\qquad
1-\mathcal R_T=\frac{x(3+\sqrt{1-x})}{4(1+\sqrt{1-x})},\quad x=1-\beta^2.
\]

O quociente tende a um para β→1 e vale 1/4 no limiar β=0. Logo, aplicar essa conversão calibrada em onda nula a uma onda massiva produz erro relativo de 75% no limiar. Trata-se de um **benchmark de projeção tensorial**, não da amplitude de um modo adicional, nem de erro de um ajuste de dados de PTA.

O capítulo 5 do TG apresenta k=(1,0,0,1), l=(1,0,0,−1)/2; o apêndice usa os dois vetores com fator 1/√2. São tetradas relacionadas por um boost, e Ψ4 muda por fator dois. A matriz impressa na p. 37 precisa ter sua normalização rastreada juntamente com a escolha da orientação complexa. Não transportar sem auditoria os coeficientes da matriz de um conjunto de tetradas para outro.

Há ainda uma ambiguidade nominal: a Eq. (4.21) chama Aμν à amplitude de H̄μν, mas o apêndice insere Aμν diretamente em gμν=ημν+εAμνe^{iφ}. A reprodução de (5.58)–(5.61) deve declarar explicitamente que usa **o A métrico do apêndice**, e não presumir que as amplitudes de (4.21) são intercambiáveis quando o traço não é zero.

Quanto às massas e unidades, o TG define M na Eq. (4.19) e em seguida fornece uma velocidade com m_g. A notação e o fator numérico precisam ser mantidos separados ao reproduzir historicamente a ação: esta implementação usa μ=m_gc/ℏ definido operacionalmente pela dispersão física e não atribui sem demonstração o mesmo valor a todo símbolo M ou m_g de convenções distintas. O fator 2 e a restauração de c nas equações impressas (4.17)–(4.19) foram examinados na [auditoria de normalização](auditoria_normalizacao.md), que distingue a cadeia literal do TG, a do artigo de 2004 e a massa operacional.

## 6. Confronto primário com Hyun, Kim e Lee

A [Eq. (3.30) do preprint de Hyun et al.](https://arxiv.org/pdf/1810.09316), publicado em PRD 99, 124002 (2019), fornece as seis amplitudes na mesma escolha de componentes livres (htt,hzz,hyy,hxy,hxz,hyz). Após fixar convenções de assinatura e sinal, suas expressões coincidem com o mapa E_V acima. A Eq. (3.27) é a forma equivalente com componentes espaciais livres; sua parametrização pode esconder a singularidade de Δ→0. Essa comparação é um benchmark de reprodução conhecido, não uma reivindicação de originalidade. O confronto foi incluído como identidade simbólica separada no teste.

A classificação E(2) usa o grupo que preserva um vetor de onda nulo. Para um vetor temporal massivo, o grupo estabilizador de Lorentz é SO(3); não se deve converter a classificação aproximada do TG em uma classificação exata E(2) da teoria massiva. Usar uma tetrada nula como base permanece matematicamente possível. A matriz de marés do observador é a ponte operacional mais direta neste projeto.

## 7. Evidências computacionais e limites

Execução:

```sh
.venv/bin/python scripts/reproduzir_tg.py
```

Dependências fixadas: SymPy 1.14.0, mpmath 1.3.0. Arquivos: `src/polarizacoes/foundations.py`, `tests/test_polarizacoes.py`, `results/C04/validacao.json`. A prova usa variáveis simbólicas gerais, menores explícitos não nulos e duas construções independentes da curvatura; não apenas postos genéricos retornados por um CAS. Os exemplos racionais e a tabela de escalas do script preliminar continuam sendo úteis como regressão e apresentação numérica.

Limitações: não foram calculadas aqui ORFs, respostas integrais de PTAs, distribuições de fontes, ruído, evidências bayesianas, estabilidade de uma ação, propagação cosmológica ou observáveis astrofísicos. Os cinco vínculos de FP em massa não nula não autorizam tratar um sexto escalar independente como polarização FP. Seis deformações geométricas não demonstram seis graus de liberdade saudáveis. Nada nesta subparte substitui C05–C13.

## 8. Passagem futura para PTA: versão da resposta importa

A auditoria bibliográfica de C03 identificou a versão v3 de Liang–Trodden, `2108.05344v3` (24/07/2026), arquivada em `literature/papers/`. A seção III dessa versão atualiza a resposta dos pulsars e do observador quando H0μ≠0; a Eq. (22) inclui o termo −ε00(1+A Ω·p)/2. Isso deverá ser incorporado explicitamente em C05 e C10. A relação local pl/pb derivada aqui não é uma função de resposta PTA: resposta espectral e redshift dependem da trajetória da luz, da métrica temporal e das geodésicas dos observadores. Não inserir pl/pb em uma soma de respostas escalares independentes, nem usar sem auditoria fórmulas de códigos anteriores a essa correção. Esta subparte não implementou ou validou tal resposta.
