# Apresentação do experimento com Codex

[PDF](../../output/pdf/experimento/experimento_codex.pdf) · [Fonte Beamer / LaTeX](experimento.tex) · [Roteiro de fala e fontes](roteiro.md)

**Uma dissertação pronta. Um pesquisador formado?**

Apresentação para discussão na pós-graduação, em formato 16:9, com **12 slides principais e três de apoio**. O roteiro sugere **25 minutos**, com adaptações para 20 ou 30 minutos. Não exige conhecimento de ondas gravitacionais.

A narrativa começa pela pergunta sobre formação, apresenta o desafio e as decisões do agente, examina as correções e a revisão pelo Gemini e discute contribuição científica, evidência e avaliação. O encerramento propõe questões sobre originalidade, compreensão e delegação da pesquisa. Métricas e hipóteses de custo ficam detalhadas no apoio.

A fonte foi reescrita em Beamer, com composição tipográfica própria, diagrama em TikZ e tabelas LaTeX. O PDF é produzido diretamente pelo XeLaTeX. Textos, diagrama e tabelas permanecem editáveis na fonte.

## Fontes e atribuições

As métricas se referem à pesquisa na tag v1.0.0. A revisão posterior do artigo está no commit `26ae3ac`. As fontes de cada slide aparecem no roteiro e nas notas Beamer. As imagens em `assets/` reproduzem a primeira página do TG, da dissertação v1.0.0 e do manuscrito revisado, como evidência documental.

Flavio Ribeiro aparece como apresentador. As atribuições originais das capas, incluindo nomes fictícios, permanecem nas imagens. A apresentação não cita participantes de conversas privadas nem reproduz essas conversas.

## Compilação

Na raiz do repositório, com Python 3 e uma distribuição TeX que contenha XeLaTeX, Beamer, TikZ, TeX Gyre, `fontspec`, `babel`, `booktabs` e `latexmk`:

```sh
bash presentations/experimento/build.sh
```

As fontes TeX Gyre Heros e Pagella são carregadas pelos arquivos da distribuição TeX, sem depender das fontes instaladas no sistema operacional. A compilação não requer PowerPoint, LibreOffice ou bibliotecas de geração de slides.

Editar `experimento.tex` para alterar o conteúdo e a composição. Editar `timing.json` para atualizar a fala, as fontes ou os tempos. O script de compilação executa `gerar_roteiro.py`, que sincroniza `roteiro.md` e `notas.tex`. As notas ficam ocultas no PDF da audiência.

Os arquivos auxiliares de compilação ficam em `tmp/presentations/experimento/beamer/`. O PDF final é copiado para `output/pdf/experimento/experimento_codex.pdf`.

## Verificação desta entrega

Os 15 slides do PDF compilado foram renderizados e inspecionados individualmente. O manifesto registra os hashes do PDF, das fontes e das páginas documentais de origem. Tempos de fala são sugestões, sem ensaio cronometrado.
