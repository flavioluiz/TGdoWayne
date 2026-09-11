# Auditoria bibliográfica final dirigida — 11/09/2026

**Resultado:** seis complementos primários recomendados para a bibliografia/matriz, com PDFs locais baixados e verificados: 86 páginas e 10.731.866 bytes. São antecedentes ausentes do catálogo de 31 artigos, não seis descobertas publicadas hoje. A consulta dirigida não encontrou um novo estudo PTA massivo que já execute a comparação específica A0/A/B/C do projeto. Isso é resultado limitado da busca, não prova de prioridade ou inexistência.

O catálogo, a atualização computacional C07, a leitura metodológica, a matriz de 17 trabalhos, o protocolo de busca e o plano C08 foram confrontados. Seus hashes estão em `input_sources.json`. Não houve alteração de ROOT, execução dos códigos dos artigos, integração de terceiros no Git ou alteração do protocolo científico em andamento.

## Seis entradas prioritárias

| Entrada proposta | Contribuição concreta e localizadores da leitura dirigida | Consequência para o projeto |
|---|---|---|
| [Alsing–Wandelt, 1712.00012v2](https://arxiv.org/abs/1712.00012v2), MNRAS Letters 476, L60–L64 (2018) | PDF pp.2–5: expansão em ponto fiducial, Eqs.4–8 e score gaussiano Eq.17 com termos de média e covariância; Seção5 explicita modos de falha. | Antecedente para Fisher local e compressão por score. “Massive” no título significa redução de dados; não gravidade massiva. Não usar preservação de Fisher como prova de posterior integralmente preservada. |
| [Pollard, 1107.3797v2](https://arxiv.org/abs/1107.3797v2), preprint consultado de 2012 | PDF pp.1–3 e6: exemplo de estatística insuficiente que preserva Fisher; Teorema7 dá score comprimido como esperança condicional sob diferenciabilidade em média quadrática. | Base rigorosa para a identidade de perda de Fisher e para distinguir informação local de suficiência global. O registro editorial não foi confirmado na fonte primária nesta busca; o BibTeX permanece como preprint, sem DOI editorial inferido. |
| [Gersbach et al., 2406.11954v2](https://arxiv.org/abs/2406.11954v2), PRD111,023027 (2025) | PDF pp.7–8,12,14–15: PFOS, Eqs.26–32, covariância entre pares, normalização broadband/narrowband, P–P de 100 simulações e comparação com OS broadband. A normalização usa estimativas CURN; independência entre frequências é uma hipótese examinada, não uma identidade geral. | Frequência explícita, covariância de pares e calibração já são antecedentes PTA diretos. Os testes não são SBC conjunta de massa+quatro nuisances nem a comparação A0/A/B/C. |
| [Gersbach et al., 2509.07090v1](https://arxiv.org/abs/2509.07090v1), [PRD113,103031,19/05/2026](https://journals.aps.org/prd/abstract/10.1103/d55k-75p9) | PDF pp.5–7,9–10,16: combina PFOS, covariância de pares e distribuição nula incluindo variância cósmica; busca anisotropia em frequências individuais. | Antecedente recente de benefício de conservar frequência e de calibração da detecção. Não oferece limite de massa nem aprovação da família gaussiana A/B no experimento físico CN. |
| [Wang–Zhao, 2307.04680v4](https://arxiv.org/abs/2307.04680v4), PRD109,L061502 (2024) | PDF pp.2–5: Eq.6 ajusta correlações angulares com erros diagonais; priori uniforme em velocidade em [0,01,1]; Eq.2 converte para massa. A p.4 usa f=(15 anos)⁻¹ para NANOGrav e f=(3,4 anos)⁻¹ para CPTA. Eq.9 acrescenta monopolo/dipolo; Eq.12 é forecast Fisher. | Benchmark direto para f_ref, suporte e prioris. A posterior de massa herda a priori em velocidade. Não comparar seus limites com C07 como se dados, frequências e prioris fossem iguais; monopolo/dipolo isoladamente tampouco é novidade. |
| [Crisostomi et al., 2506.13866v1](https://arxiv.org/abs/2506.13866v1), preprint de 2025 | PDF pp.1–4 e9: Eqs.10–11 distinguem covariância Fourier não diagonal da aproximação; Eq.17 usa redução de posto e Eq.20 propõe avaliação FFT/interpolação. Controles Matérn e PTA simulado mostram diferenças de posterior. | A janela finita pode correlacionar frequências. Isso limita extrapolar C07, cujo gerador define coeficientes independentes, para TOAs reais. É outro problema que zerar covariâncias entre componentes do vetor angular B10. Não exige mudar a campanha em curso. |

As contagens são as dos PDFs efetivamente baixados: **6,12,24,23,7,14 páginas**, respectivamente. Comentários do arXiv podem informar outra contagem editorial. O download não equivale à leitura integral: `reading_status` delimita páginas/seções consultadas.

## Código primário associado

Foi inspecionado, sem execução, `compute_PFOS` em [DEFIANT/core.py, commit 7c523e45dc0c27326d24635da5e6686fa3e03b9c](https://github.com/GersbachKa/defiant/blob/7c523e45dc0c27326d24635da5e6686fa3e03b9c/defiant/core.py#L830). A implementação conserva o índice de frequência, oferece covariância entre pares e distingue normalização narrowband. Isso reforça que esses ingredientes já têm implementação pública. Não foi auditado todo o repositório nem certificada sua reprodução de resultados. Snapshots de README/código e metadados de commit permanecem em `metadata/`, com hashes em `supplemental_metadata_log.json`.

Os artigos também indicam PTAfast/Cobaya, Enterprise/Discovery e MAPS; citar essa indicação não significa que os executáveis tenham sido instalados, verificados ou executados nesta auditoria.

## Identidades que C08 pode explicitar, sem nova campanha

Esta é uma dedução para o contrato do projeto, apoiada pelo resultado regular de Pollard, não uma contribuição inédita. Se `Y=W X` é compressão determinística **fixa, independente de θ**, e as famílias completas/comprimidas são as distribuições corretas do mesmo experimento, então

\[
s_Y(Y)=\mathbb E_\theta[s_X(X)\mid Y],\qquad
I_X-I_Y=\mathbb E_\theta\{\operatorname{Cov}_\theta[s_X\mid Y]\}\succeq0.
\]

É preciso declarar regularidade e o ponto interior avaliado. Fronteira u=0, mudança de suporte ou derivada singular perto do limiar exigem tratamento próprio. Se W depende de estimativas obtidas dos próprios dados, essa identidade não deve ser aplicada omitindo o procedimento de seleção de W.

Para o controle gaussiano pareado do projeto, `μ_B=W μ_A` e `Σ_B=W Σ_A Wᵀ` definem a família comprimida exata. A expressão de Fisher inclui derivadas da média **e** da covariância; a norma `ΔμᵀΣ⁻¹Δμ` sozinha não resume uma aproximação que altera também Σ. Para comparar C com B no mesmo espaço, é necessário conservar o termo de determinante e as diferenças de covariância na divergência gaussiana.

Com a mesma priori própria, a identidade de informação mútua da cadeia `θ→X→Y` dá

\[
I(\theta;X)-I(\theta;Y)
=\mathbb E_X D_{\rm KL}\{p(\theta\mid X)\Vert p(\theta\mid Y(X))\}\ge0.
\]

Ela é uma média preditiva, não uma ordenação da largura/limite unilateral em cada dado. Comparar A0 físico com a aproximação gaussiana A_CN muda a família probabilística: não se pode interpretar esse contraste usando apenas a desigualdade de compressão. A separação A0–A, A–B e B–C já prevista continua necessária. Não transformar evidências absolutas em espaços de dados distintos em um fator de Bayes.

A priori de Wang–Zhao permite uma nota analítica útil, sem novo cenário: para β uniforme em [β_min,1] e `u=√(1−β²)`, a densidade induzida é

\[
\pi_u(u)=\frac{u}{(1-\beta_{\min})\sqrt{1-u^2}},\quad
0\le u\le\sqrt{1-\beta_{\min}^2}.
\]

Ela não é uniforme em u ou u². Aqui β_min=0,01; a relação é uma mudança de variável, não reprodução do limite publicado.

## Atualização de 11/09 e resultado negativo delimitado

As cópias diretas das seis listagens arXiv, salvas nesta auditoria, exibem **11/09/2026**: astro-ph.CO44, astro-ph.HE35, astro-ph.IM30, gr-qc65, stat.CO5 e stat.ME38. Total217 entradas,195 IDs distintos após duplicações entre categorias. Foram triados títulos de todas e resumos de itens potencialmente ligados ao núcleo; não se afirma leitura integral das195 obras. Uma resposta inicial do buscador para stat.CO ainda mostrava10/09; a cópia direta posterior atualizou para11/09. A evidência final usa os HTMLs locais, não aquela resposta em cache.

Os oito registros centrais verificados continuam nas versões do catálogo: Zhao2607.14790v1; Han2604.23384v2; Choi2507.02059v2; Cordes2407.04464v2; Franciolini2505.24695v1; Dwivedi2608.13991v1; Liang2108.05344v3; Owen2608.17143v1. Históricos completos estão em `version_checks.json`.

Uma atualização próxima merece **registro de triagem**, sem virar um sétimo PDF/candidato deste pacote: [Sala–Vitale2507.20846](https://arxiv.org/abs/2507.20846), [PRD114,062005,09/09/2026](https://journals.aps.org/prd/abstract/10.1103/hwmv-xt1k). O registro direto apresenta v3 em10/09/2026 às07:48UTC, listado em11/09, enquanto a resposta inicial do buscador ainda mostrava v2. O resumo trata espectros/Wishart e poucos periodogramas em LISA Pathfinder. O escopo das fórmulas para matrizes singulares e o regime M=1 do nosso gerador **não foram verificados**, logo não se transfere a fórmula fechada nem se declara que resolve a inferência PTA. Não foi baixado seu PDF.

Outras exclusões dirigidas: [EDD2609.11177](https://arxiv.org/abs/2609.11177) trata backend instrumental. [eHMC1810.04449](https://arxiv.org/abs/1810.04449), novamente listado, calibra parâmetros de leapfrog; não justifica trocar agora o SNIS validado. [Beyond the BLUE2609.10475](https://arxiv.org/abs/2609.10475) aplica Fisher a amplitude em mapas mm/submm; foi excluído por menor relevância que os fundamentos já selecionados. [2608.18365](https://arxiv.org/abs/2608.18365) trata sensibilidades/HMC de problemas inversos rugosos; não é análise PTA. Esses itens foram triados por título/resumo, sem leitura integral ou adoção metodológica.

A busca não cobriu exaustivamente todas as bases de citações, idiomas, artigos ainda não indexados ou todo o dia civil futuro. Seus resultados não autorizam afirmar “primeiro estudo”. As seis adições tornam a alegação de contribuição mais restrita: avaliação reprodutível do erro introduzido por uma compressão e por f_ref, com controles probabilísticos e prioris declarados, no domínio físico validado.

## Entrega e integração

- `catalog_additions.json`: seis registros com URL PDF versionada, data, licença verificada, SHA256, bytes, páginas e leitura real. O `local_path` aponta para o arquivo que existe; o campo `suggested_local_path_after_integration` não afirma que houve cópia.
- `bibliografia_additions.bib` e `matrix_additions.csv`: somente metadados/texto próprios para revisão e integração por ROOT.
- `search_log.json`, `new_listing_inventory.json`, `version_checks.json`: protocolo, escopo e evidências de revisão.
- `download_log.json`, `supplemental_metadata_log.json`: êxito dos downloads e snapshots.
- `papers/`, `text/`, `metadata/`: acervo local de consulta, **não publicar no Git neste pacote**.

Licenças verificadas no registro de cada versão: Alsing/Pollard/Crisostomi usam licença não exclusiva do arXiv; Wang–Zhao, CC BY-NC-ND4.0; os dois Gersbach, CC BY4.0. A licença da cópia arXiv não é presumida como licença editorial. Nenhum PDF foi redistribuído. Todos os seis downloads foram concluídos; a primeira tentativa sem acesso de rede falhou por DNS e a execução autorizada posterior conseguiu acesso normal aos endereços públicos.
