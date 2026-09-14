# Apresentação do experimento com Codex

[PDF — revisão 7](../../output/pdf/experimento/experimento_codex_7.pdf) · [Fonte Beamer / LaTeX](experimento.tex) · [Roteiro de fala e fontes](roteiro.md)

**Uma dissertação gerada. Uma pesquisa que faz sentido?**

Apresentação para discussão na pós-graduação, em formato 16:9, com **12 slides principais e três de apoio**. O roteiro sugere **25 minutos**, com adaptações para 20 ou 30 minutos. Não exige conhecimento de ondas gravitacionais.

A revisão 7 começa pelo resultado atual: a primeira leitura especializada questionou clareza, coerência e utilidade, e o experimento não demonstrou uma dissertação adequada. Os slides distinguem execução e mérito, revisão entre modelos e avaliação humana, limites da busca bibliográfica e dois próximos experimentos possíveis: recuperação delimitada ou nova proposta com orientação científica. O slide 5 mantém volume e custos como medidas desta tentativa. Os três apoios preservam métricas, custos e links de comparação.

A fonte foi reescrita em Beamer, com composição tipográfica própria, diagrama em TikZ e tabelas LaTeX. O PDF é produzido diretamente pelo XeLaTeX. Textos, diagrama e tabelas permanecem editáveis na fonte.

## Fontes e atribuições

As métricas de código, análises e goal se referem à v1.0.0; os custos são as estimativas históricas, sem nova consulta de preços. A revisão agy está no commit `09b3584`. A reavaliação de 13/09/2026 usa uma síntese anonimizada do retorno especializado encaminhado pelo proponente, em `output/pdf/relatorio_experimento/reavaliacao_especialista.md`. É leitura inicial, não auditoria completa ou parecer de banca. A resposta posterior do Gemini não é tomada como validação independente. Os produtos científicos e as revisões 4, 5 e 6 desta apresentação permanecem preservados.

Flavio Ribeiro aparece como apresentador. As atribuições originais das capas, incluindo nomes fictícios, permanecem nas imagens. A apresentação não cita participantes de conversas privadas nem reproduz essas conversas.

## Compilação

Na raiz do repositório, com Python 3 e uma distribuição TeX que contenha XeLaTeX, Beamer, TikZ, TeX Gyre, `fontspec`, `babel`, `booktabs` e `latexmk`:

```sh
bash presentations/experimento/build.sh
```

As fontes TeX Gyre Heros e Pagella são carregadas pelos arquivos da distribuição TeX, sem depender das fontes instaladas no sistema operacional. A compilação não requer PowerPoint, LibreOffice ou bibliotecas de geração de slides.

Editar `experimento.tex` para alterar o conteúdo e a composição. Editar `timing.json` para atualizar a fala, as fontes ou os tempos. O script de compilação executa `gerar_roteiro.py`, que sincroniza `roteiro.md` e `notas.tex`. As notas ficam ocultas no PDF da audiência.

Os arquivos auxiliares de compilação ficam em `tmp/presentations/experimento/beamer/`. O PDF final é copiado para `output/pdf/experimento/experimento_codex.pdf` e `output/pdf/experimento/experimento_codex_7.pdf`. Os dois arquivos são idênticos. O nome com a revisão distingue esta entrega das cópias anteriores.

## Verificação desta entrega

Os 15 slides foram recompilados e renderizados para revisão visual do conjunto; os slides alterados foram também inspecionados em tamanho ampliado. O manifesto registra hashes e a distinção em relação à revisão 6. Tempos de fala são sugestões, sem ensaio cronometrado.
