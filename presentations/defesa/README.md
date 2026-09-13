# Defesa de mestrado — 50 minutos

Apresentação Beamer em formato 16:9, com **32 slides principais e 7 slides de apoio** para a discussão com a banca. O roteiro distribui 50 minutos entre os slides principais; perguntas ficam fora desse tempo. A duração efetiva depende do ensaio.

- [PDF da apresentação](../../output/pdf/defesa/defesa_mestrado_50min.pdf)
- [Fonte Beamer](defesa.tex)
- [Roteiro de fala, com tempos e transições](roteiro_50min.md)

A exposição percorre a resposta física de PTAs, o desenho das comparações e os resultados de calibração, compressão, dependência da priori, helicidade zero e ajuste de timing. O material de apoio reúne convenções, fundamentos não lineares, marginalização e referências.

Os gráficos foram redesenhados a partir dos resultados da dissertação concluída. As curvas de dispersão e de posterior igual à priori são ilustrações analíticas identificadas nos slides. Não foram executadas novas inferências para a apresentação. As legendas distinguem incerteza numérica, erro Monte Carlo e alcance condicional dos contrastes.

## Compilação

Na raiz do repositório, com uma distribuição TeX que inclua Beamer, TikZ, Latin Modern e `latexmk`:

```sh
bash presentations/defesa/build.sh
```

As figuras PDF estão incluídas. A compilação utiliza também a figura de geometria em `figures/aplicacao/geometria_academica.pdf`; mantenha a estrutura do repositório.

Para regenerar figuras e roteiro, com Python, NumPy e Matplotlib:

```sh
python3 presentations/defesa/gerar_figuras.py
python3 presentations/defesa/gerar_roteiro.py
bash presentations/defesa/build.sh
```

`figures/sources.json` identifica as fontes dos gráficos; `timing.json` contém os tempos por slide. A apresentação é um material complementar e não modifica o release da dissertação.
