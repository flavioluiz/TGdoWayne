# C_full: preflight próprio, sem execução

Status: **prospectivo, não autorizado e não executado**. Este arquivo define apenas os gates para a resposta C_full e sua representação; nenhum banco nativo ou posterior está previsto.

Definição: Γ_full,k(u)=Γ_física,1(u), para k=1,…,4. Apenas a ORF é repetida. Mantêm-se as quatro frequências físicas, os espectros do sinal e ruído, a normalização por scale_k, os estimadores H, os pesos de compressão e as observações do experimento C07. A expressão não significa copiar a covariância total da primeira frequência para todas as demais.

A identidade externa será C_full_CN/C_full_G, com kernel interno B_CN/B_G para as duas classes de observação. O novo manifest incluirá variante, hashes da tabela/coefs, configuração/priori, dados, fontes, oráculos reutilizados e estes gates. Nenhum manifest físico C07 ou C_beta constitui aprovação de C_full.

## Curvas e oráculos existentes

**Coarse:** primeiro canal da tabela histórica C07 com4169 nós, `tmp/c07_sampler/results/table_beta4097_local.npz`, cujo hash `ceafa7abcb53c405665cad4babff787ebd3ca9a33ca85d9f6cfd72ce3e7cc740` foi conferido contra o relatório arquivado em ROOT `results/C07/orf_interpolation/dense_local_validation.json`. A construção da cúbica reproduzirá a convenção histórica x=−β: not-a-knot em β=1, derivada zero em β=0. Ela deverá passar Bernstein/PSD sem fallback; qualquer falha encerra o gate.

**Fine:** curva física original do primeiro canal com8336 nós e coeficientes já identificados bit a bit contra o arquivo ROOT. Usar `tmp/c08_beta_table/first_curve_root.npz`, sem respline. O arquivo final repete seus coeficientes e matrizes em4 canais:307.261.440B de coeficientes +76.824.576B de matrizes. A expansão deve ser bit a bit em cada canal.

**Oráculos:** primeiro canal dos143 controles C_beta históricos e dos72 controles novos já avaliados. Os arquivos são `tmp/c08_beta_table/results/gates/validation_matrices.npz` (`oracle[:,0]`) e `tmp/c08_beta_table_v2/results/oracle_channel01.npz` (`Gamma_fine`). São quadraturas completas do canal1, ordens1496/3012 e1536/3092; hashes e identidades serão congelados antes de executar C_full. Todos os controles usam β efetivamente representado por u. **Zero novas integrais harmônicas ou angulares**: a reprodução da ORF do canal1 não exige recalcular os oráculos disponíveis. A evidência angular anterior é herdada explicitamente; não será descrita como novos testes geométricos C_full.

## Gates prospectivos

1. Conferir hashes, metadados, geometria, fases, shapes, finitude, Hermiticidade, endpoints e PSD/Bernstein. Conferir o vínculo da curva fine com a primeira curva ROOT. Repetição dos canais exata; espectros/ruídos/observações inalterados.
2. Reavaliar **215 massas×64 nuisances novos×32 observações×3 representações**:1.320.960 logL. Nuisances uniformes na mesma priori retangular, seed808140201; a lista de215 massas está fixada no JSON. Usar coarse/fine/oráculo com Γ_1 repetida, mantendo os espectros por frequência. Critérios independentes: máximo |ΔlogL|≤.001 para coarse/fine e fine/oráculo. Não utilizar logL C_beta antigos como logL C_full.
3. Em u={0,.5,1}, nos primeiros6 nuisances da nova regra e nas3 representações,54 casos de momentos terão referência independente. Montar C_k diretamente dos três espectros e Γ_1: sinal correlacionado + ruídos diagonais; calcular μ_i=tr(H_iC_k), Σ_ij=tr(H_iC_kH_jC_k), somando com w_k e w_k². Comparar com o kernel comprimido por componentes, erro normalizado≤10⁻¹⁰. Para cada caso,32 densidades de `scipy.stats.multivariate_normal.logpdf` serão comparadas à normalização do kernel, erro absoluto≤10⁻⁸. Esses **1.728 logL adicionais são contabilizados**, apesar de servirem apenas à verificação independente.
4. Verificar âncoras u={0,.2,.5,.8,1}, sem inferência. O primeiro canal tem de coincidir. Em u=1, todos os canais C_full herdam a matriz de ORF tensorial no limiar, de posto≤5. A exigência de positividade da covariância total continua incluindo ruído.
5. **Em massa zero C_full não coincide em geral com B:** mesmo β=1, as fases de pulsar y_k variam com frequência em B; C_full usa somente y_1. Registrar a discrepância matricial e de momentos usando as matrizes físicas ROOT em u=0. Não impor igualdade incorreta, nem forçar diferença positiva por alteração numérica. Já C_beta=B em u=0 por definição, pois conserva y_k; essa comparação distingue as duas aproximações. O limite ideal somente-termo-Terra não será confundido com o modelo finito com termos de pulsar.
6. Exportar tabela/coeficientes explicitamente, registrar hashes e relatório finito. Não aprovar automaticamente futuras regiões posteriores; parâmetros, observações e controles cobrem somente o domínio declarado.

## Orçamento independente

Ledger **C_full próprio**, iniciado em zero: **1.322.688 logL previstos**, teto **1.400.000**; teto harmônico0 e angular0. O cap C_beta1,6M permanece intacto e não é reinterpretado. Reservar1GiB numérico/1,5GiB RSS, um trabalhador/BLAS1. Curvas e gates não têm base harmônica residente; exportação pode ocorrer em processo fresco separado, explicitamente decidido na autorização/receita antes da execução. Não construir banco de likelihood nativo.

A expectativa é de segundos a poucas dezenas de segundos de cálculo e IO, não uma promessa. Registrar tempo/RSS reais por fase. Cópias caller/coeficientes/exportação e buffers do carregador têm orçamento simultâneo, não só tamanho do arquivo. Qualquer falha preserva resultados e interrompe sem aumentar resolução, número de amostras ou tolerâncias. Não há posterior, campanha128C, mapa T/janela ou edição C07 neste preflight.
