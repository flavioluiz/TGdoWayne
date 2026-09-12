# Restauração da produção C09

Os caches nominais, controles B10, refinamento do caso de omissão, produção
de distâncias, respostas de seus limiares e componentes SBC estão arquivados
em `results/C09/production_reproducibility/`. O manifesto vincula 24.238
arquivos lógicos: usa 11 ZIPs novos (511.962.640 bytes) e reaproveita arquivos
idênticos em 20 ZIPs anteriores, sempre com conferência de SHA-256.

Três caches excedem o tamanho individual escolhido para os pacotes. Foram
divididos em partes ordenadas, descritas em `large_files` no manifesto.
O hash do arquivo lógico completo também foi verificado após concatenar
as partes. Não abrir uma parte isolada como se fosse um arquivo NPZ.

Após clonar o repositório, a verificação sem escrever arquivos é:

```sh
python3 scripts/restaurar_producao_c09.py
```

Para restaurar os caminhos `tmp/...` na raiz do checkout:

```sh
python3 scripts/restaurar_producao_c09.py --destination .
```

O comando não sobrescreve arquivos existentes de conteúdo diferente.
Alternativamente, indique uma pasta separada. A validação executada usou
`tmp/c09_restore_verification/` e releu todos os 24.238 arquivos gravados,
comparando seus hashes com o manifesto. O recibo está em
`results/C09/production_reproducibility/restore_validation.json`.

O escopo do pacote é explícito: campanhas selecionadas completas e
dependências locais com vinculações SHA atualmente correspondentes.
Snapshots antigos que diferem dos arquivos atuais continuam nos arquivos
históricos dos respectivos experimentos. Os módulos do repositório, o
experimento C07 e sua tabela ORF permanecem nos caminhos versionados.
Integridade de arquivo não substitui validação científica; os resultados
indeterminados e as tentativas interrompidas não foram apagados.

A primeira tentativa de empacotamento parou antes de escrever ZIPs quando
encontrou um cache maior que 75 MiB. A fonte e o registro dessa tentativa
foram preservados em `history/`; a solução foi particionar arquivos grandes,
sem recalcular resultados ou alterar os caches originais.
