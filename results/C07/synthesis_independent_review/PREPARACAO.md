# Auditoria independente de síntese C07 — aguardando fechamento

`audit_synthesis.py` foi preparado pela leitura das fontes/protocolos, sem abrir prefixos da campanha ou produtos de síntese. Sua CLI exige o SHA comunicado por ROOT do `summary.json` e do `campaign_complete.json` já fechados, além dos caminhos de `campaign_plan.json`, NPZ, CSVs e configuração.

Não importa os helpers ROOT. Usa NumPy/SciPy diretamente para confrontar KS finito-n, estatísticas dos PITs e histogramas20, contagens/cobertura e intervalos Clopper–Pearson, as famílias Holm93/62/15, os pares e quantis descritivos, os envelopes de erro numérico e os limites conservadores de contagens e de McNemar. O retângulo de discordâncias é varrido por total de discordâncias, sem copiar a grade 2D do helper original. Os resultados de sensibilidade continuam condicionais aos intervalos aproximados; não constituem prova de precisão de integração ou de calibração.

O inventário lógico exige todos os2500 alvos/15000 PITs, a identidade runtime/driver e a presença de hashes dos compactos. O NPZ agregado é verificado contra o SHA do resumo. Nesta primeira auditoria não se reabrem todos os2500 compactos: a máscara de resolução específica por função é conservada do produto agregado. Não há leitura de raws ou recomputação de ORF/likelihood.

Os testes pequenos em `helper_toy.json` verificam somente a implementação independente dos helpers: três retângulos comparados à enumeração binomial e343 amostras sintéticas dentro de intervalos, além de Holm/CP. Não são SBC da PTA.

Limites:30s CPU/256MiB, um processo e um thread numérico. A execução real da auditoria permanece pendente do sinal de fechamento de ROOT. Não executar apontando para prefixos correntes.
