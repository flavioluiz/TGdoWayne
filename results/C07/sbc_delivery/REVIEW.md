# Auditoria de síntese e apresentação

Leitura independente de `src/inference/campaign_sbc.py` e sua interação com
`sbc_sensitivity.py`: não identifiquei discrepância nas famílias 93/62/15, nos
eventos de cobertura via PIT ou na separação nominal/sensibilidade. O modelo
correto gera 31 hipóteses por método (6 PIT + 20 unilaterais + 5 centrais); os pares
centrais geram 15. A função de resolução evita propagar a falha de outro PIT,
mas exige os controles comuns de normalização/peso/saturação/logZ.

Limite de contrato do núcleo: `resolved_by_function` conta as especificações
por função, mas não exige sua igualdade ao inventário 204 exato. O loader desta
entrega verifica igualdade de cada linha, tipos/formatos e coerência das flags
com erros e multiplicidade. Isso é uma guarda de entrada; nenhum arquivo ROOT
foi modificado. Metadados de validação externa são proveniência condicional,
sem inferência de aprovação científica a partir de KS ou um campo booleano.

O TOY64 independente usa theta~Normal(0,1), U=Phi(theta), y|theta~Normal(theta,0,7²).
A posterior latente é Normal(mu,v), v=(1+1/sigma²)^-1, mu=v*y/sigma². Quantis deU
sãoPhi(mu+sqrt(v)*Phi^-1(p)); seus PITs são calculados analiticamente. Para logL,
o quadrado da distância ao dado dividido porv tem distribuição qui-quadrado não
central com5 graus de liberdade e não centralidade ||mu-y||²/v; a CDF de logL na
verdade corresponde à sobrevivência dessa distância. Os três modelos de referência
usam sigma 0,7; duas aproximações usam 0,35 e 0,45 para testar erro especificado.
Os 155 p-valores nominais reproduzem scipy.stats.kstest(method='exact') e binomtest.
Fixtures positivos de MCSE/evidência testam schema, não precisão PTA.

QA visual final: dois PDFs de uma página,18 e 12 painéis; SVGs correspondentes.
Poppler renderizou ambos a 1800 pixels. Títulos, eixos, legendas, símbolos gregos e
rodapés estão legíveis; nenhuma linha é truncada ou sobreposta. A anotação de
CDF analítica foi movida para o canto inferior para não ocultar a cauda das
aproximações. O título e o rodapé explicitam que o TOY não é resultado PTA.
Faixa numérica azul e DKW ideal cinza são distintas. O visual não decide calibração.

Nenhuma posterior da campanha 500 foi carregada, gerada ou sintetizada nesta tarefa.
