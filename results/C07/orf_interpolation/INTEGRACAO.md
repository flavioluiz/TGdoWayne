# Integração da tabela angular

O arquivo científico e os relatórios foram copiados sem alterar bytes. O inventário mapeia o único ajuste de caminho: `executed_sources/tmp/` tornou-se `executed_sources/preparatory/`, para não ficar oculto pela regra geral do Git. O README e o manifesto de entrega preservados são históricos; a receita local pode ser chamada como `.venv/bin/python results/C07/orf_interpolation/rebuild_orf_table.py --cache tmp/rebuild_orf_cache --output tmp/rebuilt_orf_table.npz`. Sem `--execute`, apenas o preflight é executado.

A aprovação da interpolação é restrita à geometria, frequências e caixa de prioris da validação. Não é uma garantia analítica uniforme ou validação posterior. As observações da futura campanha são geradas por ORFs calculadas e verificadas diretamente nas verdades contínuas, sem usar esta interpolação.
