# Auditoria independente de C05

Data: 10/09/2026. Resultado: **derivação TT e benchmarks refinados confirmados**, com dois problemas materiais de interface a corrigir antes de uso inferencial e uma convenção de sinal a explicitar na escrita. O protótipo e seus arquivos não foram alterados. Esta é a auditoria do protótipo anterior à integração. Os nomes de scripts abaixo identificam os arquivos temporários examinados; seus testes estão incorporados em `tests/test_orf.py`. Os diagnósticos e hashes originais foram preservados em `results/C05/audit_original/`. A interface final incorporou as correções de domínio e resolução; consulte `validacao_orf.md` e os resultados versionados para o estado atual.

## 1. Fontes e conteúdo conferidos

Leitura de `SUBSIDIO_C05.md`, `response_prototype.py`, testes, scripts e JSONs das duas campanhas. Os oito testes existentes foram executados novamente: todos passaram, em cerca de 0,36 segundos, excluindo importações. Não repeti as campanhas longas inteiras; conferi seus registros e acrescentei verificações físicas independentes.

Fontes primárias locais:

- [Cordes et al., arXiv:2407.04464v2](https://arxiv.org/pdf/2407.04464v2): Eqs. (1)–(7), (15)–(16), (22), (25), (37)–(43), correspondendo especialmente às páginas PDF 2, 4, 7–8 e 11. As páginas 4 e 11 foram também renderizadas e inspecionadas visualmente nesta auditoria.
- [Liang–Trodden, arXiv:2108.05344v3](https://arxiv.org/pdf/2108.05344v3): Eqs. (20)–(26), (34)–(36), texto de normalização da Fig. 3 e Eq. (45). Páginas PDF 8 e 13 inspecionadas visualmente. A Fig. 3 contém uma inconsistência entre legenda e texto quanto a renormalizar a origem; a comparação algébrica utiliza o valor fixo `beta_T=3/(4pi)` declarado no texto, sem transportar a legenda como definição.

## 2. Derivação, projetor e normalização

O denominador `D=1+beta Omega.p` está correto para `p` apontando da Terra para o pulsar, `Omega` indicando propagação e a fase `exp[i omega(t-beta Omega.x/c)]`. A fase do pulsar é `exp[-i y D]`. Em TT, `H_0mu=0`; os termos temporais de recepção da Eq. (22) de Liang v3 não alteram a resposta espacial usada. Isso não valida a extensão automática aos demais modos.

Existe uma escolha de sinal global a declarar: na convenção geométrica de C04, `(+---)` com `g_ij=-delta_ij+H_ij`, a equação `dp_0/dlambda=(partial_0 H_ij)p^i p^j/2` dá

```text
(nu_E-nu_P)/nu_P = +p_i p_j (H_E-H_P)_ij/(2D).
```

Assim, a resposta positiva do código representa esse ganho fracionário. Para o redshift usual `z=(nu_P-nu_E)/nu_P` e residual de chegada com atraso positivo `r=int z dt`, recomenda-se escrever `R_z=-R_codigo`. A ORF e a PSD são idênticas porque o mesmo sinal atua nos dois pulsars. A alternativa de definir `z` como ganho também é consistente, mas então o residual de chegada é `-int z dt`. A redação do capítulo deve escolher uma das duas explicitamente. A conjugação da fase de Fourier em relação a C04 é uma questão separada desse sinal global.

O projetor TT foi confirmado por uma segunda construção que forma explicitamente as polarizações `e+=e_theta e_theta-e_phi e_phi` e `e_cross=e_theta e_phi+e_phi e_theta`, ambas com norma ao quadrado dois. Ele produz

```text
sum_A (p_a p_a:e_A)(p_b p_b:e_A)
 = 2(delta-mu_a mu_b)^2-(1-mu_a^2)(1-mu_b^2).
```

O prefator `3/(32pi)` da integral sobre esse projetor inclui corretamente os dois fatores `1/2` da resposta. Não há fator dois ausente.

A normalização de Cordes é consistente com a adotada no subsídio:

```text
<h_A(f,Omega) h_A'*(f',Omega')> = S_h(|f|)/(8pi) delta_AA' delta(f-f') delta²(Omega,Omega'),
S_z,ab bilateral = Gamma_ab S_h/3,
S_r,ab unilateral = Gamma_ab S_h/(6pi² f²)
                    = Gamma_ab h_c²/(12pi² f³),  h_c²=2f S_h.
```

Aqui `[S_h]=s`, `[S_z]=s` e `[S_r]=s³`, pois o resíduo tem unidade de tempo. A identidade `r_tilde=z_tilde/(i2pi f)` vale para `f!=0`; constante de integração, projeção do modelo de timing, janelas e amostragem irregular não foram implementadas em C05. Tampouco foi assumida uma relação com densidade de energia que exigiria especificar a teoria de geração/propagação.

A comparação com Liang Eq. (35) confere: `A=beta`, o símbolo de normalização do artigo vale `beta_T=3/(4pi)`, e `L1=C²`, portanto `log L1=2 log C` relativamente à Eq. (41) de Cordes. A base circular do artigo tem norma um, justificando a tradução da soma de polarizações. A resposta do segundo pulsar precisa ser conjugada; copiar literalmente uma soma sem conjugação de componentes circulares seria incorreto.

## 3. Expansão harmônica e limites

A recorrência de `P_l^2` e o peso `3(2l+1)/[32(l-1)l(l+1)(l+2)]` conferem com Cordes Eqs. (15)–(16). O produto `c_l(y_a)c_l(y_b)*` preserva distâncias diferentes; a forma `|c_l|²` só serve quando os coeficientes são iguais. Os multipolos GR apenas Terra `c_l=4(-1)^l` são um benchmark, não a afirmação de que os coeficientes com termos dos pulsars finitos sejam os mesmos.

Cada corte harmônico comum produz uma matriz positiva semidefinida: o teorema de adição escreve `P_l(p_a.p_b)` como soma de produtos de harmônicos esféricos, e os coeficientes de distância entram como amplitudes complexas. Essa propriedade exige uma montagem consistente da matriz; aceitar cada par com cortes diferentes não assegura o mesmo resultado. Positividade semidefinida também não significa invertibilidade: direções coincidentes e o limite de limiar podem produzir autovalores nulos físicos.

O fator sinc remove o cancelamento em `D=0` sem excluir a direção. A implementação analítica com Decimal permaneceu finita nos 25 casos adicionais que incluem `beta=nextafter(1,0)`, `cosine=nextafter(±1,0)`, extremos exatos e `beta=1e-4`; esse diagnóstico de finitude sozinho não certifica precisão universal. A comparação física independente abaixo inclui `beta=nextafter(1,0)` com resposta completa e concorda até cerca de `4,5e-14`.

Os limites de autocorrelação GR e massiva conferem com Cordes Eqs. (25) e (37). A expansão em beta pequeno é consistente; o limite do resto declarado pode ser obtido de `|T_ab|<=1`, da série geométrica dos dois denominadores e da anulação dos termos ímpares por paridade. A soma majorante para ordens a partir de quatro é `beta^4(5-4beta)/(1-beta)^2`, multiplicada por `3/8`.

O limiar `beta=0` e a expressão `(1-e^-iya)(1-e^iyb) P2(delta)/5` estão corretos como limite cinemático do setor TT considerado. O parâmetro de oscilação angular é `beta*y`, e a coerência pulsar–pulsar também depende de `beta|y_a p_a-y_b p_b|`. Logo, nem grande `y` nem ausência de massa isoladamente autorizam descartar todos os termos dos pulsars. A descontinuidade diagonal de HD é uma aproximação com ordem de limites; não deve ser introduzida no integral finito.

## 4. Quatro verificações independentes executadas

`test_independent.py` usa um único céu de quadratura para seis pulsars em direções arbitrárias, incluindo um par separado por aproximadamente `1e-7` rad, direções antipodais e fases diferentes. Forma as polarizações explicitamente, sem chamar o projetor, o fator de transferência ou as coordenadas de par do protótipo. Resultados em `independent_results.json`:

1. Matriz de Gram de polarizações explícitas versus matriz harmônica, para `beta=0,0.2,nextafter(1,0),1`: diferença máxima **4,43e-14**; hermiticidade satisfeita; menor autovalor mínimo **-2,28e-15**, compatível com arredondamento. A parte imaginária de um par quase coincidente e distâncias diferentes chegou a **0,1654**, portanto não é desprezível por identidade matemática.
2. Rotação global dos pulsars, mantendo fixo o céu discreto: diferença máxima **4,85e-14**. Isso verifica isotropia numericamente sem reduzir previamente cada par ao produto escalar.
3. Extensão de frequência negativa: `Gamma(-f)=Gamma(f)*` e covariância real no tempo, simétrica e positiva semidefinida. No exemplo de um canal, descartar `Im(Gamma)` muda uma correlação em defasagem não nula em **0,08385** nas unidades normalizadas do teste.
4. Coincidência exata e aproximação contínua por posições/distâncias próximas: a correlação coincide com a auto sem um seletor diagonal; perturbações de `1e-6` rad e `1e-6` em fase alteram o resultado em menos de **3,34e-7**.

Os quatro testes passaram em aproximadamente 0,22 segundos, excluindo importações. Foram usados `N_mu=120`, `N_phi=240`, `l_max=170`, `N_mu,harm=300` e fases entre 19 e 90; essa bateria independente não amplia a certificação a fases arbitrariamente grandes.

## 5. Achados materiais e reproduções mínimas

### A. Defaults silenciosamente subresolvidos

Em GR, `y=2pi*1000.125=6283.970705342984` e mesmo pulsar:

| Cálculo | Gamma_aa |
|---|---:|
| Auto GR exata | 0,999999962017 |
| `harmonic_orf(1,1,y,y)` com defaults | 0,500346501321 |
| `direct_orf(1,1,y,y)` com defaults | 0,929066664960 |

A auto harmônica quase perde metade da potência apesar de retornar um número plausível. Para separação `pi/8`, a direta default retorna `0,275508458285`; a harmônica default retorna `0,303880599502` e fica muito próxima da resposta apenas Terra, embora não tenha retido a contribuição finita com precisão. Valores completos estão em `diagnostics.json`.

Isso **não invalida os benchmarks refinados**. Os 20 casos registrados têm diferença máxima entre métodos `2,94e-13`, e os 16 casos de coerência, `5,25e-12`. O problema é a API expor cálculos sem status de convergência, que podem ser usados acidentalmente em inferência. O teste pequeno e o benchmark grande também têm custos distintos: uma avaliação refinada em `beta≈1`, `fL/c≈1000` custa segundos; os testes que terminam em frações de segundo não representam o custo da campanha inteira.

### B. Domínio de harmonic_orf incompleto

Reproduções executadas:

```python
harmonic_orf(0.9, 1.1, lmax=20)          # Retorna ~0.493560893, cosine impossível.
harmonic_orf(0.9, float('nan'), lmax=20) # Retorna NaN.
harmonic_orf(0.9, 0, ya=10, lmax=20)   # Retorna um híbrido Terra–pulsar não declarado.
```

`direct_orf` já rejeita essas misturas/distâncias e produtos escalares fora do domínio. Recomenda-se um contrato comum: `beta` e `cosine` escalares reais finitos, `0<=beta<=1`, `-1<=cosine<=1`, duas fases finitas não negativas ou ambas ausentes, inteiros positivos para resoluções. Um cálculo misto Terra–resposta completa poderia ser útil como objeto separado, mas não deve surgir de omissão silenciosa de argumento.

## 6. Proposta de interface para integração

`checked_response.py` contém um wrapper separado, sem alterar o protótipo. Exige `Resolution` grossa e fina, `ResourceBudget`, `atol` e `rtol` explícitos. Antes de qualquer quadratura:

- Valida domínio e crescimento estrito de todas as resoluções.
- Limita a fase ao envelope auditado `[0, 2pi*1000.125+1]`, que inclui a campanha de distâncias diferentes. Esse envelope não certifica todos os seus pontos; os controles de convergência continuam obrigatórios.
- Estima trabalho de recorrências, integral angular e geração dos nós, e uma reserva de memória considerando blocos de azimute e cache. Esses números são aproximações conservadoras de planejamento, não promessa de segundos ou limite rigoroso de memória residente. Ordens acima de 20000 exigem revisão explícita da implementação.
- Rejeita o pedido quando o orçamento informado é insuficiente, sem iniciar alocação de quadratura.

O wrapper calcula separadamente refinamento dos nós harmônicos, aumento de `l_max` e, para resposta completa, refinamento direto e concordância entre os dois métodos. Para apenas Terra, compara à expressão analítica. Só retorna `(Gamma_complexa, report)` quando **todos** os critérios satisfazem `atol+rtol|Gamma|`. Falhas lançam `ConvergenceError` com relatório; o chamador precisa solicitar resoluções maiores e passar novamente pela estimativa de recursos. Assim não há crescimento automático sem orçamento. Autos e quase coincidência passam pela mesma resposta finita, preservando as fases complexas.

O acordo por refinamento é um certificado **empírico**, não um limite rigoroso do erro. C07 deve usar cortes comuns para montar a matriz e verificar sua hermiticidade/positividade e condicionamento; tolerância escalar de ORF não certifica automaticamente a estabilidade da inversão ou do posterior. Uma campanha de MCMC também precisa reutilizar multipolos por frequência/distância: o protótipo de par ainda não implementa esse cache científico, embora o subsídio corretamente o proponha.

`check_wrapper.py` verificou quatro casos convergidos, incluindo auto no limiar, par quase coincidente com fases diferentes e apenas Terra. Também verificou sete rejeições: domínio, fase fora do envelope, ausência de resoluções, orçamento insuficiente antes de qualquer chamada numérica e auto GR deliberadamente subresolvida. **Tudo passou**; evidências em `wrapper_checks.json`. A integração deverá ajustar somente o caminho de importação para o módulo definitivo e conservar os contratos.

```sh
tmp/c05_response/.venv/bin/python tmp/c05_audit/test_independent.py
tmp/c05_response/.venv/bin/python tmp/c05_audit/check_wrapper.py
```

## 7. Limites da aprovação científica

Não foram validados: inferência com dados reais, projeção do timing, médias em distância/frequência, distribuição de fontes, covariâncias de estimadores, modos escalar/vetorial, regime evanescente `f<f_g`, custos para todo um PTA real ou precisão universal em `fL/c` maior que o envelope executado. Essas tarefas permanecem nas etapas seguintes. O marco C05 pode apresentar a resposta tensorial, as reproduções primárias, os limites e a implementação com diagnóstico de convergência; deve evitar anunciar inferência física concluída.
