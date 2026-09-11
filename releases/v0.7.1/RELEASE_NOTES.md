# v0.7.1 — C07: inferência de referência e calibração

O PDF cumulativo de 83 páginas acrescenta o capítulo de inferência e validação, com referências independentes, diagnóstico de integração, 500 realizações da priori e 96 injeções fixas. A atualização bibliográfica reúne 37 PDFs locais (839 páginas), catalogados com URLs, versões e SHA-256; o catálogo e o script de download integram o repositório.

## Resultado e alcance

- **2500 inferências concluídas**, cinco análises por cada um dos 500 dados. Os controles A0_CN/A_G/B_G não apresentaram rejeição nominal após Holm na família prospectiva de 93 testes.
- A_CN/B_CN, aproximações normais nas estatísticas físicas, apresentaram 13 rejeições nominais e 10 persistentes nos envelopes numéricos da família separada de 62 testes. Os principais desvios aparecem no fator de ruído branco e na log-verossimilhança na verdade.
- **81 alvos** conservaram algum diagnóstico agregado não resolvido; **243 dos 15000 PITs** receberam envelope [0,1]. Nenhum dado foi removido. A análise não toma ausência de rejeição como prova de correção.
- Nos 96 controles A0, todos os diagnósticos numéricos passaram. Dos 448 PITs aplicáveis, 32 são estruturais e 416 numéricos. Sem GW, 128 funções sem verdade definida foram mascaradas.
- Em u=0, as coberturas unilateral/central são estruturalmente 1/0. Em u=0.995, ambos os eventos de 90% tiveram 0/32, com IC binomial 95% [0,0.109], explicitando a diferença entre SBC sob a priori e cobertura em uma verdade fixa.

A massa marginal não teve rejeição KS em nenhum modelo, mas isso não implica calibração conjunta, equivalência da compressão ou ausência de desvios condicionais. Quantis permanecem descritivos quanto ao erro horizontal de integração. Esta versão não apresenta detecção ou nova restrição observacional à massa do gráviton.

## Implementação e verificações

A inferência usa treino separado da produção IID, quatro réplicas, níveis 16384/65536, propostas defensivas congeladas, diagnósticos por função e kernels nativos confrontados com implementações independentes. As tentativas anteriores de MCMC, propostas estreitas e interpolações reprovadas permanecem registradas; uma curva SBC favorável não aprova integração reprovada.

As checagens finais passaram: 217 testes e 58 casos preservados do benchmark angular. Os componentes de inferência possuem 164 desses testes, além das referências preservadas de marginalização, cubatura A0, gerador, interpolação angular, álgebra IID e controle negativo de SBC. A auditoria independente da síntese refez 6202 verificações e reconstruiu exatamente a máscara dos 15000 PITs a partir dos 2500 diagnósticos compactos. A auditoria separada dos 96 controles refez 6508 verificações, incluindo máscaras, coberturas condicionais e os 1920 quantis preservados. As conclusões ficam condicionadas ao domínio e às margens operacionais documentados.

Custo efetivo das campanhas finais: 901130000 avaliações de verossimilhança na campanha 500×5 e 34603392 nos 96 controles. Os registros compactados preservam todos os IDs, sementes, propostas, flags e recibos; a restauração em pasta nova verifica cada arquivo. Os arrays brutos retirados são regeneráveis e não são declarados como presentes nos arquivos ZIP.

Fontes, resultados, plano, PDF e manifesto pertencem ao mesmo commit do marco. A publicação anexa o PDF versionado, após verificar o manifesto; o SHA-256 do download deve coincidir com o arquivo local.

## Próxima etapa

C08 compara a compressão consistente e duas respostas de frequência de referência, com controle normal correspondente, teoria de perda de informação e reavaliação da precisão dos quantis em subamostra prospectiva. C09–C13 continuam no roadmap. O pseudônimo e a identificação de orientação permanecem provisórios, conforme autorizado.

## Correção da publicação

A tentativa `v0.7.0` falhou na checagem Linux antes de criar o release. As funções trigonométricas da plataforma alteravam os últimos bits da geometria regenerada e, portanto, os nomes dos caches exatos; os testes agora comparam o desenho a tolerância estrita e usam a geometria versionada para ler esses caches. Os checks de integridade continuam exatos. A comparação entre diagnósticos com máscaras distintas admite somente arredondamento de 2×10⁻¹⁴ nos valores numéricos, mantendo as decisões booleanas exatas. A alteração é restrita aos testes: nenhum kernel, dado, posterior ou resultado científico foi recalculado.
