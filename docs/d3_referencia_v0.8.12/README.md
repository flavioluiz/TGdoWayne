# Referência adaptativa parcial de distância

Três ondas de Gauss–Kronrod em u usam respostas diretas nos nós, independentes
das regras GL32/64 em alfa. Duas continuações subdividem os quatro painéis de
maior erro anterior. Foram usados 1092 dos 1152 pares massa/escala reservados.
Os refinamentos angular e harmônico passaram nos pontos calculados.

As doze comparações funcionais com GL64 passam. Porém, o critério adicional
de parada da referência exige concordância entre ondas e estimador embutido
normalizado até 0,001. Apenas cinco curvas passam na última onda: as quatro
misturas B_CN/B_G e B_CN nominal do dado 14. As outras sete ficam pendentes.
Não selecionar a onda intermediária mais favorável, onde sete passaram.
O maior estimador caiu de 0,0879 para 0,0419 e 0,0200; não é cota rigorosa.

O lote consumiu 11,81 trilhões de produtos reais estimados, 172,61 s CPU nas
respostas e 4,84 s nas densidades/recuperação. Foram 10152 avaliações novas,
incluindo 162 controles SciPy refeitos porque seus valores não foram gravados.
A falha de serialização dos registros foi detectada na auditoria; não houve
nova ORF na recuperação. O total C09 passa a 5793729 avaliações.

- [Auditoria por onda e curva](../../results/C09/D3_distancias_referencia/audit.json).
- [Manifesto dos três arquivos restauráveis](../../results/C09/D3_distancias_referencia/manifest.json).

Faltam sete referências, todos os quantis/W1/eventos das distâncias e produção
D3/SBC. Os 60 nós restantes não comportam outra subdivisão pareada de 84 nós.
A continuação precisa refazer o orçamento, sem alterar tolerâncias. C09 segue
em andamento; nenhuma simulação deste lote permanece em execução.
