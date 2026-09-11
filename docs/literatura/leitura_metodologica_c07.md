# Leitura dirigida para C07–C09

Corte do projeto: 10/09/2026. Os quatro PDFs estão disponíveis em `literature/papers/`; aqui foi feita leitura dirigida de seções pertinentes, não releitura integral. Catálogo, versões, licenças e hashes estão em `literature/catalog.json`.

| Fonte primária | Trecho consultado | Consequência para o protocolo |
|---|---|---|
| [Talts et al., arXiv:1804.06788v2](https://arxiv.org/abs/1804.06788v2) | pp.3–8: identidade de calibração e estatística de rank | Verdades devem ser sorteadas continuamente da priori e dados devem vir do experimento correspondente. Quadratura não pode fabricar calibração ao reutilizar a mesma prior discreta em geração e inferência. |
| [Modrák et al., arXiv:2211.02383v3](https://arxiv.org/abs/2211.02383v3), DOI10.1214/23-BA1404 | Resumo; pp.11–16: quantidades dependentes dos dados e log-verossimilhança | SBC marginal pode deixar passar uma inferência que devolve a priori. Incluir `log L(theta;y)` e o controle negativo de dados ignorados. |
| [Säilynoja et al., arXiv:2502.03279v2](https://arxiv.org/abs/2502.03279v2), DOI10.1007/s11222-026-10825-9 | pp.1–5: posterior SBC e exemplos de vieses que se cancelam no espaço da priori | SBC global não garante precisão para toda realização ou subregião. Preservar diagnósticos por realização; considerar posterior SBC para posteriores difíceis após validação do integrador. Não alegar que esse protocolo adicional foi executado. |
| [Modrák, Stroppel e Bürkner, arXiv:2508.11814v4](https://arxiv.org/abs/2508.11814v4), rev.27/07/2026 | Resumo; introdução e recomendações finais pp.24–25 | Validar razões de evidências separadamente. Os autores propõem SBC e calibração de predições binárias; a consistência dos quantis não basta para aprovar fatores de Bayes. |

A implementação atual usa PIT contínuo calculado por integração, sem sorteio categórico de posterior. Quando se usar um amostrador independente para verificação, ranks e autocorrelação exigem o tratamento próprio do método. A escolha por RQMC preserva tamanhos potência de2 e scrambles independentes; nenhuma regra de thinning foi importada de MCMC para Sobol.

As referências não transformam a família normal das estatísticas quadráticas em exata. A precisão numérica do posterior aproximado e a adequação da verossimilhança são perguntas distintas. A0_CN e o controle normal G são necessários para separar essas perguntas no experimento atual.
