# C_full: gate de interpolação interrompido

A execução autorizada preservou o limite |ΔlogL|≤.001 e parou após118 dos215 controles. A malha coarse herdada de4169 nós apresentou **ΔlogL coarse/fine=0,001114327888** em u=0,9999945411654163 (β=0,003304185129). Nesse ponto, a diferença fine/oráculo foi4,783145869×10⁻⁶; o maior fine/oráculo nos118 pontos examinados foi1,325434300×10⁻⁵.

O caso extremo é nuisance4/observação física9, nos índices zero-based. Os logL coarse/fine/oráculo são −3696,736235970 / −3696,735121642 / −3696,735116859. A diferença matricial é7,32249×10⁻⁷ entre coarse/fine e4,32743×10⁻⁹ entre fine/oráculo. São avaliações em um ponto da priori usando uma observação de engenharia; não são precisão posterior ou resultado populacional.

A evidência indica insuficiência do controle coarse nesse caso. A falha do critério exigido permanece; não se declara aprovação da tabela fine com base apenas no subconjunto já calculado. Também não se atribui erro físico à diferença de interpolação. Os54 casos de traços/SciPy ainda não foram executados, portanto a observação prévia sobre roundoff do SciPy não explica esta parada.

Custo: **724.992 logL**, zero quadraturas harmônicas/angulares,3,092s no worker de gates (5,525s com inicialização/controle), pico489.717.760B. O teto próprio C_full1,4M está preservado. O processo de exportação não iniciou e não existe tabela C_full aprovada neste pacote. Fonte, autorização, ledger,118 caches e falha estão intactos; qualquer continuação requer novo registro prospectivo, sem reescrever esta falha. C_beta continua sendo outro artefato/modelo, cuja validação não é afetada por esta falha C_full.
