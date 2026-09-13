# TG do Wayne para não especialistas

Apresentação Beamer 16:9 para público com noções básicas de engenharia, sem exigir conhecimento prévio de relatividade. São **28 slides principais e dois de apoio**, com roteiro planejado para 50 minutos. A duração inclui pausas nos exemplos; a discussão final fica fora desse tempo.

- [Apresentação em PDF](../../output/pdf/didatica/tg_wayne_para_nao_especialistas.pdf)
- [Fonte LaTeX](apresentacao.tex)
- [Roteiro do apresentador](roteiro.md)

## Percurso didático

1. Ondas, frequência, deformação e polarização por analogias e desenhos.
2. **TG do Wayne for dummies** (slides 9–18): problema original, hipóteses, cálculo simbólico em Maple, padrões previstos e conclusão histórica sobre baixas frequências.
3. Da previsão à medição: pulsares, redes de sensores, compressão e calibração.
4. Resultados da pesquisa posterior em linguagem simples, separados das contribuições do TG.

Os resultados históricos foram conferidos no `TG_Wayne.pdf`, especialmente nos capítulos 4–6 e no apêndice A. As analogias são identificadas como ilustrações. A curva de dispersão é analítica; as contagens de cobertura e os contrastes condicionais vêm dos resultados já existentes da dissertação. Não foram feitas novas simulações.

## Compilar

Na raiz do repositório, com LaTeX/Beamer, TikZ e latexmk instalados:

```sh
bash presentations/didatica/build.sh
```

A figura PDF necessária está incluída na pasta. Para regenerá-la, use Python com NumPy e Matplotlib:

```sh
python3 presentations/didatica/gerar_figura.py
```

O PDF foi compilado e os 30 slides foram conferidos visualmente. A apresentação técnica da defesa permanece disponível separadamente.
