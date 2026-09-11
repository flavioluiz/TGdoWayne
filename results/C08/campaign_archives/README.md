# Arquivos restauráveis das campanhas C08

Os três pacotes foram empacotados, verificados e restaurados em diretórios
novos. O SHA de cada arquivo restaurado coincidiu com o original.
Nenhum original foi removido. Cada pacote inclui seu próprio verificador,
inventário comprimido e manifesto; todos esses arquivos devem viajar juntos.

| Pasta | Arquivos restaurados | Bytes restaurados | Partes ZIP | Bytes dos ZIPs |
|---|---:|---:|---:|---:|
| `engineering_main_v1` | 10821 | 344695765 | 4 | 72051520 |
| `replay_v1` | 2893 | 194676319 | 3 | 37217792 |
| `offline_v1` | 2138 | 451167813 | 5 | 130264492 |

`engineering_main_v1` conserva as duas variantes C nas fases de engenharia
e principal, fontes e proveniência selecionadas. `replay_v1` conserva os
160 alvos HIGH reproduzidos, estatísticas de CDF, quatro pares KL e recibos.
`offline_v1` conserva a execução finita original com falha por CPU, seus
143 relatórios, a continuação com 181 relatórios novos, todos os suplementos,
síntese pareada, fontes e revisões. A conclusão do transporte não transforma
falhas científicas ou numéricas em aprovação.

```sh
python3 scripts/campanha_compressao.py verificar \
  --pacote results/C08/campaign_archives/offline_v1
python3 scripts/campanha_compressao.py restaurar \
  --pacote results/C08/campaign_archives/offline_v1 \
  --destino /caminho/novo/para/restauracao --max-bytes 500000000
```

A pasta de destino deve ser nova e seu diretório pai deve existir. A
restauração usa `destino/caminho_relativo_original`. Os JSON históricos
mantêm suas strings absolutas; `C08_RELOCATION_MAP.json` documenta o novo
prefixo. O CLI não altera fontes nem autoriza uma nova execução física.

As dependências externas ficam listadas por caminho relativo e SHA. São
1289 arquivos no replay e 1150 no pacote offline; foram verificadas na raiz
original durante o fechamento. Não estão implicitamente incluídas nesses
pacotes. Para verificar uma raiz com as dependências restauradas:

```sh
python3 scripts/campanha_compressao.py verificar \
  --pacote results/C08/campaign_archives/offline_v1 \
  --dependencias /caminho/da/raiz/com/dependencias
```

Use o checkout da tag correspondente, os pacotes C07, as tabelas e os demais
pacotes C08 para resolver a proveniência pertinente. O backend nativo foi
executado no ambiente registrado; não se promete identidade binária em
outra arquitetura. Histórias de fontes antigas preservam bytes e falhas,
sem afirmar que todos os seus caminhos antigos apontam para a mesma versão
no checkout atual ou que todas as execuções históricas são reproduzíveis
integralmente apenas com o pacote selecionado.

Os recibos de transporte estão em `../campaign_archive_history/`; as
[limitações científicas](../../../docs/C08/RESULTADOS.md) acompanham o texto.
O v1 e v2 dentro dos pacotes anteriores permanecem intactos. O CLI oficial
v3 lê todos os três formatos e acrescenta uma pasta nova de recibos para os
produtos offline, sem escrever uma conclusão na execução original falha.
