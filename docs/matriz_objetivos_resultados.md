# Matriz de objetivos e resultados — preparação de C12

Estado: parcial. A etapa C11 está em execução; C12 e C13 não estão concluídas.
Esta matriz parte dos seis objetivos específicos da introdução. Os capítulos citados
contêm os resultados publicados e referências aos respectivos artefatos de validação;
a auditoria numérica cruzada do texto final ainda deverá conferir cada alegação.

| Objetivo da introdução | Evidência disponível | Interpretação e limites | Pendência para a narrativa final |
| --- | --- | --- | --- |
| Reproduzir o núcleo linear do TG, convenções, unidades e vínculos | C04 e capítulos `03_fundamentos.tex` e `03a_normalizacao.tex` | Reprodução e verificação teórica; propriedades de Fierz–Pauli/dRGT não são transferidas automaticamente ao modelo histórico de Visser | Conferir cada afirmação de novidade contra as referências originais |
| Implementar resposta tensorial dispersiva com termos da Terra e pulsares | C05, capítulo `04_resposta_pta.tex`; benchmark C11 em `results/C11/benchmark_v2/gate.json` | Limites analíticos e quadraturas independentes em domínio finito. O benchmark C11 amplia fases/geometria; não demonstra precisão uniforme em todo o suporte | Concluir validação das funções posteriores C11 |
| Gerar conjuntos sintéticos com covariância preservada | C06–C10; capítulos de metodologia/validação, gerações com sementes e auditorias. C11 prepara populações aninhadas P12K4/P16K8 | Realizações Fourier próprias no modelo periódico; não equivalem a resíduos de timing irregular. Controles gaussianos reproduzem momentos, não a distribuição quadrática | Auditar geração e acoplamento das realizações C11 efetivamente produzidas |
| Quantificar diferenças de recuperação, incerteza, calibração e informação | C07–C10; capítulos `07_resultados_compressao.tex`, `08_producao_c09.tex`, `09_helicidade_zero.tex` | A0/A, A/B e B/C separam aproximações distintas. SBC sob a priori não substitui cobertura em verdades fixas. Identificadores indeterminados são mantidos | Integrar os resultados C11 sem chamar concordância de interpolantes de validação física |
| Avaliar prioris, suporte e covariâncias | C09, produção e painel pareado de prioris no capítulo `08_producao_c09.tex` | A reponderação das mesmas realizações não constitui nova campanha SBC das prioris alternativas; suporte cinemático não é limite observacional | Auditar números/figuras e integrar dependências entre os contrastes na discussão |
| Estender à helicidade zero de Fierz–Pauli e preparar artigo | C10 publicado: capítulo `09_helicidade_zero.tex`, auditorias de produção/Fisher e arquivos do release v0.10.0 | Deformações vinculadas; amplitude escalar é uma hipótese de população. Fisher local com projeção de nuisance não substitui posterior marginalizada. Não há detecção observacional | Manuscrito e discussão em C12, apoiados também no fechamento C11 |

## Resposta que a discussão deve construir

A pergunta central é quando uma resposta em frequência de referência preserva a inferência
da massa em relação à frequência explícita e à compressão consistente. A conclusão deverá
especificar modelo gerador, suporte, espectro, distâncias, ruído, priori e precisão numérica.
Não deve condensar a pergunta numa comparação de limites superiores sem verificar informação
em relação à priori e calibração. Aproximação normal, compressão e substituição da resposta
em frequência são operações distintas e precisam conservar essa distinção na apresentação.

## Regras de rastreabilidade

- Cada número final deve apontar para o arquivo de síntese que o produz e para sua auditoria.
- Distinguir teste não rejeitado, teste inconclusivo por erro numérico e demonstração de equivalência.
- Identificar resultados de reprodução, aplicação metodológica e contribuição nova proposta.
- Usar apenas resultados C11 concluídos e validados; manter resultados parciais rotulados como draft.
- A disponibilidade pública de TOAs é reconhecida. A escolha simulada decorre da ausência local
  de um adaptador validado de timing, janela e ruído, conforme `docs/dados_publicos.md`.
- A preparação de artigo não significa submissão, aceitação ou autoria institucional estabelecida.
