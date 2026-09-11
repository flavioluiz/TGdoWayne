# Decisão ROOT: avanço de C09 por quantidade avaliada

Esta decisão autoriza o desenho prospectivo de gates distintos para as quantidades
da posterior. Não autoriza uma execução física D2/D3, não altera os resultados
históricos e não conclui C09. Cada nova execução ainda terá configuração, fontes,
dados, referências e orçamento fechados e revistos antes de começar.

O parecer independente `tmp/c09_scope_gate_review_v1/PARECER.md`, SHA-256
`c61bc9e08c61ac8a00c4cead60b26a8f295be42ed699e198f1d911b19f8c68b2`, foi lido
integralmente. ROOT aceita sua distinção entre a CDF da massa, cuja fronteira de
integração é conhecida, e o evento de log-likelihood, cuja fronteira depende da
forma da função. O exemplo analítico oscilatório do parecer demonstra que esses
dois problemas podem exigir resoluções diferentes; ele não valida as curvas PTA.

O protocolo anterior, preservado em `tmp/c09_completion_design_v1/PROTOCOLO.md`,
condicionava D2 à aprovação conjunta de D1. Para os novos pacotes D2/D3, essa
dependência é substituída por validação específica da quantidade que será usada.
O evento de logL conserva integralmente seu gate próprio, incluindo massa ambígua,
referências de numerador/denominador e evidência do backend. Sua falha não será
convertida em PASS por aprovar uma CDF de massa.

## Requisitos aceitos para os novos pacotes

1. Congelar os dados compartilhados, modelos, medidas normalizadas, suportes,
   contrastes, cortes, referências e regras de parada antes das novas análises.
   O fatorial completo/diagonal × fixo/variável usa exatamente a mesma observação,
   média variável, âncora u=0,5 e determinante completo da covariância. Oito novas
   curvas são um desenho candidato; sua seleção final deve constar do preflight.
2. Cada CDF de massa tem seu próprio numerador e denominador, referências e
   comparação entre resoluções. Preservar ΔlogZ≤0,001, ΔCDF≤0,002 e brackets
   de quantil de largura≤0,001 em u. Os endpoints devem satisfazer a desigualdade
   conservadora `F_ref(lo)+r(lo) ≤ q ≤ F_ref(hi)-r(hi)`, com concordância dos níveis.
   Preservar deltas de momentos, KL e W1≤0,001; não derivar sua aprovação do flag
   de outro produto. Para W1, a própria integral entre CDFs precisa de controle.
3. Exigir valores finitos, PSD/fatorações válidas, referências sem warnings e
   alcance explícito do backend. Uma discrepância física observada em pontos
   finitos não se torna um bound uniforme de probabilidade. Resultados da tabela
   e evidência física no domínio testado continuam identificados separadamente.
   Uma quantidade sem evidência suficiente permanece UNRESOLVED.
4. Os históricos nominal14 e D1 permanecem intactos. Não basta retirar
   `offgrid_form` de um Boolean antigo. Qualquer suplemento que reaproveite
   referências salvas deve verificar a mesma função, os SHA e a suficiência
   dessas referências para a nova regra, conservando o histórico original.
5. Manter os 18 grupos matched-SBC de 500 e a família planejada de 126 testes
   com Holm α=0,05. Há 108 testes de massa/cobertura e 18 de logL. Se parte dos
   últimos não puder ser avaliada, seus slots ficam explicitamente pendentes;
   eventual p=1 usado pelo algoritmo de multiplicidade é preenchimento
   conservador, não um resultado de aprovação. Intervalos de PIT pendentes
   [0,1] propagam-se às conclusões; nenhum dos 500 IDs é removido.
6. Verdades fixas de engenharia não são SBC. Os dados de cada grupo SBC devem
   ser gerados da própria priori e família analisadas; prioris alternativas não
   recebem calibração por reponderar um banco com outra medida. Nuisances
   conhecidas definem um estudo condicional e não validam as marginais 5D.
7. A não rejeição marginal é uma conclusão restrita aos testes feitos. Um
   algoritmo que sempre devolve a priori pode passar um SBC marginal sob o
   prior preditivo; portanto, não se afirmará aprendizagem ou calibração global
   da posterior com base apenas nesse resultado. Diagnósticos dependentes do
   dado, informação posterior e comparações condicionais permanecem necessários
   para avaliar as outras alegações, dentro de seus próprios alcances.

## Estado no momento da decisão

O nominal14 histórico tem 14 flags CDF aprovados, nove intervalos mass-PIT [0,1],
quatro estreitos e um estrutural [0,0]. Treze logL-PIT históricos são [0,1].
Essas contagens não são reclassificadas por esta decisão.

A primeira continuação D1 foi executada e auditada: 325.629 novas avaliações
armazenadas e cobradas, 152,935084 s CPU adicionais, 449,022608 s cumulativos.
Nove eventos da **tabela salva** passaram; cinco atingiram o limite de 25 mil
avaliações ao integrar as referências. Os intervalos físicos de logL dessa
continuação continuam [0,1] porque a margem probabilística do backend não foi
configurada. A continuação D1b proposta para os cinco casos é um pacote separado,
com reaproveitamento explícito dos valores salvos e nova revisão de recursos.
Não existe retry automático nem substituição do registro D1.

Esta decisão permite implementar e validar D2 em paralelo ao tratamento dos
eventos pendentes. Não dispensa os cenários de ruído, espectro, contaminantes,
distâncias e variabilidade previstos em C09, nem autoriza descrever o marco
inteiro como concluído enquanto esses produtos ainda estiverem por executar.
