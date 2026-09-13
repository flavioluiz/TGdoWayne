# Roteiro da apresentação do experimento

15 slides principais e três de apoio. Duração sugerida: **25:50**, incluindo a abertura da discussão. Público: pós-graduação, sem pressupor conhecimento de ondas gravitacionais.

O roteiro orienta a fala, sem leitura literal dos slides. Os tempos são sugestões, não resultado de ensaio. As notas e fontes também estão incorporadas ao PowerPoint.

## Ritmo e adaptações

- **Cerca de 20 minutos:** omitir os slides 4, 5 e 12, resumindo seus pontos nas transições, e limitar o slide 15 a 40 segundos.
- **Cerca de 26 minutos:** usar os 15 slides principais. A pergunta inicial e a discussão dos slides 10–15 recebem pouco mais da metade do tempo.
- **30 minutos:** ampliar a discussão final em 4 minutos e 10 segundos.
- **Apoio:** os slides 16–18 detalham métricas, custos e fontes, sem integrar o tempo principal.

## Sequência e fala sugerida

### 1. Uma dissertação em poucos dias

00:00–01:00 (60 s)

Abrir mostrando os artefatos reais. O agente produziu uma dissertação de 167 páginas e um artigo inicialmente de sete páginas. O manuscrito mostrado tem nove páginas após revisão posterior. Da criação ao encerramento do goal transcorreram 54h56min, arredondadas para 55 horas; desde o primeiro pedido foram cerca de 57 horas. O contador do goal marcou 30h51min, sem representar tempo de CPU. A provocação é o que uma entrega assim diz sobre a formação humana.

**Fontes:** Relatório, abertura e apêndice D; PDFs originais.

### 2. O que o diploma deve atestar?

01:00–03:00 (120 s)

Apresentar a pergunta antes dos detalhes de execução. Um documento pode ser útil para avaliar o resultado científico e insuficiente para demonstrar o domínio individual. Separar aprendizagem, qualidade e responsabilidade. Evitar dizer que o PDF não prova nada ou que a formação perdeu valor. O experimento não mediu aprendizagem.

**Fontes:** Relatório, abertura e seção 3.

### 3. Uma intenção ampla, um TG de partida

03:00–04:20 (80 s)

O proponente declara não dominar o tema e não ter fornecido hipóteses, equações ou código. Forneceu o TG de 2003 e solicitou continuidade implementável, validável e com potencial de publicação. O texto do slide é uma síntese dos pedidos, não uma citação literal. Não afirmar ausência completa de intervenção: houve acompanhamento e pareceres encaminhados.

**Fontes:** TG_Wayne.pdf; relatório, apêndices A a A.2.

### 4. A delegação e a revisão

04:20–05:40 (80 s)

Ler o diagrama da esquerda para a direita. O usuário definiu a intenção e acompanhou o processo. O Codex Astra coordenou três subagentes e formulou, implementou e redigiu. Os pareceres do Gemini chegaram por intermédio do usuário. A seta dupla indica crítica e resposta, não uma integração automática entre sistemas. Não houve revisão cega nem avaliação formal por pares humanos.

**Fontes:** Relatório, abertura, seção 2 e apêndices A e B.

### 5. A primeira decisão foi descartar caminhos

05:40–07:10 (90 s)

Em vez de alegar que repetiu o TG como descoberta, o agente reconheceu resultados já publicados em 2004 e antecedentes posteriores. Um trabalho de 2026 motivou uma comparação entre simplificações. Não dizer que esse artigo continha uma falha já provada. O recorte foi uma pergunta de confiabilidade com originalidade candidata.

**Fontes:** Relatório, seção 1; protocolo e decisão de recorte na literatura.

### 6. Um teste encontrou confiança excessiva

07:10–08:50 (100 s)

Explicar sem física: em dados simulados sabemos a resposta. Uma faixa de incerteza que promete conter essa resposta em 90% dos casos precisa passar por um teste. Em um parâmetro de ruído ela continha a resposta em 313 de 500 casos, 62,6%. Isso demonstra uma limitação daquela aproximação naquele teste, não erro de todos os métodos. O problema tornou-se parte do resultado científico.

**Fontes:** Relatório, seção 2 e apêndice B.1; review_efac_coverage.json.

### 7. Uma IA criticou. A outra conferiu.

08:50–10:50 (120 s)

Distinguir os ciclos. No primeiro, o Codex conferiu o parecer e acrescentou 300 análises em 50 casos sob condições fixadas, além de um estudo temporal. O complemento resolveu um problema menor. No segundo, o agente revisou o artigo sem simulações novas e recusou extrapolações: falha em simulação não prova falha inevitável em dados reais. As frases do slide são sínteses, não transcrições. A revisão foi mediada pelo usuário e não certifica o resultado.

**Fontes:** Relatório, seção 2 e apêndice A.2; article/REVISION_NOTES.md.

### 8. Concluir a tarefa não encerrou a pergunta

10:50–12:20 (90 s)

A comparação ampla continuou inconclusiva na precisão exigida. O estudo adicional respondeu sob condições fixadas, sem resolver a formulação ampla. O agente escolheu a alternativa simulada autorizada pelo plano porque não tinha um adaptador local validado para as séries reais. Há dados públicos, portanto não dizer que eram inexistentes. Discutir o risco de confundir entrega administrativa e conclusão científica.

**Fontes:** Relatório, seção 2 e apêndices B e B.1.

### 9. Escala e custo do experimento

12:20–13:40 (80 s)

As linhas incluem comentários e vazios. As análises principais reutilizam dados; não são 45 mil descobertas. A suíte básica soma 217 verificações, com outras auditorias. Não estimar equivalência a anos de trabalho humano sem comparação. O custo de US$ 50 é rateio informado; US$ 1.300 é equivalente em API Standard a preços de 13/09/2026. Fast seria aproximadamente US$ 2.600. A estimativa exclui Gemini, computação local, ferramentas e estudo de caso. Não mede o esforço de compreender e verificar. Detalhes no apoio.

**Fontes:** Relatório, apêndices C e E; estimativa_custo_api.json.

### 10. O produto e a pessoa pedem provas distintas

13:40–15:40 (120 s)

O documento continua permitindo examinar a pesquisa. O caso mostra que sua qualidade aparente não basta para atribuir domínio ao estudante. Identificar uso de IA ou exigir declaração de ferramentas tem papel de transparência, mas não responde se a pessoa entende o que foi feito. Explicar essa distinção sem tratar integridade acadêmica como dispensável.

**Fontes:** Relatório, seção 3.

### 11. Mais artigos ou mais conhecimento?

15:40–17:50 (130 s)

Apresentar como cenário, não previsão comprovada: se agentes aumentarem a produção, atenção de revisores pode limitar o sistema. Contribuições incrementais não perdem valor automaticamente. Uma réplica crítica ou limite bem determinado pode ser mais relevante que alegar uma grande descoberta. No caso, a limitação da aproximação e a inconclusão documentada permitem discutir utilidade. Pedir que a audiência pense no critério que usaria para priorizar um manuscrito.

**Fontes:** Relatório, seção 4.

### 12. O que muda entre simular e medir?

17:50–19:40 (110 s)

O experimento foi computacional. Não comparou produtividade ou qualidade com pesquisa de laboratório. Medir exige vínculo com fenômenos, calibração e desenho de ensaios; dados inéditos podem ampliar a evidência. Isso não garante superioridade do experimental: teoria e computação também contribuem e experimentos também usam automação. A pergunta comum é o que conecta a conclusão à evidência e como a pessoa responde por essa conexão.

**Fontes:** Relatório, seção 4.

### 13. A orientação pode trabalhar com outra divisão

19:40–21:50 (130 s)

O agente pode executar implementações e primeiras comparações. A oportunidade é explorar ideias antes inviáveis. O orientador e o estudante precisam construir critérios, escolher problemas e verificar resultados. Isso não retira formulação do estudante; torna importante observá-la. Distinguir atividade para aprender, que pode pedir trabalho individual, da produção científica com delegação ampla. Não reduzir o estudante a operador de agentes.

**Fontes:** Relatório, seções 3 e 4.

### 14. A formação aparece antes da defesa

21:50–24:00 (130 s)

Propor uma sequência de avaliação concreta. Antes de rodar uma modificação, o estudante registra a previsão e a razão. Depois interpreta o novo gráfico e explica uma divergência. Na defesa reconstrói um argumento central e seus limites, em parte sem assistência quando apropriado. A banca usa registros de acompanhamento para julgar autonomia e profundidade. Para o doutorado e mestrado, discutir níveis esperados sem assumir que número de páginas diferencia os títulos. Estas são propostas pedagógicas, não resultados testados no caso.

**Fontes:** Relatório, seções 3 e 5.

### 15. O que passaríamos a exigir?

24:00–25:50 (110 s)

Encerrar com espaço real para debate. Convidar a audiência a formular um critério para cada questão. O experimento fornece artefatos e decisões verificáveis; a qualidade científica deve ser examinada por especialistas, e aprendizagem requer estudo próprio. Não propor uma única política institucional a partir de um caso. Se houver mais tempo, discutir avaliação independente do manuscrito e comparação entre versões, ainda não realizadas.

**Fontes:** Relatório, seção 5.

### 16. Apoio: definições das métricas

Apoio opcional

Números históricos da v1.0.0. O manuscrito de nove páginas é posterior. O total de código arquivado não é deduplicado. O tempo do goal não é CPU. As análises compartilham dados.

**Fontes:** Relatório, apêndices C e D.

### 17. Apoio: hipóteses da estimativa de custo

Apoio opcional

Aplicação dos preços oficiais Astra Standard de 13/09/2026 aos registros únicos por resposta. Até o goal são 6.510 respostas, com agente principal e três subagentes, totalizando US$ 1.289,34. Os complementos científicos acrescentam US$ 14,29. 97,56% da entrada veio de cache. Gravações de cache zero no registro; cobrar toda entrada nova como gravação acrescentaria cerca de US$ 53, mantida a reutilização. Fast dobra o preço. Não incluir o contador do goal nem somar raciocínio duas vezes. Exclui Gemini, computação local, ferramentas adicionais e estudo de caso. US$ 50 é estimativa do usuário sobre rateio, não tarifa de API.

**Fontes:** Relatório, apêndice E; estimativa_custo_api.json; developers.openai.com/api/docs/models/gpt-6-astra.

### 18. Apoio: documentos para examinar o caso

Apoio opcional

O repositório reúne PDFs e fontes, evidências e notas de revisão. O corpo do relatório discute decisões e formação; os apêndices guardam interações, métricas e método. Conversas privadas não foram transcritas.

**Fontes:** https://github.com/flavioluiz/TGdoWayne
