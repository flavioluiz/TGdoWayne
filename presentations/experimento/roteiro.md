# Roteiro da apresentação do experimento

12 slides principais e 3 de apoio. Duração sugerida: **25:00**, incluindo a abertura da discussão. Público: pós-graduação, sem pressupor conhecimento de ondas gravitacionais.

O roteiro orienta a fala, sem leitura literal dos slides. Os tempos são sugestões, sem ensaio cronometrado. As notas Beamer ficam em `notas.tex`, ocultas no PDF da audiência.

## Ritmo e adaptações

- **20 minutos:** usar os 12 slides, reduzindo as pausas de discussão. Reservar cerca de um minuto para o encerramento e resumir em um minuto cada os slides 8, 9 e 10.
- **25 minutos:** seguir os tempos abaixo, com espaço para a pergunta inicial e a abertura do debate no slide 12.
- **30 minutos:** acrescentar cinco minutos à discussão final.
- **Apoio:** slides 13–15, sobre métricas, custos e acesso às fontes, fora do tempo principal.

## Sequência e fala sugerida

### 1. Uma dissertação pronta. Um pesquisador formado?

00:00–00:45 (45 s)

Apresentar o experimento como uma investigação sobre a delegação da pesquisa e as evidências de formação. O tema científico serviu de terreno de teste. Não houve concessão de título, defesa ou aprovação institucional. A apresentação organiza uma discussão para a pós-graduação, sem pretender representar uma posição institucional.

**Fontes:** Relatório do estudo de caso, abertura.

### 2. O documento e a formação

00:45–02:45 (120 s)

A tese central é que o produto escrito, sozinho, não basta para demonstrar o domínio individual quando sua produção pode ser amplamente delegada. O documento continua sendo evidência sobre o trabalho científico. O caso não mediu aprendizagem, não avaliou uma turma e não prova que um pesquisador foi formado. Transparência sobre ferramentas importa, mas não substitui avaliar compreensão. Transição: o que exatamente foi delegado neste caso?

**Fontes:** Relatório, seção 3.

### 3. O desafio inicial

02:45–04:25 (100 s)

O proponente declarou não dominar o tema e não forneceu uma hipótese científica nova, equações ou código. Entregou um TG de 2003 e pediu uma continuação com potencial de publicação, implementação e validação. O texto do slide resume os pedidos, sem transcrevê-los. Houve direção humana, acompanhamento operacional e encaminhamento de pareceres. A busca de novidade começou por examinar a literatura: resultados do TG já tinham publicação posterior. Um antecedente recente motivou uma pergunta sobre a confiabilidade de simplificações. Originalidade era candidata, não certificada.

**Fontes:** Relatório, seção 1 e apêndices A e B; TG original.

### 4. O percurso da pesquisa delegada

04:25–06:15 (110 s)

O diagrama resume a ordem predominante, com iterações entre as etapas. O usuário definiu a intenção. O Codex Astra formulou o recorte, organizou um plano de 13 marcos e coordenou três subagentes. Consultou antecedentes para evitar anunciar como novidade o que já existia. Executou quatro campanhas principais com 45.528 análises, que compartilham dados e não correspondem a igual número de simulações independentes. Os testes levaram a correções. Os dois pareceres do Gemini chegaram por intermédio do usuário. O artigo teve uma revisão após o encerramento do goal. O tempo humano não foi cronometrado. As três caixas escuras destacam as etapas conduzidas pelos agentes. Isso não significa ausência completa de participação humana nem permite atribuir uma porcentagem de autonomia.

**Fontes:** Relatório, seções 1 e 2 e apêndices A a D.

### 5. O que o agente entregou

06:15–08:05 (110 s)

Os números em destaque são 26.069 linhas de código e testes e 45.528 análises principais, na v1.0.0. A contagem inclui comentários e linhas vazias. As análises compartilham dados e não são 45 mil experimentos independentes. Volume não mede produtividade relativa a um pesquisador humano. A dissertação tem 167 páginas e 47 referências. O artigo revisado tem nove páginas e é posterior ao goal. O goal registrou 30h51min26s, arredondados para 31 horas, e 54h56min42s no calendário. Não é tempo de CPU. US$ 50 é o rateio de assinatura estimado pelo proponente, não uma fatura específica do experimento. O equivalente em API Standard é cerca de US$ 1.300, com complementos científicos. Hipóteses e exclusões no apoio. As capas dos produtos estão no último slide de apoio.

**Fontes:** PDFs da dissertação e do manuscrito; relatório, apêndices C a E.

### 6. Os testes mudaram as conclusões

08:05–10:25 (140 s)

Em simulações, conhece-se a resposta usada para gerar os dados. O agente identificou que uma faixa de incerteza para um parâmetro continha essa resposta menos vezes do que prometia. Isso limita a aproximação naquele teste, sem invalidar todo o método. A comparação ampla não atingiu a precisão exigida. Depois de crítica externa por modelo, um complemento respondeu a uma questão menor, com condições fixadas. O agente explicitou esses limites e reescreveu afirmações. Não equiparar esse comportamento, sem avaliação independente, ao rigor geral de um pesquisador experiente. A escolha de dados simulados era permitida pelo plano: faltava um adaptador local validado para usar as séries reais, não dados públicos no mundo. A frase sobre o teste falhar resume uma cobertura de incerteza abaixo do valor anunciado. Não significa ausência total de acertos nem ausência de erros não detectados.

**Fontes:** Relatório, seção 2 e apêndice B.1.

### 7. O Gemini criticou. O Codex conferiu.

10:25–12:45 (140 s)

O Gemini elaborou dois pareceres, encaminhados pelo usuário. No primeiro ciclo, o Codex verificou críticas e acrescentou estudos pontuais, incluindo 300 análises em 50 casos. No segundo, revisou o manuscrito com os resultados já existentes. Aceitou melhorias de exposição e contexto, mas recusou alegações de originalidade absoluta e de falha inevitável em dados reais. As frases do slide são sínteses desses movimentos, não citações. Não houve revisão cega, certificação científica nem avaliação formal por pares humanos. Perguntar que trabalho de verificação permanece para orientador e revisores humanos.

**Fontes:** Relatório, seção 2 e apêndice A.2; notas de revisão do artigo.

### 8. Qual contribuição merece atenção?

12:45–15:05 (140 s)

A automação pode aumentar a oferta de manuscritos e o esforço necessário para selecionar, compreender e verificar resultados. Essa é uma hipótese de organização da ciência, não uma consequência medida neste caso. Evitar anunciar colapso dos periódicos ou dizer que toda pesquisa incremental perde valor. Uma extensão pequena pode resolver uma incerteza relevante. No experimento, documentar a falha de uma aproximação e uma pergunta ainda inconclusiva são resultados que merecem exame. A publicação não certificaria, sozinha, a formação individual. Abrir uma breve discussão sobre qual diferença entre antes e depois de um estudo justifica atenção dos pares. A pergunta sobre variar parâmetros provoca uma discussão de relevância: uma variação pode revelar um regime novo ou resolver uma dúvida importante. O critério é a informação acrescentada, sem decretar o fim da pesquisa incremental.

**Fontes:** Relatório, seção 4.

### 9. Simular e medir exigem evidências distintas

15:05–17:05 (120 s)

Este caso foi computacional e não comparou sua produtividade à de um laboratório. Em simulações, controles com resposta conhecida permitem testar hipóteses. Medições acrescentam confronto com fenômenos e exigem instrumentação e calibração. O laboratório tem restrições materiais, mas também usa automação. Teoria e computação não perdem valor científico por serem automatizáveis. A discussão é como gerar evidência nova e interpretar seus limites, não proclamar superioridade de um tipo de pesquisa. A evidência do caso não demonstra desempenho em dados instrumentais reais. O destaque ao trabalho físico não pressupõe que toda operação de laboratório deva ser humana. Calibração e instrumentação também admitem automação.

**Fontes:** Relatório, seção 4.

### 10. O que precisamos aprender a fazer?

17:05–19:25 (140 s)

A escrita, programação e leitura continuam sendo atividades formativas. Automatizar sua execução não torna essas competências dispensáveis. A oportunidade é explorar mais perguntas e investigar variações antes caras. O risco é perder a experiência necessária para reconhecer um erro. Orientação e disciplinas podem separar momentos de aprendizagem individual e produção com assistência ampla. O estudante precisa formular perguntas relevantes, interpretar anomalias e saber quando uma linha deixou de ser promissora. O caso não permite afirmar que a delegação ensina essas capacidades. Propor uma atividade concreta: apresentar uma saída convincente do agente, pedir sinais de falha e solicitar que o estudante diga sob qual evidência a aceitaria ou rejeitaria.

**Fontes:** Relatório, seções 3 e 4.

### 11. A avaliação pode acompanhar as decisões

19:25–22:05 (160 s)

Proposta pedagógica, não intervenção avaliada neste caso. Antes de executar uma mudança, pedir uma previsão justificada. Depois, pedir que a pessoa explique o resultado, especialmente quando diverge da previsão. Na defesa, modificar uma hipótese ou condição, solicitar um argumento central e seus limites, com trechos sem assistência quando apropriado. Um teste ao vivo exige critérios justos e não deve reduzir domínio a rapidez de digitação ou memória. Registros ao longo do curso, qualificações e conversa oral podem complementar o documento final. Discutir como graduar profundidade e autonomia entre mestrado e doutorado.

**Fontes:** Relatório, seções 3 e 5.

### 12. Três questões para a pós-graduação

22:05–25:00 (175 s)

Reservar quase três minutos para abrir a discussão. A primeira questão trata da contribuição e dos patamares de originalidade e autonomia de mestrado e doutorado. A segunda trata de disciplinas, qualificações e defesas capazes de tornar compreensão observável. A terceira pergunta como ensinar a usar agentes sem impedir a construção de competências necessárias para julgá-los. O caso oferece artefatos e decisões auditáveis. Não estabelece uma política institucional nem demonstra aprendizagem. O relatório e os demais produtos estão no repositório, com fontes acessíveis no apoio.

**Fontes:** Relatório, seção 5.

### 13. Definições das métricas

Apoio opcional.

Números históricos da v1.0.0. O manuscrito de nove páginas é posterior. O total de código arquivado não é deduplicado. O tempo do goal não é CPU. As análises compartilham dados.

**Fontes:** Relatório, apêndices C e D.

### 14. Hipóteses da estimativa de custo

Apoio opcional.

Aplicação dos preços oficiais Astra Standard de 13/09/2026 aos registros únicos por resposta. Até o goal são 6.510 respostas, com agente principal e três subagentes, totalizando US$ 1.289,34. Os complementos científicos acrescentam US$ 14,29. 97,56% da entrada veio de cache. Gravações de cache zero no registro; cobrar toda entrada nova como gravação acrescentaria cerca de US$ 53, mantida a reutilização. Fast dobra o preço. Não incluir o contador do goal nem somar raciocínio duas vezes. Exclui Gemini, computação local, ferramentas adicionais e estudo de caso. US$ 50 é estimativa do usuário sobre rateio, não tarifa de API.

**Fontes:** Relatório, apêndice E; estimativa_custo_api.json; developers.openai.com/api/docs/models/gpt-6-astra.

### 15. Documentos para examinar o caso

Apoio opcional.

O repositório reúne PDFs e fontes, evidências e notas de revisão. O corpo do relatório discute decisões e formação; os apêndices guardam interações, métricas e método. Conversas privadas não foram transcritas. As imagens reproduzem as capas originais da dissertação e do manuscrito, com suas atribuições preservadas.

**Fontes:** https://github.com/flavioluiz/TGdoWayne
