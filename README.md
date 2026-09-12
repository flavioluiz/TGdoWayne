# TG do Wayne — proposta e dissertação em desenvolvimento

**Massa do gráviton e polarizações de ondas gravitacionais em PTAs: efeitos da compressão em frequência e validação estatística.**

Projeto baseado em *Estados de polarização de ondas gravitacionais com gráviton massivo*,
trabalho de graduação de Wayne Leonardo Silva de Paula (ITA, 2003). O objetivo é desenvolver
uma pesquisa de mestrado de 24 meses sobre a confiabilidade da inferência da massa do gráviton
com redes de temporização de pulsares, com potencial para um artigo metodológico.

<!-- PROJECT_STATUS:START -->
## Estado atual

**Trabalho retomado; C09 em andamento, C09–C11 ainda em draft**  
**Última etapa concluída:** C08 — Resultados sobre compressão em frequência.  
**Progresso:** 8 de 13 marcos concluídos.  
**Próxima etapa:** C09 — Robustez a prioris, ruído e covariâncias.  
**Atualização:** 2026-09-12.

**[Baixar o PDF mais recente — v0.8.7](https://github.com/flavioluiz/TGdoWayne/releases/download/v0.8.7/dissertacao.pdf)** · [Notas do release](https://github.com/flavioluiz/TGdoWayne/releases/tag/v0.8.7) · [PDF versionado no repositório](output/pdf/v0.8.7/dissertacao.pdf)

### O que já foi executado

- Leitura do TG de Wayne (ITA, 2003) e identificação de seus resultados já publicados em 2004.
- Busca bibliográfica dirigida com corte em 10/09/2026 e proposta de investigação sobre compressão em frequência em PTAs.
- Checagens cinemáticas reproduzíveis: vínculos, curvatura, relação escalar e escalas de massa/frequência.
- Proposta em LaTeX/PDF com o template ITA, cronograma de 24 meses e separação entre resultados preliminares e experimentos futuros.
- Plano de 13 commits com critérios de conclusão, PDFs cumulativos, manifesto de integridade e publicação por tag.
- Introdução da dissertação concluída: motivação, continuidade com o TG, pergunta, hipótese, objetivos, escopo e critérios de avaliação.
- Documento cumulativo da dissertação criado, com quadro explícito do estado dos capítulos e metadados vinculados à versão.
- Revisão bibliográfica detalhada, matriz com 17 entradas, inspeção de códigos públicos e segunda leitura independente dos antecedentes metodológicos.
- Acervo inicial de 22 artigos (452 páginas), com versões, URLs, licenças indicadas e SHA-256; script para baixar e verificar as cópias.
- Recorte refinado diante de trabalhos de 2025–2026; planos C05–C10 atualizados para separar compressão, distribuição probabilística, resposta e suporte.
- Derivação simbólica geral da curvatura, vínculos e postos de Visser/FP; relação escalar, limites e reprodução das projeções do TG confrontados com Hyun.
- Auditoria independente de Einstein linear, sinais, unidades e normalização histórica da massa; 19 testes simbólicos aprovados e registro reproduzível com dependências fixadas.
- Resposta tensorial com termos da Terra e dos pulsars, fases complexas e normalização espectral explícita; limites de Liang–Trodden/Cordes e Hellings–Downs reproduzidos.
- 23 testes de resposta, geometria e interface aprovados; campanha de 58 casos aceita com métodos independentes, refinamento separado e orçamento numérico explícito.
- Experimento Fourier periódico com sinal tensorial, ruídos branco/vermelho, estimadores complexos e compressão fixa; contrato A0/A/B/C e desenho prospectivo registrados.
- Onze testes do simulador aprovados; três campanhas com 131072 realizações físicas e controles cada recuperaram momentos e cumulantes, com 605 avaliações auditadas de pares ORF.
- Acervo ampliado para 26 PDFs locais (600 páginas), incluindo quatro referências metodológicas de calibração, com versões publicadas até 2026.
- Acervo atualizado até 11/09/2026: 37 PDFs locais, 839 páginas; catálogo com URLs, versões e SHA-256 e revisão dirigida dos antecedentes recentes.
- Inferência com treino separado da produção IID, quatro réplicas, proposta defensiva e backend nativo; 164 testes de componentes e referências independentes preservadas.
- Campanha de 500 realizações e cinco análises concluída; 2500 inferências, 81 alvos com algum diagnóstico pendente e 243 PITs não resolvidos, sem descarte de dados.
- Síntese SBC auditada independentemente: 6202 verificações e reconstrução exata de 15000 flags por função. Controles sem rejeição nominal; dez rejeições persistentes nas aproximações normais.
- Noventa e seis controles A0 concluídos, com 32 observações por cenário, 416 PITs numéricos e 32 estruturais; parâmetros sem verdade definida mascarados. Cobertura condicional reportada separadamente.
- Arquivos compactos restauráveis das campanhas, com verificações de SHA-256, propostas, sementes, diagnósticos e recibos preservados; capítulo 6 incorporado ao PDF cumulativo.
- Correção de portabilidade dos testes entre macOS e Linux: fixtures com geometria preservada, identidade dos caches mantida e tolerância explícita ao arredondamento BLAS.
- Mapas de compressão e resposta concluídos em massa, espectro, amplitudes, duração e janela; expansão de dispersão fraca e necessidade de covariâncias entre frequências na janela Hann projetada documentadas.
- Descrição pareada das 500 realizações de C07 preservada, com 2500 posteriores e todos os casos numericamente pendentes mantidos.
- Dezesseis alvos de engenharia e 128 alvos C_beta/C_full concluídos; 160 alvos HIGH de C07 reproduzidos com 640 réplicas de SHA e estados RNG originais idênticos.
- Controles da resposta concluídos em 288 nuvens e 324 vinculações; interrupção por CPU e continuação exclusivamente estatística registradas separadamente, sem repetir avaliações físicas.
- Síntese dos 32 dados compartilhados: 5760 quantis, 4480 diferenças de quantis e 1120 diferenças de larguras; 24 dados sorteados separados dos oito de fronteira.
- Todos os 224 contrastes primários individuais e as sete médias piloto permaneceram inconclusivos na escala de 0,01; 4300 quantis mantêm intervalos [0,1], sem alegar equivalência ou ausência de efeito.
- Divergências de forma posterior A_G para B_G avaliadas em quatro dados fixos, com MCSE e covariâncias auditadas; não tratadas como fatores de Bayes.
- Capítulo 7 incorporado ao PDF; tabelas, arquivos restauráveis, fontes, protocolos e histórico de falhas preservados com verificação de SHA-256.
- Piloto parcial C09 e reparos D1/D1b preservados: 544316 avaliações acumuladas; 13/14 eventos resolvidos na representação tabulada, caso 10 pendente e todos os intervalos do evento físico [0,1].
- Texto desenvolvido e resultados parciais de C09–C11 incorporados como drafts, com tarefas pendentes e arquivos de retomada. Nenhuma nova simulação física iniciada para v0.8.5.
- Retomada D2 executada: 13 curvas, 40 análises previstas, 175778 avaliações contabilizadas e caches preservados após limites de recursos; controles pontuais aprovados, referências funcionais incompletas.
- Auditoria reconstruiu as contagens e verificou os cinco caches históricos bit a bit; 40 estimativas tabuladas foram recuperadas como drafts, sem novas likelihoods.
- Referências D2 concluídas para 40 análises: normalização, CDF, quantis, momentos e KL passaram nos critérios operacionais, com controles físicos pontuais separados.
- Continuações D2 contabilizaram 40875 avaliações e 223,28 s CPU; caches e painéis foram reutilizados, falhas preservadas e 37 contrastes pareados sintetizados.

### O que está em andamento e o que falta

C09 em andamento: as 40 análises D2 passaram nos cinco controles primários, com 37 contrastes pareados e alcance condicional explícito. Permanecem pendentes W1, eventos de log-likelihood e D3 com calibração SBC, ruído, espectros, contaminantes, distâncias e variabilidade. C10–C11 têm drafts e preparações; C12–C13 permanecem planejados. Consulte docs/d2_v0.8.7/README.md. Nenhuma simulação permanece em execução após o fechamento deste lote.

## Roadmap

Cada linha corresponde a um commit de marco e a um PDF cumulativo. A primeira versão contém a proposta; de C02 em diante, a dissertação em desenvolvimento.

| Etapa | Entrega | Versão do PDF | Estado | Plano do commit |
|---|---|---|---|---|
| C01 | Proposta de pesquisa, plano e repositório | `v0.1.0` | Concluída | [Detalhes](implementation_plan/commits/C01_proposta_e_repositorio.md) |
| C02 | Introdução da dissertação | `v0.2.0` | Concluída | [Detalhes](implementation_plan/commits/C02_introducao.md) |
| C03 | Revisão bibliográfica e originalidade | `v0.3.0` | Concluída | [Detalhes](implementation_plan/commits/C03_revisao_bibliografica.md) |
| C04 | Fundamentos teóricos e reprodução do TG | `v0.4.0` | Concluída | [Detalhes](implementation_plan/commits/C04_fundamentos_e_tg.md) |
| C05 | Resposta de PTA e correlações validadas | `v0.5.0` | Concluída | [Detalhes](implementation_plan/commits/C05_resposta_pta.md) |
| C06 | Metodologia de simulação e dados sintéticos | `v0.6.0` | Concluída | [Detalhes](implementation_plan/commits/C06_simulacoes.md) |
| C07 | Inferência de referência e calibração | `v0.7.1` | Concluída | [Detalhes](implementation_plan/commits/C07_inferencia_validada.md) |
| C08 | Resultados sobre compressão em frequência | `v0.8.0` | Concluída | [Detalhes](implementation_plan/commits/C08_compressao_frequencia.md) |
| C09 | Robustez a prioris, ruído e covariâncias | `v0.9.0` | Em andamento | [Detalhes](implementation_plan/commits/C09_prioris_covariancias.md) |
| C10 | Extensão com helicidade zero vinculada | `v0.10.0` | Planejada | [Detalhes](implementation_plan/commits/C10_helicidade_zero.md) |
| C11 | Aplicação pública ou extensão simulada | `v0.11.0` | Planejada | [Detalhes](implementation_plan/commits/C11_aplicacao.md) |
| C12 | Discussão, conclusões e manuscrito | `v0.12.0` | Planejada | [Detalhes](implementation_plan/commits/C12_discussao_artigo.md) |
| C13 | Auditoria final e dissertação consolidada | `v1.0.0` | Planejada | [Detalhes](implementation_plan/commits/C13_auditoria_final.md) |

[Plano geral de execução](implementation_plan/README.md). O cronograma científico é de 24 meses; os marcos são liberados por critérios de conclusão, não só por data.

<!-- PROJECT_STATUS:END -->

## Pergunta de pesquisa

Em quais condições substituir a resposta dependente da frequência por uma resposta avaliada em
uma frequência de referência preserva a inferência da massa do gráviton, e quando isso altera
limites, evidências entre modelos ou a identificação de uma componente escalar?

Serão comparadas três análises das mesmas simulações: frequência explícita, compressão consistente
e aproximação por frequência de referência, com uma referência adicional em coeficientes Fourier.
A revisão C03 identificou antecedentes próximos e delimitou a contribuição candidata ao mapa de
validade dessa substituição dispersiva. Consulte a [decisão de recorte](docs/literatura/decisao_recorte.md).
Os resultados centrais do TG já foram publicados; sua reprodução é uma base de validação.

## Identificação da proposta

- **Autor:** Gráviton de Souza — pseudônimo provisório, solicitado para esta versão.
- **Programa:** Programa de Física.
- **Orientação:** Autor do TG do Wayne — identificação provisória, sem atribuir orientação formal.
- **Modelo:** template de mestrado do ITA fornecido no projeto. Os metadados acadêmicos definitivos serão atualizados posteriormente.

## Organização

| Caminho | Conteúdo |
|---|---|
| `TG_Wayne.pdf` | TG original, preservado |
| `Template_Instituto_Tecnológico_de_Aeronáutica__ITA_.zip` | Arquivo do template fornecido |
| `templates/ita/` | Template extraído, com licença e exemplos originais |
| `latex/proposta.tex` | Proposta inaugural |
| `latex/dissertacao.tex` | Documento principal da dissertação cumulativa |
| `latex/chapters.json` | Estado editorial e arquivos dos capítulos |
| `latex/capitulos_proposta/` | Texto da proposta em LaTeX |
| `latex/referencias/` | Bibliografia em BibLaTeX |
| `literature/` | Catálogo e acervo local de 37 artigos e relatórios, com script de download |
| `docs/literatura/` | Protocolo, matriz de originalidade e auditoria de métodos/códigos |
| `implementation_plan/` | Plano geral, roadmap e um Markdown por commit |
| `project_status.json` | Fonte do painel de estado do README |
| `scripts/` | Checagens, compilação, atualização do README e integridade |
| `src/polarizacoes/` | Curvatura e vínculos simbólicos gerais |
| `src/pta/` | Resposta tensorial, ORFs, simulador e estatísticas quadráticas |
| `src/inference/`, `results/C07/` | Inferência, referências, sínteses500/96, arquivos restauráveis e auditorias |
| `tests/`, `results/C04/`, `results/C05/`, `results/C06/` | 19 testes simbólicos, 23 de resposta, 11 do simulador e campanhas |
| `configs/`, `figures/` | Configurações de validação, desenho experimental e figuras científicas |
| `output/pesquisa/` | Análise inicial e resultados das checagens |
| `output/pdf/<versão>/` | PDF imutável de cada marco |
| `releases/<versão>/` | Notas da versão e manifesto de integridade |

`latex/dissertacao.tex` é o documento cumulativo, iniciado em C02. O quadro de capítulos informa as entregas concluídas e planejadas. A proposta inaugural permanece disponível em sua tag e em `latex/proposta.tex`.
O Markdown em `output/pesquisa/` preserva a análise inicial; a fonte editorial do PDF passa a ser o LaTeX.

## Artigos da revisão

Os **37 PDFs** foram baixados em `literature/papers/` (68,91 MB; 839 páginas), com versões e
SHA-256 conferidos. O [catálogo do acervo](literature/README.md) apresenta arquivos e fontes.
Para reconstituir o acervo em outro checkout, execute `python3 scripts/download_papers.py`;
para conferir as cópias locais, use `python3 scripts/download_papers.py --verify`.
O Git versiona catálogo e receita; os PDFs de terceiros permanecem no acervo local.

## Reproduzir a versão atual

O ambiente científico atual exige Python 3.11 ou superior. SymPy 1.14.0, mpmath 1.3.0,
NumPy 2.4.3, SciPy 1.17.1 e Matplotlib 3.11.1, com suas dependências, estão fixados em `requirements.txt`.
Para o PDF: TeX Live completo ou MacTeX, `latexmk`, pdfLaTeX e Biber. A classe ITA fornecida carrega
BibLaTeX, glossaries, babel em português, geometria e outros pacotes; a configuração local usa também
Latin Modern, microtype, xurl, bookmark e booktabs. A versão inaugural foi compilada com TeX Live 2026.

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
python3 scripts/checagens_preliminares.py
.venv/bin/python scripts/reproduzir_tg.py --check
.venv/bin/python scripts/validar_orf.py --check
.venv/bin/python scripts/validar_simulador.py --check
make pdf
make check
```

`make pdf` confere os metadados e o quadro de capítulos e compila uma cópia de conferência em `tmp/latex/<documento>/<documento>.pdf`, sem substituir o
PDF publicado. `make check` reexecuta os 19 testes simbólicos, os 23 testes de resposta, os 11 do simulador e os 164 de inferência e confere os registros,
além das checagens preliminares, do estado do README e dos hashes do release atual.
Também confere a procedência da campanha de 58 ORFs e das três campanhas de momentos, regenerando as amostras pequenas. Não repete todas as integrais e sorteios nesse comando.
As receitas completas do simulador estão em [dados sintéticos](docs/dados_sinteticos.md).
Os componentes inferenciais também têm uma checagem própria:
`make check-inference-components`. Ela reexecuta 164 testes e confere as evidências
de integração condicional e controles analíticos; não aprova a produção de
posteriores nem a calibração de PTA. Os protocolos estão em
[diagnósticos contínuos](docs/protocolo_diagnosticos_c07_v1.md) e
[diagnósticos de cadeias](docs/protocolo_diagnosticos_mcmc_c07_v2.md).
Para reexecutar a campanha angular C05, use `.venv/bin/python scripts/benchmark_orf.py`
(64,82 s na execução registrada).
As campanhas inferenciais e seus resultados estão descritos em [resultados C07](docs/inferencia/resultados_c07.md).
Os arquivos [500×5](results/C07/posterior500_compact/README.md) e [96 controles](results/C07/fixed96_compact/README.md) permitem restaurar diagnósticos e propostas; regenerar a produção bruta exige repetir o custo científico documentado.
A reprodução de conteúdo requer as mesmas fontes; equivalência binária entre diferentes versões
do TeX não é pressuposta. O manifesto registra a ferramenta utilizada e o SHA-256 do PDF publicado.
Para conferir uma versão anterior, faça checkout de sua tag e use o número correspondente em `VERSION`.

## Como manter o README e publicar os próximos PDFs

O quadro de capítulos e os metadados do PDF são gerados por `scripts/update_document_state.py`, usando `project_status.json` e `latex/chapters.json`.

O painel acima é gerado por `scripts/update_readme.py` a partir de `project_status.json` e
`implementation_plan/roadmap.json`. Em cada marco, atualizar etapa, trabalhos concluídos, próxima
atividade e versão no JSON; executar o gerador. A verificação do release falha se o README estiver
inconsistente. As demais seções do README podem ser editadas diretamente.

```bash
python3 scripts/update_readme.py
python3 scripts/update_document_state.py
make release VERSION=v0.8.0 DOCUMENT=dissertacao
```

O exemplo pressupõe que C08 foi concluído e que seus fontes, estado e notas de release já existem.
O [procedimento completo](implementation_plan/README.md#procedimento-de-fechamento-de-cada-marco)
inclui a inspeção visual, o commit, a tag e a conferência do download. O workflow do GitHub anexa o
**mesmo PDF que está no commit**, sem recompilá-lo. Versões `v0.*` são publicadas como pré-releases;
por isso o link “PDF mais recente” usa a tag explícita atual e não `/releases/latest`.

## Limites e procedência

Esta versão não demonstra ineditismo definitivo, detectabilidade, estabilidade não linear ou uma
nova restrição observacional. As verificações abrangem geometria, consistência linear, resposta tensorial, momentos e calibração no experimento sintético. A campanha conserva falhas numéricas e identifica desvios da aproximação normal e limitações de cobertura condicional. As comparações das respostas de frequência de referência e a extensão escalar seguem no roadmap. A submissão e a aceitação de um artigo não estão realizadas nem garantidas.

O TG e os materiais de terceiros preservam seus direitos e atribuições. O template mantém sua licença
Apache 2.0 no próprio diretório; ela não é aplicada automaticamente ao TG ou ao texto da proposta.
Consulte [a procedência do template](templates/README.md) e as referências da proposta.

## Pausa e versão intermediária v0.8.5

[Plano do commit C08.5](implementation_plan/commits/C08_5_estado_parcial_e_pausa.md) ·
[Resultados preservados e ponto de retomada](docs/pausa_v0.8.5/README.md).
Nenhuma campanha será retomada sem nova solicitação do usuário.
