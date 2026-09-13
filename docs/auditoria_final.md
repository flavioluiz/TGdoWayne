# Auditoria final — C13

A reprodução científica e a revisão editorial foram concluídas. Os resultados
abaixo distinguem os cálculos reexecutados dos insumos reutilizados. A publicação
é verificável pelo manifesto, pela tag e pelo workflow do release v1.0.0.

A primeira revisão científica solicitada pelo usuário está descrita em
`docs/revisao_cientifica_1.md`. O PDF de conferência atual tem 167 páginas;
`academic_revision_pdf_review.json` registra as novas figuras, o estudo
condicional de B/C e a inspeção dirigida. O teste de timing e as adições
teóricas também estão incorporados. Contagens e hashes de revisões anteriores
identificam os PDFs examinados naquela ocasião. A conferência visual integral do PDF atual está registrada em
`results/C13/final_pdf_visual_review.json`.

| Requisito | Evidência atual | Estado |
|---|---|---|
| Texto acadêmico sem histórico de desenvolvimento | Fontes LaTeX consolidadas; extração textual do PDF de conferência | Conferência visual integral concluída; redação de CPU, armazenamento e arquivos retirada dos capítulos 7 e 9 |
| Citações e cópias bibliográficas | `bibliography_audit.json`: 47 citações resolvidas, metadados obrigatórios presentes, 41 cópias locais com SHA-256 conferido | Passou no escopo estrutural; não prova o suporte científico de cada frase |
| Correções bibliográficas e abertura dos capítulos 3–4 | `bibliography_layout_review.json`: dez páginas conferidas, PDF com 158 páginas | Passou; paginação e datas de acesso corrigidas, referências completas inspecionadas visualmente |
| Template ITA e identificação escolhida pelo usuário | `results/C13/ita_frontmatter_review.json` | Formatação conferida; não representa homologação administrativa |
| Fundamentos, resposta angular e simulador | 19 + 23 + 11 testes executados no diretório isolado | Passou |
| Aplicação ampliada: respostas, dados e verossimilhanças | `c11_population_comparison.json`: 15.614 NPZ, 18.630 arrays idênticos | Passou |
| Aplicação ampliada: posteriores e estatística | `c11_synthesis_comparison.json`: 10.728 registros e 18 grupos com igualdade exata | Passou |
| Geração escalar | `c10_full_generation_comparison.json`: 30.000 matrizes ORF, 1.192 observações e sete arquivos idênticos | Passou desde as respostas físicas; 19 testes adicionais passaram |
| Integrais escalares | 6.344 alvos, 2.500 eventos e 210.322.632 valores de grade conferidos independentemente | Passou, reconstrução a partir dos valores armazenados |
| Síntese escalar e Fisher | `aggregate_comparisons.json`: produtos JSON iguais e arrays PIT idênticos | Passou; auditoria de Fisher reutiliza derivadas arquivadas |
| Derivadas físicas de Fisher | `fisher_derivatives_comparison.json`: oito pontos, três níveis harmônicos e dez passos; arquivo de derivadas idêntico | Passou; derivadas e diagnósticos recalculados, respostas ORF reutilizadas |
| Respostas angulares adicionais de Fisher | `fisher_orf_comparison.json`: 82 massas e 2.460 matrizes ORF regeneradas, NPZ idêntico | Passou; complementa a regeneração da tabela nodal e das derivadas |
| Geração da robustez | 5.396 observações reconstruídas; desvio máximo escalado 6,5399e-16 | Passou, usando respostas arquivadas |
| Respostas físicas da robustez | `c09_truth_responses_reproduced.json`: 84 lotes de respostas byte a byte idênticos | Passou; `c09_response_merge_comparison.json` confirma agregação e arquivo final idênticos |
| Família SBC da robustez | 126 testes recalculados; igualdade exata com a síntese publicada | Passou |
| Campanha tensorial original | `c07_synthesis_comparison.json`: 2.500 alvos, 155 testes, 15 contrastes e 14 arrays conferidos | Inferência e nova síntese concluídas: `c07_inference_full_comparison.json` e `c07_fresh_synthesis_comparison.json` |
| Geração física tensorial | `c07_generation_comparison.json`: 503 respostas, 500 observações e 514 arrays idênticos | Passou; 503 registros científicos também iguais, excluindo somente tempo e raiz de caminhos |
| Figuras e tabelas externas | `central_products_inventory.json` e `figure_table_replay.json`: 24 figuras idênticas por rasterização e cinco arquivos de tabelas idênticos | Todos os 29 produtos externos passaram |
| Mapa físico de duração e janela | `window_physical_comparison.json`: 43 trabalhadores, 79 arrays e relatórios científicos exatos | Passou; 59,16 s de CPU, limites originais preservados |
| Tabelas internas | `inline_tables_audit.json`: onze tabelas, 159 valores ligados às fontes e à precisão exibida | Passou; conferência de transcrição e arredondamento |
| Mapa físico de dispersão fraca | `weak_physical_comparison.json`: 13 trabalhadores, 99 arrays e restos da expansão exatos | Passou; 17,28 s de CPU, limites originais |
| Integrais e respostas de referência | `independent_integrals/comparison.json`: sete scripts, oito relatórios científicos exatos | Passou; integrais recalculadas e novas respostas de controle |
| Produção posterior escalar integral | `scalar_full_production_comparison.json`: 11.392 arquivos e 6.344 alvos idênticos | Passou: grades, eventos e densidades na verdade reexecutados |
| Síntese escalar da produção regenerada | `scalar_fresh_synthesis_comparison.json`: 71 testes e dez arrays PIT iguais | Passou; única diferença é o hash do recibo operacional com novos tempos |
| Inferência de robustez | `c09_nominal_inference_comparison.json`, `distance_posterior_replay/comparison.json` | Todas as 25.956 posteriores distintas e a substituição refinada reproduzidas; 87 arrays de verossimilhanças idênticos; atlas angular de distância reutilizado |
| Ligação da nova inferência à síntese de robustez | `c09_synthesis_regenerated_binding.json`: 25 arquivos de posteriores idênticos aos hashes das entradas da síntese | Passou; a agregação independente anterior usa os mesmos bytes |
| Componentes de inferência | `inference_components.log`: 164 testes no diretório isolado | Passou; não substitui campanhas completas |
| Ajuste de timing sintético | `timing_projection/results.json`, `clean_reproduction.json` e `products_reproduction.json` | 20.000 realizações por amostragem; concordância com covariâncias analíticas e reprodução exata das matrizes, tabela e duas figuras |
| Contrastes condicionais B/C | `conditional_contrasts/results.json`, `inverse_verification.json`, `clean_reproduction.json` | 300 quantis, 200 contrastes e 900 inversões verificadas; todos os raios numéricos menores que 0,01; estudo com parâmetros fixados, distinto da inferência marginalizada |
| Produtos externos do PDF atual | `current_products_inventory.json`: 28 figuras e seis arquivos de tabelas efetivamente usados pela compilação | Todos os 34 produtos ligados à reprodução; inventário histórico preservado separadamente |
| Inferência tensorial completa | `c07_inference_full_comparison.json`: 2.500 propostas, 20.000 réplicas e 175.000 arrays; diagnósticos e estados também comparados | Igualdade dos resultados científicos; 901.130.000 avaliações concluídas |
| Nova síntese tensorial | `c07_fresh_synthesis_comparison.json`: 155 testes, 15 contrastes, 14 arrays e dois CSVs | Igualdade dos resultados com a síntese anterior; vínculos dos novos arquivos conferidos |
| Figuras acadêmicas revisadas | `academic_figures_reproduction.json` | Onze figuras e 53 arrays reproduzidos; curvas, envelopes e estatísticas preservados, novos layouts |
| Artigo | Autoria definitiva, redação acadêmica e resultados condicionais atualizados, PDF de sete páginas conferido | Revisão editorial desta alteração concluída; não submetido |
| Requisitos institucionais | `c13_requisitos_institucionais.md`; programa e área conferidos | Usuário considerou a formatação suficiente e dispensou novos detalhes |
| Commit, push e release v1.0.0 | `releases/v1.0.0/manifest.json`, tag v1.0.0 e workflow de publicação | Conferência de fontes/PDF exigida pelo workflow; download deve coincidir com `pdf_sha256` do manifesto |

Os arquivos citados sem diretório estão em `results/C13`. Os parâmetros
científicos da aplicação ampliada foram preservados; a reprodução usou limite
operacional de memória de 3 GiB, registrado separadamente. O código numérico e os
hashes das fontes coincidem com os originais. Os caminhos absolutos foram
redirecionados para um diretório isolado por um adaptador auditado de E/S Python.
O ambiente de bibliotecas foi reutilizado e suas versões fixadas foram conferidas;
isso não equivale a uma instalação independente em outro sistema operacional.

Os nomes de autor, orientador e banca são definitivos conforme solicitado.
Assinaturas, data de defesa e registro institucional não foram inventados. A
existência de PDFs e de um manuscrito não implica defesa, aprovação ou aceitação.
