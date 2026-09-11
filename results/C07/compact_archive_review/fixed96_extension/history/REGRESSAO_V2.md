# Regressão da coerência de estado T1

O parecer anterior e seus bytes permanecem preservados. A correção ROOT exige exatamente cinco flags booleanas e deriva o estado das flags retidas, conferindo sua concordância com recibo, estado e diagnóstico.

`independent_checks_v2.py` repetiu a fixture mascarada de 96 alvos e a alteração coerente de hashes que, na v1, promovia um alvo com todas as flags falsas. A v2 rejeita esse caso com `Numerical state contradicts its retained flags.` O transporte continua preservando os bytes NPZ, o zero estrutural em u=0, os NaNs/máscaras de parâmetros indefinidos no cenário sem GW, todos os IDs e os 95 alvos não resolvidos da fixture. Resultado separado: `independent_results_v2.json`, 7,288 s CPU, zero posterior/likelihood.

O teste de compatibilidade sobre um arquivo histórico de três alvos também verificou seus 260 arquivos sem inferir aprovação científica, conforme `backward_compatibility_v2.json`. Isso valida o transporte e a coerência interna dos registros; não recalcula nem certifica a inferência.
