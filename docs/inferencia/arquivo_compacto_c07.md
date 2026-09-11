# Arquivamento compacto C07

Entrega exclusiva em `tmp/c07_compact_archive/`; nenhuma fonte ROOT foi alterada. A campanha real não foi empacotada enquanto estava ativa.

O utilitário `scripts/compactar_calibracao.py` usa apenas a biblioteca padrão do Python. Sua finalidade é transporte e integridade: não calcula posteriores, não executa SBC, não aprova resultados numéricos e não remove originais. `pack` exige conclusão integral registrada pelo driver e obtém seu lock não bloqueante; o padrão exige os 2.500 IDs. Ensaios menores exigem `--engineering` explícito.

## Conteúdo e organização

- ZIPs determinísticos por grupos lógicos de 64 alvos; partições adicionais quando necessárias para manter cada arquivo abaixo de 90 MiB. Há cerca de 40 grupos para 2.500 alvos.
- ZIPs separados para metadados globais: ledger completo, tentativas, estado final e fontes congeladas. Arquivos desconhecidos dentro da campanha são preservados, não ignorados.
- `inventory.json.gz` registra caminho, tamanho, SHA256 e ZIP de cada membro, todos os IDs/estados e hashes dos raws já aposentados. `bundle.json` é pequeno e vincula o inventário e os ZIPs por SHA256.
- Propostas, fit original, transformação de broadening, RNG, oito checkpoints, recibos, diagnósticos JSON/NPZ, flags e amostras descritivas permanecem byte a byte. `NUMERICALLY_UNRESOLVED` tem o mesmo tratamento de preservação que os demais estados.
- A única exclusão de arquivo existente permitida é o lock transitório `.campaign.lock`. Qualquer arquivo ainda presente em `raw/` provoca recusa: o empacotador não substitui a política de retirada do driver nem apaga sobras.
- Logs externos, síntese e evidências são incluídos somente por `--supplement LABEL=PATH`. São guardados sob `supplements/LABEL/`, separados dos caminhos originais sob `campaign/`.

## Uso após a conclusão

Exemplo a adaptar aos caminhos finais; não executar contra a campanha ativa:

```sh
python3 scripts/compactar_calibracao.py pack \
  --campaign tmp/c07_posterior500_v1 \
  --output results/C07/posterior500_compact \
  --supplement progress-log=tmp/c07_posterior500_v1.log \
  --supplement synthesis=results/C07/synthesis \
  --dependency data=results/C07/prior_predictive/data.npz \
  --dependency table=results/C07/orf_interpolation/orf_table_pilot12x4.npz

python3 scripts/compactar_calibracao.py verify \
  --bundle results/C07/posterior500_compact

python3 scripts/compactar_calibracao.py extract \
  --bundle results/C07/posterior500_compact \
  --destination tmp/c07_restored
```

O diretório pai da saída deve existir, e a saída deve ser nova. Não existe opção de sobrescrita. O teto padrão de restauração é 8 GiB e pode ser declarado explicitamente com `--maximum-restored-bytes`; o inventário descomprimido tem guarda de 128 MiB. Symlinks, arquivos especiais, caminhos absolutos, `..`, colisões, inventários duplicados e membros inconsistentes são recusados. O script também é copiado para o pacote, permitindo verificar/extrair sem instalar o projeto.

Os arquivos originais continuam no lugar depois de um `pack` bem-sucedido. A política Git deve incluir somente o diretório compacto, as tabelas/sínteses finais selecionadas e os scripts; não adicionar a árvore extraída. A verificação completa lê cada arquivo/entrada uma vez por fase, sem reabrir todo o ledger a cada alvo. A compressão não deduplica arquivos iguais: preserva caminhos sem introduzir um armazenamento de objetos novo.

## Reprodução de raws aposentados

O pacote preserva as propostas e receitas; não conserva os arrays raw grandes. `input_dependencies` contém os SHA256 de dados, tabela, configurações e backend original. Os argumentos `--dependency ROLE=PATH` verificam os arquivos explicitamente disponíveis, sem copiá-los automaticamente. A ausência desses argumentos não é uma alegação de pacote autossuficiente.

Para reproduzir um alvo, use as mesmas fontes congeladas/checkout correspondente, configurações preservadas, tabela/dados e proposta. A CLI já existente `scripts/infer_calibration.py produce` aceita `--target`, `--proposals`, `--output` e `--raw`; os dois últimos devem apontar para **novos diretórios**, e todos os argumentos de runtime, backend e threads devem corresponder à identidade arquivada. Não usar o `--resume` do driver para apagar/reescrever alvos finalizados: ele apenas verifica tais alvos. Compare os SHA256 dos raws reproduzidos aos checkpoints originais, separando os tempos novos dos artefatos científicos originais.

O manifesto de build permite reconstruir o C++; igualdade binária ou numérica bit a bit em outra plataforma/versão de bibliotecas não é prometida. Os hashes de fontes e arquivos detectam alteração em relação ao manifesto; a autenticidade deste último depende do commit/release que publica seu SHA256. Nenhum critério científico é inferido a partir da integridade do ZIP.

## Verificações feitas

`python3 -m unittest discover -s tmp/c07_compact_archive/tests -v`: cinco testes passam. O fixture possui dois alvos sintéticos de transporte, um `UNRESOLVED`, oito checkpoints por alvo e uma tentativa computacional falha preservada no ledger. Os bytes de teste não são posteriors e não simulam validação física.

Os testes cobrem roundtrip de todos os bytes, determinismo dos ZIPs, preservação do estado não resolvido, suplementos, não sobrescrita, recusa por campanha incompleta/lock ativo/raw remanescente, checksum/estado ausente/symlink, corrupção de ZIP, caminhos perigosos, limite de arquivo/restauração e contagem do ledger. Não foi executada nem sintetizada uma campanha nova.

Leitura exploratória dos alvos reais já concluídos 0–2 da campanha ativa encontrou 42 arquivos e aproximadamente 255 kB por alvo, sugerindo cerca de 105 mil arquivos e 638 MB não comprimidos para 2.500 alvos, além dos metadados/ledger. Isso é projeção de tamanho baseada em três alvos, não inventário final nem garantia de compressão. `pack` calcula e confere os tamanhos efetivos ao terminar a campanha.
