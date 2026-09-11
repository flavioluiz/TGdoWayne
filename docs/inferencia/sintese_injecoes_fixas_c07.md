# Síntese condicional fixed96, versão 1 prospectiva

Preparada em10/09/2026, antes da produção dos posteriores fixed96. O pacote
não lê a campanha500 e não executa verossimilhanças, treino ou amostragem.
Mantém três cenários de32 dados e somente o modelo A0_CN. A análise é um
diagnóstico condicional a verdades fixas; não há KS, teste de uniformidade,
Holm, comparação de Bayes factors ou seleção de alvos aprovados.

## Inventário e proveniência

O leitor exige `campaign_complete.json` com os96 IDs exatos, a mesma identidade
do plano e escopo `FIXED_TRUTH96_NOT_SBC`. Confere96 JSON e96 NPZ mascarados,
seus nomes, target/datum/modelo/schema/status, formas e tipos dos arrays,
máscaras e valores de verdade contra a geração congelada. Rejeita missing,
duplicatas, tipos impróprios, seleção de subconjunto ou schema da campanha500.

São conferidos os hashes dos dados/configuração experimental, geração,
protocolo científico original, protocolo numérico e síntese. Os hashes dos
scripts usados pelo produtor/runtime são verificados contra seus snapshots;
os do leitor contra os snapshots do runtime/driver. As oito réplicas por alvo
precisam ocupar exatamente os dois níveis16384/65536 e réplicas0…3, com os
mesmos hashes do produtor. O recibo ROOT é conferido com o arquivador existente:
preserva produtor, diagnóstico, NPZ, proposta e oito checkpoints/RNG. Os hashes
arquivados devem concordar com os produtos lidos. O estado numérico arquivado
precisa ser consistente com os arrays, inclusive a lista final de não resolvidos.

O manifesto externo de evidências usa o mesmo formato de entradas com
`role/path/sha256`, exigindo ORF, kernel e referência posterior. Isso registra
presença e integridade da evidência revisada; não afirma validade universal
da inferência em cada cenário fixo a partir de uma chave de aprovação.

## Máscaras e finalidades

Nos dois cenários com sinal, as cinco coordenadas e logL na verdade são
definidos. Na ausência exata de GW, somente log10_Ar e log10_EFAC possuem
verdade: massa, amplitude, inclinação GW e logL-na-verdade continuam NaN com
`applicable=false`. Não recebem PIT, cobertura, viés de recuperação ou valor
finito substituto. Os20 quantis de cada posterior continuam registrados como
descrição do ajuste do modelo sinal+ruído fora da priori geradora.

Em u=0 com sinal, a priori contínua sem átomo e o suporte u≥0 provam
`F_u(0)=0`. Seu intervalo numérico é exatamente[0,0], com flag estrutural;
não depende de contagens MCMC/IID. Dessa forma,[0,U90] possui cobertura
estrutural1 e o intervalo central de caudas iguais exclui0, cobertura estrutural0.
Ambos são explicados como propriedades do suporte; não como reprovação de
uma exigência de90% frequentes para intervalos Bayesianos.

Outras funções constantes amostradas continuam não resolvidas. A elegibilidade
numérica de cada PIT requer sua MCSE≤0,00335, resolução finita, seus12
contrastes entre réplicas, seu refinamento, os12 contrastes/refinamento de logZ,
controle de peso nos dois níveis e saturação≤10⁻¹². Uma falha de outro PIT ou
dos20 cortes auxiliares não reprova automaticamente todas as funções.
O caso estrutural é independente desses controles amostrais; as falhas dos
demais integrais permanecem no mesmo alvo e no inventário.

## Sensibilidade numérica prospectiva

Para cada PIT aplicável e resolvido, usa-se

`[max(0,Fhat−0,002−z×MCSE), min(1,Fhat+0,002+z×MCSE)]`,

com `z = Φ⁻¹(1−0,01/(2×576))`. A família576=96×6 é fixada antes da execução e
não diminui quando funções indefinidas/estruturais são omitidas. Existem448
PITs aplicáveis, dos quais32 são estruturais; a família mantém a reserva
conservadora. Os20 cortes auxiliares não entram nesse envelope de PITs.
Funções aplicáveis não resolvidas recebem[0,1]. Valores indefinidos recebem
NaN; não há clipping dos PITs calculados nem substituição por zero.

Essas faixas são uma análise **aproximada de sensibilidade numérica**, fundada
na estimativa assintótica de MC e no componente determinístico de referência.
Não constituem confiança exata conjunta: nem quatro réplicas nem pesos
observados moderados excluem caudas ou modos não visitados. O uso conservador
dos extremos é matematicamente válido condicionado à validade das faixas.

Por cenário e função definida, reporta-se a ECDF descritiva dos PITs com limites
`#{upper_i≤t}/32` e `#{lower_i≤t}/32`. Nenhuma comparação com distribuição
uniforme é feita. Os32 dados sempre permanecem no denominador, inclusive
PITs numericamente não resolvidos.

## Cobertura condicional e quantis

Para cada parâmetro definido, contam-se as inclusões no intervalo desde o
limite inferior da priori até U90 (`PIT≤0,9`) e no intervalo central de90%
(`0,05≤PIT≤0,95`). Sob a posterior contínua declarada, essas identidades
relacionam a CDF verdadeira com os quantis; as contagens calculadas a partir
da CDF estimada permanecem condicionais à integração numérica.

São apresentados k/32 e intervalos Clopper–Pearson pontuais de95%, sem p-valor
contra uma hipótese de cobertura0,9. Esses intervalos resultam da inversão
binomial exata para a frequência das decisões calculadas em dados/aleatoriedade
independentes sob o mesmo procedimento. Não removem erro de integração nem
garantem a cobertura do intervalo posterior ideal. A resolução binomial é
grosseira: desvio padrão5,30 pontos percentuais em probabilidade0,9 e máximo
8,84 pontos; a precisão da campanhaN500 não se aplica aqui.

As faixas numéricas determinam contagens mínima/máxima: no limite superior,
`upper≤0,9` garante inclusão e `lower≤0,9` permite inclusão; no central,
inclusão certa exige `[lower,upper]⊆[0,05;0,95]` e possível exige interseção.
Reporta-se também a união dos intervalos CP sobre essa faixa de contagens,
obtida pelos extremos monotônicos. É uma combinação condicional de
sensibilidade aproximada e intervalos binomiais pontuais, não um intervalo
simultâneo exato. O caso estrutural explicita separadamente o valor1 ou0
conhecido, além do registro amostral.

Os20 quantis são resumidos por mínimo/mediana/máximo entre os32 dados, com
contagens dos controles de CDF em cortes independentes. Isso não certifica
erro horizontal dos quantis. O relatório não calcula viés para parâmetros
sem verdade e não atribui um limite em unidades físicas de massa sem a
transformação/escala explicitamente especificada no experimento.

## Verificações e limites da entrega

Dez testes passaram. Eles verificam contagens de contrastes192/204/156 e
6/7/3; máscaras; tratamento estrutural; falha por função; MCSE infinita;
rejeição de flags falsas; CP por inversão independente das caudas binomiais;
contagens possíveis por enumeração; preservação de96 alvos; família576 fixa;
e inventário/arquivo ROOT com fixtures determinísticas TOY de96 alvos.
O teste completo preserva um alvo deliberadamente não resolvido e rejeita
arquivo ausente, schema errado e fonte alterada. Não são posteriores PTA.

`results/toy_summary.json` é um exemplo rotulado TOY, sem amostras físicas,
sem seed aleatória e sem avaliações de likelihood. Os arquivos ROOT e as
fontes usadas pela produção500 não foram modificados.
