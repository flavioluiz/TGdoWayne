# Síntese pareada C08 — complemento prospectivo

Fixado por ROOT após a engenharia independente, antes de executar as 128
posteriores principais C e antes do replay HIGH C07. Os resultados C07 já
publicados são conhecidos; este complemento não é apresentado como registro
anterior à campanha C07. Não muda seleção, sementes, likelihood ou critérios
de produção. Deriva do protocolo C08 com SHA
`188e4a0b5728b7437628152063ff4fe3cd6cbb1d8e89af8887b0824a5e40fb57`.

1. Sete contrastes, sempre operação nova menos anterior: A_CN−A0_CN,
   B_CN−A_CN, B_G−A_G, C_beta_CN−B_CN, C_beta_G−B_G,
   C_full_CN−C_beta_CN, C_full_G−C_beta_G.
2. Primário: diferença do limite U95 de u. Escala material: .01 da largura
   da priori. Secundários: outros 19 quantis e cinco larguras Q95−Q05,
   mantidos como descrição sem novas decisões de rejeição.
3. Reuso500: todas as identidades e falhas C07 permanecem. Quantis desses
   compactos têm apenas interpretação descritiva; a precisão vertical da
   CDF não certifica seu erro horizontal. Nenhum teste populacional de
   equivalência é obtido desse reuso.
4. Coorte32: os 24 IDs aleatórios fornecem a síntese pareada piloto; os oito
   casos de fronteira aparecem individualmente e como descrição separada.
   Nenhuma falha é substituída, omitida ou reclassificada pelo sinal do efeito.
5. Intervalo numérico da diferença: [l_novo−h_anterior,h_novo−l_anterior].
   Faixa trivial continua no cálculo. Para cada dado, classificar o intervalo
   relativo a [−.01,.01]: inteiramente acima/abaixo = efeito material resolvido;
   inteiramente dentro = compatibilidade operacional no caso; demais = inconclusivo.
6. Para a média nos 24 IDs, bootstrap pareado por ID com 10000 réplicas,
   semente 808110601 e o mesmo sorteio entre os sete contrastes. Usar
   percentis alpha/(2*7) e 1−alpha/(2*7), alpha=.05, para a família primária
   das sete médias. A envoltória operacional combina o percentil inferior
   das médias dos limites inferiores com o superior dos limites superiores.
   Publicar também o bootstrap das estimativas pontuais. Essa construção
   separa a variação entre dados da incerteza numérica e não é um intervalo
   frequentista exato. A calibração assintótica dos endpoints e a aproximação
   bootstrap, com n=24, limitam a interpretação conjunta; não alegar cobertura
   total de 95% pela soma de duas construções aproximadas.
7. A decisão sobre a média usa a mesma faixa material, com o rótulo de média
   piloto e a ressalva acima. Não implica adequação em todos os dados ou
   equivalência populacional. Casos individuais permanecem disponíveis.
8. Regimes fixos: u=[0,.5,.9,1], gamma=[3,4.25,5.5]. Contagens reais,
   limites direitos inclusivos apenas na última célula, sem cobertura
   condicional quando n<20. Sinal/ruído rotula os cenários usando parâmetros
   geradores, depois da inferência, e nunca altera a proposta ou seleção.
9. Não comparar logZ de A e B como fator de Bayes. O apêndice opcional de
   momentos/KL, se efetivamente executado e validado, mantém os quatro IDs
   previamente registrados e não estima ordenação média populacional.

Não há avaliações de likelihood ou leitura de HIGH C/C07 por este documento.
