# TG do Wayne — proposta e dissertação em desenvolvimento

**Massa do gráviton e polarizações de ondas gravitacionais em PTAs: efeitos da compressão em frequência e validação estatística.**

Projeto baseado em *Estados de polarização de ondas gravitacionais com gráviton massivo*,
trabalho de graduação de Wayne Leonardo Silva de Paula (ITA, 2003). O objetivo é desenvolver
uma pesquisa de mestrado de 24 meses sobre a confiabilidade da inferência da massa do gráviton
com redes de temporização de pulsares, com potencial para um artigo metodológico.

<!-- PROJECT_STATUS:START -->
## Estado atual

**Proposta de pesquisa concluída; dissertação ainda não iniciada**  
**Última etapa concluída:** C01 — Proposta de pesquisa, plano e repositório.  
**Progresso:** 1 de 13 marcos concluídos.  
**Próxima etapa:** C02 — Introdução da dissertação.  
**Atualização:** 2026-09-10.

**[Baixar o PDF mais recente — v0.1.0](https://github.com/flavioluiz/TGdoWayne/releases/download/v0.1.0/proposta_pesquisa.pdf)** · [Notas do release](https://github.com/flavioluiz/TGdoWayne/releases/tag/v0.1.0) · [PDF versionado no repositório](output/pdf/v0.1.0/proposta_pesquisa.pdf)

### O que já foi executado

- Leitura do TG de Wayne (ITA, 2003) e identificação de seus resultados já publicados em 2004.
- Busca bibliográfica dirigida com corte em 10/09/2026 e proposta de investigação sobre compressão em frequência em PTAs.
- Checagens cinemáticas reproduzíveis: vínculos, curvatura, relação escalar e escalas de massa/frequência.
- Proposta em LaTeX/PDF com o template ITA, cronograma de 24 meses e separação entre resultados preliminares e experimentos futuros.
- Plano de 13 commits com critérios de conclusão, PDFs cumulativos, manifesto de integridade e publicação por tag.

### O que está em andamento e o que falta

C01 é a entrega inaugural. A próxima atividade é C02: redigir a introdução da dissertação. A revisão sistematizada de originalidade, as ORFs, as simulações, a inferência e o artigo ainda não foram executados. Não há ajuste de dados observacionais ou nova restrição de massa nesta versão.

## Roadmap

Cada linha corresponde a um commit de marco e a um PDF cumulativo. A primeira versão contém a proposta; de C02 em diante, a dissertação em desenvolvimento.

| Etapa | Entrega | Versão do PDF | Estado | Plano do commit |
|---|---|---|---|---|
| C01 | Proposta de pesquisa, plano e repositório | `v0.1.0` | Concluída | [Detalhes](implementation_plan/commits/C01_proposta_e_repositorio.md) |
| C02 | Introdução da dissertação | `v0.2.0` | Próxima — não iniciada | [Detalhes](implementation_plan/commits/C02_introducao.md) |
| C03 | Revisão bibliográfica e originalidade | `v0.3.0` | Planejada | [Detalhes](implementation_plan/commits/C03_revisao_bibliografica.md) |
| C04 | Fundamentos teóricos e reprodução do TG | `v0.4.0` | Planejada | [Detalhes](implementation_plan/commits/C04_fundamentos_e_tg.md) |
| C05 | Resposta de PTA e correlações validadas | `v0.5.0` | Planejada | [Detalhes](implementation_plan/commits/C05_resposta_pta.md) |
| C06 | Metodologia de simulação e dados sintéticos | `v0.6.0` | Planejada | [Detalhes](implementation_plan/commits/C06_simulacoes.md) |
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
e aproximação por frequência de referência. A contribuição candidata exige confirmação na revisão
inicial. Os resultados centrais do TG já foram publicados; sua reprodução é uma base de validação.

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
| `latex/proposta.tex` | Documento principal da proposta |
| `latex/capitulos_proposta/` | Texto da proposta em LaTeX |
| `latex/referencias/` | Bibliografia em BibLaTeX |
| `implementation_plan/` | Plano geral, roadmap e um Markdown por commit |
| `project_status.json` | Fonte do painel de estado do README |
| `scripts/` | Checagens, compilação, atualização do README e integridade |
| `output/pesquisa/` | Análise inicial e resultados das checagens |
| `output/pdf/<versão>/` | PDF imutável de cada marco |
| `releases/<versão>/` | Notas da versão e manifesto de integridade |

`latex/dissertacao.tex` será criado em C02. Os capítulos futuros não são apresentados como concluídos.
O Markdown em `output/pesquisa/` preserva a análise inicial; a fonte editorial do PDF passa a ser o LaTeX.

## Reproduzir a versão atual

As checagens preliminares exigem apenas Python 3.10 ou superior, sem bibliotecas adicionais.
Para o PDF: TeX Live completo ou MacTeX, `latexmk`, pdfLaTeX e Biber. A classe ITA fornecida carrega
BibLaTeX, glossaries, babel em português, geometria e outros pacotes; a configuração local usa também
Latin Modern, microtype, xurl, bookmark e booktabs. A versão inaugural foi compilada com TeX Live 2026.

```bash
python3 scripts/checagens_preliminares.py
make pdf
make check
```

`make pdf` compila uma cópia de conferência em `tmp/latex/<documento>/<documento>.pdf`, sem substituir o
PDF publicado. `make check` confere as checagens, o estado do README e os hashes do release atual.
A reprodução de conteúdo requer as mesmas fontes; equivalência binária entre diferentes versões
do TeX não é pressuposta. O manifesto registra a ferramenta utilizada e o SHA-256 do PDF publicado.
Para conferir uma versão anterior, faça checkout de sua tag e use o número correspondente em `VERSION`.

## Como manter o README e publicar os próximos PDFs

O painel acima é gerado por `scripts/update_readme.py` a partir de `project_status.json` e
`implementation_plan/roadmap.json`. Em cada marco, atualizar etapa, trabalhos concluídos, próxima
atividade e versão no JSON; executar o gerador. A verificação do release falha se o README estiver
inconsistente. As demais seções do README podem ser editadas diretamente.

```bash
python3 scripts/update_readme.py
make release VERSION=v0.2.0 DOCUMENT=dissertacao
```

O exemplo pressupõe que C02 foi concluído e que seus fontes, estado e notas de release já existem.
O [procedimento completo](implementation_plan/README.md#procedimento-de-fechamento-de-cada-marco)
inclui a inspeção visual, o commit, a tag e a conferência do download. O workflow do GitHub anexa o
**mesmo PDF que está no commit**, sem recompilá-lo. Versões `v0.*` são publicadas como pré-releases;
por isso o link “PDF mais recente” usa a tag explícita atual e não `/releases/latest`.

## Limites e procedência

Esta versão não demonstra ineditismo definitivo, detectabilidade, estabilidade não linear ou uma
nova restrição observacional. As checagens implementadas são cinemáticas; os testes estatísticos
fazem parte dos marcos futuros. A submissão e a aceitação de um artigo não estão realizadas nem garantidas.

O TG e os materiais de terceiros preservam seus direitos e atribuições. O template mantém sua licença
Apache 2.0 no próprio diretório; ela não é aplicada automaticamente ao TG ou ao texto da proposta.
Consulte [a procedência do template](templates/README.md) e as referências da proposta.
