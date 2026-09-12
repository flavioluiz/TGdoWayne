# SBC de massa: síntese preliminar

Os PITs de massa foram calculados para as 25.956 posteriores de base a partir
dos caches, sem novos dados, verossimilhanças ou respostas físicas. Os valores
verdadeiros foram usados depois da inferência, como limites de integração da
CDF posterior. O arquivo `results/C09/production_mass_PIT/records.json` retém
cada análise e os resultados nas malhas fina/grossa e nas ordens 16/32.

O intervalo operacional é centrado na CDF fina e usa a maior diferença
observada entre malhas ou ordens. Ele não é uma cota rigorosa do erro físico.
A classificação também exige os controles anteriores da análise. Assim,
25.122 PITs de massa ficaram resolvidos nesse alcance; os 834 casos A0 de
distância com falha pontual mantiveram `[0,1]`. Não houve exclusão de dados.

A síntese usa os 18 grupos previstos, com 500 IDs em cada um:

- Nove grupos centrais: três prioris, A0, A gaussiano e B gaussiano completo variável.
- Três autocontroles de covariância comprimida.
- Quatro grupos de ruído: A0 e B gaussiano em dois cenários.
- Duas misturas globais de distância: A0 e B gaussiano.

Modelos aproximados e cenários de massa fixa não foram inseridos nessa
família como se fossem modelos geradores correspondentes. Os modelos dos
grupos são condicionais aos parâmetros de ruído e espectro conhecidos.

Dos 9.000 PITs de massa dos grupos correspondentes, 8.621 ficaram resolvidos;
os outros 379 pertencem a A0 com mistura de distância. Os 455 casos A0 de
distância nominal incorreta continuam registrados na produção, mas não são
um grupo correspondente à distribuição geradora.

A família completa de 126 testes permaneceu na correção de Holm. Os eventos
de log-verossimilhança ainda não foram calculados e mantiveram `[0,1]`.
Resultados preliminares:

| Classificação condicional aos intervalos fornecidos | Testes |
|---|---:|
| Não rejeição para todos os valores admissíveis nesses intervalos | 102 |
| Indeterminados numericamente | 6 |
| Eventos de log-verossimilhança não avaliados | 18 |

Os seis testes indeterminados são os testes de massa do grupo A0 com mistura
de distância. Nenhuma não rejeição é uma prova de calibração global,
identificabilidade ou informação efetiva dos dados. A incerteza dos
intervalos fornecidos limita a interpretação estatística da tabela.

Os resultados estão em `results/C09/SBC_mass_preliminary/`, com registro dos
grupos e hashes. O cálculo dos PITs consumiu 23,610 segundos de CPU e pico
RSS de 1.012.236.288 bytes, abaixo de 1,5 GiB. O acumulado de avaliações
permaneceu em 67.017.097. Permanecem necessários eventos, tratamento das
falhas e consolidação dos resultados antes do fechamento de C09.
