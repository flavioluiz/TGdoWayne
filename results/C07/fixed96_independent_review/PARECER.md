# Parecer independente — 96 cenários fixos C07

**PASS no âmbito auditado**, com6508 verificações e diferença máxima1,1102230246251565×10⁻¹⁶. A síntese fechada, os96 JSONs/NPZs compactos e os vínculos de produtores/recibos preservam todos os IDs, máscaras, quantis e flags. Nenhuma fonte ou saída ROOT foi modificada; não houve leitura de raw, ORF, likelihood ou geração de posterior.

O fechamento corresponde aos SHAs comunicados por ROOT: complete `70b3da6322bc99f4ccd172a86577efb22b9fe37221bd504044af174f7452b2b1`, plan `9552d99a4c838409d3daa1fc7bb67e8236d2cb6bc6c0091bb3c5ffed95b10a2f`, summary `1273de6e7f2b835a5c349c5df243b60ac5f865ff0f55f61bfb2715e0ac0c11d5` e arrays `1c43bd6f5cfc278f9e87e7abbf24dcd0400a04a125be80b21191cdf2584dbc32`. O inventário, a configuração geradora, os metadados de geração e as fontes executadas foram conferidos por SHA.

## Máscaras e inventário

A reconstrução independente usa NumPy/SciPy diretamente, sem importar os helpers ROOT. As comparações de valores/flags dos compactos com o NPZ agregado são exatas. Os dois níveis IID e seus contrastes mantêm os denominadores prospectivos19584 e672, apesar das omissões justificadas. Foram efetivamente registrados17664 contrastes de réplicas e512 de refinamento, conforme o protocolo.

| Cenário | Dados retidos | PITs aplicáveis | Estruturais | Numéricos resolvidos | Slots indefinidos |
|---|---:|---:|---:|---:|---:|
| Massa zero com sinal | 32 | 192 | 32 | 160 | 0 |
| u=0,995 | 32 | 192 | 0 | 192 | 0 |
| Ausência de GW | 32 | 64 | 0 | 64 | 128 |
| Total | **96** | **448** | **32** | **416** | **128** |

Os32 PITs estruturais de massa zero são exatamente0, com MCSE0 e flag estrutural. A elegibilidade estrutural decorre da priori contínua sem átomo no limite inferior; os outros indicadores constantes não recebem essa exceção.

Na ausência de GW, massa, amplitude GW, inclinação GW e logL-na-verdade permanecem indefinidos: PIT, MCSE e faixa sãoNaN e a aplicabilidade é falsa. Apenas Ar eEFAC têm verdades pontuáveis nesse cenário. As1920 quantidades de quantis (96×5×4) continuam presentes e descritivas, inclusive para os parâmetros sem verdade geradora; seus resumos usam todos os32 dados de cada cenário.

Não há alvo com algum dos cinco flags numéricos globalmente falso, nem PIT aplicável unresolved neste conjunto. Isso é um resultado desta produção finita, não uma propriedade geral da proposta de importância.

## Coberturas condicionais

Foram recalculadas as24 linhas de cobertura dos12 pares cenário/parâmetro definidos, suas contagens certas/possíveis, intervalos Clopper–Pearson pontuais e a união desses intervalos sobre as contagens possíveis. Os envelopes ECDF foram obtidos diretamente pelas desigualdades de cada intervalo, conservando o denominador32. Não foi executado KS, teste de uniformidade ou hipótese de cobertura Bayes universal de90%.

Em u=0, [0,U90] contém a verdade em32/32 dados e o intervalo central a exclui em0/32, como exige a estrutura do suporte. Os campos de cobertura populacional estrutural são1 e0, separadamente dos intervalos binomiais descritivos.

Em u=0,995, ambos os intervalos contêm a verdade em0/32 dados, e as faixas numéricas de contagem também são[0,0]. Esse é um resultado condicional importante a relatar, compatível com a distinção entre inferência sob uma priori e desempenho em uma verdade fixa. A verificação não o converte em falha numérica, nem aplica automaticamente uma hipótese nominal de90% ao cenário fixo. O intervalo CP pontual para uma frequência observada0/32 é[0;0,10888116].

As faixas de sensibilidade mantêm família576, alphaMC0,01 e parcela determinística0,002. São aproximações condicionais de erro numérico. Os CP são pontuais para32 repetições, sem garantia simultânea entre todos os parâmetros/cenários; a precisão horizontal dos quantis não é certificada apenas por MCSE de CDF.

## Custos e limitações

A auditoria dos produtos fechados consumiu **2,82429s CPU, incluindo imports**, com RSS113.311.744B, dentro de30s/256MiB. Os cinco grupos TOY preliminares usaram apenas intervalos/contagens sintéticos e respeitaram o teto10s; não são validação PTA. Nenhum arquivo de campanha foi lido por esses TOYs.

Os hashes e vínculos dos compactos/recibos foram conferidos, incluindo os papéis de produtor, diagnóstico, numérico e proposta. Não se refez o replay dos estados RNG nem se reavaliaram os kernels físicos: esses controles pertencem às evidências próprias do projeto. O presente PASS certifica apenas a concordância aritmética, o inventário e a aplicação das máscaras/escopos nos produtos examinados.

`audit_fixed.py` é o auditor; `closed96/review.json` contém as verificações e24 linhas de cobertura, `hash_inventory.json` os96 vínculos, e `independent_resolved.npy` a máscara reconstruída. `commands.sh`, os logs e `package_manifest.json` permitem conferir os bytes e reproduzir a leitura em uma nova pasta de saída.
