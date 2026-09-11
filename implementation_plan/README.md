# Plano de execução por commits e releases de PDF

Este plano transforma a proposta de mestrado em uma sequência de **13 marcos**. Cada marco é um
commit que inclui o texto atualizado, os artefatos científicos pertinentes, um PDF cumulativo e
seu manifesto. Cada commit de marco recebe uma tag e um GitHub Release. O estado efetivamente
executado é mantido no README da raiz e em `project_status.json`; a tabela abaixo descreve
a sequência de marcos, sem transformar etapas futuras em resultados já produzidos.

## Regra de acompanhamento

O [README da raiz](../README.md) é o painel público do estado atual. Deve mostrar: última etapa concluída,
trabalho em andamento, próxima etapa, entregas efetivamente executadas, roadmap e link direto para
o PDF mais recente. `project_status.json` alimenta esse painel; `roadmap.json` contém os marcos e versões.
O script `update_readme.py` gera o painel e `verify_release.py` bloqueia inconsistências na publicação.

Durante um marco, o texto e os experimentos podem ser trabalhados localmente. O commit só ocorre quando
os critérios daquele marco estiverem satisfeitos. O estado publicado corresponde sempre à última entrega
validada; ao fechar o marco, o README explica o que foi concluído e o próximo trabalho. Se for necessário
publicar um estado parcial, criar um marco explícito de acompanhamento com novo commit e PDF, sem
marcar o capítulo como concluído.

## Sequência de marcos

| Commit | Entrega cumulativa | Tag | Janela | Descrição detalhada |
|---|---|---|---|---|
| C01 | Proposta de pesquisa, plano e repositório | `v0.1.0` | Preparação, antes do mês 1 | [Plano](commits/C01_proposta_e_repositorio.md) |
| C02 | Introdução da dissertação concluída | `v0.2.0` | 1 | [Plano](commits/C02_introducao.md) |
| C03 | Revisão bibliográfica e originalidade | `v0.3.0` | 1–2 | [Plano](commits/C03_revisao_bibliografica.md) |
| C04 | Fundamentos teóricos e reprodução do TG | `v0.4.0` | 3–5 | [Plano](commits/C04_fundamentos_e_tg.md) |
| C05 | Resposta de PTA e correlações validadas | `v0.5.0` | 6–8 | [Plano](commits/C05_resposta_pta.md) |
| C06 | Metodologia de simulação e dados sintéticos | `v0.6.0` | 9–10 | [Plano](commits/C06_simulacoes.md) |
| C07 | Inferência de referência e calibração | `v0.7.0` | 10–12 | [Plano](commits/C07_inferencia_validada.md) |
| C08 | Resultados sobre compressão em frequência | `v0.8.0` | 12–14 | [Plano](commits/C08_compressao_frequencia.md) |
| C09 | Robustez a prioris, ruído e covariâncias | `v0.9.0` | 14–15 | [Plano](commits/C09_prioris_covariancias.md) |
| C10 | Extensão com helicidade zero vinculada | `v0.10.0` | 16–18 | [Plano](commits/C10_helicidade_zero.md) |
| C11 | Aplicação pública ou extensão simulada | `v0.11.0` | 19–20 | [Plano](commits/C11_aplicacao.md) |
| C12 | Discussão, conclusões e manuscrito | `v0.12.0` | 20–22 | [Plano](commits/C12_discussao_artigo.md) |
| C13 | Auditoria final e dissertação consolidada | `v1.0.0` | 22–24 | [Plano](commits/C13_auditoria_final.md) |

As janelas representam meses desde o início acadêmico. A preparação C01 antecede esse início.
Há sobreposição entre redação e pesquisa; a ordem dos commits segue as dependências e os critérios de
aceitação. O prazo não substitui validação científica.

## Estrutura do PDF ao longo do projeto

- **C01:** proposta de pesquisa autônoma, com contexto, síntese bibliográfica, objetivos, metodologia,
  validação prevista, checagens preliminares, cronograma e referências.
- **C02 em diante:** dissertação cumulativa, iniciada por `latex/dissertacao.tex`. Cada versão mantém os
  capítulos já concluídos e incorpora a nova entrega. Um quadro inicial informa o estado de cada capítulo.
- **C12:** dissertação com texto científico integral e manuscrito de artigo disponível para revisão.
- **C13:** versão consolidada após auditoria, com metadados acadêmicos definitivos e requisitos institucionais conferidos.

Capítulos ainda não escritos não terão texto de exemplo, resultados fictícios ou marcação de conclusão.
Resultados nulos e reduções de escopo podem constituir entregas válidas quando documentados e sustentados.
C10 e C11 têm decisões condicionais descritas em seus planos; a decisão e o título do marco deverão refletir
honestamente o que tiver sido obtido.

## Procedimento de fechamento de cada marco

1. Abrir o Markdown do marco e concluir tarefas, produtos e critérios científicos. Registrar comandos,
   configurações, sementes, dados e resultados relevantes; não versionar grandes caches ou credenciais.
2. Atualizar os capítulos e seu quadro de estado. Atualizar `project_status.json`, inclusive trabalho
   concluído, etapa, versão, documento, caminho do PDF, data e próxima atividade. Se o recorte mudou,
   justificar a alteração e atualizar também os planos futuros.
3. Escrever `releases/<versão>/RELEASE_NOTES.md` com conteúdo do PDF, mudanças, validação executada,
   limitações e próxima etapa. Nunca chamar de executado um teste apenas planejado.
4. Executar `python3 scripts/update_readme.py` e `make release VERSION=<versão> DOCUMENT=<documento>`.
   Usar `DOCUMENT=proposta` em C01 e `DOCUMENT=dissertacao` depois. O comando cria o PDF e os hashes.
5. Renderizar **todas as páginas** com Poppler e revisar capa, sumário, tabelas, equações, referências,
   cabeçalhos, rodapés e quebras. Corrigir problemas e repetir a geração até a versão estar pronta.
6. Após qualquer mudança em uma entrada do manifesto, gerar novamente o release. Executar
   `python3 scripts/verify_release.py <versão>` e os testes científicos pertinentes. Rever `git diff` e os
   arquivos preparados antes do commit.
7. Fazer um único commit de marco com fontes, documentação, resultados necessários, PDF e manifesto.
   Criar tag anotada com o mesmo número. Enviar branch e tag sem reescrever histórico.
8. Conferir o workflow **Publicar PDF do marco**, abrir o release e baixar o PDF. Comparar seu SHA-256
   com `manifest.json`. A tag deve apontar para o commit que contém exatamente esse PDF.

Exemplo para C02, somente depois de cumprir os passos anteriores:

```bash
git add README.md project_status.json implementation_plan latex scripts tests configs results figures releases output/pdf
# Incluir apenas os caminhos existentes e pertinentes ao marco; rever git diff --cached.
git commit -m "docs: conclui introducao da dissertacao"
git tag -a v0.2.0 -m "C02: introducao da dissertacao"
git push --atomic origin main v0.2.0
```

A lista do `git add` é ilustrativa: alguns diretórios só existirão mais adiante. Não enviar chaves,
tokens ou dados cujo uso/publicação não estejam autorizados. O manifesto de cada release vincula
fontes e PDF por hashes; a tag vincula o conjunto ao commit, evitando um ciclo de autorreferência
entre hash do commit e conteúdo do próprio commit.

## Automação e integridade

O workflow `.github/workflows/release.yml` é acionado por tags `v*`. Ele verifica as checagens
preliminares, a consistência do README e o manifesto, e usa o token do próprio Actions para criar
o release com o PDF já versionado. Não é necessário token pessoal no projeto. O GitHub precisa
permitir execução de Actions com escrita de conteúdo para esse workflow.

O build local usa pdfLaTeX, latexmk e Biber; o CI de publicação confere integridade, mas não substitui
os testes científicos nem a inspeção visual. A publicação exige ambos. Para um release anterior,
verificar no checkout de sua tag, pois as fontes na branch principal evoluem.

## Correções e mudanças no plano

Antes do commit, corrigir livremente até satisfazer os critérios. Depois de publicado, **não alterar
nem mover a tag, não substituir o PDF e não usar push forçado**. Criar um novo marco de correção,
com Markdown próprio (por exemplo, `C03a_correcao_bibliografia.md`), commit, versão patch
(por exemplo, `v0.3.1`), novo PDF, notas e manifesto. Inserir esse marco no roadmap e atualizar o estado.
Assim, até um commit corretivo preserva a regra de uma entrega de PDF por commit.

A sequência de 13 marcos é a linha de base, não um impedimento a mudanças justificadas. Reordenamentos,
reduções de escopo ou uma lacuna já resolvida na literatura devem ser registrados na primeira versão
afetada. Nenhum marco será marcado como concluído apenas porque seu prazo chegou.

## Definição de conclusão do projeto

Os resultados centrais devem ser reproduzíveis, as conclusões devem responder à pergunta de pesquisa
e a dissertação deve estar integralmente revisada. O artigo é um produto planejado; sua submissão,
aceitação e a defesa têm estados próprios. A tag `v1.0.0` não certifica aprovação institucional.
