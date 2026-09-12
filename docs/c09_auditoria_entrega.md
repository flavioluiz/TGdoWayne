# Auditoria da entrega C09

Esta auditoria aplica os critérios do plano C09 à entrega de resultados
condicionais. Encerrar a etapa não aprova os casos indeterminados e não
conclui C10–C13. A publicação requer adicionalmente manifesto, PDF,
commit/tag remotos e conferência dos assets do GitHub Release.

| Requisito do plano | Evidência e conclusão |
|---|---|
| Prioris em massa, massa ao quadrado e logarítmica com corte | `paired_prior_panel/` contém cinco medidas sobre os mesmos 32 dados e dez modelos, 1.600 integrações, 1.280 contrastes adicionais. Corte e Jacobianos são explicitados no capítulo 8. |
| Informação e suporte | KL, W1, CDF, odds e quantis estão registrados por análise; a seção de produção distingue os efeitos da medida de priori, do suporte e dos dados. Não identifica informação apenas pela proximidade de quantis. |
| Fatorial da covariância | `robustness_synthesis/paired_contrasts.json` registra 24 contrastes de 500 pares, separando fixa/variável de completa/diagonal. Há sinais positivos e negativos; não se afirma conservadorismo universal ou equivalência. |
| Espectros e contaminantes | 768 posteriores espectrais e 1.536 análises de inclusão/omissão preservam os cenários e as massas fixas. Doze contrastes de 64 pares demonstram que omissão pode reduzir o limite. |
| Ruídos e variabilidade | 3.000 posteriores nos dois ruídos alternativos; 1.152 nas fronteiras. Os 90 grupos têm mediana e percentis 10/90 de quantis, com envelopes numéricos e número de casos resolvidos. Cenários de sementes próprias não são chamados de pareados. |
| Distâncias | 3.000 posteriores e três contrastes de 500 pares. Mistura global explícita; 834 falhas pontuais de interpolação A0 mantidas como quantis [0,1]. Ausência de conclusão é relatada, sem descartar IDs. |
| Escala h/T | O capítulo deriva a conversão de quantis e a referência 0,95 h/T sob priori uniforme e likelihood constante, delimitando a comparação com MeerKAT. Não há nova restrição observacional. |
| SBC representativa | `SBC_operational_events/` conserva 18 grupos, 500 IDs por grupo e os 126 testes com Holm. São 116 não rejeições condicionais e dez indeterminações; os intervalos operacionais não são certificados físicos uniformes. |
| Estabilidade numérica | Malhas aninhadas, ordens de quadratura, testes analíticos, controles SciPy e referências independentes selecionadas estão vinculados aos respectivos registros. O capítulo distingue integração, limiares e domínio interpolado do evento. Não se generaliza uma verificação pontual a toda a função. |
| Reprodutibilidade | `production_reproducibility/restore_validation.json` confirma a restauração e releitura dos 24.238 arquivos lógicos. Configurações, fontes, dados, respostas, caches, falhas e custos são preservados. |

Os caminhos de resultados na tabela são relativos a `results/C09/`.
O PDF inclui a fundamentação e o histórico de C01–C08, o histórico dos
pilotos C09 e a seção de produção consolidada. C10 e C11 continuam drafts;
discussão, conclusões e auditoria final do projeto permanecem no plano.

Limites materiais: experimento periódico de Fourier, parâmetros auxiliares
conhecidos, 834 PITs de massa e 2.287 eventos sem resolução operacional na
produção completa. A calibração é condicional à validade dos envelopes
numéricos observados. Esses limites devem acompanhar qualquer artigo que
use os resultados; sucesso de compilação ou de testes não os elimina.
