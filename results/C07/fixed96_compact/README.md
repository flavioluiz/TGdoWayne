# C07 — arquivo compacto e verificável

96 alvos preservados; 0 com estado NUMERICALLY_UNRESOLVED. Escopo original: `FIXED_TRUTH96_NOT_SBC`. Nenhum alvo foi descartado por resultado científico ou numérico. Este pacote transporta artefatos; não aprova calibração. O escopo FIXED_TRUTH96_NOT_SBC preserva a geração e as máscaras de verdades indefinidas; os cenários fixos não constituem SBC.

```sh
python3 compactar_calibracao.py verify --bundle .
python3 compactar_calibracao.py extract --bundle . --destination /caminho/novo
```

A extração restaura `campaign/` e eventuais `supplements/`, byte por byte, sem sobrescrever destinos. Os ZIPs também podem ser abertos por ferramentas padrão, mas use o verificador para conferir o inventário completo. `inventory.json.gz` associa cada caminho ao SHA256 e ao ZIP, preserva todos os IDs/estados e os hashes dos raws aposentados. O próprio inventário e cada ZIP são vinculados por `bundle.json`. Preserve o SHA256 deste arquivo no commit/release: hashes oferecem integridade, não autenticação independente.

As fontes, configurações, propostas congeladas, receitas/estados RNG, oito checkpoints, recibos, diagnósticos, ledger e tentativas permanecem nos caminhos originais dentro de `campaign/`. Pequenas amostras descritivas não são amostras IID da posterior e não substituem os diagnósticos. Os raws grandes já aposentados pelo driver não são incluídos. Nenhum original é removido por este utilitário.

Para reproduzir, restaure o pacote fora da árvore versionada, disponibilize as dependências de entrada com os SHA256 de `bundle.json` e use as fontes/receitas congeladas. `verify --dependency data=... --dependency table=...` verifica explicitamente esses arquivos externos; também admite qualquer outro papel de `input_dependencies`. Configurações copiadas estão em cada `archive_target_*/input_*.json`; dados/tabela/binário nativo podem existir separadamente no repositório. O manifesto de build preservado permite reconstruir o backend; igualdade binária entre plataformas não é prometida. Uma nova produção deve usar destino separado e a mesma proposta/agenda RNG; restaurar um alvo finalizado não autoriza sobrescrever checkpoints para recriar raw. O driver com `--resume` apenas revalida alvos já finalizados.

A verificação não deserializa posteriors nem refaz SBC. Logs externos, síntese e evidências só estão incluídos quando explicitamente passados como suplementos. Os limites científicos da síntese original permanecem válidos.
