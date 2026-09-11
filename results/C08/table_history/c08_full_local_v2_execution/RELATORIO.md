# C_full v2: tabela passou nos gates finitos previstos

Artefato final: `results/C_full_table.npz`, **8448 nós**,4canais, coeficientes explícitos em x=−β. SHA256: `96e552bc97b4978fbe8c8c825c63cef8c7cf6ad31895b4eb22204aaaf0f150ed`. Relatório consolidado: **`results/final_report.json`**; os relatórios originais dos cinco workers permanecem intactos.

A curva física inicial do primeiro canal (8336nós) tornou-se coarse. O fine próprio C_full acrescentou somente112nós, subdividindo por2 todos os intervalos uniformes β≤1/64, mantendo patches anteriores. Junção C1, paridade no limiar, nós antigos e coeficientes externos preservados; nenhuma alteração da curva C_beta ou do arquivo físico C07. A matriz resultante do primeiro canal é repetida bit a bit nos4canais; espectros e ruídos continuam variando com a frequência física.

| Gate | Máximo observado | Limite |
|---|---:|---:|
|Oráculos harmônicos coarse/fine |1,96×10⁻¹³|10⁻⁸|
|4 comparações angulares novas |1,21×10⁻¹⁴|10⁻⁷|
|ΔlogL coarse/fine |3,72222×10⁻⁵|.001|
|ΔlogL fine/oráculo |1,29513×10⁻⁵|.001|
|Traços independentes: média |3,18×10⁻¹⁶|10⁻¹⁰|
|Traços independentes: covariância |1,07×10⁻¹⁵|10⁻¹⁰|
|SciPy logpdf normalizado |5,01×10⁻¹²|10⁻⁸|

A validação cobre215 controles históricos e72novos, com64nuisances por coorte e32observações de engenharia. Os57controles históricos dentro do patch receberam nova avaliação fine; os158externos reutilizaram os caches somente após igualdade de Γ bit a bit. Os72novos controles e suas sementes foram fixados antes da execução. As54 referências por traços e SciPy usaram corretamente nuisances históricos nos endpoints e novos no ponto interior. A auditoria posterior conferiu287caches logL,54referências finitas, fontes/insumos, ledger e a repetição dos coeficientes, sem novos logL ou ORFs.

No limite u=1, a ORF tensorial C_full tem posto5 em todos os canais. Em u=0, o primeiro canal coincide exatamente com a resposta física; os outros diferem porque C_full congela as fases do pulsar na primeira frequência. As maiores diferenças matriciais por canal são[0;7,03664×10⁻⁴;6,70163×10⁻⁴;5,45926×10⁻⁴]. Isso confirma que C_full não deve ser identificado com B nem mesmo em massa zero para estas fases finitas. A afirmação é sobre esta geometria/modelo, não sobre um limite ideal somente-termo-Terra.

Custo novo exato: **16.722.391.296produtos harmônicos,1.352.456pontos angulares,560.832logL**. Cumulativo próprio C_full: **1.883.520logL**, dentro do novo teto2M; os limites e fracassos da execução inicial continuam registrados separadamente. Os5workers sequenciais levaram aproximadamente25,8s com inicialização; pico712.392.704B (0,664GiB), abaixo do teto1,5GiB. Nenhum banco nativo ou posterior foi executado.

A primeira candidata continua **FAILED**, pois seu coarse4169 apresentouΔlogL=.0011143. A continuação original completou os215controles sem apagar essa falha. A v2 é uma nova execução e uma nova curva, com autorização, fontes, limites e ledger próprios. Os gates finitos aprovados não são prova uniforme de erro em todo o domínio e não aprovam automaticamente futuras regiões posteriores. C08 ainda exige sua análise inferencial/calibração e o mapa T/janela separado.

Nota de implementação: a fonte executada escreve os registros de referência com `allow_nan=False` antes de registrar PASS/exportar; todos os54 registros foram auditados como finitos. Um guard explícito de finitude no ponto da comparação torna erros futuros mais claros, mas não foi introduzido retroativamente na fonte executada.
