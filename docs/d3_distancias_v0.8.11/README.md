# Omissões B_G e integração inicial de distâncias

As quatro omissões B_G completam o trio prospectivo A0/B_CN/B_G nos quatro
dados contaminados. A_G é um controle suplementar. Todos os quatro controles
primários e W1 passaram: o piloto totaliza 165 análises completas nesse alcance.
As diferenças de Q95 são negativas nesses dados fixos, sem inferência populacional.

Foram calculados 1920 novos pares de massa/escala, quatro frequências e três
resoluções. Todos passaram nos refinamentos angular e harmônico. As 12 integrações
iniciais (dois dados, três famílias, nominal/mistura) concordam entre GL32/64.
A mistura soma densidades conjuntas completas com pesos 0,25/0,5/0,25;
não mistura covariâncias nem introduz latentes independentes por frequência.

**Draft:** a referência adaptativa independente, os quantis, W1 e os eventos
de logL dessas posteriores ainda faltam. A concordância GL32/64 não substitui
essa referência. Os controles ORF têm alcance nos nós finitos calculados.
Os casos de engenharia não são SBC. C09 permanece aberto.

- [Auditoria e resultados](../../results/C09/D3_distancias_iniciais/audit.json).
- [Manifesto dos arquivos restauráveis](../../results/C09/D3_distancias_iniciais/manifest.json).
- [Omissões B_G](../../results/C09/D3_distancias_iniciais/BG_fontes_execucoes.zip).
- [Distâncias, fontes e execuções](../../results/C09/D3_distancias_iniciais/distancias_fontes_execucoes.zip).

O lote adiciona 127999 avaliações de likelihood; C09 acumula 5783577.
As respostas de distância consumiram 262,85 s CPU; omissões e integrações,
11,16 e 1,76 s CPU. Nenhuma simulação deste lote permanece em execução.
Próxima etapa: referência independente de distância, controles funcionais
restantes e campanha representativa D3/SBC, antes do encerramento C09.
