# C_full v2: refinamento local mínimo proposto

Status: **não autorizado/não executado**. A primeira candidata C_full permanece falha; os215 controles originais terminaram por continuação diagnóstica autorizada, com uma falha coarse/fine e nenhuma fine/oráculo. O máximo fine/oráculo foi1,92520×10⁻⁵. As54 referências por traços/SciPy passaram: erros normalizados máximos μ=2,65×10⁻¹⁶, Σ=1,07×10⁻¹⁵ e logpdf=4,55×10⁻¹²; maior condicionamento77,07. Isso motiva uma etapa pequena e mensurável de resolução, sem afrouxar critérios.

**Coarse novo:** a curva fine8336 original inteira, imutável. **Fine novo:** dividir por2 somente a grade uniforme na região geométrica β≤1/64, mantendo todos os nós/patches antigos. São **112 novos nós**,353 nós candidatos locais,8448 nós globais. Não é uma modificação restrita ao ponto que falhou.

O spline local será clamped à derivada da curva antiga no join x=−β e à derivada zero em β=0; os coeficientes externos e matrizes nos nós antigos permanecem bit a bit. Reutilizar o stitch C1 já testado em C_beta, sem fallback nem clipping. Esta é uma curva própria C_full: não modifica a primeira curva C_beta nem o arquivo físico C07.

Nos353 candidatos locais, recalcular Γ_1 com as fases físicas y_1 integrais e duas ordens harmônicas:122/264 e162/344. O maior βy é21,8166. Comparar ambas entre si e com os241 nós antigos antes de restaurar exatamente as matrizes antigas. Custo:739.842.816 produtos; buffers estimados2,51MB. A repetição para os4 canais C_full ocorre somente após esses controles.

Acrescentar **72 controles novos**, fixados por seed808150101, distintos dos215 históricos:24uniformes emu,24uniformes emβ,16log-uniformes emβ e8âncoras geométricas. A lista exata está no JSON. Todos recebem oráculos completos do canal1, ordens1496/3012 e1536/3092, independentemente das ordens locais. Custo15.982.548.480 produtos. Acrescentar4 comparações diretas (2pares×2β) com1.352.456 pontos angulares; os oráculos harmônicos desses anchors já existem no conjunto histórico e serão reutilizados por identidade.

Os215 caches originais fornecem o novo coarse (fine antigo) e o oráculo. Apenas57 controles dentro do patch exigem novo fine:116.736logL. Fora dele, reutilizar fine antigo somente após conferir Γ bit a bit. Os72 novos controles recebem64 nuisances novos (seed808150201) e32observações nas3representações:442.368logL. Mais54casos independentes de momentos/SciPy:1.728logL, usando u={0, u(β=3/(8×64)),1}; nos endpoints, os primeiros6 nuisances da coorte histórica, e no novo ponto interior os primeiros6 da coorte nova, permitindo comparar com caches da própria regra sem avaliações de logL ocultas. Totalnovo: **560.832logL**.

Todos os critérios permanecem: quadraturas10⁻⁸, direto10⁻⁷, coarse/fine e fine/oráculo.001, momentos normalizados10⁻¹⁰ e SciPy absoluto10⁻⁸. Resultados finitos não são prova uniforme; gates posteriores seguem separados. Falha interrompe e preserva, sem refinamento automático.

## Orçamento próprio proposto

O ledger C_full parte do histórico **1.322.688logL/zeroquadraturas**. Adicionar **16.722.391.296produtos /1.352.456pontos angulares /560.832logL** leva a **1.883.520logL cumulativos**. Solicitação explícita de limites v2 próprios:20bilhões deprodutos,2milhões de pontos angulares,600mil novos logL e2milhões cumulativos. O limite original C_full1,4M permanece registrado na execução original; esta proposta não o reinterpreta. Os tetos/ledger C_beta também não mudam.

Cinco processos novos e sequenciais, previamente definidos: curva local; oráculo coarse; oráculo fine; direto+gatesLL; exportação. Um trabalhador/BLAS1,1GiB numérico/1,5GiB RSS por trabalhador. Nenhum banco nativo ou posterior. A memória da base do canal1 é pequena frente ao teto; ainda assim os processos frescos evitam depender da liberação do alocador observada na falha C_beta. Expectativa operacional de poucas dezenas de segundos, a medir, incluindo IO/inicialização. Sem execução antes da leitura/autorização deste preflight.
