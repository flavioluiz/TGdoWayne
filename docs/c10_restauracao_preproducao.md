# Restauração da preparação, piloto e geração C10

O pacote em `results/C10/preproduction_reproducibility/` preserva os diretórios
concluídos de preparação, piloto, refinamentos e geração populacional. A
produção de posteriores em andamento está explicitamente excluída.

O manifesto cobre 104.184 arquivos lógicos. Foram escritos 14 ZIPs novos,
totalizando 499.961.346 bytes, e reutilizados 167 arquivos idênticos de dois
ZIPs anteriores. Arquivos grandes são recompostos a partir de partes
ordenadas, com verificação do SHA-256 do arquivo completo.

Para conferir os arquivos sem escrever:

```sh
python3 scripts/restaurar_preproducao_c10.py
```

Para restaurar os caminhos originais depois de clonar o repositório:

```sh
python3 scripts/restaurar_preproducao_c10.py --destination .
```

Arquivos existentes de conteúdo diferente não são sobrescritos. A validação
foi realizada em `tmp/c10_preproduction_restore_check/`, com restauração e
verificação de todos os 104.184 arquivos. O recibo está em
`results/C10/preproduction_reproducibility/restore_validation.json`.

As tentativas fracassadas e seus resultados parciais estão preservados. A
integridade dos arquivos não aprova resultados científicos indeterminados
nem substitui a auditoria dos posteriores. Os PDFs de artigos de terceiros
continuam no acervo local separado, conforme a política do catálogo.

## Testes do marco

Após uma clonagem limpa, restaurar as referências antes de executar os testes:

```bash
python3 scripts/restaurar_preproducao_c10.py --destination .
make check-scalar
```

O restaurador confere os hashes e recusa sobrescrever arquivos diferentes. O
workflow de publicação executa essa restauração e os testes C10. As simulações
populacionais não são repetidas pelos testes de componentes.
