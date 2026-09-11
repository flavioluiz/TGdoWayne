# Caudas e limite de variância da ampliação fixa

A deficiência observada é de eficiência finita, não prova de variância infinita.
Há uma distinção útil entre o controle matemático e a validação operacional.

## Suporte e momentos

Considere a variável logit z em R^5 e a transformação para a priori retangular
física: theta_i=l_i+(h_i-l_i) sigmoid(z_i). A densidade transformada da priori é

    J(z)=prod_i sigmoid(z_i)[1-sigmoid(z_i)],

pois as larguras da densidade uniforme cancelam o Jacobiano linear. Para os
modelos C07 e um dado fixo, as covariâncias CN são contínuas no suporte compacto
e têm piso estritamente positivo de ruído branco (limite inferior de EFAC e
sigma_a>0). Para os estimadores quadráticos, o mapa H é linearmente
independente: tr(H_i C H_j C) é definida positiva, e a compressão fixa mantém
esse piso. Assim, a verossimilhança normalizada é contínua e limitada no
suporte, incluindo u=0/1. Isso pressupõe a validade desses contratos de C06 e
não se transfere automaticamente a outro modelo de observação.

Uma componente Student global de massa positiva, covariância definida
positiva e nu>2 possui uma cota inferior

    q(z) >= c (1+||z||)^[-(nu+5)]

com constante c>0 dependente do ajuste. Como J(z) <= exp(-||z||_1), a razão
L(theta(z))J(z)/q(z) é limitada e tem todos os momentos polinomiais finitos sob
q. A defesa global já existente garante suporte completo e uma cauda
assintótica suficiente neste problema. Ela não fornece um limite numérico
útil para quantas amostras são necessárias: as constantes podem ser enormes,
e a região mal coberta observada está a uma distância moderada na covariância
global, antes de a comparação assintótica nu=3/nu=5 ser relevante.

## Ampliação e piora máxima da variância assintótica

Escreva g para a mistura gaussiana local original normalizada e t para a
Student global original. A proposta antiga e a proposta ampla são

    q0 = 0.85 g + 0.15 t,
    q1 = 0.75 g + 0.10 g_wide + 0.15 t.

As médias e pesos relativos de g_wide são os de g, com covariâncias9C.
Como g_wide e t são não negativas,

    q1 >= (15/17) q0.

Se p é a posterior normalizada e F a CDF verdadeira num corte, a variância
assintótica SNIS por ponto tem a forma

    V_q(F) = integral p(z)^2 [I(z<=cut)-F]^2 / q(z) dz.

Portanto, para qualquer corte fixo,

    V_q1(F) <= (17/15) V_q0(F).

O mesmo limite vale para o segundo momento do estimador de evidência antes
de subtrair sua média ao quadrado. Para CDF, o desvio padrão assintótico pode
piorar por no máximo sqrt(17/15)=1.06458. Essa é uma garantia matemática global
de piora limitada; não garante melhora, MCSE de uma realização específica,
limite para o maior peso observado ou aprovação de todos os dados. A melhora
nos16 testes independentes continua sendo evidência empírica separada.

A mudança de proposta não altera a posterior alvo, a priori, a ORF, o modelo
físico ou o significado do Bayes factor, desde que logq1 completo substitua
logq0 apenas para novos sorteios de q1. Reutilizar um conjunto antigo como se
tivesse sido sorteado de q1 seria incorreto. Reutilização por importance
sampling continua possível mantendo o denominador correspondente à proposta
de origem ou com uma regra MIS derivada explicitamente; isso não foi feito
como inferência no ensaio relatado.
