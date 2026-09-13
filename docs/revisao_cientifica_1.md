# Primeira revisão científica solicitada pelo autor

A formatação institucional foi considerada suficiente pelo usuário. O trabalho
passa a priorizar a argumentação física, a redação acadêmica e as questões
numéricas abaixo, sem novas buscas de detalhes de capa ou banca.

| Comentário | Conferência e encaminhamento |
|---|---|
| Unidades naturais e SI | Conversões inseridas na abertura do capítulo 3; o diagnóstico histórico depende de interpretar o parâmetro como massa SI. |
| Fierz–Pauli, vDVZ, BD e Vainshtein | Nova seção distingue resposta linear com fontes, perda de vínculo não linear e screening. Três revisões foram acrescentadas e baixadas em `literature/papers`. |
| Bases escalares | Novo apêndice deriva as conversões. Bases com norma comum um ou dois dão a mesma razão entre coeficientes; a diferença vem de reescalamento relativo ou projeção de maré. |
| sinc | A definição sin(x)/x já existia. Removida a nota de NumPy e explicitado sinc(0)=1. |
| Aproximação normal | Falhas de calibração promovidas a resultado central. Comparações B_CN/C_CN são condicionais à densidade aproximada; controle A_G/B_G isola compressão. Edgeworth é possibilidade a validar, não solução demonstrada. Cobertura confirmada: A_CN 313/500 = 62,6%; B_CN 412/500 = 82,4%. Em A_CN, a contagem sob incerteza numérica varia de 299 a 325 (`results/C13/review_efac_coverage.json`). |
| Jacobiano e caudas | Apêndice deriva o determinante unitário, ds/(s ln 10), integrais CN/normal, suporte e convergência. |
| Precisão de B/C | A comparação principal já usa 24 realizações sorteadas mais oito casos de fronteira. Complemento concluído: 50 IDs previamente escolhidos da população P16K8, seis modelos e 300 posteriores condicionais de massa. Inversão de envelopes de CDF: todos os 200 contrastes com raio numérico menor que 0,01; intervalos das quatro médias dentro de [-0,01;0,01]. A comparação marginalizada original permanece inconclusiva. Não se afirma equivalência populacional. Dados em `results/C13/conditional_contrasts`. |
| Limite imposto pela priori | Exemplo Q95=0,95 e KL=0 destacado no Resumo, Introdução, Discussão e Conclusões. Proximidade numérica de um limite publicado com essa escala não demonstra, sozinha, ausência de informação naquele estudo. |
| Degenerescência escalar | Consequência angular explicitada na Discussão: exata no limiar e no modelo especificado; perto dele a separação depende de sensibilidade e da banda. |
| Ajuste de timing | Concluído: 20.000 séries por amostragem, regular e irregular, com três ajustes pareados. Covariâncias analíticas confrontadas com ajustes por mínimos quadrados em cada série. Matrizes e figuras reproduzidas no diretório isolado; resultados em `results/C13/timing_projection`. Novo experimento e duas figuras no capítulo 10. A projeção, e não a adição de uma média determinística Mδξ, altera a covariância. |
| Tom de auditoria | Discussão, Conclusões e resumos reescritos; históricos de execução e detalhes de arquivos retirados do texto. Seção de validação reescrita em termos de precisão, pesos de importância e calibração. Notas de hashes e merge removidas da bibliografia. Conferência visual integral final concluída; limpeza adicional retirou CPU, armazenamento e identidade de arquivos dos capítulos 7 e 9. |
| Legibilidade das figuras | Painéis indicados redesenhados com fontes maiores e legendas curtas. Figuras de quantis e de SBC escalar divididas; mapa de médias reorganizado. Onze figuras acadêmicas derivadas dos mesmos dados, incluindo a informação da população ampliada; valores e envelopes preservados, reprodução conferida separadamente. |

As modificações editoriais e teóricas não alteram os resultados numéricos
anteriores. Simulações novas devem ter hipóteses e critérios definidos antes
de sua interpretação. Esta revisão integra o fechamento C13, sem release
intermediário.
