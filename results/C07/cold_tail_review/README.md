# Auditoria da cauda de propostas frias do C07

Estado: seis propostas novas foram congeladas e avaliadas; o caso original que
falhou foi reproduzido byte a byte. A inspeção encontrou deficiência local da
proposta, sem erro na densidade ou na verossimilhança. A ampliação local descrita
abaixo tem validação de densidade/sorteio, mas ainda não aprovação inferencial.
Tudo neste diretório é temporário. Nenhuma fonte da raiz foi alterada.

## 1. Comparação prospectiva de treinos

`config.json` foi congelado antes de qualquer execução. Alvos globais
25=A_CN/dado9, 51=A_G/dado3, 78=B_G/dado14; quatro cadeias; treinos novos de
8192 e 32768 passos, sementes 907140101/907140102; seleção fixa de 2048 estados;
quatro componentes EM, 80 iterações, piso 0,03 e inflação 1,1. Todas as seis
propostas ficaram fixas antes da produção IID. Cada alvo/treino/nível/réplica
teve uma corrente independente pela receita em `config.json`.

Nenhuma verdade injetada foi lida. A grade de 54 cortes (cinco parâmetros e
logL, nove probabilidades) estava fixada por um piloto anterior independente.
A ordem física é **u, log10 Agw, gamma_GW, log10 Ar, log10 EFAC**. Os cortes em
logL provêm da tabela antiga553, mas continuam cortes escalares fixos válidos
para planejar o erro da função com a tabela8336; não comparamos as duas ORFs
como se fossem iguais.

| Treino | IID por réplica | Alvo25: cortes/54, MCSE máximo | Alvo51 | Alvo78 |
|---|---:|---|---|---|
|8192|16384|53; 0,003656|51; 0,004863|51; 0,004476|
|8192|65536|54; 0,002014|54; 0,002295|54; 0,002781|
|32768|16384|54; 0,002956|47; 0,005652|32; 0,012052|
|32768|65536|54; 0,002058|54; 0,002708|54; 0,001870|

A precisão por corte segue MCSE <= 0,00335, usando o máximo entre influência
IID e dispersão de réplicas; ESS não substitui esse cálculo. As três famílias
separadas de 162 contrastes (dois refinamentos e comparação entre treinos no
nível alto) não apresentaram discordância simultânea, com maiores desvios
padronizados 2,906, 2,478 e 2,404. O alvo78 no nível baixo do treino32768 teve
pmax=0,010563 e falhou a guarda de exclusão individual. A passagem dos novos
níveis altos **não corrige retrospectivamente** o caso original25 e não garante
que um treino mais longo elimine caudas raras.

Resultados completos: `results/grid_diagnostics.json`, resumo
`results/grid_summary.json`. Fontes usadas: `executed_sources/src/`, manifesto
`source_manifest.json`. Configurações, sementes, estados selecionados, janela
adaptativa final, todas as seis propostas e os quatro NPZ completos permanecem
preservados. Nenhum desses estados de treino é chamado de amostra posterior.

## 2. Reprodução da falha original25

`replay_original.py` usou os módulos arquivados da execução original, copiados
para `replay_sources/src/`; a proposta original e a semente de produção
907130102 foram mantidas. Os oito arquivos brutos de 16384/65536 x quatro
réplicas reproduzem exatamente seus SHA256 históricos. Os estados de RNG
antes/depois também conferem. Manifestos, receita e dados estão preservados;
nada foi sobrescrito na execução original. `results/replay_summary.json` traz
os oito pares de hashes.

O maior peso da produção original alta pertence à réplica0, índice18751:

- Peso normalizado 0,0113267698944, suficiente para dominar o erro observado.
- Unidade [u, Agw, gamma, Ar, EFAC] =
  [0,192314; 0,999307; 0,539506; 0,742585; 0,800152].
- Física: log10Agw=-14,001385; gamma=4,348764; log10Ar=-15,143538;
  log10EFAC=0,180710. Agw está perto do limite superior de sua priori.
- Logit Agw=7,27425; menor distância quadrática de Mahalanobis às quatro
  Gaussianas=69,7714. A Student global fornece 0,99999999934 da densidade q
  nesse ponto.
- LogL=-72,67223316363867. Recomputar covariâncias e momentos e aplicar
  Cholesky independente nos 20 maiores pesos concorda até 2,85e-14. Esse
  controle usa a mesma ORF interpolada aprovada; não é nova quadratura ORF.
- A densidade q concorda com a soma explícita de densidades SciPy até
  1,64e-13 nos três ajustes examinados.

Assim, trata-se de uma deficiência local da proposta ao longo de Agw alto e
inclinação moderada; há variabilidade de pesos legítima, não bug detectado de
RNG, normalização ou kernel. A interpretação como modo separado não está
estabelecida: a evidência é compatível com prolongamento curvo e cauda de uma
região posterior. A proposta nova8192 aumenta a densidade nesse ponto 3,125x;
a32768 reduz para 0,331x. Isso demonstra por que aprovar uma semente nova não
resolve o problema de projeto.

`results/tail_audit.json` contém formas das componentes, vinte pontos,
responsabilidades, controles independentes e regiões exploratórias. Estas
regiões foram escolhidas após ver os pesos: seus números não são critérios
prospectivos ou certificação de posterior. Eventos sem presença em todas as
réplicas ficam com erro não resolvido, serializado como null.

## 3. Candidatos: comparação de densidades, sem nova produção

O relatório autoritativo é `results/tail_density_comparison_v2.json`; não
confundir cálculos exploratórios de pesos com uma produção da nova proposta.
Nenhuma amostra já produzida sob q_antiga pode ter seu denominador simplesmente
trocado por q_nova e ser apresentada como amostra desta última.

No ponto mais extremo original25:

| Candidato | q_nova/q_antiga |
|---|---:|
| Student global nu=3, mesma covariância, fração0,15 |0,69263|
| Quatro Student locais nu=5, covariâncias preservadas; global igual |1,73643|
| Mistura meio a meio de ajustes8192 original e novo |2,06233|
| 0,75 GM(C) + 0,10 GM(9C) + 0,15 Student global |10,42932|

A Student nu=3 tem cauda assintótica mais pesada, mas reduz a densidade no raio
observado. Para dimensão5 e covariância igual, com r² quadrático nessa matriz,

    t3/t5 = (3/8) 3^(5/2) (1+r²/3)^5 / (1+r²)^4
           ~ r² / (8 3^(3/2)).

O ponto observado tem r²=14,9494 depois da escala global3; a razão é0,69263.
A troca nu=3 não é recomendada para esse problema apenas com argumento de
cauda assintótica.

O candidato local amplo reutiliza a classe de densidade já auditada: oito
Gaussianas, copiando as quatro médias e covariâncias originais; quatro têm
covariância C e massa total0,75, quatro têm covariância9C e massa0,10. A mesma
Student global conserva massa0,15. O fator3 em desvio padrão repete a escala
ampla já usada na proposta global. A regra é fixa, igual para qualquer dado,
sem aprender componentes a partir da produção ou da verdade. Em todo ponto:

    q_ampla >= (0,75/0,85) q_antiga = (15/17) q_antiga.

Portanto o ganho exploratório de cobertura não pode reduzir a densidade
original por mais de11,765%; a distribuição científica posterior não muda.
Isso **não garante** MCSE suficiente: uma nova produção independente deve
confirmar a proposta, com o mesmo protocolo.

`wide_component_validation.py` testou a densidade contra SciPy e o sorteio
vetorizado contra 40 CDFs analíticas projetadas de uma mistura Gauss/Student,
com 65536 sorteios de engenharia, semente907140110 e família de erro0,01.
Não houve chamadas à verossimilhança e não há aprovação inferencial nesse teste.
O custo adicional é de densidade em oito componentes, sem novo treino ou banco
de verossimilhança. Está proposto um teste de16 alvos, dois níveis16384/65536,
quatro réplicas, 5.242.880 avaliações, antes de qualquer campanha500.

## 4. Recursos e integridade

Comparação nova: 2.457.624 avaliações; replay original:327.680; vinte controles
Cholesky independentes. Total2.785.324 de um orçamento10milhões. Pico RSS da
comparação4.001.906.688 bytes em Darwin, abaixo4GiB por293.060.608 bytes; esse
pico observado não é uma garantia de limite RSS. Bancos estimados e RSS são
medidas diferentes. Arquivos brutos privados continuam preservados.

As fontes antigas tiveram dois erros apenas de API no script auxiliar:
`diagnose_tail.py` usou atributo inexistente `covs`; v2 corrigiu para `cov`,
mas passou um escalar onde a tabela requer vetor. `diagnose_tail_v3.py` é a
execução concluída. Os scripts/logs malsucedidos ficam como histórico; nenhum
resultado científico veio deles. `compare_tail_densities.py` tinha uma frase
assintótica incorreta; v2 corrige a frase e acrescenta as Student locais. Os
valores de densidade da v1 estavam corretos. Não se substituíram bytes usados.

Recomendação: validar prospectivamente a defesa local ampla, conservando a
falha original e o protocolo. Se houver falha em algum dado futuro, registrar
a incerteza e aplicar apenas uma regra de remediação previamente declarada;
não repetir sementes até obter passagem nem declarar cobertura500 com base
em três ou dezesseis casos de engenharia.

## 5. Novo ensaio16 da ampliação fixa

Após autorização explícita do root, `wide_production/config.json` congelou as
16 propostas derivadas, sementes907150101, dois níveis16384/65536 e quatro
réplicas. Foram usadas **todas as mesmas propostas frias originais** do piloto
integrado, inclusive o ajuste25 que falhou. A regra ampla foi idêntica nos16
casos. Nenhum ajuste foi substituído por uma semente favorável.

A execução terminou com5.242.880 avaliações novas,8.028.204 cumulativas no
orçamento10milhões. Produção e IO levaram8,771s após setup10,704s; RSS máximo
3.494.854.656 bytes. Permanecem128 arquivos NPZ armazenados sem compressão,
592.741.120 bytes. Esses tempos curtos medem este ensaio16 com fontes e ambiente
registrados; não são promessa de tempo da campanha500 ou sua diagnóstica.

O protocolo adicional de54 cortes fixos semverdades passou864/864 no nível
alto; maiorMCSE0,00258901, alvo78. Todas16 guardas de exclusão individual passam.
No alvo25, MCSEmáximo0,00198234, pmax0,000626419 e ESS de concentração83029.
Os864 contrastes de refinamento independentes não discordaram sob a família
simultânea declarada (maior desvio padronizado3,17270). As falhas do nívelbaixo
continuam presentes no relatório completo, sem serem ocultadas.

A fonte genérica de diagnósticos, as grade/cortes e os hashes de todos os raws
estão registrados em `wide_production/fixed_grid_diagnostics.json`; resumo em
`fixed_grid_summary.json`. O checker independente dos26CDF/PIT e20brackets
A0d14 será entregue pelo agente `introducao_c02`. A passagem destes54 cortes
não substitui esse checker nem constitui aprovação da campanha500.

Ver `wide_production/PROVENANCE_NOTE.md` antes de integrar as propostas: os
hashes novos dos arquivos derivados são válidos e foram conferidos, mas alguns
campos de identidade internos foram herdados como histórico do ajuste. O ROOT
deve criar registros novos com identidade própria para a política ampliada.

Auditoria adicional das16 propostas: `wide_production/all_densities_audit.json`
confere512 âncoras contraSciPy, os parâmetros originais/cópias e o limite
q_ampla/q_original >=15/17. O teste exige igualdade exata do logq armazenado
quando o mesmo lote é reavaliado. A primeira versão tentou exigir igualdade
bit a bit após trocar o tamanho do lote para32; isso falhou por arredondamento
BLAS. `audit_all_densities_v2.py` reavalia o lote original inteiro e só então
seleciona32 âncoras, mantendo o critério de igualdade exata. O histórico da
primeira verificação permanece em seu script/log; nenhuma amostra mudou.

O checker independente fechou em `tmp/c07_wide16_diagnostics/`:416/416 CDFs,
96/96PITs,16/16 guardas e20/20 brackets A0d14 passaram no nívelalto;
MCSE máximo0,0026238534, alvo62/A_G/logLtruth. Não houve falhas ou casos
não resolvidos em3264 comparações de réplicas e152 de refinamento. Todas128
SHA256 e identidades de logw conferem. Esse resultado é aprovação deste ensaio
de engenharia, não resultado SBC500. A verificação final independente dos54
cortes está sendo documentada separadamente pelo mesmo agente.

`NOTA_VARIANCIA_PROPOSTA.md` deriva por que a defesa Student já dá momentos
finitos neste modelo compacto e por que q_ampla>=15/17 q_antiga limita a piora
da variância assintótica de qualquer CDF a17/15 (erro padrão a1,06458x).
Não é garantia de precisão de uma produção finita ou justificativa para
ignorar qualquer diagnóstico que venha a falhar.
