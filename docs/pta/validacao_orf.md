# Resposta tensorial de PTA: implementação e validação C05

O capítulo 4 deriva a resposta a partir do fóton e das frequências medidas por
observadores livres. A implementação é própria, construída das equações citadas;
não incorpora código dos autores dos artigos. Esta etapa valida a resposta TT,
sem inferência de massa ou modelo de população escalar.

## Convenções e referências primárias

`p` aponta da Terra para o pulsar; `Omega` indica propagação da onda. A fase é
`exp[+i omega(t-beta Omega.x/c)]`, conjugada da escolha de C04. Define-se
`beta=ck/omega=vg/c`, `y=2 pi fL/c` e `D=1+beta Omega.p`. A velocidade de fase é
`c/beta`. O ramo viajante exige `f>=fg`, com `fg=mg c²/h`; abaixo do limiar a função
recusa o argumento e não fabrica uma raiz real. Isso não é uma regra para excluir
dados ou impor limites empíricos de massa.

Na assinatura (+---), o núcleo positivo armazenado representa o ganho de frequência.
O redshift usual `z=(nu_P-nu_E)/nu_P` tem resposta com sinal oposto, e o resíduo de
atraso é sua integral. Esse sinal comum cancela na ORF. Para `H_0mu != 0`, a correção
dos observadores é necessária; o capítulo explicita sua redução à combinação
`Q_ij=H_ij+beta Omega_i H_0j+beta Omega_j H_0i+beta² Omega_i Omega_j H_00`.
Os testes C05 validam TT; a helicidade zero terá validação própria em C10.

Fontes consultadas no acervo:

- [Liang–Trodden, v3](https://arxiv.org/abs/2108.05344v3): seções III–IV e apêndice B;
  observadores e recepção Eqs.17–26; normalização e resposta TT Eqs.34–36;
  tradução preparatória do escalar Eq.45. A versão v3 é de 24/07/2026, apesar da
  publicação bibliográfica de 2021. A normalização do artigo é traduzida de sua
  definição algébrica, sem assumir que legenda e texto da Fig.3 sejam consistentes.
- [Cordes et al., v2](https://arxiv.org/abs/2407.04464v2): espectro Eqs.1–7;
  expansão harmônica Eqs.15–16; auto finita Eqs.22/25; limite assintótico Eq.37;
  fórmula terrestre Eqs.40–43. Essas expressões são referências independentes de
  integração, após compatibilizar polarizações e a normalização.

Usamos `e_A:e_B=2 delta_AB` e `Gamma=3/(8pi) integral sum_A R_a R_b*`.
Com `<h_A h_A'*>=Sh/(8pi) delta_AA' delta(f-f') delta²(Omega,Omega')`, o espectro
unilateral do resíduo é `Sr_ab=Gamma_ab Sh/(6 pi² f²)=Gamma_ab hc²/(12 pi² f³)`,
onde `hc²=2 f Sh`. Assim, `[Sh]=s` e `[Sr]=s³`. A diagonal não é renormalizada
para um em cada massa. Não se pressupõe uma relação com densidade de energia
de uma teoria completa de geração.

## Métodos e contrato de aceitação

`src/pta/response.py` contém a cinemática e a transferência sinc estável em `D=0`.
`src/pta/orf.py` contém o projetor TT integrado no céu, os multipolos de Legendre
e os benchmarks analíticos. O primeiro método usa Gauss–Legendre e trapézios
periódicos; o segundo usa uma recorrência de polinômios associados e soma multipolar.
A fórmula terrestre usa Decimal com 90 dígitos e limites especiais; a expansão
regular para beta pequeno tem um limite explícito para o resto no domínio da troca.

`pta.checked_orf` exige duas `Resolution`, um `ResourceBudget`, `atol>0` e `rtol>=0`.
Nenhuma resolução é presumida. A função compara separadamente nós harmônicos,
corte multipolar, quadratura direta e acordo entre métodos; apenas Terra utiliza
a referência analítica. Todos os erros devem ser menores que `atol+rtol*abs(Gamma)`.
Uma falha lança `ConvergenceError` com relatório, sem crescimento automático.
As rotinas `raw_` são instrumentos para construir esses controles e não certificam
convergência por retornarem um número finito.

O orçamento é conferido antes de qualquer quadratura. Seus proxies de trabalho e
memória não são garantias de tempo ou limites rigorosos de RSS. O envelope aceito
é `0<=y<=2*pi*1000.125+1`, com ordens no máximo 20000. Esse envelope limita a
extrapolação das campanhas; seus pontos interiores ainda precisam passar pelos
controles de convergência. Refinamento e acordo independentes são evidência empírica,
sem constituir uma prova de precisão universal em todo o contínuo.

Para uma matriz de rede, cortes comuns preservam a estrutura de Gram harmônica.
Aceitar pares isoladamente com cortes diferentes não assegura a positividade da
matriz montada. C06 deverá compartilhar multipolos, estimar o custo da rede e
verificar hermiticidade, positividade e condicionamento. Pequeno erro escalar da
ORF não certifica automaticamente uma inversa de covariância ou posterior.

## Testes integrados e evidências

`scripts/validar_orf.py` executou **23 testes**: oito testes da resposta, quatro
verificações físicas independentes e onze controles da interface. Os resultados
estão em `results/C05/test_results.json`, com hashes dos cinco módulos C05, do teste
e do script. O modo `--check` reexecuta os testes, confere hashes e versões de
NumPy/SciPy e não substitui o registro. Adicionar um módulo independente de outra
etapa não invalida por si só essa evidência.

A construção física independente forma polarizações explícitas num céu comum,
confronta a matriz harmônica e verifica uma rotação global, frequência negativa,
covariância real no tempo e continuidade na coincidência. Ela conserva pares quase
coincidentes e distâncias diferentes, nos quais a parte imaginária pode ser relevante.
Autovalores negativos na escala de arredondamento são distinguidos de falhas físicas.

Os registros `benchmark_results.json` (20 casos), `coherence_results.json` (16 casos
e duas raízes HD) e `independent_results.json` preservam as execuções iniciais.
`integration_equivalence.json` registra 32 comparações selecionadas entre protótipo
e módulos reorganizados, sem diferença numérica, e os hashes dos registros originais.
Esses arquivos não são apresentados como uma nova execução integral na raiz.
A campanha ampliada de aceitação é registrada separadamente por `benchmark_orf.py`.

A campanha integrada de `results/C05/checked_benchmark_results.json` executou 58 casos
em 64,82 s contra os módulos definitivos: 20 principais, 16 de coerência, 20 autos
com referência independente e dois zeros HD. Todos passaram; máximos absolutos dos
controles por grupo: 1,38e-12, 5,36e-12, 3,81e-12 e 1,63e-6. O confronto auto/1D
teve diferença máxima 7,05e-13. As resoluções, recursos e critérios foram fixados em
`configs/benchmarks_orf/c05.json` antes da execução. O script exige cada erro absoluto
<=1e-5 e, para |Gamma|>1e-5, também relativo <=1e-3, além do critério do wrapper.
As fontes, o script e a configuração possuem hashes antes/depois coincidentes.

A quadratura direta nos zeros HD não teve erro monotônico sob refinamento: o primeiro
zero passou de +1,843e-7 para -1,441e-6, ambos dentro da tolerância. O relatório
preserva ambos os valores e sua diferença; não seleciona a malha mais favorável.
O comando `--verify-only results/C05/checked_benchmark_results.json` confere o registro
contra as fontes/configuração atuais sem alegar uma nova execução das integrais.

A [auditoria independente](auditoria_independente.md) documenta as fórmulas e os
problemas da interface inicial. As correções estão na implementação integrada:
domínio comum, fases sempre em pares, resolução obrigatória, teto de recursos e
rejeição da auto GR sub-resolvida. O exemplo de sub-resolução demonstra por que
apenas retornar uma curva plausível não é um critério de validação.

## Alcance dos limites e reprodução

No limiar, `Gamma_aa=(4/5) sin²(y/2)`: grande distância sozinha não elimina fases.
A escala de variação angular é `beta*y`; a coerência do par depende também de
`beta |y_a p_a-y_b p_b|`. A ORF completa é contínua na coincidência espacial.
O salto da aproximação Hellings–Downs envolve incoerência e uma ordem de limites.
Incerteza de distância, largura de canais e médias de fase ainda exigem modelagem.

```sh
.venv/bin/python scripts/validar_orf.py --check
.venv/bin/python scripts/benchmark_orf.py
MPLCONFIGDIR=tmp/matplotlib .venv/bin/python scripts/figuras_orf.py
```

A campanha histórica pode ser reexecutada separadamente com `benchmark_response.py`
e `benchmark_coherence.py`; isso substitui seus registros e tempos locais, exigindo
revisão antes de outra publicação. Não reescrever os arquivos de um release já
publicado. Nenhum desses comandos executa inferência, SBC ou análise de dados reais.
