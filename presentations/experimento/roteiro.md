# Roteiro da apresentação do experimento

21 slides principais e dois de apoio. Duração sugerida: **26:35**, incluindo a abertura da discussão. Público: pós-graduação, sem pressupor conhecimento de ondas gravitacionais.

O roteiro é um guia de fala, não um texto para leitura literal. Os tempos são estimativas de apresentação, não medições de ensaio. As notas também estão incorporadas ao PowerPoint.

## Ajustes de duração

- **Cerca de 20 minutos:** omitir os slides 6, 7, 13, 19 e 20 (total restante: 20:15), resumindo essas informações nas transições.
- **Cerca de 27 minutos:** apresentar os 21 slides principais na sequência.
- **Cerca de 30 minutos:** acrescentar aproximadamente três minutos de discussão no slide 21. Usar os slides 22 e 23 apenas para responder a questões.

## Sequência e fala sugerida

### 1. Pesquisa acadêmica com agentes de IA

00:00–00:35 (35 s)

Apresentar o experimento como estudo de caso. O tema de ondas gravitacionais forneceu a tarefa científica, mas a pergunta desta apresentação é sobre automação, formação e avaliação. Não pressupor conhecimento de física.

**Fontes:** Relatório do estudo de caso, introdução.

### 2. A pergunta do experimento

00:35–01:40 (65 s)

Distinguir qualidade do produto, aprendizagem e responsabilidade. A proposta era observar até onde o agente iria com orientação científica inicial mínima. O objetivo não é detectar uso de IA em textos.

**Fontes:** Relatório, seções 8 a 10.

### 3. O ponto de partida

01:40–03:00 (80 s)

O proponente forneceu um trabalho de graduação e pediu extensões implementáveis com potencial de artigo. Declarou não dominar a área. O agente precisou procurar antecedentes e formular o recorte. A imagem é a página real do TG e não uma representação gerada.

**Fontes:** TG_Wayne.pdf, página 1. Relatório, seções 1 e 3.

### 4. Quem tomou quais decisões

03:00–04:10 (70 s)

A participação humana foi de direção, recursos, formato e mediação dos pareceres. O Codex coordenou três subagentes e executou o trabalho científico. O Gemini elaborou dois pareceres, conforme esclarecido pelo usuário. Não se conhece sua versão.

**Fontes:** Conversa de execução. Relatório, seções 2, 2.1 e 4.

### 5. Cronologia do experimento

04:10–05:35 (85 s)

Todos os horários são de Brasília. A primeira fase incluiu pausas e mudanças de estado. A revisão do artigo ocorreu depois do goal original e não está incluída em seu contador.

**Fontes:** Relatório, seções 1, 2, 2.1 e 7.

### 6. Como o agente procurou novidade

05:35–07:00 (85 s)

Os resultados centrais do TG já tinham publicação derivada. O agente considerou caminhos alternativos e encontrou antecedentes próximos. A decisão foi reduzir a reivindicação de novidade a uma comparação controlada, e não inventar as técnicas empregadas. Não houve revisão sistemática exaustiva.

**Fontes:** output/pesquisa/proposta_mestrado.md e docs/literatura/decisao_recorte.md.

### 7. Execução orientada por etapas

07:00–08:10 (70 s)

O plano tinha 13 marcos. Não se esperou o cronograma convencional de 24 meses. Cada marco previa entregas verificáveis e PDF. Houve versões intermediárias, dificuldades de recursos e mudanças de método. A etapa concluída não garante que sua pergunta tenha resposta definitiva.

**Fontes:** implementation_plan/roadmap.json. Relatório, seção 4.

### 8. Os produtos do estudo

08:10–09:20 (70 s)

As imagens mostram páginas reais dos documentos. A dissertação final tem 167 páginas. O manuscrito tinha sete na v1.0.0 e passou a nove. Também existem duas apresentações científicas. O produto atual continua sem defesa institucional ou submissão editorial.

**Fontes:** output/pdf/v1.0.0/dissertacao.pdf, página 1. article/manuscript.pdf, página 1.

### 9. Escala do trabalho executado

09:20–10:35 (75 s)

O gráfico mede linhas físicas na tag v1.0.0, incluindo comentários e linhas vazias. As 45.528 análises somam C07, C09, C10 e C11 e compartilham dados, portanto não são observações independentes. Não somar reproduções como novos experimentos.

**Fontes:** evidencias.json, code_groups. Relatório, seção 6.

### 10. Tempo de execução e tempo de formação

10:35–11:50 (75 s)

O goal retornou 111086 segundos. O calendário entre criação e encerramento foi 197802 segundos, com pausas. A revisão adicional do artigo levou cerca de 6min37s no Codex, sem incluir o Gemini. Não é uma comparação de produtividade com um estudante.

**Fontes:** Eventos do goal e complementos_pos_goal.json. Relatório, seção 7.

### 11. Custos: uma ordem de grandeza

11:50–13:05 (75 s)

O usuário estima ter gasto uma semana de sua cota, à qual atribui cerca de US$ 50. É um rateio da assinatura, sem equivalência contratual com créditos. A conta da API Standard aplica preços de 13/09/2026 aos registros individuais do agente principal e três subagentes: US$ 1.289,34 até o goal e US$ 14,29 de complementos científicos, total de US$ 1.303,63. Entrada sem cache: 20.583.691 tokens; em cache: 822.046.336; saída: 5.229.122. 97,56% da entrada foi cache. Não somar o contador do goal. Fast dobra o preço. Gravações de cache não aparecem nos registros; considerar toda entrada nova como gravação acrescentaria cerca de US$ 53, mantida a reutilização. Exclui Gemini, ferramentas, computação local e elaboração do estudo de caso. Uma nova execução pode custar diferente.

**Fontes:** Relatório, seção 7.1; estimativa_custo_api.json. Preços em developers.openai.com/api/docs/models/gpt-6-astra, consultados em 13/09/2026.

### 12. Um controle expôs confiança excessiva

13:05–14:30 (85 s)

Explicar cobertura como a frequência com que uma faixa estimada contém o valor usado para gerar os dados. Em um parâmetro de ruído, uma análise nominal de 90% atingiu 313 de 500 casos, 62,6%. Não generalizar esse número para todos os parâmetros ou todos os métodos. A incerteza numérica levava a contagens de 299 a 325, ainda longe de 450.

**Fontes:** docs/revisao_cientifica_1.md e results/C13/review_efac_coverage.json.

### 13. Correções e perguntas ainda abertas

14:30–15:50 (80 s)

Separar erro editorial, problema de execução e limitação científica. A descrição das aproximações em uma versão estava incorreta, mas o cálculo usava a semântica correta. A comparação ampla continuou inconclusiva. Um estudo com 50 casos e parâmetros fixados respondeu a uma pergunta menor com precisão.

**Fontes:** docs/c12_errata_v0110.md, docs/revisao_cientifica_1.md.

### 14. Dois ciclos de revisão com Gemini

15:50–17:05 (75 s)

O primeiro parecer motivou novos estudos, como as 300 análises condicionais e o teste de ajuste temporal. O segundo foi uma revisão do manuscrito e não iniciou novas simulações. Não se dispõe da conversa original do Gemini ou de sua versão.

**Fontes:** Relatório, seções 2 e 2.1. article/REVISION_NOTES.md.

### 15. O Codex filtrou o segundo parecer

17:05–18:25 (80 s)

Mostrar o valor e o risco do feedback automatizado. O agente aceitou melhorias de exposição, mas as notas de revisão recusam novidade absoluta, certeza de falha em dados reais e amplificações extremas não demonstradas. O ponto é o contraste entre persuasão retórica e suporte científico.

**Fontes:** article/REVISION_NOTES.md, commit 26ae3ac.

### 16. O que o caso demonstra

18:25–19:45 (80 s)

Evitar extrapolar o estudo de caso. Os produtos existem e há rastros de execução. Não houve avaliação científica independente completa, teste de aprendizagem ou aceitação editorial. Uma revisão entre modelos é observável, mas seu ganho de qualidade não foi medido por avaliadores externos.

**Fontes:** Relatório, seções 8 a 10.

### 17. A divisão do trabalho pode mudar

19:45–21:05 (80 s)

Oportunidades: explorar ideias que não chegariam à implementação e testar mais alternativas. Dificuldade: produzir pode se tornar mais rápido que compreender e validar. Não apresentar esse deslocamento como medição de todo o campo, mas como hipótese sustentada pela experiência do caso.

**Fontes:** Relatório, seções 8 e 9.

### 18. Formação precisa aparecer no processo

21:05–22:20 (75 s)

Destacar responsabilidades compartilhadas pelo programa, orientador e estudante. Propor avaliações distribuídas e distinguir exercício para aprender de tarefa de produção. A defesa deve complementar esse percurso. O caso não testa a eficácia destas propostas.

**Fontes:** Relatório, seção 8.

### 19. Relevância e capacidade de revisão

22:20–23:30 (70 s)

Discutir possíveis consequências de aumento da produção sem afirmar colapso observado de periódicos. Origem humana ou de IA não decide relevância. Contribuições incrementais podem ser valiosas se resolvem incerteza importante. Oportunidade de usar a capacidade extra para profundidade, controle e síntese.

**Fontes:** Relatório, seção 9.

### 20. Próximas avaliações do experimento

23:30–24:45 (75 s)

Estas são propostas ainda não executadas. Especialistas poderiam comparar artigo antes e depois do Gemini, checar argumentos e reproduzir resultados centrais. Para aprendizagem seria necessário outro desenho com estudantes e medidas antes e depois.

**Fontes:** Relatório, seção 10.

### 21. Questões para discussão

24:45–26:35 (110 s)

Reservar cerca de dois minutos para encerrar ou abrir uma conversa. Na versão de 20 minutos, selecionar apenas uma questão. Na de 30 minutos, usar o tempo restante para ouvir respostas. Não tratar os produtos como títulos acadêmicos aprovados.

**Fontes:** Relatório do estudo de caso, discussão.

### 22. Apoio: leitura correta das métricas

Apoio opcional

Abrir apenas se perguntarem pelas contagens. Todas são do fechamento v1.0.0, exceto o manuscrito revisado. Os arquivos de evidências documentam regras e exclusões.

**Fontes:** evidencias.json, complementos_pos_goal.json.

### 23. Apoio: documentos e fontes

Apoio opcional

Links completos também estão nas notas e no README. A apresentação usa a conversa de execução e artefatos do próprio projeto. Discussões privadas não foram transcritas.

**Fontes:** https://github.com/flavioluiz/TGdoWayne
