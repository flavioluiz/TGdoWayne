# Auditoria independente do protótipo C++ C07

**Conclusão sobre a matemática: não foi encontrado defeito nas fórmulas ou nos índices para as entradas válidas testadas.** O protótipo original não era um wrapper público seguro. O candidato final `native_owned.py` acrescenta as verificações e a posse dos dados necessárias para seu uso como backend interno; o módulo NumPy continua sendo a referência obrigatória. Esta revisão não certifica toda a aproximação posterior, a tabela fora de seu domínio validado ou a calibração SBC.

## Fontes e escopo

Todos os arquivos auditados foram copiados, sem edição, para `sources/`. Os originais em `tmp/c07_cpp_moments/` não foram alterados por este agente. Fontes principais:

- `full.cpp`: SHA256 `fb4220e9beaf3e9be83c7ec74007033cdabd9ce620facda629b76ef161aafd2c`.
- `full_guarded.cpp`: `4e089ba8588158d7ab3233c2601a55942ddfeb1e28c6d06578a582f22da66154`.
- `native_guarded.py`, antecedente: `984bfafaf96acbd9da1b5afe16f970da3307aeb3d31bd730138a4bfe39bca4ce`.
- `native_owned.py`, candidato final: `5da411e92c3340370ce8eebb94862cf32d39f99053f7f871f3c716c0ac8a391f`.
- Biblioteca final `full_guarded.dylib`: `a9e909e653a2a34fa2d40295fd7f3cc28bfc7acf058591bd0adc5ab938bea9d0`.

A diferença textual entre os dois C++ contém somente o nome/ABI da função, número de intervalos e verificações iniciais; os corpos das operações matemáticas permanecem iguais. A tabela física usada foi `table_beta8193_local.npz`, com8336nós, coordenada−β e condição de derivada nula no limiar, SHA256 `75632dfbdd9cce8b60b9f760a3177a76798a4adb7ac9ccc724092aeaf53ad70d`. A validação dessa interpolação pertence ao registro independente do projeto; esta auditoria compara cálculos na mesma tabela.

## Conferência das fórmulas

Para A0_CN, em cada frequência o kernel forma C=P_gΓ+P_r diag(red²)+P_w diag(σ²). A fatoração usa

    L_ab = [C_ab − Σ_{j<b} L_aj conjugate(L_bj)] / L_bb,

com pivô real positivo e solução progressiva v=L⁻¹q. O termo acumulado é −q†C⁻¹q−logdetC−Plogπ, somado nosKcanais. Assim, a CN própria não recebe um fator1/2 indevido. O conjugado está no segundo fator da atualização de Cholesky; a norma complexa aparece em `std::norm(v)`. Na entrada válida Hermitiana, a diagonal é real, verificada pelo construtor final.

Para A/B, a normal real usa −½[(y−μ)ᵀΣ⁻¹(y−μ)+logdetΣ+Dlog(2π)], somada nos canais quando não comprimida. A tabela cúbica em uma fração local f tem componentes C₀,C₁,C₂,C₃ e pesos P_g(1,f,f²,f³), maisP_r,P_w para os dois ruídos. São6componentes e21pares s≤t.

A média de cada estimador é μ_a=Tr(H_aC). A covariância CN dos estimadores é ReTr(H_aCH_bC). Para s<t, o coeficiente correto de w_sw_t é

    ReTr(H_a C_s H_b C_t + H_a C_t H_b C_s).

O Python original calcula2ReTr(H_aC_sH_bC_t) e depois simetriza os índices de estimador a,b. Pela ciclicidade do traço, essa combinação equivale à expressão acima. O C++ não deve multiplicar novamente por2. A ordem dos21pares coincide com a construção do banco. O empacotamento `tril_indices(D)` segue00,10,11,20,21,22,…, exatamente a ordem dos loops nativos.

Na compressão, μ_B=Σ_k w_kμ_k e Σ_B=Σ_k w_k²Σ_k. O quadrado é necessário porque os blocos Fourier são independentes no experimento declarado. O kernel usa `wm` na média e `wc=wm*wm` na covariância; também comprime as observações com os mesmos pesos. Não acrescenta covariância entre frequências ou uma hipótese de independência de segmentos observacionais que não exista no modelo.

O alvo está em ordem modelo–realização: `model=target/nd`, `id=target%nd`. O mapa é0=A0_CN(q),1=A_CN(yfísico),2=B_CN(zfísico),3=A_G(ygaussiano),4=B_G(zgaussiano). `kind=(model>=3)` seleciona o grupo correto. Testes comnd=3e7, alvos intercalados e todos os cinco modelos detectariam uma codificação acidental de16realizações.

O kernel calcula somente logL normalizada na medida dos dados padronizados; não acrescenta priori nem Jacobiano logit. Constantes de CN/normal foram conferidas. A existência dessas constantes não autoriza Bayes factors entre dados comprimidos e completos, que vivem em espaços diferentes.

## Verificação numérica independente

`independent_review.py` constrói matrizes Hermitianas complexas SPD a partir de coeficientes de Bernstein SPD. As matrizesH são aleatórias, com partes imaginárias não nulas. A referência forma C diretamente e usa `slogdet`, solução de sistemas emC e traços matriciais completos para μ/Σ; não utiliza os bancos polinomiais da implementação auditada. Os bancos usados pela chamada nativa foram construídos separadamente com os dois termos cruzados explícitos.

Foram avaliados360pontos em(P,K,D)=(3,3,3),(5,4,6),(16,8,16), mais120avaliações após transformação unitária consistente deC,H,q. Todos os cinco modelos foram cobertos. O maior erro absoluto foi3,41×10⁻¹³, e a invariância unitária diferiu em1,42×10⁻¹⁴. Isso inclui o limite máximo dos buffers locais; não extrapola para P>16,D>16ouK>8.

`physical_review.py` avaliou512pontos selecionados por nova seed entre estados posteriores históricos e recalculados na tabela8336. Nenhuma likelihood foi inspecionada para escolher os índices. O máximo |ΔlogL| contra a fórmula matricial direta foi8,53×10⁻¹⁴. Outros400pontos cobriram os80alvos emu=0,nextafter(0,1),.5,nextafter(1,0),1; erro máximo2,91×10⁻¹¹, relativo escalado1,57×10⁻¹⁵. Os dados e índices estão salvos em`results/physical_arrays.npz`; isso não é uma nova produção posterior ou SBC.

O ensaio físico do ROOT em16384pontos adicionais da priori está preservado em`sources/full_benchmark.json`; ele é evidência complementar, não uma execução desta auditoria. Não se atribui a esta revisão seu benchmark de desempenho ou seu teste multithread.

## Negativas e defeitos do antecedente

Dez grupos de controles negativos do kernel original passaram: θnão finito, alvos negativos/fora do domínio/não inteiros/booleanos, massa fora de[0,1], pivôs CN e normal negativos, covariânciaNaN e dimensões acima da capacidade. Não houve jitter, clipping de autovalores ou substituição da likelihood com falha.

Foram demonstradas limitações concretas do antecedente, em chamadas com buffers de tamanho válido: dimensões zero devolviam0como logL, modelo de índice5era tratado como uma normal existente e parte imaginária diagonal era ignorada. O wrapper original também aceitava strings numéricas/booleanos emθe não validava os comprimentos dos bancos. Ponteiros inválidos, buffers curtos, `nd=0` e segmentos fora da memória não foram executados; sua falta de verificação foi estabelecida pela leitura do contrato, sem provocar comportamento indefinido.

O wrapper `native_guarded.py` passou34verificações de entrada/estado, porém mantinha alias com o arraytargets do chamador. O ROOT criou a versão separada `native_owned.py`, copiandoθeIDs antes da validação final e do uso nativo. O mesmo conjunto de34verificações passou nessa versão, e foi confirmado que IDs entregues ao C++ não compartilham memória com o chamador. O antecedente foi preservado, sem atribuir retroativamente a ele essa proteção.

Os34controles incluem bancos truncados/não finitos/não simétricos, Γnão Hermitiana, diagonal complexa, shapes de observação, compressão inconsistente, nós não crescentes, coordenada incorreta, frequências/escala/dt inválidos, ruído branco zero, tipos e domínio de entrada, IDsuint64fora do domínio, lote vazio, covariância de momento não SPD, input desalinhado e tentativas de escrever nos buffers estáticos. Um teste modifica depois da construção as frequências, escala,dt,ruídos,pesos,nós,coeficientes,bancos,q,y,z e osbounds originais: a saída permanece idêntica bit a bit. Não se confunde esse teste com uma corrida de mutação concorrente.

## Contrato recomendado para integração

1. Expor somente o wrapper com cópias próprias, shapes/dtypes reais ou complexos declarados, finitude, alinhamento e domínio físico validados. Manter a função C como detalhe interno; ela não recebe comprimentos independentes de cada buffer e, portanto, não é uma API segura para ponteiros arbitrários.
2. Usar um banco construído pelo módulo NumPy de referência, com tabela/ordem de modelos/estatísticas/frequências rastreáveis. A simetria e os shapes não provam que um banco arbitrário corresponde aΓ,H e ao ruído; essa consistência exige o construtor e os crosschecks independentes. A combinação de coeficientes precisa manter a validação PSD/interpolação do projeto.
3. Manter limites1≤P,D≤16,1≤K≤8,nd≥1eI≥1; validar índices de segmento/target e não consumir resultados parciais quando a função sinaliza erro. Lotes de tamanho zero podem devolver vetor vazio após validar o restante do contexto. Os resultados permanecemfloat64.
4. Preservar os dados estáticos em buffers próprios alinhados/contíguos/read-only e copiar as entradas por chamada. Uma chamada não altera caches globais ou o modelo de origem. O carregamento deve receber explicitamente a biblioteca compilada; não compilar ou baixar código silenciosamente durante inferência.
5. Registrar compilador, plataforma/arquitetura, flags de compilação, hashes da fonte e binário. Evitar flags que descartem as verificações de NaN/Inf ou alterem a semântica numérica sem nova validação. Para cada plataforma suportada, conferir tamanho/layout complexo e executar as fixtures; os binários `.dylib` auditados são os deste ambiente, não artefatos universais.
6. Preservar o backend NumPy como referência e fallback explícito. Repetir os controles relevantes quando mudarem fórmula, ordenação, tabela, banco, ABI ou compilação. O backend acelerado não substitui diagnósticos de peso, MCSE, refinamento posterior ou a investigação científica dos controles SBC.

Não há defeito matemático conhecido remanescente no candidato final sob esse contrato. A decisão de integrar e recompilar é do ROOT, com a evidência local deste pacote. A confirmação física específica de`native_owned` está concluída em`results/owned_physical_review.json`: os912resultados foram idênticos bit a bit aos do kernel original, com os mesmos erros contra a referência NumPy. Nenhuma fórmula ou tolerância foi alterada para obter essa concordância.
