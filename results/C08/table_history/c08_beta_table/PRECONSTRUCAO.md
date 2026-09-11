# Construção proposta apenas da tabelaC_beta

Estado: **não iniciada**. Pré-cálculo de nós e custos em `preflight_v2.json`;
`prepare_preflight_v2.py` não chamou quadratura, base harmônica ou likelihood.
Este documento delimita a próxima autorização, sem modificar a execuçãoC07.

## Método e fontes

Criar um pacote temporário com cópias exatas e hashes de `orf_blas.py`, módulos
C05 usados, geometria e a primeira curva da tabelaC07. Um novo construtor
aceitaráβ explícito porcanal, chamando `RealHarmonicBasis.evaluate(beta,y_k)`.
Não usar `ExactNodeORF.evaluate(u)`: ele insere o caminho dispersivoB, diferente
deC_beta. Nenhuma fonte/cache doC07 será editada.

A assinatura do cache novo inclui schemaC08_beta, canal, β efetivo, fases,
pontos, ordens, normalização e hashes de fontes. Valores existentes só são
reutilizados após validação de assinatura/coordenadas/hash/shape/finitude/
Hermiticidade/PSD e erros coarse/fine finitos. Arquivos são novos e atômicos;
colisão discordante aborta. Checkpoints por frequência/resolução e blocos
permitem interromper sem reclassificar uma tabela parcial como completa.

Canal1: reutilizar sua splineC07 numericamente em todoβ, preservando os nós e
breakpoints. Canais2/3/4: construir curvas novas em todoβ∈[0,1], com as fases
reais. A frequência1 **também** recebe143 verificações harmônicas independentes
nos nós de validação; a aprovaçãoC07 não é herdada para a respostaC_beta.

## Nós e orçamento fechado

As malhas são uniformes emβ com8193 pontos, mais camada j/131072 no canal2 e
j/262144 nos canais3/4, j=0…128. Coarse usa4097 e j pares. Converter β→u e
recalcular β efetivamente representável antes da avaliação, removendo
explicitamente duplicatas. Isso evita tabelar um ponto diferente daquele
representado pelo kernel emu perto de1.

| Canal | Nós novos de tabela | Coarse de interpolação | Avaliaçõesincluindo controles | Multiplicações reais |
|---:|---:|---:|---:|---:|
|1|0, primeira curva reutilizada|curvaC07|143|0,03174T|
|2|8313|4157|8454|6,90479T|
|3|8317|4159|8458|15,10275T|
|4|8317|4159|8458|26,46915T|

Total pré-calculado: **48.508.435.951.296** produtos reais; teto50T;
reserva1.491.564.048.704. A estimativa conta as duas multiplicações reais por
coeficiente harmônico (partes real/imaginária), em ordens grosseira e fina,
e já inclui143 pontos de validação e as âncoras diretas. Não contar esse número
como FLOPs universais: recorrências, contrações geométricas e quadratura direta
têm contadores próprios. Não fazer novo refinamento que ultrapasse o teto.

Uma base por frequência/resolução, loteβ8, BLAS `VECLIB_MAXIMUM_THREADS=1`,
nenhum pool e nenhum subprocesso paralelo. Maior estimativa base+buffers
594.231.232bytes; com resultados/reserva≈652.83MB. Teto estimado1GiB e teto
operacionalRSS1,5GiB=1.610.612.736bytes, medido em bytesDarwin. Registrar RSS
antes/depois da base e a cada checkpoint; interromper/retomar se houver
pressão de memória ou competição prejudicial comC07. Isso é monitoramento
operacional, não uma garantia que `ru_maxrss` imponha um limite ao sistema.
Pré-verificar somas de arrays antes de alocação. Banco nativo de likelihood
C08 não será construído neste processo.

A união dos nós de todas as curvas, preservando também os breakpoints antigos
do primeiro canal, tem8464 pontos. Matrizes comuns≈78MB; coeficientes cúbicos
≈312MB. Gerar a representação comum por subdivisão algébrica dos polinômios;
não refazer uma spline sobre pontos amostrados de outra spline sem validar
essa mudança. Liberar bases harmônicas antes de reunir/interpolar curvas.

Projeção histórica: cerca de29min de BLAS em condiçõesC07 anteriores, acrescida
de controles e contenção com a campanha500. Reservar até45min de trabalho em
um processo, mas medir; não prometer esse tempo ou que8193 nós bastarão.

## Gates numéricos antes de chamar a tabela de utilizável

1. **Por nó**, exigir ordens coarse/fine nas resoluções de `preflight_v2.json`,
   diferença absoluta da matriz≤1e-8, finitude, Hermiticidade e PSD com o mesmo
   limiar de arredondamentoC07, sem clipping. Guardar erro porcanal/nó.
2. **Âncoras físicas/analíticas:** β=0, expressão exata de posto≤5 e derivada
   β nula; β=1 confrontado com o caminho masslessC07. Preservar fases e
   normalização; não zerar a resposta no limiar.
3. **Método independente:**24 pares/casos diretos, canais2–4, β desejados
   [.001,.05,.5,.9] e pares(3,8)/(0,11), nas fases reais. As coordenadas usadas
   são os β efetivos após conversão. Cada caso tem quadratura direta coarse/
   fine própria, com todas as ordens≤20000. Exigir diferença interna e contra
   a matriz harmônica≤1e-7, com tolerância absoluta perto de zeros. O orçamento
   angular planejado é2.051.757.104 pontos/produtos de ordem, teto8bilhões;
   memória direta estimada máxima514.552.384bytes. As ordens são proporcionais
   aβy e crescem entre as duas resoluções; isso é uma proposta a verificar,
   não uma prova analítica de convergência. Não guardar base deLegendre durante
   o pico da quadratura direta.
4. **Interpolação:** splineclamped derivadaβ=0 no limiar, PSD de controles de
   Bernstein e fallbacklinear explícito quando necessário. Comparar curvas
   coarse/fine e fine/oráculo em143 nós, com128 sorteados independentemente
   por massa,β e logβ, mais âncoras determinísticas. Registrar separadamente
   pontos off-grid e pontos que coincidem com a malha; não chamartodos143 de
   off-grid. Fonte/seed808120101 jácongeladas.
5. **Sensibilidade da likelihood, sem nova inferência:** usar as16 observações
   antigas de engenhariaC07 e64 nuisances uniformes com seed independente,
   fixada antes do cálculo; comparar o normal comprimidoC_beta em resposta
   coarse, fine eoráculo. São143×64×32×3=878.592 valores de logL, teto1M.
   Recalcular μ/Σ por traços, incluindo normalização; não usar um banco nativo
   gigantesco. Exigir |ΔlogL|≤.001 tanto para coarse/fine quanto fine/oráculo.
   Estes pontos não são uma posteriorC e não exigemRNG/doação de dados500.

Uma falha de gate preserva a tabela parcial/candidata e o relatório. Não
relaxar tolerância ou crescer a malha automaticamente. A reserva abaixo50T
permite apenas um refinamento posteriormente decidido e orçado; uma malha
16385uniforme excederia o teto e não está autorizada.

## Produto e o que ele ainda não aprova

Entregar matrizes, curvas/interpolador, hashes, relatórios coarse/fine/diretos,
âncoras e logL, custo/RSS e descrição do domínio. Só declarar **tabela candidata
aprovada nesses gates** se todospassarem. Antes de usar numa posteriorC_beta,
ainda é preciso comparar a interpolação em pontos relevantes da própria
posterior e executar os testesIID de precisão. Não transferir a aprovação para
janelaHann, outras durações/fases, famíliasA ou500posteriorsC.

O mapa distribucionalT/janela sugerido pelo root tem protocolo/orçamento
separado em `tmp/c08_execution_design/`; não está incluído nesta construção
nem será iniciado junto dela sem nova coordenação.
