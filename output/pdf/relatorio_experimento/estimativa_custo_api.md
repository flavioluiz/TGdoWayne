# Estimativa do equivalente em API

Data dos preços: 13/09/2026. Esta é uma estimativa contrafactual, não uma fatura.

## Resultado

Pesquisa do primeiro pedido até o goal: **US$ 1.289,34** em GPT-6 Astra Standard. Inclui o agente principal e três subagentes, em 6.510 registros individuais de resposta. Apresentações científicas e revisão posterior do artigo acrescentam **US$ 14,29**, chegando a **US$ 1.303,63**. A conversa de elaboração do relatório/apresentação do experimento fica fora deste recorte, assim como Gemini, computação local e tarifas de ferramentas.

| Categoria, até o goal | Tokens | USD por milhão | Estimativa USD |
|---|---:|---:|---:|
| Entrada sem cache | 20.583.691 | 10 | 205,84 |
| Entrada lida de cache | 822.046.336 | 1 | 822,05 |
| Saída, incluindo raciocínio registrado | 5.229.122 | 50 | 261,46 |
| Total | 847.859.149 | | 1.289,34 |

O agente principal responde por US$ 720,81 e os subagentes por US$ 568,53. O período anterior à criação do goal representa US$ 21,55; o intervalo da criação ao encerramento representa US$ 1.267,79.

## Método e limites

Somados os campos `payload.usage` de `token_usage_record`, com identificação única por `response_id`. Não houve duplicações entre os arquivos selecionados. Os totais conferem com `thread_token_usage` ao final de cada arquivo original. Para a sessão retomada, usaram-se apenas incrementos. Não foram somados snapshots cumulativos, nem o contador de 25.719.766 tokens do goal. Os eventos `token_count` exibem outro acumulado; por isso a fonte escolhida foi o registro dedicado por resposta.

97,56% da entrada veio de cache. O histórico da conversa e os resultados de ferramentas podem ser apresentados ao modelo muitas vezes. Tokens de raciocínio já estão dentro da saída e não foram somados novamente. Nenhuma requisição medida ultrapassa 272 mil tokens de entrada (máximo: 248.087). Os registros de consumo analisados estão associados a Astra; a passagem por Luna não tem registro individual de consumo atribuído.

O campo de gravação de cache é zero em todos esses registros. Na API Astra atual, gravações custam US$ 12,50/milhão. Se toda a entrada não atendida por cache fosse gravada, o acréscimo sobre a conta acima seria de aproximadamente US$ 53 para o recorte completo, mantida a mesma taxa de reutilização. Uma execução nova pode ter outra taxa de cache. Fast custa o dobro de Standard: aproximadamente US$ 2.607 para o mesmo consumo, antes de adicionais. Não foi possível estabelecer o service tier de faturamento a partir desses registros.

Os US$ 50 sugeridos pelo usuário são um rateio da assinatura, não uma conversão contratual da cota em dólares de API. A relação aproximada de 26 vezes se aplica apenas a essa comparação contábil, não ao custo interno do provedor.

Fontes oficiais: [Astra](https://developers.openai.com/api/docs/models/gpt-6-astra), [cache](https://developers.openai.com/api/docs/guides/prompt-caching), [preços de ferramentas](https://developers.openai.com/api/docs/pricing). Dados agregados: [dados agregados](estimativa_custo_api.json).
