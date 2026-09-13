# Apresentação do experimento com Codex

[PDF](../../output/pdf/experimento/experimento_codex.pdf) · [PowerPoint editável](experimento_codex.pptx) · [Roteiro de fala e fontes](roteiro.md)

São 21 slides principais e dois de apoio, em formato 16:9. O roteiro sugere 26 minutos e 35 segundos e explica adaptações para 20 ou 30 minutos. A apresentação aborda a delegação da pesquisa, busca de novidade, execução, correções, os dois pareceres do Gemini estimativas de custo e questões de formação e avaliação. Não exige conhecimento de ondas gravitacionais.

## Fontes e versões

As métricas se referem à pesquisa na tag v1.0.0. A revisão posterior do artigo está no commit `26ae3ac`. As fontes de cada slide aparecem no roteiro e nas notas do PowerPoint. As três imagens em `assets/` são reproduções da primeira página do TG, da dissertação v1.0.0 e do manuscrito revisado, usadas como evidência documental. As atribuições originais permanecem nas imagens. Conversas privadas de terceiros não foram reproduzidas.

## Compilação

`build.mjs` cria os objetos editáveis com `@oai/artifact-tool`. A apresentação contém um gráfico nativo com planilha incorporada e duas tabelas nativas. O PDF é exportado pelo LibreOffice.

No ambiente de criação, indicar os caminhos de Node.js, Python, LibreOffice, do pacote `@oai/artifact-tool` e da skill de apresentações do Codex:

```sh
export PRESENTATIONS_SKILL=/caminho/para/skills/presentations
export RUNTIME_NODE_MODULES=/caminho/para/node_modules
export NODE_EXECUTABLE=/caminho/para/node
export PYTHON_EXECUTABLE=/caminho/para/python3
export SOFFICE_EXECUTABLE=/caminho/para/soffice
bash presentations/experimento/build.sh
```

Os arquivos temporários, renders e recibos de validação ficam em `tmp/presentations/experimento/`. A compilação requer a skill e o runtime indicados; o PDF e o PowerPoint distribuídos podem ser abertos sem eles. Após alterar conteúdo, sincronizar o roteiro e `timing.json` com as notas geradas e conferir novamente todos os slides. A recompilação pode alterar hashes por metadados e versões do renderizador.

## Verificação desta entrega

O pacote PowerPoint passou nas verificações de integridade, geometria, fontes e estrutura editável de gráfico e tabelas, além da reimportação pelo artifact-tool. Os 23 slides do PDF exportado pelo LibreOffice foram renderizados e inspecionados individualmente. Não foi feito teste de abertura no Microsoft PowerPoint. O manifesto registra os hashes desta entrega e das páginas documentais de origem.
