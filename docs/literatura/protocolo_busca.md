# Auditoria dirigida de literatura para C03

Data de execução e corte: **10 de setembro de 2026**. O relógio da sessão foi consultado e retornou `2026-09-10 21:08:27 UTC`; portanto, julho–setembro de 2026 não são datas futuras neste projeto. A data de revisão é obtida do histórico do arXiv, não da data dinâmica impressa pela conversão HTML (que pode mostrar 24 de agosto de 2026 em trabalhos antigos).

## Pergunta operacional

Há comparação calibrada, no mesmo conjunto de realizações PTA dispersivas, entre (A) inferência que conserva frequências, (B) compressão de dados, média teórica e covariância pelo mesmo operador fixado antes da inferência e (C) substituição da resposta por uma frequência de referência, separando os efeitos de priori de massa, covariância angular e aproximação da distribuição do estimador?

## Fontes e procedimentos efetivamente usados

- Busca web por título, arXiv ID e combinações temáticas; validação de cada achado relevante no arXiv, site do autor, repositório de código do autor ou repositório institucional da publicação.
- Leitura dirigida do texto completo HTML das referências centrais, especialmente métodos, aproximações, resultados e discussão. Consultar um artigo não significa reproduzir seus resultados. O catálogo distingue leitura dirigida, triagem e consulta anterior.
- Expansão por referências e links de código dos artigos centrais; consulta à página de publicações de Chris Choi, CERN Document Server, PTAfast e seu notebook associado a Bernardo–Ng.
- Download de PDFs com revisão explícita (`v1`, `v2` etc.), identificação `%PDF`, leitura de metadados com `pdfinfo` e cálculo SHA-256. São cópias locais para leitura; não publicar automaticamente os binários no Git. Licença do preprint pode diferir da versão editorial.
- Inspeção estática de scripts e notebooks públicos, com commit e hashes registrados. Não executados nesta auditoria: a existência de código acessível não é evidência de reprodutibilidade integral.

Não foi realizada revisão sistemática exaustiva: não houve varredura completa de Scopus/Web of Science, acesso a dados privados, contato com autores, nem uma busca de citações que garanta completude. Resultados negativos abaixo significam “não localizado nas consultas e fontes inspecionadas”.

## Consultas executadas

| Grupo | Consulta literal ou combinação |
|---|---|
| Compressão específica | `"pulsar timing" "graviton mass" "frequency" "compression"` |
| MeerKAT | `"graviton mass" "MeerKAT" covariance prior frequency` |
| Código | `"pulsar timing" "massive gravity" "github"` |
| Frequências | `site:arxiv.org "pulsar timing" "frequency-resolved" "graviton"` |
| Compressão geral | `site:arxiv.org "pulsar timing" "frequency" "compression" correlation` |
| Priori recente | `site:arxiv.org "graviton" "prior" "2026" pulsar` |
| Variância cósmica | `site:arxiv.org "Testing gravity with cosmic variance-limited pulsar timing array correlations"` |
| Atualidade | `"graviton mass" "2026" "pulsar timing" -site:researchgate.net` |
| Covariância | `"graviton" "frequency-dependent" "covariance" pulsar` |
| Metadados/código | `"2607.14790" code OR github OR supplement` e mesmas variantes para `2507.02059`, `2604.23384`, `2505.24695` |
| Dispersão/espectro | `"A novel probe of graviton dispersion relations at nano-Hertz frequencies" arxiv` |
| Granularidade | `"massive gravity" "per-frequency" pulsar` |

## Critérios de inclusão e classificação

Incluir fontes primárias que forneçam pelo menos um de: resposta/ORF dispersiva, polarizações físicas, estimadores e covariâncias PTA, inferência de massa, métodos de compressão e validação de verossimilhança. Antecedentes anteriores a 2024 entram quando necessários para evitar falsa reivindicação de novidade. Usar referências gerais de gravidade massiva como fundamentos, sem converter essa discussão em contribuição nova.

Separar: artigo publicado; preprint sem publicação confirmada; tese acadêmica; software; apresentação de congresso. O arXiv pode omitir atualização editorial: Franciolini et al. aparece como preprint em seu registro, mas o [registro institucional do CERN](https://cds.cern.ch/record/2933693) confirma PRD 112, 103516, publicado em 12/11/2025, DOI `10.1103/sjtb-gnz5`.

Para exclusão: retirar homônimos de “compressão” referentes à propagação do trem de ondas e não à redução de dados; resultados de matéria condensada com identificador semelhante; conteúdos sem pertinência ao problema e páginas secundárias quando há fonte primária acessível.

## Pendências delimitadas

1. Repetir a busca antes da submissão de artigo: trabalhos de 2026 e apresentações recentes tornam a prioridade competitiva.
2. Verificar versões editoriais e erratas em C13; alguns registros arXiv carecem de DOI editorial.
3. Para Zhao–Wang, Cordes et al., Han–Zhao e Franciolini et al., não foi localizado repositório de análise vinculado diretamente nos textos e buscas inspecionados. Essa ausência não prova inexistência. Usar equações publicadas como benchmarks independentes; documentar qualquer produto faltante.
4. A apresentação PPC2026 de Kahniashvili em 01/09/2026 anuncia prescrição fenomenológica para desacoplamento escalar/vetorial. É pesquisa em andamento, não substitui uma derivação Fierz–Pauli nem estabelece resultado revisado por pares: https://indico.global/event/15267/contributions/157529/.

## Produtos locais

- `literature/catalog.json`: referências e downloads, com caminho, versão, bytes, SHA-256, licença e grau de consulta.
- `docs/literatura/code/*/provenance.json`: commits e arquivos do código lido.
- `matriz_originalidade.csv`: comparação dos antecedentes e contribuição candidata.
- `decisao_recorte.md`: decisão e requisitos científicos para os próximos marcos.

O script versionado `scripts/download_papers.py` reconstitui a biblioteca a partir das URLs **versionadas** e dos SHA-256 congelados em `literature/catalog.json`. Não resolve novamente a versão mais recente. O utilitário exploratório usado na coleta inicial permanece temporário.

## Complemento dirigido de 11/09/2026

A [auditoria posterior](atualizacao_20260911/REPORT.md) preserva o corte inicial
acima e acrescenta uma consulta em 11/09/2026. Foram triadas seis listagens arXiv
(217 entradas, 195 identificadores distintos), revisões de oito artigos centrais
e antecedentes específicos ausentes do catálogo. Entraram seis PDFs adicionais;
a matriz reúne agora 23 entradas. O relatório distingue títulos/resumos,
leitura dirigida e códigos inspecionados, sem afirmar revisão sistemática
exaustiva ou prioridade absoluta. O catálogo atual tem 37 PDFs locais e 839 páginas.
