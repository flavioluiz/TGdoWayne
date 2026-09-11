# C_beta v2: refinamento geométrico local, ainda não iniciado

A tentativa v1 permanece reprovada: entre143 massas originais, houve uma
falha coarse/fine de0,00187059. O fine/oráculo passou em todas, máximo
0,000161165. O refinamento proposto conserva integralmente essa evidência.

O **fine v1 torna-se o coarse v2 inteiro**. O novo fine adiciona subcélulas
uniformes com passo1/65536 (oito por célula uniforme original) em
0≤β≤1/64, preservando todos os nós finos antigos, inclusive a camada que já
é mais densa perto de0. O limite1/64 é uma fronteira geométrica existente na
malha. Ele cobre toda a regiãoβ≤.01 e uma margem; não seleciona apenas o
ponto da falha. Fora da região, preservar os coeficientes antigos exatamente.

Na região, usar quadraturas harmônicas coarse/fine próprias, dimensionadas
pelo máximoβy nela, com margens100/220 e refinamento+40/+80. Isso reduz o
custo mantendo a mesma integral normalizada. Confrontar também os nós antigos
recalculados com suas matrizes já validadas em alta ordem. Para a nova spline,
os valores dos nós antigos continuam sendo os da fonte v1; as quadraturas
locais são controles adicionais desses valores. Os novos nós usam a quadratura
local fina. No encontro com a parte preservada, fixar o valor e a primeira
derivada da curva antiga; emβ=0, fixar a derivada zero. A união é C1 e por
partes cúbica. Verificar continuidade, todos os controles Bernstein e ausência
de clipping; não supor que essa nova representação seja C2 no encontro.

Manter o canal1 exato da ROOT. Somente canais2–4 ganham novos nós. As curvas
resultantes têm9153/9185/9185 nós, abaixo do teto10000 por frequência. A união
com a primeira curva preservada tem9248 nós. Coeficientes comuns340,88MB e
matrizes85,23MB; não construir banco nativo ou posterior neste processo.

Os143 controles históricos permanecem. Nas36 massas dentro da região,
avaliar apenas o novo fine, reutilizando os logL antigos fine/oráculo com
hashes e identidade conferidos. Fora da região, reuso só após igualdade
bit a bit das matrizes e dos polinômios pertinentes. Adicionar64 massas
independentes (24 uniformes emu,24 emβ,16 emlogβ) e8 âncoras geométricas,
seed808130101; as72 são distintas e não coincidem com as143 históricas.
Para elas, usar64 nuisances novas, seed808130201, e as32 observações antigas
de engenharia. Avaliar antigo fine/novo fine/oráculo. Nenhuma verdade entra
na seleção. Doze novos pares diretos nas fases reais verificamβ=1/256 e1/64,
com duas ordens em cada caso.

| Recurso | Novo previsto | Cumulativo previsto | Teto proposto |
|---|---:|---:|---:|
| Produtos reais harmônicos |440.505.844.992 |48.948.941.796.288 |50.000.000.000.000 |
| logL |516.096 |1.394.688 |600.000 novos;1.600.000 cumulativos |
| Trabalho angular direto |5.844.792 |2.057.601.896 |8.000.000.000 cumulativos |

Os516.096 logL incluem73.728 novos nos controles históricos e442.368 nos72
controles novos. O teto original1M não é reescrito: ele continua associado à
v1. A v2 requer autorização explícita da parcela adicional e registra ledger
novo, com baseline e hash do ledger original. A parcela não usada da reserva
não autoriza refinamentos automáticos.

Um worker, VECLIB=1, tetoRSS1,5GiB e estimativa de arrays1GiB permanecem.
A maior base ainda é a do oráculo fora da região, cerca594MB de arrays/buffers;
a medição v1 chegou1,36GB RSS. Liberar curvas/bases entre estágios e registrar
RSS em bytes Darwin. O custo deve ser de alguns minutos, dominado pelos
72 oráculos novos e oito preparações de base; medir, sem prometer prazo.

Todos os limiares anteriores são mantidos, inclusive |ΔlogL|≤.001 para
coarse/fine e fine/oráculo. Uma nova falha interrompe a execução e preserva
os resultados. Não haverá inferência C, mapa T/Hann ou edição de fonte C07.

O primeiro rascunho `preflight.py` falhou apenas ao converter uma lista para
β; seu código/log foram preservados. O preflight válido é
`preflight_corrected.py` → `preflight.json`, sem quadratura ou logL.
