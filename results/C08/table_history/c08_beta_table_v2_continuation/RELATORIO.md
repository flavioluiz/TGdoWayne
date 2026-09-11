# Tabela C_beta: validação v2 concluída no domínio declarado

A candidata **C_beta**, para os12 pulsares e4 frequências do experimento C07, passou nos gates prospectivos de tabela. O arquivo `results/C_beta_common_table.npz` contém **9248 nós**, quatro canais e coeficientes cúbicos explícitos em **x=−β**. SHA256: `4944d15738864697afe19c159a6da7b732ac712d6308806427a9a3106d2c84d7`.

C_beta usa β(f_ref) em todos os canais, mantendo as fases físicas y_k=2πf_kL/c de cada canal. Os coeficientes têm de ser carregados explicitamente. Refazer spline pelas matrizes na união não preserva necessariamente a função validada. A primeira curva física do ROOT, arquivo `results/C07/orf_interpolation/orf_table_pilot12x4.npz`, foi identificada por hash na autorização e na herança v1; seus nós/matrizes/coeficientes originais permanecem bit a bit na curva individual do canal1. A exportação comum utiliza somente subdivisão polinomial, com diferenças de avaliação da ordem do arredondamento.

| Gate | Resultado máximo | Critério |
|---|---:|---:|
| Quadraturas locais coarse/fine |1,41×10⁻¹³|10⁻⁸|
| Reprodução dos nós antigos pela quadratura local |2,97×10⁻¹³|10⁻⁸|
| Oráculos independentes, quadraturas harmônicas completas |7,53×10⁻¹³|10⁻⁸|
|12 comparações angulares novas: resolução/método |2,45×10⁻¹⁴|10⁻⁷|
|ΔlogL coarse/fine |1,87888×10⁻⁴|10⁻³|
|ΔlogL fine/oráculo |8,84463×10⁻⁵|10⁻³|
|Subdivisão: diferença de avaliação |1,12×10⁻¹⁶|10⁻¹¹|

Todas as matrizes de controle Bernstein passaram PSD/Hermiticidade com a tolerância de arredondamento declarada; não houve clipping de autovalores ou fallback. A junção local preserva C0 até5,56×10⁻¹⁷ e C1 até a representação exata neste cálculo; a derivada na extremidade β=0 fica abaixo de9,50×10⁻¹⁶.

O **fine v1 inteiro tornou-se coarse v2**. A v2 refinou geometricamente todos os intervalos uniformes β≤1/64, por fator8, preservando nós antigos e todos os coeficientes externos bit a bit. Nenhuma escolha foi feita a partir de PIT ou verdade. Os143 controles históricos permanecem, com seus64 nuisances e32 observações; apenas36 pontos dentro da região alterada exigiram recalcular o novo fine. Os107 pontos externos reutilizaram logL somente após verificar Γ bit a bit. Além disso,72 controles novos e64 nuisances novos, fixados antes da execução, foram avaliados contra32 observações em coarse/fine/oráculo. Isso totalizou **516.096 novos logL**. A auditoria posterior reproduziu os máximos lendo os215 caches e conferiu213 hashes de fontes/insumos, sem nova avaliação de logL/ORF.

O maior erro coarse/fine ocorreu no controle novo u=0,9999997179467736. O maior fine/oráculo ocorreu em u=0,9997984137756888, fora da região local refinada, com coarse=fine nesse ponto. Isso documenta a limitação restante da malha externa; não se confunde coarse=fine externo com erro nulo em relação ao oráculo.

## Histórico de falhas preservado

A v1 original falhou cientificamente: ΔlogL coarse/fine=0,001870588>0,001. Sua continuação diagnóstica terminou os143 controles, preservando essa falha. O primeiro processo da v2 passou nas curvas locais e nos oráculos1–3, mas parou no guard de memória ao preparar a base coarse do canal4: pico **2.109.554.688B**, acima de1,5GiB, em47,247s. Esse processo permanece **falho**, com fonte, autorização, ledger e relatório intactos em `../c08_beta_table_v2/`; não é reclassificado como sucesso.

Após novo preflight e autorização, esta continuação executou coarse k4 e fine k4 em dois processos novos e sequenciais, seguidos por um terceiro processo de gates/exportação sem base harmônica. Não repetiu quadraturas concluídas. Os trabalhadores k4 tiveram picos de673.824.768B e680.198.144B; gates/exportação atingiram **1.377.828.864B=1,283GiB**, dentro do teto1,5GiB. Tempo da continuação: **50,475s**. O custo anterior de preparação/tempo/memória permanece registrado; o fato de a falha ocorrer antes de avaliar β não significa trabalho computacional nulo.

| Recurso | v1 | v2 interrompida | Continuação | Cumulativo final | Teto |
|---|---:|---:|---:|---:|---:|
|Produtos harmônicos reais |48.508.435.951.296|215.183.215.872|225.322.629.120|48.948.941.796.288|50.000.000.000.000|
|Pontos angulares diretos |2.051.757.104|0|5.844.792|2.057.601.896|8.000.000.000|
|logL |878.592|0|516.096|1.394.688|1.600.000|

Os produtos contabilizam a contração harmônica conforme o contrato histórico. A preparação das bases tem custo separado de tempo/RSS, não se adiciona ficticiamente à contagem de multiplicações da contração. Nenhum teto foi ampliado na continuação. A estimativa numérica não representa garantia de RSS; bytes acima são medições Darwin por processo. A auditoria leve adicional levou4,711s e943.407.104B, sem logL/ORF.

## Escopo da aprovação e integração

O status é **PASS nos testes finitos de tabela declarados**. Não é um limite uniforme matemático para todo o espaço de parâmetros, nem validação das futuras regiões posteriores C_beta. A precisão MC e os controles específicos de posterior ainda são gates separados. Não foram produzidas posteriores C, bancos nativos de likelihood, mapas T/janela ou alterações C07.

Para revisão, usar `results/final_report.json`, `results/controller_report.json`, `audit_completed.json`, as três autorizações/ledgers encadeadas e a tabela com coeficientes explícitos. As curvas individuais estão em `../c08_beta_table_v2/results/curve_channel*.npz`. O carregador em `../c08_runtime_design/src/frozen_coefficient_orf_v2.py` valida em tiles e não faz respline; seu próprio relatório separa arrays caller/loader/backend. C_full terá identidade, preflight e gates próprios; a aprovação desta tabela C_beta não se transfere automaticamente.
