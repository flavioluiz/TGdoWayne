# Pesquisa acadêmica com agentes de IA: um experimento

Este repositório documenta um experimento de **automação de pesquisa científica com o Codex**, partindo de um trabalho de graduação para produzir uma proposta, uma dissertação e um manuscrito de artigo. O objetivo é investigar o que um agente consegue formular, implementar, validar e escrever com orientação inicial ampla, e usar essa experiência para discutir **formação, avaliação e organização da pesquisa na pós-graduação**.

O estudo de ondas gravitacionais foi o problema científico escolhido para o experimento. A questão central deste repositório é o processo de pesquisa com IA e suas implicações para mestrado, doutorado e trabalho dos pesquisadores.

## Resultado atual: a primeira avaliação especializada questiona a entrega

**Atualização de 13/09/2026: o experimento não demonstrou a produção autônoma de uma dissertação de mestrado adequada.** Na primeira leitura, um especialista no tema e autor do trabalho de partida questionou a clareza, a coerência científica do conjunto e a utilidade dos cálculos. Diante desse retorno, a avaliação atual do proponente é que o trabalho não atende ao objetivo acadêmico no estado em que foi entregue. Pode haver partes aproveitáveis; isso ainda precisa ser demonstrado.

Essa leitura é inicial, sem auditoria completa de cada resultado ou parecer formal de banca. Entretanto, ela muda a interpretação do caso: **o encerramento do goal, o volume de código e os testes internos não equivalem à validação científica**. Os pareceres de outro LLM também não asseguraram que a entrega fizesse sentido para um especialista. Os custos abaixo são os custos desta tentativa, não o preço de uma dissertação cientificamente validada.

A revisão bibliográfica foi dirigida por termos e antecedentes selecionados. Não há registro de um levantamento sistemático dos trabalhos que citaram o artigo de 2004 derivado do TG. O agente documentou a mudança de foco para análises estatísticas de sinais de pulsares, mas a pertinência dessa escolha não foi validada por um especialista antes da execução extensa. A [síntese da reavaliação](output/pdf/relatorio_experimento/reavaliacao_especialista.md) separa evidências, avaliações e hipóteses sem reproduzir conversas privadas.

## Nova versão candidata a revisão humana: v2.0.0-rc.3

**24/09/2026:** a dissertação foi reescrita por completo, com base nas críticas à v1.x: [PDF — 62 páginas](output/pdf/v2.0.0-rc.3/dissertacao.pdf) · [fontes, diagnóstico e verificações](dissertacao_v2/README.md). A nova versão volta à pergunta física do TG, os estados de polarização com gráviton massivo, e a leva até o observável de redes de temporização de pulsares. Ela reaproveita os cálculos existentes e reinterpreta as simulações com as limitações declaradas, entre elas o regime pouco informativo sobre a massa. A reescrita foi feita pelo Claude (Opus 5.5) sem nova campanha numérica. **Ainda não passou por revisão especialista.** A v1.1.0 permanece preservada abaixo para comparação.

## Materiais sobre o experimento

| Material | Acesso | Conteúdo |
|---|---|---|
| **Relatório do estudo de caso** | [PDF](output/pdf/relatorio_experimento/relatorio.pdf) · [LaTeX](output/pdf/relatorio_experimento/relatorio.tex) | Interações, avaliação especializada inicial, revisão das conclusões, métricas e próximos experimentos |
| **Apresentação do experimento, 20–30 min** | [PDF — revisão 7](output/pdf/experimento/experimento_codex_7.pdf) · [Beamer / LaTeX](presentations/experimento/experimento.tex) · [Roteiro](presentations/experimento/roteiro.md) | 12 slides principais e três de apoio, com duração sugerida de 25 minutos |
| Evidências da execução | [Métricas históricas](output/pdf/relatorio_experimento/evidencias.json) · [Complementos após o goal](output/pdf/relatorio_experimento/complementos_pos_goal.json) · [Revisão pelo agy](output/pdf/relatorio_experimento/revisao_agy.json) | Contagens, eventos do goal, revisão do artigo e reescrita pelo Gemini |

## Compare as versões do Codex e do Gemini

**A mesma pesquisa, duas maneiras de apresentar os resultados.** Neste experimento, o texto final do **Codex é mais defensivo**, enfatizando limites e ressalvas; a revisão do **agy / Gemini 3.8 Flash (High) é mais afirmativa**, colocando as contribuições e os caminhos futuros em primeiro plano. Os PDFs abaixo permitem examinar esse contraste diretamente.

| Documento | Versão final do Codex | Versão revisada pelo Gemini |
|---|---|---|
| **Dissertação** | [PDF — 167 páginas, v1.0.0](output/pdf/v1.0.0/dissertacao.pdf) | [PDF — 170 páginas, v1.1.0](output/pdf/v1.1.0/dissertacao.pdf) |
| **Artigo / manuscrito** | [PDF — 9 páginas, commit `26ae3ac`](output/pdf/comparacao_llms/manuscrito_codex.pdf) | [PDF — 9 páginas, commit `09b3584`](output/pdf/comparacao_llms/manuscrito_gemini.pdf) |
| **Apresentação de defesa** | [PDF — 39 slides, commit `293d12a`](output/pdf/comparacao_llms/defesa_codex.pdf) | [PDF — 39 slides, commit `61fa375`](output/pdf/comparacao_llms/defesa_gemini.pdf) |

**Sugestão de leitura:** abra os pares lado a lado e compare resumos, introduções e conclusões; na apresentação de defesa, compare a abertura, a exposição dos resultados e o fechamento. O que ficou mais claro? O que passou a parecer mais relevante? Onde a afirmação ficou mais forte sem novos resultados? Esse contraste ajuda a discutir como a escrita influencia a avaliação do mérito científico.

A versão final do Codex já incorporava pareceres do Gemini; na rodada seguinte, o agy recebeu um pedido explícito de revisão afirmativa. Portanto, o contraste documenta estes textos e suas instruções, não uma característica universal dos modelos. Os dados e o código científico permaneceram os mesmos nessa revisão. As cópias de comparação foram preservadas sem reedição; [origem e hashes dos seis PDFs](output/pdf/comparacao_llms/manifesto.json).

## Produtos científicos gerados no experimento

Esses materiais permitem examinar o resultado da automação. São produtos sob crítica especializada inicial, preservados como evidência do experimento. Sua existência não significa adequação como dissertação, defesa, aprovação institucional, submissão ou aceitação de artigo.

| Produto | PDF | Fontes e contexto |
|---|---|---|
| **Dissertação consolidada** | [Dissertação v1.1.0, 170 páginas](output/pdf/v1.1.0/dissertacao.pdf) | [LaTeX](latex/dissertacao.tex) · [Release v1.1.0](https://github.com/flavioluiz/TGdoWayne/releases/tag/v1.1.0) · [Histórico v1.0.0](https://github.com/flavioluiz/TGdoWayne/releases/tag/v1.0.0) |
| **Artigo / manuscrito revisado** | [Versão atual, 9 páginas](article/manuscript.pdf) | [LaTeX](article/manuscript.tex) · [PDF versionado](output/pdf/article/manuscript.pdf) · [Notas da revisão](article/REVISION_NOTES.md) |
| **Apresentação de defesa** | [Slides para 50 minutos](output/pdf/defesa/defesa_mestrado_50min.pdf) | [Roteiro](presentations/defesa/roteiro_50min.md) · [Beamer](presentations/defesa/README.md) |
| **Apresentação do estudo para público leigo** | [Apresentação didática](output/pdf/didatica/tg_wayne_para_nao_especialistas.pdf) | [Roteiro](presentations/didatica/roteiro.md) · [Beamer](presentations/didatica/README.md) |
| Proposta inicial de pesquisa | [Proposta v0.1.0](output/pdf/v0.1.0/proposta_pesquisa.pdf) | [Plano de execução](implementation_plan/README.md) |
| Trabalho de graduação de partida | [TG original](TG_Wayne.pdf) | Documento anterior ao experimento, preservado com sua atribuição |

**Versões:** a dissertação e o manuscrito foram revisados diretamente pelo **agy / Gemini 3.8 Flash (High)** no commit `09b3584`, tag **v1.1.0**. A pedido do proponente, a revisão valorizou a exposição das contribuições, reorganizou as conclusões em quatro seções e acrescentou cinco direções de trabalhos futuros. A dissertação passou de 167 para 170 páginas; o artigo manteve nove. Não houve nova campanha numérica registrada, e o código e os resultados científicos não mudaram no commit. O relatório examina a reorganização editorial e o fortalecimento de alegações com a mesma evidência. A crítica especializada impede tratar a revisão afirmativa como ganho de clareza ou de qualidade já demonstrado. As versões anteriores permanecem no histórico.

## Como o experimento foi conduzido

O proponente declarou não dominar a área científica e pediu ao Codex que lesse o TG e procurasse uma continuação implementável, com potencial de publicação. O agente selecionou o recorte, buscou antecedentes, criou um plano de 13 marcos e executou a pesquisa com três subagentes. O usuário acompanhou recursos, pediu pausas e retomadas, definiu entregas e orientou a apresentação dos resultados.

O **Gemini elaborou dois pareceres**, encaminhados pelo usuário ao Codex. O primeiro contribuiu para a revisão da dissertação e novos estudos pontuais. O segundo motivou melhorias do manuscrito com os resultados existentes. O Codex incorporou sugestões e também limitou alegações sem suporte. A versão do Gemini nesses dois pareceres não foi informada.

Em uma terceira rodada, o usuário pediu ao **agy / Gemini 3.8 Flash (High)** uma revisão direta por considerar a redação pessimista. A conversa local confirma dois pedidos: propor melhorias e depois implementá-las com trabalhos futuros, PDFs e publicação. O modelo passou de parecerista a executor editorial; o relatório e o slide 7 discutem como essa mudança afeta a apresentação e a percepção do valor científico.

A execução principal ocorreu de **10 a 13 de setembro de 2026**, predominantemente com **GPT-6 Astra**. O goal original foi marcado como concluído em 13/09, às 01:04 de Brasília. As apresentações, a revisão posterior do artigo pelo Codex e a reescrita pelo agy ocorreram depois desse encerramento.

## O que os registros mostram

| Medida | Valor e alcance |
|---|---|
| Tempo registrado pelo goal | **30 h 51 min 26 s**; não é tempo de CPU ou de formação |
| Intervalo no calendário do goal | **54 h 56 min 42 s**, com pausas e retomadas |
| Código principal na v1.0.0 | **26.069 linhas** em módulos, scripts e testes, incluindo comentários e linhas vazias |
| Campanhas principais | **45.528 análises** em quatro campanhas; incluem análises diferentes dos mesmos dados |
| Plano científico | **13 marcos encerrados pelo agente**, sem certificação de adequação científica |
| Revisão posterior do artigo pelo Codex | Cerca de **6 min 37 s** no turno do Codex; exclui o trabalho no Gemini e não altera o contador do goal |
| Revisão direta pelo agy | **20 min 47 s** de calendário; **15 min 44 s** após autorização; sem goal e sem nova campanha numérica |

**Estimativa de custo:** cerca de US$ 1.300 em API Standard, aplicando os preços de 13/09/2026 ao consumo registrado, incluindo os complementos científicos; aproximadamente US$ 2.600 em Fast. O proponente atribui cerca de US$ 50 ao rateio de uma semana da assinatura. São medidas diferentes. A conta exclui Gemini (pareceres e revisão pelo agy), computação local, tarifas adicionais de ferramentas e elaboração do estudo de caso. Veja a [memória de cálculo](output/pdf/relatorio_experimento/estimativa_custo_api.md).

Os números são registros deste caso, não fatores gerais de produtividade. Quantidade de código, simulações ou páginas não comprova qualidade científica. O relatório distingue os produtos da v1.0.0 dos complementos posteriores para evitar dupla contagem.

## Questões que o caso ajuda a discutir

- **Formação e domínio individual:** que competências precisam ser demonstradas pessoalmente quando a execução pode ser delegada?
- **Divisão do trabalho:** como agentes podem viabilizar novas ideias e mudar a participação de orientadores e estudantes?
- **Verificação:** quanto esforço é necessário para compreender, reproduzir e julgar o material produzido?
- **Relevância:** como valorizar perguntas, controles e sínteses úteis, além da quantidade de artigos?
- **Avaliação:** como combinar acompanhamento durante o curso, defesa e atribuição transparente das decisões?
- **Revisão entre modelos:** quais críticas ajudam, quais exageram conclusões e o que ainda requer avaliação especializada?
- **Narrativa e mérito:** quanto uma revisão afirmativa melhora a clareza e quanto muda a percepção de valor dos mesmos resultados?

O repositório contém um estudo de caso, sem grupo de comparação ou medida de aprendizagem. Há evidências de execução e correções internas; a primeira leitura externa especializada questiona a coerência e a utilidade científica da entrega. Uma comparação central permaneceu inconclusiva em seu escopo mais amplo. O artigo não foi submetido e não houve defesa ou aprovação institucional. Os nomes fictícios usados nos produtos acadêmicos fazem parte do experimento.

## Próximos experimentos possíveis

1. **Avaliar se algo pode ser recuperado:** selecionar com especialista uma pergunta pequena e uma alegação verificável; confrontar literatura e cálculo independente antes de reescrever. Admitir encerrar essa tentativa se não houver contribuição útil.
2. **Refazer com orientação científica prévia:** partir de proposta humana ou discutida com especialista, com critérios de êxito e revisões intermediárias antes de ampliar as simulações. Contabilizar o trabalho humano necessário.
3. **Testar melhores meios de revisão bibliográfica:** acrescentar rastreamento de citações e acesso autorizado a bases; comparar cobertura e relevância com a busca por termos. Separar o efeito das ferramentas do efeito da orientação.

São propostas, ainda não executadas. Os produtos científicos permanecem intactos. O critério passa a ser uma resposta compreensível, correta e útil, com esforço de verificação medido; produzir mais documentos não resolve a avaliação negativa.

## Navegação técnica e reprodução

O histórico detalhado do estudo de ondas gravitacionais, seu roadmap, os comandos científicos e as instruções de compilação estão em **[PESQUISA.md](PESQUISA.md)**. A [auditoria final](docs/auditoria_final.md), o [guia de reprodução](docs/reproducao.md) e as [notas do artigo](article/REVISION_NOTES.md) distinguem cálculos refeitos, insumos reutilizados e revisões de texto.

| Diretório | Finalidade |
|---|---|
| `output/pdf/relatorio_experimento/` | Relatório, LaTeX e evidências do estudo de caso |
| `presentations/experimento/` | Apresentação sobre automação da pesquisa, fonte editável e roteiro |
| `src/`, `scripts/`, `tests/`, `results/` | Implementação, verificações e resultados científicos |
| `latex/`, `article/` | Dissertação e manuscrito |
| `literature/`, `docs/`, `implementation_plan/` | Bibliografia, decisões, documentação e plano histórico |
| `releases/`, `output/pdf/v*/` | Manifestos e PDFs das versões da pesquisa |

O comando `make readme` atualiza o painel científico de `PESQUISA.md`; este README é a apresentação do experimento. Para verificar integralmente uma versão histórica, use o checkout da tag correspondente: os manifestos congelam também a documentação daquela versão. A revisão atual do artigo compila com `make article`. A apresentação do experimento tem [instruções próprias](presentations/experimento/README.md).

O TG, o template e os artigos de terceiros mantêm suas atribuições e licenças. A discussão do estudo de caso apresenta temas gerais e não reproduz conversas privadas de terceiros.
