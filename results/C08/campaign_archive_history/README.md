# Transporte portátil de evidências C08

O pacote `bundle_engineering_main_v2/` preserva **10.821 arquivos e 344.695.765 bytes** de engenharia/main, fontes, configurações, receitas, recibos, reviews e histórico selecionado. São quatro ZIPs, somando **72.051.520 bytes**; cada arquivo fica abaixo de 90 MiB. O SHA256 de `bundle.json` é `bdc393fa11be1eeea1e456ed3ddd04a21378db4a287a0e7def57df158560dcd2`.

Engenharia C_beta/C_full: 8+8 alvos, nenhum guard final não resolvido. Main: 64+64 alvos; C_beta conserva o alvo 1489 não resolvido, C_full conserva 1327/1355/2102/2327/2461. Os dados do arquivo preservam todos os flags e endpoints; completar transporte não aprova precisão, a comparação científica ou SBC32. Os brackets originais main ainda registram a falta de evidência determinística, sem substituição por resultados posteriores.

O utilitário padrão proposto para integração é `scripts/campanha_compressao.py`. Ele usa apenas a biblioteca padrão do Python e não importa o runtime científico. Esta entrega não modificou scripts ou fontes oficiais. Também há uma cópia byte a byte do utilitário dentro do bundle, SHA `cde31612240f4534848e5cc220b9850b382feaa1d7bc8363d8c2411222a68d62`.

```sh
python3 scripts/campanha_compressao.py verificar --pacote CAMINHO_DO_BUNDLE
python3 scripts/campanha_compressao.py restaurar --pacote CAMINHO_DO_BUNDLE --destino NOVA_RAIZ
```

O destino deve ser novo. A restauração reproduz cada caminho relativo original, por exemplo `NOVA_RAIZ/tmp/c08_posterior_campaign/main/...`, verificando SHA de todos os arquivos. Um `C08_RELOCATION_MAP.json` explicita o prefixo histórico e a nova raiz. Nenhum JSON histórico é reescrito; suas strings absolutas continuam sendo evidência da execução original. Reexecutar código que consome caminhos absolutos exigirá argumentos/configuração de transporte próprios e autorização apropriada; esta ferramenta restaura evidência e não inicia inferência.

O comando opcional abaixo verifica também os dez arquivos externos declarados, incluindo partes comprimidas das tabelas, manifests, dados C07 e o binário nativo da execução histórica:

```sh
python3 scripts/campanha_compressao.py verificar --pacote CAMINHO_DO_BUNDLE --dependencias RAIZ_DO_REPOSITORIO
```

As duas tabelas descomprimidas, somando 815.503.680 bytes, **não** foram duplicadas. Seus hashes esperados e caminhos originais estão em `selection.reconstructed_dependencies` no inventário. Use os transportes existentes `results/C08/orf_tables/C_beta_parts` e `C_full_parts`, com seus respectivos manifests e `compactar_arquivo.py`, para uma restauração separada. Essa etapa não refaz spline nem transforma números. Não se afirma que o arquivo mínimo contém todos os caches necessários para repetir inalterada cada quadratura histórica.

`inventory.json.gz` vincula caminho, tamanho, SHA e ZIP de cada membro; preserva também os hashes dos raws aposentados, os quatro audits, dependências e exclusões. `bundle.json` vincula os ZIPs, o inventário e o utilitário. Conservar seu SHA no commit/release fornece a referência externa de integridade: o arquivo não pretende autenticar a si próprio.

O planejamento exige conclusão de cada campanha, ROOT review vinculado, 8/64 alvos e famílias 16/128, sete artefatos por estado e seis adicionais por alvo main. Verifica os guards originais sem filtrar falhas. A compactação mantém o lock da campanha concluída, revalida hashes antes/durante/depois da cópia, rejeita raws remanescentes, symlinks, caminhos inseguros, alteração da seleção, alteração do inventário e saída dentro de qualquer raiz selecionada. Saídas são publicadas apenas depois da verificação dos ZIPs. Não há remoção de fontes nem sobrescrita de destinos.

Cinco testes TOY passaram (`tests_first.log`), incluindo ida e volta com falha preservada, corrupção, traversal, lock ocupado, raw remanescente, destino existente, orçamento de restauração, alias por symlink e modificação de fonte depois da cópia. O pacote real passou `empacotar`, `verificar --dependencias` e `restaurar`; os recibos `*_intent.json`/`*_result.json` conservam comando, fonte, inventário, custo e exit code. Custos reais: compactação 30,815 s CPU/63.176.704 bytes RSS, verificação 3,330 s/51.888.128 bytes, restauração 9,539 s/51.871.744 bytes. Zero física, likelihood, ORF ou deserialização de amostras.

Dois achados preliminares do revisor foram corrigidos antes dos testes e da compactação: rehash final dos bytes de includes não protegidos pelo lock da campanha e resolução do destino contra todas as raízes. A fonte anterior permanece em `history_before_io_review/`. O inventário v1 também permanece, mas v2 acrescentou três evidências de entrada ausentes e as receitas explícitas das tabelas. `closure_audit_v2.json` confirma cobertura dos hashes de fontes, inputs e extra_inputs dos quatro runtimes/planos.

O replay obrigatório e o estágio de resposta finita não fazem parte deste bundle. Novos pacotes devem ter seleção, conclusão e review próprios; nenhum deles deve substituir este histórico já congelado.
