# Ensaio prospectivo de treinamento curto

O alvo A_G/d14 foi selecionado antes deste ensaio por ser um gargalo do piloto. Dois treinos independentes partiram de pontos uniformes na priori, com4096 ou8192 passos adaptativos, quatro trajetórias e seeds907103101/907103102. Os movimentos foram fixados previamente: massa pela priori0,15; nuisance pela priori0,20; Student independente0,45; passeio aleatório0,20. A adaptação termina antes de congelar a proposta, e os estados de treino não integram as estimativas IID posteriores.

O script de treino carrega apenas q, x_physical e x_gaussian. Não carrega o array truth. Para cada nível, seleciona512 índices fixos da metade final, incluindo as quatro trajetórias:2048estados entram no mesmo EM de quatro componentes,80iterações, piso de covariância0,03 e inflação1,10. Uma Student-t5 global de escala3 recebe fração defensiva0,15. Os estados adaptativos são material de treino; não são apresentados como amostras posteriores válidas.

A ORF usada é a tabela refinada8336 em beta, com condição de derivada nula no limiar, hash75632dfbdd9cce8b60b9f760a3177a76798a4adb7ac9ccc724092aeaf53ad70d. A validação dessa tabela é externa a este ensaio. O banco de momentos usa a pré-alocação matematicamente equivalente de `tmp/c07_memory_kernel/`.

Treino4096:5,89s, seguido de1,44s de EM. Treino8192:13,49s e1,58s de EM. Esses tempos de alvo único não devem ser multiplicados diretamente por2500 para prever uma implementação em lotes: o custo fixo Python pode ser amortizado ao treinar vários alvos em conjunto. Tampouco se deve pressupor esse ganho sem medi-lo.

Cada proposta já congelada recebeu uma nova avaliação IID de32768pontos×4réplicas, com seeds907103301/907103302. Os arrays truth foram carregados somente nessa avaliação para diagnóstico, depois de congeladas ambas as propostas. Os pesos são completos e incluem o Jacobiano da transformação logit e a densidade conjunta normalizada da proposta. O custo de avaliação/gravação foi9,10s e10,13s, após56,06s de setup compartilhado. Os NPZ seguem o contratoR,N,T=1,P5 dos outros benchmarks.

Sanidade descritiva: ESS agrupado51715,6/51917,5 e maior peso0,0009952/0,0006268. Essas métricas não aprovam precisão. O checker independente avaliará os cortes e a grade sem verdades. Mesmo um resultado favorável neste caso não garante precisão em todos os500 novos dados; os diagnósticos de produção precisam continuar ativos.

Os relatórios summary.json e evaluation_summary.json, as propostas congeladas, os estados selecionados e os snapshots de cada fase preservam origem, sementes, custos e hashes. Nenhuma realização da campanha500 foi gerada aqui.
