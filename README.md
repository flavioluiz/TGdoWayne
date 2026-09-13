# Pesquisa acadêmica com agentes de IA: um experimento

Este repositório documenta um experimento de **automação de pesquisa científica com o Codex**, partindo de um trabalho de graduação para produzir uma proposta, uma dissertação e um manuscrito de artigo. O objetivo é investigar o que um agente consegue formular, implementar, validar e escrever com orientação inicial ampla, e usar essa experiência para discutir **formação, avaliação e organização da pesquisa na pós-graduação**.

O estudo de ondas gravitacionais foi o problema científico escolhido para o experimento. A questão central deste repositório é o processo de pesquisa com IA e suas implicações para mestrado, doutorado e trabalho dos pesquisadores.

## Materiais sobre o experimento

| Material | Acesso | Conteúdo |
|---|---|---|
| **Relatório do estudo de caso** | [PDF](output/pdf/relatorio_experimento/relatorio.pdf) · [LaTeX](output/pdf/relatorio_experimento/relatorio.tex) | Interações, decisões, erros, revisões, métricas, modelos e questões para discussão |
| **Apresentação do experimento, 20–30 min** | [PDF](output/pdf/experimento/experimento_codex.pdf) · [Beamer / LaTeX](presentations/experimento/experimento.tex) · [Roteiro](presentations/experimento/roteiro.md) | 12 slides principais e três de apoio, com duração sugerida de 25 minutos |
| Evidências da execução | [Métricas históricas](output/pdf/relatorio_experimento/evidencias.json) · [Complementos após o goal](output/pdf/relatorio_experimento/complementos_pos_goal.json) | Definições das contagens, eventos do goal e revisão posterior do artigo |

## Produtos científicos gerados no experimento

Esses materiais permitem examinar o resultado da automação. Sua existência não significa defesa, aprovação institucional, submissão ou aceitação de artigo.

| Produto | PDF | Fontes e contexto |
|---|---|---|
| **Dissertação consolidada** | [Dissertação v1.0.0, 167 páginas](output/pdf/v1.0.0/dissertacao.pdf) | [LaTeX](latex/dissertacao.tex) · [Release](https://github.com/flavioluiz/TGdoWayne/releases/tag/v1.0.0) |
| **Artigo / manuscrito revisado** | [Versão atual, 9 páginas](article/manuscript.pdf) | [LaTeX](article/manuscript.tex) · [Notas da revisão](article/REVISION_NOTES.md) |
| **Apresentação de defesa** | [Slides para 50 minutos](output/pdf/defesa/defesa_mestrado_50min.pdf) | [Roteiro](presentations/defesa/roteiro_50min.md) · [Beamer](presentations/defesa/README.md) |
| **Apresentação do estudo para público leigo** | [Apresentação didática](output/pdf/didatica/tg_wayne_para_nao_especialistas.pdf) | [Roteiro](presentations/didatica/roteiro.md) · [Beamer](presentations/didatica/README.md) |
| Proposta inicial de pesquisa | [Proposta v0.1.0](output/pdf/v0.1.0/proposta_pesquisa.pdf) | [Plano de execução](implementation_plan/README.md) |
| Trabalho de graduação de partida | [TG original](TG_Wayne.pdf) | Documento anterior ao experimento, preservado com sua atribuição |

**Versões:** a dissertação permanece na v1.0.0. O artigo recebeu uma revisão posterior, em 13/09/2026, registrada no commit `26ae3ac`, com base em novo parecer do Gemini. O manuscrito passou de sete para nove páginas, com duas figuras e dez referências, sem novas simulações. O release v1.0.0 conserva a redação anterior do artigo.

## Como o experimento foi conduzido

O proponente declarou não dominar a área científica e pediu ao Codex que lesse o TG e procurasse uma continuação implementável, com potencial de publicação. O agente selecionou o recorte, buscou antecedentes, criou um plano de 13 marcos e executou a pesquisa com três subagentes. O usuário acompanhou recursos, pediu pausas e retomadas, definiu entregas e orientou a apresentação dos resultados.

O **Gemini elaborou dois pareceres**, encaminhados pelo usuário ao Codex. O primeiro contribuiu para a revisão da dissertação e novos estudos pontuais. O segundo motivou melhorias do manuscrito com os resultados existentes. O Codex incorporou sugestões e também limitou alegações sem suporte. A versão do Gemini não foi informada.

A execução principal ocorreu de **10 a 13 de setembro de 2026**, predominantemente com **GPT-6 Astra**. O goal original foi marcado como concluído em 13/09, às 01:04 de Brasília. As apresentações e a última revisão do artigo ocorreram depois desse encerramento.

## O que os registros mostram

| Medida | Valor e alcance |
|---|---|
| Tempo registrado pelo goal | **30 h 51 min 26 s**; não é tempo de CPU ou de formação |
| Intervalo no calendário do goal | **54 h 56 min 42 s**, com pausas e retomadas |
| Código principal na v1.0.0 | **26.069 linhas** em módulos, scripts e testes, incluindo comentários e linhas vazias |
| Campanhas principais | **45.528 análises** em quatro campanhas; incluem análises diferentes dos mesmos dados |
| Plano científico | **13 marcos concluídos**, com resultados, limitações e histórico de falhas |
| Revisão posterior do artigo | Cerca de **6 min 37 s** no turno do Codex; exclui o trabalho no Gemini e não altera o contador do goal |

**Estimativa de custo:** cerca de US$ 1.300 em API Standard, aplicando os preços de 13/09/2026 ao consumo registrado, incluindo os complementos científicos; aproximadamente US$ 2.600 em Fast. O proponente atribui cerca de US$ 50 ao rateio de uma semana da assinatura. São medidas diferentes. A conta exclui Gemini, computação local, tarifas adicionais de ferramentas e elaboração do estudo de caso. Veja a [memória de cálculo](output/pdf/relatorio_experimento/estimativa_custo_api.md).

Os números são registros deste caso, não fatores gerais de produtividade. Quantidade de código, simulações ou páginas não comprova qualidade científica. O relatório distingue os produtos da v1.0.0 dos complementos posteriores para evitar dupla contagem.

## Questões que o caso ajuda a discutir

- **Formação e domínio individual:** que competências precisam ser demonstradas pessoalmente quando a execução pode ser delegada?
- **Divisão do trabalho:** como agentes podem viabilizar novas ideias e mudar a participação de orientadores e estudantes?
- **Verificação:** quanto esforço é necessário para compreender, reproduzir e julgar o material produzido?
- **Relevância:** como valorizar perguntas, controles e sínteses úteis, além da quantidade de artigos?
- **Avaliação:** como combinar acompanhamento durante o curso, defesa e atribuição transparente das decisões?
- **Revisão entre modelos:** quais críticas ajudam, quais exageram conclusões e o que ainda requer avaliação especializada?

O repositório contém um estudo de caso, sem grupo de comparação ou medida de aprendizagem. Há evidências de execução e correção de rota, mas a contribuição científica continua sujeita a avaliação externa. Uma comparação central permaneceu inconclusiva em seu escopo mais amplo. O artigo não foi submetido e não houve defesa ou aprovação institucional. Os nomes fictícios usados nos produtos acadêmicos fazem parte do experimento.

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
