# Revisão independente da extensão `--fixed96`

Foram lidos o script e os testes ROOT, comparando o script atual com os bytes
anteriores já preservados em `original/`. A versão consultada foi copiada para
`review_sources/`; nenhum arquivo ROOT foi alterado. A revisão é de transporte
e consistência dos artefatos, sem deserializar ou recalcular inferência real.

## Extensão fixed96

O novo ramo exige escopo `FIXED_TRUTH96_NOT_SBC`,96 datasets, somente A0_CN,
IDs0–95 sem ausência/duplicação, correspondência datum=target e marcador de
escopo mascarado nos estados. Exige o schema operacional mascarado e vincula
generation/data/protocol aos hashes do plano. O snapshot de geração substitui
o antigo arquivo de logL na verdade, preservando a semântica de logL indefinida
nos casos sem sinal. O inventário de máscaras da geração é verificado como
[64,64,64,96,96],64 logL definidas e três blocos de32.

A CLI torna engineering/fixed96 mutuamente exclusivos. O ramo de engineering
também ficou mais estrito, exigindo seu escopo próprio; o padrão continua
reservado aos2500 alvos da campanha prior predictive. O README transportado
apresenta explicitamente o escopo, sem converter casos fixos em SBC.

Lock, hashes, oito checkpoints por alvo, receipts, raw retirement, ledger e
inventário seguem os controles anteriores. Falhas numéricas são transportadas;
o compactador não seleciona apenas aprovados. A extração é para destino novo,
com verificação de todos os bytes antes de publicar a árvore restaurada.

## Verificações adicionais executadas

O script independente cria uma fixture de transporte de96 alvos e substitui
dois produtos binários por NPZ reais pequenos, explicitamente rotulados como
fixture sem inferência:

- target0: PIT e MCSE estruturais zero, com marcador estrutural verdadeiro;
- target64: três parâmetros e logL indefinidos, NaNs e máscaras falsas.

Pack, verify e extract preservaram **cada byte** desses arquivos, os NaNs,
as máscaras e todos os96 IDs/95 estados unresolved. Cinco controles passaram;
uma questão de consistência descrita abaixo foi reproduzida separadamente.
CPU total7,5985 s, nenhuma likelihood, posterior ou dado PTA avaliado.

O compactador não deve interpretar o significado estatístico das máscaras.
A validade científica delas continua pertencendo ao gerador/reader/síntese
verificados; aqui foram testados seu vínculo documental e transporte fiel.

## T1 — lacuna anterior de consistência dos rótulos numéricos

O ramo comum aceita `RECORDED_NUMERICAL_CHECKS_PASSED` mesmo quando as cinco
flags retidas são falsas, se state, receipt, release e completion forem
religados coerentemente com esse rótulo. A reprodução altera apenas esses
rótulos/hashes da fixture do target95; todas as cinco flags do diagnóstico
permanecem falsas. O audit aceita e o inventário declared unresolved cai de95
para94. Não é um erro introduzido pelo novo ramo fixed96, mas também é alcançável
por ele.

Isso não exige recalcular inferência para ser detectado: exigir exatamente
as cinco chaves booleanas já definidas e conferir o rótulo contra `all(flags)`
é uma verificação de consistência dos metadados. O produtor/driver correto já
gera essa relação; não foi encontrado indício de que os resultados atuais a
violem. A sugestão é uma guarda contra um conjunto de artefatos internamente
religado, porém semanticamente contraditório, não uma alegação de dados reais
incorretos.

Reprodução e evidência estão em `independent_checks.py` e
`independent_results.json`. A execução também confirmou que os hashes das
fontes ROOT permaneceram inalterados. Os nove testes já executados pelo ROOT
são antecedentes separados; esta revisão não os apresentou como uma nova
execução independente.
