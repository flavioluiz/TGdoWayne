# Apresentação do experimento com Codex

[PDF — revisão 6](../../output/pdf/experimento/experimento_codex_6.pdf) · [Fonte Beamer / LaTeX](experimento.tex) · [Roteiro de fala e fontes](roteiro.md)

**Uma dissertação pronta. Um pesquisador formado?**

Apresentação para discussão na pós-graduação, em formato 16:9, com **12 slides principais e três de apoio**. O roteiro sugere **25 minutos**, com adaptações para 20 ou 30 minutos. Não exige conhecimento de ondas gravitacionais.

A narrativa começa pela pergunta sobre formação, apresenta o desafio e as decisões do agente, examina as correções, os pareceres do Gemini e a reescrita direta pelo agy e discute contribuição científica, evidência e avaliação. O encerramento propõe questões sobre originalidade, compreensão e delegação da pesquisa. O slide 5 destaca código, análises, páginas, tempo e custos. As definições das métricas, as hipóteses de custo e quatro links para comparar os PDFs do Codex e do Gemini ficam no apoio.

A fonte foi reescrita em Beamer, com composição tipográfica própria, diagrama em TikZ e tabelas LaTeX. O PDF é produzido diretamente pelo XeLaTeX. Textos, diagrama e tabelas permanecem editáveis na fonte.

## Fontes e atribuições

As métricas de código, análises e goal se referem à pesquisa na tag v1.0.0. A revisão posterior do artigo pelo Codex está no commit `26ae3ac`; a revisão direta pelo agy / Gemini 3.8 Flash (High), no commit `09b3584`, tag v1.1.0. O slide 5 mostra a dissertação atual com 170 páginas, identificando as 167 do goal. O slide 7 compara os papéis dos modelos e a mudança de narrativa. Os custos continuam excluindo Gemini e agy. As fontes de cada slide aparecem no roteiro e nas notas Beamer. A capa do TG permanece como evidência documental. O apoio 15 traz links para as duas versões da dissertação e do artigo, permitindo comparar as narrativas mais defensiva e mais afirmativa deste caso. As imagens dos produtos permanecem arquivadas em assets. As revisões 4 e 5 permanecem preservadas como PDFs separados.

Flavio Ribeiro aparece como apresentador. As atribuições originais das capas, incluindo nomes fictícios, permanecem nas imagens. A apresentação não cita participantes de conversas privadas nem reproduz essas conversas.

## Compilação

Na raiz do repositório, com Python 3 e uma distribuição TeX que contenha XeLaTeX, Beamer, TikZ, TeX Gyre, `fontspec`, `babel`, `booktabs` e `latexmk`:

```sh
bash presentations/experimento/build.sh
```

As fontes TeX Gyre Heros e Pagella são carregadas pelos arquivos da distribuição TeX, sem depender das fontes instaladas no sistema operacional. A compilação não requer PowerPoint, LibreOffice ou bibliotecas de geração de slides.

Editar `experimento.tex` para alterar o conteúdo e a composição. Editar `timing.json` para atualizar a fala, as fontes ou os tempos. O script de compilação executa `gerar_roteiro.py`, que sincroniza `roteiro.md` e `notas.tex`. As notas ficam ocultas no PDF da audiência.

Os arquivos auxiliares de compilação ficam em `tmp/presentations/experimento/beamer/`. O PDF final é copiado para `output/pdf/experimento/experimento_codex.pdf` e `output/pdf/experimento/experimento_codex_6.pdf`. Os dois arquivos são idênticos. O nome com a revisão distingue esta entrega das cópias anteriores.

## Verificação desta entrega

Os 15 slides foram renderizados para revisão visual do conjunto; os slides com as novas métricas e a interação com o agy foram também inspecionados em tamanho ampliado. Nesta revisão, os slides 7 e 15 foram novamente renderizados e conferidos. O PDF tem conteúdo diferente da revisão 5. O manifesto registra os hashes do PDF, das fontes e das páginas documentais de origem. Tempos de fala são sugestões, sem ensaio cronometrado.
