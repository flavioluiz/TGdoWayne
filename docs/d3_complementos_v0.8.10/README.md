# Complementos do piloto D3

Foram geradas nove observações gaussianas B: três prioris centrais e três
variantes adicionais de covariância (diagonal variável, completa fixa e
diagonal fixa). A distribuição geradora coincide com a família analisada;
a média continua variável e a âncora é u=0,5. São controles de engenharia,
não uma nova amostra SBC. Uma reconstrução com momentos por traços e streams
RNG preservados reproduziu as observações com erro máximo 4,44e-16.

Os quatro dados contaminados do piloto foram reanalisados omitindo o
contaminante em A0, A_G e B_CN, preservando exatamente as observações.
As 21 análises novas passaram nos cinco controles primários. Foram cobradas
454608 avaliações e 38,85 s CPU, sem novas respostas ORF.

Os doze contrastes de Q95 (omissão menos inclusão) são negativos nos casos
fixos avaliados. Isso não estabelece uma direção universal ou uma frequência
populacional. No dado gaussiano 10, Q95 passou de [0,9677; 0,9687] para
[0,1075; 0,1085], excluindo a massa injetada u=0,5 ao omitir o monopolo.
KL passou de 0,0833 para 2,2281 nat. Uma posterior mais distante da priori
não comprova adequação do modelo; estreitamento não basta para escolher
a análise. O exemplo não é uma restrição observacional.

A referência W1 foi estendida para integrar várias curvas em uma malha
adaptativa comum, mantendo likelihood, priori, escala e normalização próprias
em cada coluna. A reutilização de fatorizações não reduz a contagem de valores
de likelihood. Dois refinamentos e integrais tabuladas são confrontados;
os testes analíticos também verificam que as colunas não são confundidas.
As 161 análises passaram em W1, com maior discrepância 5,154e-6. Foram
contabilizadas 1315806 avaliações adicionais. Os demais workers somaram
249,52 s CPU medidos, separados da reserva debitada ao primeiro worker.

A primeira execução W1 terminou as referências, mas falhou ao serializar
flags NumPy. As referências e caches foram recuperados sem novas likelihoods.
Como o tempo do worker não foi gravado, sua reserva de 60 s foi debitada
explicitamente, sem apresentá-la como medição. A recuperação não teve tempo
instrumentado. O código foi corrigido e ganhou teste de regressão de JSON.
Fonte original, logs e estados de falha permanecem no pacote.

- [Auditoria e resultados por curva](../../results/C09/D3_complementos/audit.json).
- [Controles e omissões](../../results/C09/D3_complementos/controles_e_omissoes.zip).
- [W1, fontes e execuções](../../results/C09/D3_complementos/W1_fontes_execucoes.zip).
- [Manifesto e dependências](../../results/C09/D3_complementos/manifest.json).

Ainda faltam as posteriores da mistura de distâncias, os eventos de logL e
a campanha representativa D3/SBC. Todos os controles mantêm alcance operacional
em domínio físico finito, sem certificado uniforme de erro de probabilidade.
C09 permanece em andamento; C10–C13 também não foram concluídos.
