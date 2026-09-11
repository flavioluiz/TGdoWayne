# Proveniência das propostas derivadas

Os JSON em `proposals/` preservam uma cópia do registro do ajuste original e
acrescentam `original_sha256` e `broadening`. O SHA256 **do arquivo derivado**
está em `config.json`, `execution_manifest.json` e em cada registro do índice
`execution_summary.json`; esses hashes foram conferidos antes e depois da
execução.

Os campos herdados `identity`, `proposal_content_hash` e metadados do ajuste
identificam o **ajuste histórico**, não o conteúdo derivado. Não devem ser
utilizados para aceitar esses arquivos como checkpoints do runtime ROOT.
O produtor temporário não os utilizou como credenciais: construiu a classe
numérica auditada e verificou os SHA256 novos. Os arquivos executados ficam
inalterados para preservar seus hashes.

Na implementação integrada, preservar o hash do ajuste original num campo
específico, gerar um novo registro após a transformação e recomputar seu hash
de conteúdo e identidade antes do congelamento. A fonte de produção também
precisa registrar a política de ampliação na configuração/fingerprint.

A transformação numérica foi igual em todos os16 casos: massas absolutas
0,75 nas quatro Gaussianas originais, 0,10 em quatro cópias com covariância9C,
0,15 na Student global existente; médias, pesos relativos, covariâncias
originais e todos os parâmetros científicos permanecem os mesmos. Não houve
novo ajuste ou consulta a verdades.
