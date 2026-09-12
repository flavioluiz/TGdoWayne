# D2: referências funcionais e contrastes pareados

As 40 análises de 13 funções passaram nos controles operacionais de normalização,
CDF, quantis, momentos e KL. Foram usados os mesmos dados, parâmetros auxiliares
conhecidos e resposta do piloto nominal14. Não foram gerados novos dados ou ORFs.
Essa validação condicional com controles físicos pontuais não constitui um
certificado uniforme de probabilidade física ou uma campanha SBC.

## Resultados e alcance

Os desvios máximos foram 1,310671e-5 em logZ, 8,820314e-6 em CDF e 8,634999e-6
em KL; os intervalos operacionais dos quantis têm largura de até 0,00098.
A síntese contém 37 contrastes de Q95: oito de covariância, um de contaminante,
um de compressão e 27 de priori/suporte. Os intervalos propagam incerteza
numérica; não são intervalos de confiança de um efeito entre realizações.

No dado 6, fixar a covariância reduz Q95 nas estruturas completa e diagonal.
No dado 7, alguns contrastes de diagonalização permanecem sem sinal resolvido.
No dado 13, incluir o monopolo aumenta Q95; no dado 7, a compressão B_G reduz Q95
em relação a A_G. Não se infere uma direção universal desses efeitos.

## Execuções preservadas

| Tentativa | Valores adicionais | CPU (s) | Resultado |
|---|---:|---:|---|
| Continuação1 | 1411 | 3,293173 | Erro de serialização após primeira referência; caches e painel salvos |
| Continuação2 | 35293 | 207,186015 | 38 análises aprovadas; duas referências no limite por curva |
| Continuação3 | 4171 | 12,800408 | 40 análises aprovadas nos cinco controles primários |

Total adicional desde v0.8.6: **40875 avaliações e 223,279596 s CPU**, dentro da
reserva original das continuações (100000 valores e 480 s). O saldo global foi
realocado explicitamente para as duas caudas restantes; nenhum custo foi apagado.
O histórico do diagnóstico C09 passa a 760969 avaliações e 888,798588 s CPU.
Esses números não representam o custo total do projeto ou dos testes/editoria.

A correção converte flags NumPy para booleanos Python antes da gravação JSON.
A regressão real recuperou a referência já concluída sem novas likelihoods.
A retomada preserva cortes, escala, medidas, contribuições e erros; a última
execução reutilizou 504 painéis completos. Todos os valores importados foram
conferidos bit a bit. O recibo de falha original continua preservado.

## Arquivos

- [Auditoria](../../results/C09/D2_continuacao/audit.json).
- [37 contrastes](../../results/C09/D2_continuacao/contrastes_pareados.json).
- [Fontes, execuções e referências](../../results/C09/D2_continuacao/fontes_execucoes_e_referencias.zip),
  com 609 membros relidos e conferidos por SHA-256.
- Recibos de cada execução e manifesto em `results/C09/D2_continuacao/`.
- `scripts/arquivar_d2_continuacao.py` e `scripts/tabelas_d2.py` preservam e
  apresentam os resultados sem executar novas likelihoods.

O arquivo depende dos snapshots v0.8.5/v0.8.6 e dos dados/fontes C06–C08 vinculados.
Seus caminhos locais preservam a proveniência; não se afirma reprodução integral
em outra máquina sem restaurar essas dependências.

## Pendências para C09

W1 e eventos de log-likelihood mantêm seus estados próprios, sem herdar aprovação
dos quantis. D3 ainda requer a campanha representativa de prioris/ruídos,
espectros, contaminantes, distâncias, variabilidade e calibração SBC. Os 14 casos
nominais e os contrastes D2 não substituem essa campanha. C09 permanece aberto.
