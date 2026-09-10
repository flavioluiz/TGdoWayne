# v0.6.0 — C06: simulador e momentos validados

PDF cumulativo de 56 páginas com cinco capítulos concluídos. O novo capítulo define o experimento
periódico de Fourier, as unidades do espectro, o sinal tensorial e os ruídos branco
e vermelho. Estimadores angulares preservam partes reais e imaginárias; a compressão
fixa propaga médias e covariâncias. O contrato distingue A0, A, B, C_full, C_beta e
um controle normal com os mesmos momentos dos estimadores físicos.

Onze testes passaram. Três campanhas completas, com 131072 realizações físicas e
controles pareados cada, recuperaram os momentos no caso massivo, em GR e sem sinal.
As maiores discrepâncias foram 3,502, 3,936 e 3,187 erros-padrão Monte Carlo, abaixo
do limiar empírico predefinido de seis. Foram auditadas 605 avaliações de pares ORF.
A amostra pequena de cada campanha foi regenerada pela semente; dados, fontes e
configurações possuem hashes. As evidências e testes de C04/C05 são preservados.

A assimetria e a curtose físicas permanecem após a compressão. Concordância de
momentos não valida uma likelihood gaussiana para estimadores quadráticos. Não há
posterior, SBC, cobertura ou restrição observacional nesta etapa. O desenho prospectivo
fixa cinco parâmetros, geometria e extensões para C07. A janela atual é periódica,
sem ajuste de temporização ou representação de dados reais de uma PTA.

O acervo chegou a 26 PDFs locais, com quatro referências metodológicas adicionais.
Catálogo e receita de download estão versionados; artigos de terceiros permanecem
em literature/papers/, fora do Git. README, planos, capítulo e manifesto refletem C06.

A figura vetorial usa 65536 sorteios adicionais e distingue a distribuição física
do controle normal. Todas as 56 páginas foram renderizadas e inspecionadas, sem
referências indefinidas ou caixas de texto excedendo as margens. Consulte
`docs/validacao_v0.6.0.md` para verificações e limites.
