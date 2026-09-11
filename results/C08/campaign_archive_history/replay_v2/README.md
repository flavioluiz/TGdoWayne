# Transporte C08 v2 — candidato para replay fechado

Extensão separada de `tmp/c08_campaign_archive_v1/scripts/campanha_compressao.py`
SHAcde31612240f4534848e5cc220b9850b382feaa1d7bc8363d8c2411222a68d62.
O v1, seu bundle engenharia/main e os scripts oficiais permanecem intactos.
Não houve nova física, LL, ORF, banco ou leitura de arrays reais. A v2 mantém
o formato de arquivos/inventário e adiciona dispatch por `kind`; lê bundles
v1 e v2. Um bundle v1 conserva sua própria cópia do verificador v1.

`kind` omitido ou `campaign` usa exatamente a auditoria de engenharia/main
v1, preservando as cinco flags e os targets unresolved. `kind=replay` exige
completion `ALL160_MATCHED_HIGH_REPLAYS_ARCHIVED`, ROOT review
`ROOT_C08_REPLAY_RESULT_REVIEW_v1/ALL160_REPLAY_PRODUCTS_REVIEWED` e SHA do
complete/replay plan. Verifica 160 archives/states,640 recibos RAW/RNG,
coorte32×5, ledger41.943.040 e cross1.048.576, zero reservas abertas,
oito recibos opcionais com9/2 artifacts e quatro pares KL. Os artifacts
referenciados precisam estar no inventário transportado. Não repete a
auditoria de álgebra/estatística: utiliza a revisão ROOT já vinculada.

O inventário retém[0,1]/UNRESOLVED originais e as40 falhas LOW de peso
informadas pelo recibo ROOT. Os valores/statistics seguem como bytes exatos;
não há parsing de NPZ numérico nem alteração de flags. `LOSSLESS_BYTES_...`
continua sendo estado de transporte, sem nova aprovação científica.

`prepare_replay_selection.py` prepara somente a seleção pequena. Ela contém
a raiz do replay e fontes/autorizações/recibos/intent/plan/cuts necessários.
Propostas, checkpoints, compactos, recibos C07 originais e oito inputs do
runtime são dependências externas por caminho relativo e SHA; não se inclui
a árvore C07, seus bancos/tabelas, nem os344MB de engenharia/main C08 já
transportados. O bundle separado C07 continua necessário para resolver esses
itens. `verificar --dependencias <raiz>` verifica os seus bytes explicitamente;
sem esse parâmetro, verificam-se os bytes presentes no bundle e preserva-se
a lista externa, sem afirmar que ela foi incluída ou validada localmente.

Os guards de pack/verify/restore são os do v1 revisado: locks de campanhas
fechadas; nomes relativos canônicos; rejeição de symlink/special/raw; output
novo resolvido fora de todas as raízes selecionadas; SHA antes/durante/depois
da cópia e rehash final do inventário; tipos/tamanhos/SHA de todos os membros
ZIP; restauração em staging e SHA exato antes da publicação. Partes<=90MiB,
inventário descomprimido<=128MiB e teto de bytes de restore explícito. Os
originais não são removidos. Caminhos absolutos históricos continuam em seus
JSON; `C08_RELOCATION_MAP.json` informa o novo prefixo sem reescrever fontes.

`kind=offline` é apenas um contrato futuro: requer uma consolidação ROOT
explícita `C08_OFFLINE_ROOT_COMPLETE_v1/ALL_SELECTED_ANALYSIS_BYTES_PRESERVED`,
com identity, scope, workers_exited, failures preservados e inventário de
artifacts. O receipt `ROOT_C08_OFFLINE_ROOT_REVIEW_v1/OFFLINE_ROOT_COMPLETE_REVIEWED`
vincula completion SHA, root path, lock path, identity e contagem. Saídas
finite parciais ou continuações não são aceitas diretamente: ROOT precisa
consolidá-las primeiro nesse contrato, incluindo todas as falhas. Nenhuma
raiz offline real está nesta seleção e nenhum PASS é inferido do status de
transporte. Múltiplas raízes futuras podem compartilhar um lock explícito;
o processo adquire cada caminho de lock uma só vez.

Validação candidata: os cinco TOYs de transporte v1 são reaplicados à cópia
v2, mais um replay sintético160×4 que mantém uma falha e dependências C07
externas, e uma raiz offline sintética que preserva UNRESOLVED e rejeita
revisão ROOT pendente. Os números de ledger nos fixtures são apenas campos
de contrato; nenhum desses cálculos é executado.

Preparação/inventário e exemplos prospectivos:

```
.venv/bin/python -B tmp/c08_campaign_archive_v2/prepare_replay_selection.py
.venv/bin/python -B tmp/c08_campaign_archive_v2/scripts/campanha_compressao.py planejar --selecao tmp/c08_campaign_archive_v2/selection_replay_v1.json --repositorio . --saida tmp/c08_campaign_archive_v2/inventory_replay_v1.json
```

Pack e restore reais aguardam revisão ROOT do código e inventário. A promoção
ao caminho oficial `scripts/campanha_compressao.py` também não foi realizada.
