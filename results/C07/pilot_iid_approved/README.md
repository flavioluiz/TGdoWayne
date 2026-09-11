# Piloto IID com tabela angular validada

A produção prospectiva usou16 alvos e níveis 16384/65536 por replicação, com quatro replicações independentes e propostas GMM congeladas antes dos novos sorteios. O ajuste dessas propostas pertence ao piloto anterior; os16 alvos não fazem parte da futura SBC500.

No nível 65536,416/416 CDFs passaram a meta MCSE 0,00335; maior erro 0,002984612. Os16 alvos passaram também a guarda observada de dominância dos pesos. Os20 brackets A0d14 foram compatíveis com a cubatura e suficientemente precisos. Não houve discordância nos 3264 contrastes de replicações ou 152 de refinamento. No nível 16384,385/416 CDFs passaram. São verificações numéricas finitas, com intervalosMC assintóticos; não provam ausência de modos nunca visitados.

A tabela de 8336 nós é `../orf_interpolation/orf_table_pilot12x4.npz`. O checker raiz usa `configs/calibration/diagnostics_iid_8336_execution.json`, com os mesmos critérios v1 aplicados aos níveis congelados no PROSPECTIVO. Relatórios e fontes históricos foram copiados byte a byte; apenas o nome de pasta `executed_sources/tmp` foi mapeado para `executed_sources/preparatory`. O inventário registra os caminhos. As amostras grandes estão nos caminhos locais indicados em `results/summary.json`, preservadas com hashes, sem incluí-las no Git.

O piloto aprova a precisão dos alvos e funções nele testados. A nova campanha ainda precisa de geração independente, ajuste por dado sem acesso às verdades, diagnósticos por realização e análise SBC.
