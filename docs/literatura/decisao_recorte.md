# Decisão de recorte em 10/09/2026

**Continuar com o recorte, mas estreitar a alegação de originalidade.** A pergunta não é se incluir frequência, covariância completa ou polarizações adicionais melhora uma análise: essas ferramentas têm antecedentes diretos. A matriz confronta cada peça com as referências próximas; a contribuição candidata é sua auditoria controlada no problema dispersivo de massa, com os mesmos dados e convenções.

## Pergunta refinada

Em quais regiões de massa, distribuição espectral e intensidade sinal/ruído a substituição de uma resposta PTA dispersiva por uma resposta em `f_ref = 1/T` altera limites e cobertura, quando comparada tanto à inferência por frequência quanto à compressão consistente do mesmo experimento? Quanto da alteração vem da perda de informação, do erro de modelo, da priori ou da aproximação de covariância/verossimilhança?

## Definição das comparações

1. **A — frequências conservadas:** estimadores e modelo por frequência. Uma referência adicional **A0** em coeficientes Fourier gaussianos testa a redução para estimadores e a aproximação probabilística de A. A/B/C conservarão a mesma família de verossimilhança para isolar os contrastes sob essas hipóteses.
2. **B — compressão consistente:** fixar operador `W` independente do parâmetro avaliado; aplicar `y=W d`, `mu_y=W mu` e `C_y=W C W^T`. Se `W` depender dos dados, sua seleção deve entrar na validação; não chamar a transformação de exata apenas porque a média e a covariância foram propagadas. Produtos quadráticos geralmente não têm distribuição gaussiana exata.
3. **C — frequência única:** usar os mesmos dados comprimidos e convenções de B, trocando a resposta dispersiva pela avaliação em `f_ref`, na média e na covariância de sinal de modo declarado e consistente. Uma troca apenas na média será ablação específica; suporte espectral não será alterado simultaneamente sem controle próprio. A–B mede perda de informação sob hipóteses compatibilizadas e calibradas; B–C mede erro de aproximação da resposta. Diagonalização e escolha de priori entram em ablações separadas.

Relatar cobertura de intervalos, distribuição de limites, viés, informação/priori, falsos positivos e convergência. Uma priori cinemática `m <= h/(c^2 T)` não é limite observacional por si só. Não há teorema geral de que remover correlações fora da diagonal seja conservador.

## Escopo da contribuição publicável

O artigo deverá entregar um mapa quantitativo de validade e um procedimento reprodutível que preserve os efeitos dispersivos sob compressão. Reproduzir somente ORFs ou apresentar posterior mais estreita é insuficiente. Resultado de ausência de viés relevante também é cientificamente útil se o domínio de validade e a precisão numérica forem demonstrados.

A inclusão posterior de helicidade zero fica condicionada à derivação da resposta completa vinculada de Fierz–Pauli e à separação entre amplitude observável e excitação pela fonte. Não introduzir seis amplitudes independentes como se fossem seis graus físicos saudáveis, nem impor desaparecimento de helicidade zero no limite sem massa por conveniência do ajuste.

**Atualização de versão a incorporar em C05/C10:** Liang–Trodden possui [revisão v3 de 24/07/2026](https://arxiv.org/html/2108.05344v3). Sua seção III explicita o movimento dos observadores quando existem componentes temporais da perturbação; a Eq. (22) inclui um termo com `epsilon_00`. Isso torna inadequado usar sem auditoria fórmulas escalares/vetoriais de códigos publicados em 2025. Fixar versão e derivar a resposta por uma via independente. A matriz já referencia v3; o histórico bibliográfico continua distinguindo artigo de 2021 e revisão de 2026.

**Estado epistemológico:** nenhum estudo equivalente à comparação tripla calibrada foi localizado nas fontes consultadas. Isso sustenta investimento na execução, não uma declaração de prioridade absoluta. C03 encerra a decisão bibliográfica; a novidade e utilidade final dependem dos resultados de C08–C11 e de nova busca antes de submeter.

A [segunda leitura independente](segunda_leitura_metodos.md) detalha páginas e equações dos antecedentes. Os [ajustes metodológicos](ajustes_metodologicos.md) foram incorporados aos planos C05–C10.
