# v0.8.5 — estado preservado e pausa solicitada

O usuário solicitou publicar a situação atual e pausar o objetivo para poupar créditos.
Não havia simulações físicas em execução na chegada desse pedido. Nenhuma campanha física
nova foi iniciada para esta versão. A preparação dos próximos executores também foi interrompida.

C01–C08 permanecem concluídos. C09 está parcial; os capítulos de C09, C10 e C11 são **drafts**.
O PDF inclui o texto desenvolvido, resultados parciais, limites de interpretação e tarefas
pendentes. A versão v0.8.5 não substitui o marco futuro v0.9.0 e não encerra C09.

## Resultados efetivamente disponíveis

- C09: piloto nominal com 14 cenários e reparos D1/D1b executados. Há 544316 avaliações
  acumuladas de log-verossimilhança na contabilidade do piloto/reparos e 484,422282 s CPU
  no respectivo ledger. Esses números não são o custo de todo o projeto.
- D1 resolveu operacionalmente nove eventos na representação tabulada. D1b recuperou
  mais quatro com 8099 avaliações novas. O caso 10 continua não resolvido.
- A aprovação tabulada de 13/14 casos não é uma aprovação do evento no modelo físico:
  seus intervalos conservadores permanecem [0,1]. Não se publicou nova calibração SBC.
- C10: controles anteriores da resposta escalar/tensorial e seus nós estão preservados.
  As interpolações lineares 129→257 e 257→513 falharam, com erros máximos aproximados
  0,23918 e 0,10553. Reutilização dos valores nodais foi revisada separadamente;
  a campanha posterior bidimensional não foi executada.
- C11: viabilidade documental, desenho simulado e testes sintéticos de componentes;
  nenhuma inferência observacional ou campanha física C11 executada.
- Acervo: 37 PDFs conferidos por SHA-256 em `literature/papers/`. Catálogo e receita de
  aquisição são versionados; cópias locais dos artigos continuam separadas do Git.

## Como ler os arquivos preservados

Os três ZIPs em [results/pausa_v0.8.5](../../results/pausa_v0.8.5) guardam o estado local
C09–C11, incluindo fontes, configurações, caches, relatórios, falhas e rascunhos.
Cada manifesto registra os membros, tamanhos e SHA-256. Todos os membros dos ZIPs foram
relidos e comparados às fontes originais. Os recibos principais de C09 também estão
nesta pasta, fora dos ZIPs, para leitura direta.

O nome de um arquivo ou uma palavra `PASS` em um teste sintético não certifica uma
campanha física. D2 runtime e C11 pilot16 são preparações interrompidas, não congeladas
para produção. O pacote C10 lifecycle está congelado como candidato, com testes
sintéticos, mas sem revisão final/execução do piloto físico. Os documentos prospectivos
contêm quotas e controles planejados; não devem ser lidos como contagens executadas.

Para consultar os arquivos, extraia o ZIP em uma pasta vazia. Seus membros preservam
os caminhos `tmp/...`; nenhum script é executado durante a extração. Referências
absolutas e dependências históricas mantêm a proveniência original. Os ZIPs não são
uma prova de reprodução integral em outra máquina: dados/fontes externos a esse
recorte podem depender dos artefatos C06–C08 já versionados ou dos arquivos locais.
Não execute drivers automaticamente ao restaurar.

## Ponto de retomada

1. Retomar somente após nova solicitação do usuário; verificar hashes e estado antes
   de lançar processos. Os rascunhos não autorizam execução por conta própria.
2. C09: revisar e congelar o executor D2 de comparações sobre os mesmos dados;
   concluir referências por priori e os controles de covariância/contaminação.
3. C09: implementar e validar D3, incluindo calibração com verdades sorteadas da
   priori, ruídos, espectros, distâncias e controles fixos. Preservar os casos
   não resolvidos. Não converter o piloto nominal em SBC nem descartar o caso 10.
4. C10: revisar o pacote final e o orçamento, executar primeiro o piloto limitado
   com resposta nodal e controles de integração; somente depois avaliar a campanha.
5. C11: decidir formalmente entre aplicação observacional com adaptador validado e
   extensão simulada; revisar custo e executar o benchmark antes da inferência.
6. C12–C13: redigir discussão, conclusões e manuscrito com base no que for efetivamente
   validado; realizar a auditoria final. Não há submissão de artigo ou defesa concluída.

O registro [estado_preservado.json](estado_preservado.json) distingue estado editorial,
contagens científicas e arquivos. O README principal aponta para o PDF desta versão.
