# Auditoria read-only do preflight C_full local v2

Foram conferidos o plano, seus hashes, a malha, os controles, os dois ledgers
históricos e os metadados/formatos dos 215 caches. Nenhuma quadratura,
likelihood, spline nova ou campanha foi executada por esta auditoria.
Os arquivos existentes foram preservados. A autorização posterior informada
pelo responsável é separada deste parecer; o preflight original permanece
prospectivo como registro histórico.

As contagens reproduzem exatamente o plano: 8336 nós antigos, 241 no patch,
353 candidatos locais, 112 inseridos e 8448 globais; 57 dos 215 controles
históricos no patch; 72 novos controles distintos dos históricos e bit a bit
iguais à lista gerada pela seed 808150101.

| Parcela | Verificado |
|---|---:|
| Produtos harmônicos locais | 739.842.816 |
| Produtos dos novos oráculos | 15.982.548.480 |
| Produtos novos totais | 16.722.391.296 |
| Trabalho angular novo | 1.352.456 |
| logL novos nos históricos | 116.736 |
| logL novos nos controles novos | 442.368 |
| logL das referências SciPy | 1.728 |
| logL novos totais | 560.832 |
| logL históricos cumulativos | 1.322.688 |
| logL cumulativos planejados | 1.883.520 |

O ledger original soma 724.992 logL; a continuação soma 597.696, incluindo
as 1.728 referências SciPy originais. Os 215 caches têm arrays logL finitos
de shape (64, 32), u correto e hashes comuns válidos de nuisances e
observações. A coorte antiga foi reproduzida bit a bit pela seed 808140201.
Todos os hashes publicados no preflight conferiram.

## Cuidados concretos para a implementação

1. Os caches têm **duas identidades de execução**: índices 0–117 pertencem
   à execução original (`d2d301cd…`); 118–214 à continuação (`e2dba0ec…`).
   O reuso deve reconhecer cada identidade por seu bloco de origem.
2. O vetor histórico de 215 controles é uma concatenação, **não uma lista
   globalmente ordenada**. Não usar `searchsorted` nele sem uma ordenação
   explícita e o mapeamento correspondente. Os anchors diretos estão em
   hist[202] (β=1/256) e hist[194] (β=1/64).
3. Nas referências SciPy, u=0 corresponde a hist[0] e u=1 a hist[142], ambos
   com os seis primeiros nuisances antigos. O novo ponto β=3/512 corresponde
   a new[58], u=0.999982833714964, com os seis primeiros nuisances novos
   (seed 808150201). Misturar essas coortes invalidaria a comparação cache/SciPy.
4. A representação coarse v2 usa `logL_fine` antigo, não `logL_coarse` antigo.
   Fora do patch, o novo fine só herda esse mesmo cache após igualdade de Γ.
   Dentro dele, inclusive u=1, deve comparar SciPy ao novo fine efetivamente
   avaliado, além do coarse/oráculo histórico apropriado.
5. Usar β efetivo recuperado de u no direto e na quadratura. Os anchors
   representam β=0.003906249999999999 e 0.015624999999998222. O novo anchor
   SciPy representa β=0.005859375000004136.

O stitch consultado trabalha em x=−β, fixa a derivada lateral externa e
derivada zero no limiar, preserva coeficientes externos e matrizes antigas,
e verifica C0/C1 no encontro. Os controles Bernstein e gates da curva nova
ainda pertencem à execução autorizada, não a esta auditoria.

`worker.py` apareceu ao final da auditoria e foi lido sem execução. Confirmei
o uso de `np.where` nos históricos, coarse v2 a partir de `logL_fine`, a
escolha correta de coortes nos três pontos SciPy e a comparação dos caches
com as matrizes de cada representação. Hash da revisão:
`2666e65ffd4e01ec8b5617fd3a00e5fe29ca2b0fa2ccf477ccc93601c71a2c46`.

Foi sugerido ao responsável recolocar o guard explícito de finitude para
`[em, ec, el]` no loop SciPy, pois NaN não aciona comparações apenas com `>`.
Contudo, a serialização por `write_json(... allow_nan=False)` dos resultados
SciPy ocorre **antes do PASS** e já rejeita NaN/Inf. Portanto, a sugestão é
defesa adicional, não uma vulnerabilidade de falso PASS. A leitura posterior
dos 54 registros executados confirmou finitude de erros e condicionamentos.
Nenhuma fonte executada foi alterada para essa recomendação.

O responsável acrescentou antes do congelamento a verificação explícita de
`z['identity']` contra `historical_cache_identities[0 if j<118 else 1]`.
Conferi essa condição na fonte congelada, além dos hashes, u, nuisances e
observações; as duas identidades históricas estão corretamente contempladas.

Não foi encontrado erro aritmético ou incompatibilidade no plano auditado.
A melhoria de finitude pode ser incorporada a uma versão futura sem alterar
a evidência executada. Este parecer não constitui PASS científico da candidata C_full v2.

Detalhes numéricos, índices e identidades completas estão em `PARECER.json`.
Os hashes da evidência consultada estão em `input_hashes.json`.
