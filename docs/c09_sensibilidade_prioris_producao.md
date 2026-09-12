# Sensibilidade pareada às prioris em C09

Painel prospectivo dos primeiros 32 dados centrais gerados sob priori uniforme em u.
Cada observação foi analisada com dez modelos e cinco medidas normalizadas.
As 1.600 integrações incluem 320 resultados uniformes já existentes, recalculados
a partir do cache. Há 1.280 contrastes adicionais; não são novas observações nem SBC.

A tabela apresenta medianas descritivas sobre os 32 dados. O intervalo da mediana
de q95 decorre dos intervalos numéricos das duas malhas; não é intervalo de confiança
populacional. KL está em nats e compara cada posterior à sua própria priori.
As odds comparam a probabilidade posterior e a priori de u ≤ 0,2.

| Modelo | Priori | q95 da priori | Mediana q95 posterior | Mediana KL | Mediana razão de odds |
|---|---|---:|---:|---:|---:|
| A0_CN | uniform_u | 0.9500 | [0.9355, 0.9360] | 0.04893 | 0.9732 |
| A0_CN | uniform_u_squared | 0.9747 | [0.9670, 0.9675] | 0.04019 | 1.0367 |
| A0_CN | log_uniform_u_0.001 | 0.7079 | [0.6856, 0.6861] | 0.03205 | 0.9047 |
| A0_CN | log_uniform_u_0.0001 | 0.6310 | [0.6184, 0.6189] | 0.02610 | 0.8999 |
| A0_CN | log_uniform_u_0.01 | 0.7943 | [0.7663, 0.7668] | 0.04079 | 0.9167 |
| A_G | uniform_u | 0.9500 | [0.9451, 0.9456] | 0.10281 | 0.6748 |
| A_G | uniform_u_squared | 0.9747 | [0.9692, 0.9697] | 0.04479 | 0.6950 |
| A_G | log_uniform_u_0.001 | 0.7079 | [0.7866, 0.7871] | 0.07541 | 0.6105 |
| A_G | log_uniform_u_0.0001 | 0.6310 | [0.7366, 0.7371] | 0.06055 | 0.6017 |
| A_G | log_uniform_u_0.01 | 0.7943 | [0.8381, 0.8385] | 0.07845 | 0.6326 |
| B_CN_full_variable | uniform_u | 0.9500 | [0.9473, 0.9478] | 0.00230 | 1.0324 |
| B_CN_full_variable | uniform_u_squared | 0.9747 | [0.9736, 0.9741] | 0.00130 | 1.0434 |
| B_CN_full_variable | log_uniform_u_0.001 | 0.7079 | [0.6944, 0.6949] | 0.00199 | 1.0200 |
| B_CN_full_variable | log_uniform_u_0.0001 | 0.6310 | [0.6165, 0.6170] | 0.00166 | 1.0197 |
| B_CN_full_variable | log_uniform_u_0.01 | 0.7943 | [0.7834, 0.7839] | 0.00232 | 1.0206 |
| B_CN_diagonal_variable | uniform_u | 0.9500 | [0.9478, 0.9482] | 0.00280 | 1.0325 |
| B_CN_diagonal_variable | uniform_u_squared | 0.9747 | [0.9739, 0.9744] | 0.00171 | 1.0403 |
| B_CN_diagonal_variable | log_uniform_u_0.001 | 0.7079 | [0.6956, 0.6961] | 0.00191 | 1.0202 |
| B_CN_diagonal_variable | log_uniform_u_0.0001 | 0.6310 | [0.6175, 0.6180] | 0.00157 | 1.0200 |
| B_CN_diagonal_variable | log_uniform_u_0.01 | 0.7943 | [0.7846, 0.7851] | 0.00235 | 1.0208 |
| B_CN_full_fixed | uniform_u | 0.9500 | [0.9470, 0.9475] | 0.00229 | 1.0475 |
| B_CN_full_fixed | uniform_u_squared | 0.9747 | [0.9734, 0.9739] | 0.00126 | 1.0576 |
| B_CN_full_fixed | log_uniform_u_0.001 | 0.7079 | [0.6905, 0.6910] | 0.00168 | 1.0364 |
| B_CN_full_fixed | log_uniform_u_0.0001 | 0.6310 | [0.6114, 0.6119] | 0.00138 | 1.0366 |
| B_CN_full_fixed | log_uniform_u_0.01 | 0.7943 | [0.7808, 0.7813] | 0.00206 | 1.0360 |
| B_CN_diagonal_fixed | uniform_u | 0.9500 | [0.9470, 0.9475] | 0.00226 | 1.0464 |
| B_CN_diagonal_fixed | uniform_u_squared | 0.9747 | [0.9734, 0.9739] | 0.00136 | 1.0565 |
| B_CN_diagonal_fixed | log_uniform_u_0.001 | 0.7079 | [0.6910, 0.6915] | 0.00166 | 1.0354 |
| B_CN_diagonal_fixed | log_uniform_u_0.0001 | 0.6310 | [0.6119, 0.6123] | 0.00137 | 1.0355 |
| B_CN_diagonal_fixed | log_uniform_u_0.01 | 0.7943 | [0.7810, 0.7815] | 0.00204 | 1.0350 |
| B_G_full_variable | uniform_u | 0.9500 | [0.9514, 0.9519] | 0.00790 | 0.9453 |
| B_G_full_variable | uniform_u_squared | 0.9747 | [0.9749, 0.9753] | 0.00444 | 0.9428 |
| B_G_full_variable | log_uniform_u_0.001 | 0.7079 | [0.7239, 0.7244] | 0.00561 | 0.9472 |
| B_G_full_variable | log_uniform_u_0.0001 | 0.6310 | [0.6509, 0.6514] | 0.00457 | 0.9463 |
| B_G_full_variable | log_uniform_u_0.01 | 0.7943 | [0.8052, 0.8057] | 0.00682 | 0.9494 |
| B_G_diagonal_variable | uniform_u | 0.9500 | [0.9509, 0.9514] | 0.00805 | 0.9504 |
| B_G_diagonal_variable | uniform_u_squared | 0.9747 | [0.9746, 0.9751] | 0.00444 | 0.9508 |
| B_G_diagonal_variable | log_uniform_u_0.001 | 0.7079 | [0.7217, 0.7222] | 0.00554 | 0.9486 |
| B_G_diagonal_variable | log_uniform_u_0.0001 | 0.6310 | [0.6482, 0.6487] | 0.00451 | 0.9476 |
| B_G_diagonal_variable | log_uniform_u_0.01 | 0.7943 | [0.8033, 0.8037] | 0.00664 | 0.9513 |
| B_G_full_fixed | uniform_u | 0.9500 | [0.9497, 0.9502] | 0.00753 | 0.9792 |
| B_G_full_fixed | uniform_u_squared | 0.9747 | [0.9744, 0.9749] | 0.00499 | 0.9814 |
| B_G_full_fixed | log_uniform_u_0.001 | 0.7079 | [0.7127, 0.7132] | 0.00485 | 0.9759 |
| B_G_full_fixed | log_uniform_u_0.0001 | 0.6310 | [0.6375, 0.6380] | 0.00395 | 0.9752 |
| B_G_full_fixed | log_uniform_u_0.01 | 0.7943 | [0.7970, 0.7975] | 0.00589 | 0.9775 |
| B_G_diagonal_fixed | uniform_u | 0.9500 | [0.9500, 0.9504] | 0.00767 | 0.9755 |
| B_G_diagonal_fixed | uniform_u_squared | 0.9747 | [0.9744, 0.9749] | 0.00497 | 0.9773 |
| B_G_diagonal_fixed | log_uniform_u_0.001 | 0.7079 | [0.7139, 0.7144] | 0.00494 | 0.9724 |
| B_G_diagonal_fixed | log_uniform_u_0.0001 | 0.6310 | [0.6387, 0.6392] | 0.00403 | 0.9717 |
| B_G_diagonal_fixed | log_uniform_u_0.01 | 0.7943 | [0.7977, 0.7982] | 0.00611 | 0.9742 |

Nas famílias completas variáveis, os quantis mudam apreciavelmente com a
medida e com o corte logarítmico. Para A0, a mediana de q95 fica perto de 0,936
com priori uniforme, 0,967 com uniforme em u² e 0,619–0,767 nos três cortes
logarítmicos. As medianas de KL correspondentes ficam entre 0,026 e 0,049 nat.
Essas duas observações devem ser apresentadas juntas: um limite menor não
estabelece, por si só, maior informação dos dados. KL pequena na mediana
não implica informação nula em todas as realizações.

Os modelos CN e gaussianos usam observações pareadas com marginais diferentes;
os contrastes de priori acima mantêm o mesmo dado dentro de cada modelo.
As diferenças de KL entre prioris usam referências distintas e não são um teste
universal de qualidade ou identificabilidade.

Todas as comparações entre malhas passaram, preservadas as tolerâncias de C09.
Os controles finitos de verossimilhança são reutilizados porque a priori não
altera essa função. As referências adaptativas para os cortes logarítmicos
adicionais passaram nos dados 0 e 31 para A0 e B_CN/B_G completos variáveis
(12 posteriores; `results/C09/production_references/audit.json`). Isso é uma
verificação representativa, não uma referência adaptativa para cada um dos
1.280 contrastes. A calibração e as misturas de distância continuam pendentes.
Os intervalos W1 e de distância entre CDFs nos dados brutos dizem respeito à
tabela positiva normalizada; não incluem erro físico uniforme.

Fontes: `results/C09/paired_prior_panel/` e `scripts/painel_prioris_c09.py`.
Nenhuma nova avaliação de verossimilhança ou resposta física foi feita neste painel.
