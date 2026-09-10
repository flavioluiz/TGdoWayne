# Código e suplementos: inspeção dirigida

Consulta em 10/09/2026. Nenhum código externo foi executado ou incorporado ao repositório do projeto. As cópias ficam em `tmp/c03_audit/code/` e servem apenas à leitura; verificar licenças antes de reutilizar implementação.

## Choi–Kahniashvili

A página [publicações do autor](https://chrischoi314.github.io/publications/) fornece o link do [repositório associado](https://github.com/ChrisChoi314/graviton_mass_ORF). Foi fixado o commit `8a63e6617489c3bb54c7683dda7ac074a183d8f3`; URLs e SHA-256 por arquivo constam de `code/choi/provenance.json`.

- `src/important_functions.py`: funções analíticas e integrações Monte Carlo para setores tensorial, vetorial e escalar, com argumento `k_abs_k_0` e fases `fL1`, `fL2`.
- `src/rigorous_fit.py`, linhas 26–80: fixa massa e distâncias, varre 99 valores da razão de propagação, soma modos com pesos fixos e minimiza soma de resíduos quadráticos divididos por erros individuais. Não há ali posterior, matriz completa no ajuste final, injeções com cobertura nem comparação A/B/C.
- `src/table_1.py`: computa os chi-quadrados de referência com erros diagonais para os dados binados.
- `src/fig_2.py`, linhas 86–166: contém leitura de covariância dos estimadores por par e calcula alternativas de médias com covariância **dentro** de cada bin. Entretanto, os arrays `rho_avg`/`sig_avg` efetivamente salvos e recarregados são os da média ponderada simples; os nomes com sufixo `_corr` não são a comparação inferencial de interesse.

Essa inspeção distingue código disponível de validação realizada: os scripts podem requerer dados e dependências adicionais. Não foi investigado se outras branches, releases ou trabalho privado incluem nova análise.

## Bernardo–Ng / PTAfast

Commit `1ea54bf5456635d1301d5c6b42d98e2c601d3a02`, pasta [app3_cvlimitedgravity](https://github.com/reggiebernardo/PTAfast/tree/1ea54bf5456635d1301d5c6b42d98e2c601d3a02/app3_cvlimitedgravity).

`cvlimitedgravity.ipynb` compara multipolos e velocidades para `fD=1000`, incluindo combinação escalar de respostas transversal e longitudinal. `vg_modified.ipynb` relaciona massa, frequência e velocidade e plota bandas observacionais. Os notebooks inspecionados não implementam a comparação A/B/C da proposta. O vínculo escalar e a variância cósmica não devem ser apresentados como inéditos.

## Outras referências centrais

Foram consultados os textos integrais HTML e registros do arXiv de Zhao–Wang, Cordes et al., Han–Zhao e Franciolini et al., e executadas buscas de ID com `code OR github OR supplement`. Não se localizou um repositório de análise atribuído aos autores nesses caminhos. O botão padrão “Report GitHub Issue” do arXiv refere-se a erros de renderização e **não** é código científico. Não inferir inexistência de código a partir de sua ausência no artigo.

Franciolini et al. possui versão editorial no [CERN Document Server](https://cds.cern.ch/record/2933693), além do preprint; a página de registro apareceu na busca com metadados editoriais, enquanto acesso direto posterior mostrou desafio antiautomação. Nenhuma tentativa de contornar esse desafio foi feita. O arXiv forneceu o PDF local da versão consultada.
