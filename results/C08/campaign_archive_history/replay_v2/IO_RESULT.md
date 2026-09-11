# Replay C08: transporte e roundtrip concluídos

Status: `ALL_REPLAY_BYTES_PACKED_DEPENDENCIES_VERIFIED_AND_RESTORED`.
O ROOT autorizou explicitamente apenas pack, verificação com a raiz de
dependências original e restauração em destinos novos. Essa mensagem está
transcrita em `ROOT_IO_authorization.json`; não representa assinatura
criptográfica do ROOT. A promoção do script oficial permanece pendente.

As três operações encerraram com código zero e stderr vazio:

| Operação | CPU do subprocesso (s) | Wall (s) |
| --- | ---: | ---: |
| Empacotar e verificar internamente | 2,477256 | 2,486223 |
| Verificar, incluindo dependências C07 | 0,357945 | 0,361273 |
| Verificar e restaurar | 0,769479 | 0,858822 |

Foram transportados **2.893 arquivos, 194.676.319 bytes**. Os três ZIPs
somam **37.217.792 bytes**; os seis arquivos necessários ao bundle completo
somam **37.510.242 bytes**. Cada ZIP está abaixo do teto de 94.371.840 bytes.
A restauração verificou o SHA de cada arquivo selecionado antes da publicação
do novo destino. As **1.289 dependências C07 externas** também tiveram seus
bytes verificados com `verificar --dependencias` na raiz original.
Essas dependências continuam externas ao bundle replay.

O recibo `io_execution/roundtrip.json` registra 3,604680 s de CPU dos três
filhos, incluindo startup e encerramento, e 0,059154 s do controlador até
o snapshot imediatamente anterior à escrita do recibo: **3,663834 s CPU**
e 3,724984 s wall observados. A pequena escrita final/saída do controlador
ocorre após esse snapshot. Os comandos separados de preparação/relatório
não integram esse relógio do roundtrip. RSS máximo observado: 44.236.800 B
nos filhos e 27.082.752 B no controlador; a soma dos máximos individuais é
71.319.552 B, sem alegação de pico simultâneo medido ou garantia de RSS.

O CLI, a seleção, o inventário, a revisão ROOT e os demais 16 vínculos
congelados foram conferidos antes e depois. O script v1, seu manifesto de
bundle engenharia/main e o script oficial v1 mantiveram seus SHA. O pack
também refez o hash das fontes selecionadas ao final. Nenhum arquivo
original foi removido. Não houve ORF, likelihood, banco, nova álgebra
numérica ou desserialização de arrays reais; a leitura binária serviu
exclusivamente à cópia e ao hash.

Destinos publicados, ambos criados novos:

- `bundle_replay_v1/`: três ZIPs, `inventory.json.gz`, verificador autônomo
  `campanha_compressao.py` e `bundle.json`.
- `restored_replay_v1/`: os caminhos relativos originais e
  `C08_RELOCATION_MAP.json`. Strings históricas absolutas permanecem intactas.

O manifesto do bundle tem SHA
`dc19cc38d0b6d6a36ac123e782d8092d6bc63f45061ba3cc82356d5c4ba59d25`.
Seleção e inventário continuam os aprovados, respectivamente
`c23906ae128be9a8e45c7000a3b3d193cf0e55e7e17abee6581b7260df8d9e0a`
e `7b4634fcc0e48b3aa4abe9b825431b25c5d9c56343e705ce452e91d8f4d3a7ea`.
`io_delivery_manifest.json` vincula os demais recibos e produtos de transporte.
O README/preflight/manifesto candidato anteriores permanecem como registro
prospectivo congelado; este relatório documenta a execução posterior.

Para a promoção futura do executável oficial, a cópia mínima é somente
`scripts/campanha_compressao.py` deste candidato para o mesmo caminho na
raiz do repositório, conservando o SHA v2 aprovado. É autônomo e usa apenas
a biblioteca padrão. Os dois arquivos de teste podem ser copiados sem
alteração para `tests/test_transport.py` e `tests/test_root_kinds.py`, como
validação adicional de manutenção; não são dependências do CLI. O preparador
da seleção específica de replay, autorizações e dados não são dependências
de runtime do CLI. O v1 dentro dos bundles legados deve permanecer intacto.

Para copiar o bundle replay, os seis arquivos de `bundle_replay_v1/` são
indivisíveis. Não é necessário copiar a restauração duplicada nem as árvores
C07, engenharia/main ou tabelas físicas para essa operação. A verificação
externa futura requer separadamente uma raiz que contenha as dependências
C07 de SHA já declarados. Nenhuma promoção/cópia oficial foi realizada aqui.
