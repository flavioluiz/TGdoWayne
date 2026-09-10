# TG do Wayne — proposta e dissertação em desenvolvimento

**Massa do gráviton e polarizações de ondas gravitacionais em PTAs: efeitos da compressão em frequência e validação estatística.**

Projeto baseado em *Estados de polarização de ondas gravitacionais com gráviton massivo*,
trabalho de graduação de Wayne Leonardo Silva de Paula (ITA, 2003). O objetivo é desenvolver
uma pesquisa de mestrado de 24 meses sobre a confiabilidade da inferência da massa do gráviton
com redes de temporização de pulsares, com potencial para um artigo metodológico.

<!-- PROJECT_STATUS:START -->
## Estado atual

**Resposta tensorial de PTA validada; metodologia de simulação em andamento**  
**Última etapa concluída:** C05 — Resposta de PTA e correlações validadas.  
**Progresso:** 5 de 13 marcos concluídos.  
**Próxima etapa:** C06 — Metodologia de simulação e dados sintéticos.  
**Atualização:** 2026-09-10.

**[Baixar o PDF mais recente — v0.5.0](https://github.com/flavioluiz/TGdoWayne/releases/download/v0.5.0/dissertacao.pdf)** · [Notas do release](https://github.com/flavioluiz/TGdoWayne/releases/tag/v0.5.0) · [PDF versionado no repositório](output/pdf/v0.5.0/dissertacao.pdf)

### O que já foi executado

- Leitura do TG de Wayne (ITA, 2003) e identificação de seus resultados já publicados em 2004.
- Busca bibliográfica dirigida com corte em 10/09/2026 e proposta de investigação sobre compressão em frequência em PTAs.
- Checagens cinemáticas reproduzíveis: vínculos, curvatura, relação escalar e escalas de massa/frequência.
- Proposta em LaTeX/PDF com o template ITA, cronograma de 24 meses e separação entre resultados preliminares e experimentos futuros.
- Plano de 13 commits com critérios de conclusão, PDFs cumulativos, manifesto de integridade e publicação por tag.
- Introdução da dissertação concluída: motivação, continuidade com o TG, pergunta, hipótese, objetivos, escopo e critérios de avaliação.
- Documento cumulativo da dissertação criado, com quadro explícito do estado dos capítulos e metadados vinculados à versão.
- Revisão bibliográfica detalhada, matriz com 17 entradas, inspeção de códigos públicos e segunda leitura independente dos antecedentes metodológicos.
- Acervo local de 22 artigos (452 páginas), com versões, URLs, licenças indicadas e SHA-256; script para baixar e verificar as cópias.
- Recorte refinado diante de trabalhos de 2025–2026; planos C05–C10 atualizados para separar compressão, distribuição probabilística, resposta e suporte.
- Derivação simbólica geral da curvatura, vínculos e postos de Visser/FP; relação escalar, limites e reprodução das projeções do TG confrontados com Hyun.
- Auditoria independente de Einstein linear, sinais, unidades e normalização histórica da massa; 19 testes simbólicos aprovados e registro reproduzível com dependências fixadas.
- Resposta tensorial com termos da Terra e dos pulsars, fases complexas e normalização espectral explícita; limites de Liang–Trodden/Cordes e Hellings–Downs reproduzidos.
- 23 testes de resposta, geometria e interface aprovados; campanha de 58 casos aceita com métodos independentes, refinamento separado e orçamento numérico explícito.

### O que está em andamento e o que falta

C06 em andamento: experimento Fourier, dados sintéticos, estimadores e propagação da covariância. Inferência, calibração estatística e artigo ainda não estão concluídos.

## Roadmap

Cada linha corresponde a um commit de marco e a um PDF cumulativo. A primeira versão contém a proposta; de C02 em diante, a dissertação em desenvolvimento.

| Etapa | Entrega | Versão do PDF | Estado | Plano do commit |
|---|---|---|---|---|
| C01 | Proposta de pesquisa, plano e repositório | `v0.1.0` | Concluída | [Detalhes](implementation_plan/commits/C01_proposta_e_repositorio.md) |
| C02 | Introdução da dissertação | `v0.2.0` | Concluída | [Detalhes](implementation_plan/commits/C02_introducao.md) |
| C03 | Revisão bibliográfica e originalidade | `v0.3.0` | Concluída | [Detalhes](implementation_plan/commits/C03_revisao_bibliografica.md) |
| C04 | Fundamentos teóricos e reprodução do TG | `v0.4.0` | Concluída | [Detalhes](implementation_plan/commits/C04_fundamentos_e_tg.md) |
| C05 | Resposta de PTA e correlações validadas | `v0.5.0` | Concluída | [Detalhes](implementation_plan/commits/C05_resposta_pta.md) |
| C06 | Metodologia de simulação e dados sintéticos | `v0.6.0` | Em andamento | [Detalhes](implementation_plan/commits/C06_simulacoes.md) |
| C07 | Inferência de referência e calibração | `v0.7.0` | Planejada | [Detalhes](implementation_plan/commits/C07_inferencia_validada.md) |
| C08 | Resultados sobre compressão em frequência | `v0.8.0` | Planejada | [Detalhes](implementation_plan/commits/C08_compressao_frequencia.md) |
| C09 | Robustez a prioris, ruído e covariâncias | `v0.9.0` | Planejada | [Detalhes](implementation_plan/commits/C09_prioris_covariancias.md) |
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
| `literature/` | Catálogo e acervo local de 22 artigos, com script de download |
| `docs/literatura/` | Protocolo, matriz de originalidade e auditoria de métodos/códigos |
| `implementation_plan/` | Plano geral, roadmap e um Markdown por commit |
| `project_status.json` | Fonte do painel de estado do README |
| `scripts/` | Checagens, compilação, atualização do README e integridade |
| `src/polarizacoes/` | Curvatura e vínculos simbólicos gerais |
| `src/pta/` | Resposta tensorial, ORFs e verificação de convergência |
| `tests/`, `results/C04/`, `results/C05/` | 19 testes simbólicos, 23 testes de resposta e benchmarks |
| `configs/benchmarks_orf/`, `figures/C05/` | Configurações de validação e figuras científicas |
| `output/pesquisa/` | Análise inicial e resultados das checagens |
| `output/pdf/<versão>/` | PDF imutável de cada marco |
| `releases/<versão>/` | Notas da versão e manifesto de integridade |

`latex/dissertacao.tex` é o documento cumulativo, iniciado em C02. O quadro de capítulos informa as entregas concluídas e planejadas. A proposta inaugural permanece disponível em sua tag e em `latex/proposta.tex`.
O Markdown em `output/pesquisa/` preserva a análise inicial; a fonte editorial do PDF passa a ser o LaTeX.

## Artigos da revisão

Os **22 PDFs** foram baixados em `literature/papers/` (25,15 MB; 452 páginas), com versões e
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
make pdf
make check
```

`make pdf` confere os metadados e o quadro de capítulos e compila uma cópia de conferência em `tmp/latex/<documento>/<documento>.pdf`, sem substituir o
PDF publicado. `make check` reexecuta os 19 testes simbólicos e os 23 testes de resposta e confere os registros,
além das checagens preliminares, do estado do README e dos hashes do release atual.
Também confere a procedência da campanha de 58 ORFs; não repete suas integrais nesse comando.
Para reexecutar a campanha completa, use `.venv/bin/python scripts/benchmark_orf.py`
(64,82 s na execução registrada).
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
make release VERSION=v0.6.0 DOCUMENT=dissertacao
```

O exemplo pressupõe que C06 foi concluído e que seus fontes, estado e notas de release já existem.
O [procedimento completo](implementation_plan/README.md#procedimento-de-fechamento-de-cada-marco)
inclui a inspeção visual, o commit, a tag e a conferência do download. O workflow do GitHub anexa o
**mesmo PDF que está no commit**, sem recompilá-lo. Versões `v0.*` são publicadas como pré-releases;
por isso o link “PDF mais recente” usa a tag explícita atual e não `/releases/latest`.

## Limites e procedência

Esta versão não demonstra ineditismo definitivo, detectabilidade, estabilidade não linear ou uma
nova restrição observacional. As verificações implementadas abrangem geometria, consistência linear e resposta tensorial de PTA; os testes estatísticos
fazem parte dos marcos futuros. A submissão e a aceitação de um artigo não estão realizadas nem garantidas.

O TG e os materiais de terceiros preservam seus direitos e atribuições. O template mantém sua licença
Apache 2.0 no próprio diretório; ela não é aplicada automaticamente ao TG ou ao texto da proposta.
Consulte [a procedência do template](templates/README.md) e as referências da proposta.
