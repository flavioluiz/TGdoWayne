# v0.3.0 — C03: revisão bibliográfica e decisão de recorte

A dissertação cumulativa passa a incluir a introdução e a revisão bibliográfica detalhada,
em 23 páginas. A revisão tem corte em 10/09/2026 e confronta teoria, resposta de PTA,
inferência de massa, compressão e validação estatística.

## Entregas

- Capítulo com nove seções e seis equações; bibliografia com versões arXiv explícitas.
- Protocolo de busca dirigida, matriz de 17 entradas e auditoria de códigos de Choi/PTAfast.
- Segunda leitura independente de Han–Zhao e Franciolini et al., com páginas e equações.
- 22 artigos baixados em `literature/papers/`, 452 páginas e 25.149.237 bytes, todos conferidos.
  O Git contém catálogo, fontes e script de obtenção; as cópias locais de terceiros não são anexadas ao release.
- Planos C05–C10 refinados para separar A0 (Fourier), A (estimadores por frequência),
  B (compressão consistente) e C (resposta em frequência de referência).
- README, estado editorial e manifesto atualizados; o catálogo integra os hashes de entrada.

## Decisão científica

Há antecipação parcial substancial: multifrequência, covariância completa e auditoria de
verossimilhanças/compressão já possuem antecedentes. A contribuição candidata foi delimitada
ao mapa calibrado de validade da substituição dispersiva por `f_ref`. A revisão sustenta
continuar, sem afirmar prioridade absoluta ou prometer publicação.

Liang–Trodden v3 (24/07/2026) passa a ser a versão fixada para a resposta, incluindo
os termos temporais relevantes à extensão escalar. A0–A, A–B e B–C terão controles separados;
propagar momentos não torna gaussiana a distribuição de estimadores quadráticos.

## Verificação e alcance

PDF compilado com pdfLaTeX/Biber; todas as páginas renderizadas e inspecionadas. Corrigidos
um cabeçalho longo e quebras internas de referências. Downloads conferidos por SHA-256,
formato, identificação e número de páginas. O script também foi testado contra URL sem versão
e hash divergente; `--verify` não acessa a rede. Detalhes em `docs/validacao_v0.3.0.md`.

C04 está em andamento. Esta versão não contém campanha de inferência, novo limite de massa
ou detecção de polarização. Metadados acadêmicos provisórios permanecem como solicitados.
