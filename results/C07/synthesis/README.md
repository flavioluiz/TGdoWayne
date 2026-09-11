# Síntese condicional de calibração

CONTINUOUS_PRIOR_PREDICTIVE_SBC_WITH_NUMERICAL_SENSITIVITY

Todos os 500 dados de cada um dos cinco modelos foram retidos.

As famílias prévias93/62/15 são preservadas. Testes nominais condicionam-se aos PITs calculados; as faixas de sensibilidade usam erro determinístico0,002 + zBonferroni×MCSE (alphaMC0,01, família15.000). Funções não resolvidas recebem [0,1].

A presença e integridade das evidências externas não constituem aprovação automática. Não rejeitar uniformidade não prova correção; quantis são descritivos e precisão de CDF não certifica erro horizontal. As bandas DKW mostradas nas figuras descrevem a amostragem IID ideal e são distintas da sensibilidade numérica.

| Modelo | Funções resolvidas (por coordenada) | Rejeições nominais | Rejeições robustas |
|---|---|---:|---:|
| A0_CN | [497, 497, 497, 497, 497, 497] | 0 | 0 |
| A_CN | [490, 487, 489, 489, 489, 488] | 8 | 6 |
| B_CN | [495, 495, 495, 495, 495, 494] | 5 | 4 |
| A_G | [489, 487, 489, 489, 487, 488] | 0 | 0 |
| B_G | [490, 491, 491, 491, 491, 491] | 0 | 0 |
