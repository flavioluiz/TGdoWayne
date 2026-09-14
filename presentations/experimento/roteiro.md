# Roteiro da apresentação do experimento

12 slides principais e 3 de apoio. Duração sugerida: **25:00**, incluindo a abertura da discussão. Público: pós-graduação, sem pressupor conhecimento de ondas gravitacionais.

O roteiro orienta a fala, sem leitura literal dos slides. Os tempos são sugestões, sem ensaio cronometrado. As notas Beamer ficam em `notas.tex`, ocultas no PDF da audiência.

## Ritmo e adaptações

- **20 minutos:** usar os 12 slides, reduzindo as pausas de discussão. Reservar cerca de um minuto para o encerramento e resumir em um minuto cada os slides 8, 9 e 10.
- **25 minutos:** seguir os tempos abaixo, com espaço para a pergunta inicial e a abertura do debate no slide 12.
- **30 minutos:** acrescentar cinco minutos à discussão final.
- **Apoio:** slides 13–15, sobre métricas, custos e acesso às fontes, fora do tempo principal.

## Sequência e fala sugerida

### 1. Uma dissertação gerada. Uma pesquisa que faz sentido?

00:00–00:45 (45 s)

A abertura foi revista após a primeira leitura especializada, recebida em 13/09/2026. O caso não demonstrou uma dissertação adequada. Há muita execução documentada, mas coerência e utilidade foram questionadas. Não identificar o revisor nem reproduzir falas privadas. É uma leitura inicial, não parecer formal de banca ou auditoria de todos os cálculos.

**Fontes:** Relatório, seções 2.2–2.3; reavaliacao_especialista.md; protocolo_busca.md.

### 2. O documento não encerrou a pesquisa

00:45–02:45 (120 s)

O proponente passou a considerar a entrega inadequada como dissertação no estado atual. A nova evidência exige rever a interpretação anterior, centrada no volume e no problema da formação. A questão agora inclui se o próprio produto faz sentido. Não inferir que todos os cálculos estejam errados ou que toda pesquisa com IA fracassa. A possibilidade de reaproveitamento continua sem demonstração.

**Fontes:** Relatório, seções 2.2–2.3; reavaliacao_especialista.md; protocolo_busca.md.

### 3. O desafio inicial

02:45–04:25 (100 s)

O proponente declarou não dominar o tema e não forneceu uma hipótese científica nova, equações ou código. Entregou um TG de 2003 e pediu uma continuação com potencial de publicação, implementação e validação. O texto do slide resume os pedidos, sem transcrevê-los. Houve direção humana, acompanhamento operacional e encaminhamento de pareceres. A busca de novidade começou por examinar a literatura: resultados do TG já tinham publicação posterior. Um antecedente recente motivou uma pergunta sobre a confiabilidade de simplificações. Originalidade era candidata, não certificada.

**Fontes:** Relatório, seção 1 e apêndices A e B; TG original.

### 4. O percurso da pesquisa delegada

04:25–06:15 (110 s)

O diagrama resume a ordem predominante, com iterações entre as etapas. O usuário definiu a intenção. O Codex Astra formulou o recorte, organizou um plano de 13 marcos e coordenou três subagentes. Consultou antecedentes para evitar anunciar como novidade o que já existia. Executou quatro campanhas principais com 45.528 análises, que compartilham dados e não correspondem a igual número de simulações independentes. Os testes levaram a correções. Os dois pareceres do Gemini chegaram por intermédio do usuário. O artigo teve uma revisão após o encerramento do goal. O tempo humano não foi cronometrado. As três caixas escuras destacam as etapas conduzidas pelos agentes. Isso não significa ausência completa de participação humana nem permite atribuir uma porcentagem de autonomia. Depois dos pareceres, o proponente mudou também o executor: pediu ao agy/Gemini uma revisão direta para valorizar os resultados na escrita. A leitura especializada posterior questionou a coerência e utilidade. A transição de tema foi registrada, mas a decisão não teve validação científica prévia por especialista.

**Fontes:** Relatório, seções 1 e 2 e apêndices A a D. Relatório, seção 2.1 e apêndice A.3.

### 5. O volume produzido não assegurou mérito

06:15–08:05 (110 s)

A dissertação tinha 167 páginas ao concluir o goal e passou a 170 na revisão do agy, v1.1.0. O artigo foi de sete a nove páginas na revisão anterior pelo Codex e manteve nove com o agy. Os 26.069 incluem comentários e linhas vazias; 45.528 são análises principais de quatro campanhas, com reutilização de dados. Código e campanhas são contagens históricas, sem novas campanhas nessa revisão. O contador do goal marca 30 h 51 min, em cerca de 55 h de calendário; não mede CPU nem tempo de formação. Os US$ 50 são o rateio aproximado da assinatura informado pelo usuário; cerca de US$ 1.300 é a equivalência de API Standard dos registros do Codex, incluindo complementos científicos. Ambos excluem o custo do Gemini e do agy. A rodada do agy levou 20 min 47 s de calendário e não se soma ao contador histórico do goal. Todos os valores são custo e volume desta tentativa, sem equivalência com uma dissertação adequada.

**Fontes:** Relatório, apêndices A.3 e C–E; revisao_agy.json.

### 6. Testes internos validam a pesquisa?

08:05–10:25 (140 s)

O exemplo concreto é uma falha de calibração: para um parâmetro de ruído em 500 casos simulados, a faixa anunciada como 90% continha a resposta conhecida em 313 casos, ou 62,6%. Não se trata de intervalos fraudulentos nem de falha de todos os resultados do estudo. O agente registrou a limitação da aproximação. Em outros momentos, reconheceu que a comparação ampla continuava inconclusiva, respondeu a uma questão mais restrita e conteve alegações de originalidade. O slide reúne esses movimentos de revisão, sem atribuir todos à mesma causa. Não afirmar ausência geral de alucinações ou fabricação sem uma auditoria independente de todo o trabalho. Testes implementados no próprio projeto não garantem que a pergunta seja útil, o modelo adequado ou a interpretação correta.

**Fontes:** Relatório, seção 2 e apêndice B.1.

### 7. Trocar o agente mudou a narrativa

10:25–12:45 (140 s)

Dois pareceres Gemini foram encaminhados ao Codex; depois o agy reescreveu diretamente para uma narrativa afirmativa. Houve mudança de estrutura e fortalecimento de alegações, sem nova campanha científica nessa revisão. A crítica humana posterior impede chamar isso de ganho de clareza comprovado. Os problemas não podem ser atribuídos só ao Gemini, pois recorte e implementação precedem sua reescrita. Os pares de PDFs permanecem no README e apoio 15. Uma resposta posterior do Gemini à crítica é hipótese interpretativa, não validação independente.

**Fontes:** Relatório, seções 2.1–2.2; revisao_agy.json; reavaliacao_especialista.md.

### 8. A primeira leitura especializada foi negativa

12:45–15:05 (140 s)

A crítica especializada inicial questionou termos, coerência e utilidade. Não reduzir o problema a estilo nem explicar a reação como simples preferência de área do leitor. A resposta posterior do Gemini defendeu alguns resultados, mas não é auditoria independente. Também não concluir que tudo está errado: é necessário verificar alegações específicas. O experimento não atingiu adequação científica demonstrada, mesmo tendo encerrado seu goal operacional.

**Fontes:** Relatório, seções 2.2–2.3; reavaliacao_especialista.md; protocolo_busca.md.

### 9. Busca bibliográfica: alcance e lacunas

15:05–17:05 (120 s)

O protocolo registra busca por termos, leitura dirigida, referências e inspeção de código. Não registra levantamento sistemático de artigos que citaram a publicação de 2004. Seguir antecedentes e seguir citações posteriores são caminhos complementares. O catálogo tem 41 PDFs e 1.214 páginas; isso mede acervo, não compreensão. O deslocamento para análises de sinais de pulsares está documentado, portanto não foi oculto no histórico. Sua pertinência científica não foi validada antes da execução extensa. Ferramentas de citações e acesso autorizado a bases podem melhorar cobertura, mas sua contribuição deve ser comparada e não presumida.

**Fontes:** Relatório, seções 2.2–2.3; reavaliacao_especialista.md; protocolo_busca.md.

### 10. O que precisamos aprender a fazer?

17:05–19:25 (140 s)

A capacidade de executar tarefas não substituiu o julgamento da pergunta e da utilidade. Ensinar a formular, contestar e interromper uma linha sem contribuição. Prever um resultado antes do teste, interpretá-lo depois e sustentar uma conclusão diante de mudança de hipótese são exemplos de avaliação. Este caso não mediu aprendizagem e não prova que toda execução científica virou tarefa simples.

**Fontes:** Relatório, seções 2.2–2.3; reavaliacao_especialista.md; protocolo_busca.md.

### 11. Recuperar uma parte ou recomeçar?

19:25–22:05 (160 s)

Duas propostas ainda não executadas. Recuperação: escolher com especialista uma alegação pequena, explicar o problema e verificar por via independente antes de reescrever. Encerrar se não houver contribuição útil; não insistir pelo investimento acumulado. Nova execução: proposta humana ou discutida antes do código, exemplo mínimo e avaliações intermediárias antes de aumentar as simulações. Medir esforço humano e custo de revisão, não apenas tokens. Como teste adicional, comparar ferramentas de citações com busca por termos, mantendo condições comparáveis para separar acesso e supervisão.

**Fontes:** Relatório, seções 2.2–2.3; reavaliacao_especialista.md; protocolo_busca.md.

### 12. Três questões para a pós-graduação

22:05–25:00 (175 s)

Abrir a discussão sobre relevância da pergunta, avaliação precoce do argumento e custo humano de revisão. O caso demonstra produção de artefatos e correções internas, mas não êxito científico autônomo. A leitura inicial negativa deve orientar os próximos testes sem generalização universal. Não atribuir à IA a substituição de anos de formação; tampouco descartar apoio computacional sem avaliar tarefas delimitadas.

**Fontes:** Relatório, seções 2.2–2.3; reavaliacao_especialista.md; protocolo_busca.md.

### 13. Definições das métricas

Apoio opcional.

Números históricos da v1.0.0. O manuscrito de nove páginas é posterior. O total de código arquivado não é deduplicado. O tempo do goal não é CPU. As análises compartilham dados. A revisão v1.1.0 pelo agy acrescentou páginas à dissertação (167 para 170), mas não mudou essas contagens históricas. Seus 20 min 47 s são calendário de outra conversa, sem goal.

**Fontes:** Relatório, apêndices C e D.

### 14. Hipóteses da estimativa de custo

Apoio opcional.

Aplicação dos preços oficiais Astra Standard de 13/09/2026 aos registros únicos por resposta. Até o goal são 6.510 respostas, com agente principal e três subagentes, totalizando US$ 1.289,34. Os complementos científicos acrescentam US$ 14,29. 97,56% da entrada veio de cache. Gravações de cache zero no registro; cobrar toda entrada nova como gravação acrescentaria cerca de US$ 53, mantida a reutilização. Fast dobra o preço. Não incluir o contador do goal nem somar raciocínio duas vezes. Exclui Gemini, computação local, ferramentas adicionais e estudo de caso. US$ 50 é estimativa do usuário sobre rateio, não tarifa de API. A revisão direta pelo agy/Gemini 3.8 Flash também está excluída: não foi obtido consumo faturável verificado para essa rodada.

**Fontes:** Relatório, apêndice E; estimativa_custo_api.json; developers.openai.com/api/docs/models/gpt-6-astra.

### 15. A mesma pesquisa, duas narrativas

Apoio opcional.

Abrir os quatro links: dissertação final do Codex v1.0.0 (167 páginas), revisão Gemini v1.1.0 (170 páginas), artigo final do Codex no commit 26ae3ac (9 páginas) e revisão Gemini no commit 09b3584 (9 páginas). Comparar resumos, introduções e conclusões. A narrativa do Codex é mais defensiva e a do Gemini, mais afirmativa neste caso. Perguntar o que ganhou clareza e quais alegações ficaram mais fortes com os mesmos dados. A versão Codex já incorporava pareceres do Gemini; o agy recebeu um pedido específico de revisão afirmativa. Não se trata de uma comparação controlada entre modelos. O README também oferece cópias preservadas, links para o relatório, fontes e demais produtos. As duas versões precisam de avaliação científica; a revisão afirmativa não assegurou clareza para o especialista.

**Fontes:** README, seção Compare as versões do Codex e do Gemini; relatório, seção 2.1; output/pdf/comparacao_llms/manifesto.json.
