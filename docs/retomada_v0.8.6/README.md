# Retomada C09 — v0.8.6

O usuário autorizou retomar o trabalho. C01–C08 permanecem concluídos; C09 está
em andamento. A v0.8.5 e seus snapshots não foram alterados.

## Execução e resultado

O executor D2 foi conectado aos dados nominal14 e validado por seis testes
sintéticos. Foram planejadas 13 curvas e 40 análises, sob teto de 200000 novas
avaliações e 180 s CPU. Os controles das 13 curvas contra 16 respostas harmônicas
e três densidades SciPy por curva passaram em seu domínio finito.

Nove curvas atingiram suas cotas durante referências; o lote foi interrompido
na décima pelo limite de CPU. O encerramento consumiu recursos adicionais:
181,096710 s CPU no total, excedendo o teto em 1,096710 s. O supervisor registra
`FAILED_NO_AUTOMATIC_RETRY`. Seu recibo mantém uma reserva superior de 200000
avaliações, pois rejeitou o recibo final do worker por recursos.

A auditoria posterior reconstruiu **175778 avaliações contabilizadas**, incluindo
uma reserva interrompida sem valor reutilizável. Conferiu os valores históricos
bit a bit e os 1070 arquivos originais. Isso não converte a execução em aceita.
O histórico científico contabilizado é 720094 avaliações e 665,518992 s CPU;
não corresponde ao custo de todo o projeto ou aos testes/edição posteriores.

Todos os 13 caches e 248 painéis de referência concluídos foram preservados.
Esses painéis não cobrem as normalizações completas. As 40 estimativas recuperadas
dos caches são **drafts da representação tabulada**, sem referência funcional
concluída. Não há novo SBC, inferência observacional ou limite físico validado.

## Arquivos e reprodução da auditoria

- [Auditoria](../../results/C09/D2_retoma/audit.json),
  [recibo original](../../results/C09/D2_retoma/execution_end.json) e
  [estimativas draft](../../results/C09/D2_retoma/posteriores_draft.json).
- [Arquivo de execução e fontes](../../results/C09/D2_retoma/execucao_e_fontes.zip)
  com manifesto de todos os membros e SHA-256.
- `scripts/arquivar_d2.py` confere hashes, identidades e contabilidade.
- `scripts/resumir_d2_draft.py` calcula resumos tabulados sem novas likelihoods.

Os scripts pressupõem os caminhos locais preservados nos arquivos de C09 e os
dados/tabelas C06–C08. Extração não executa scripts; os ZIPs não constituem uma
prova de portabilidade integral dos executores físicos.

## Próxima execução

1. Reservar explicitamente CPU para encerramento e persistência; o teto do
   worker sozinho não garante o teto somado ao controlador.
2. Usar os caches e os painéis já concluídos. Dimensionar o custo das referências
   restantes por curva antes de fixar nova cota; preservar o histórico desta falha.
3. Concluir controles por função, incluindo W1, sem converter precisão pontual
   da resposta em margem uniforme de probabilidade.
4. Implementar D3: ruído, espectros, contaminantes, distâncias, variabilidade,
   SBC representativo e controles condicionais. C10–C13 continuam pendentes.
