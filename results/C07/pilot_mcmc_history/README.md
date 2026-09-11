# Pilotos MCMC preservados — C07

Três pilotos de 16 dados × 5 alvos, com tabelas ORF ainda não aprovadas. Nenhum satisfez todos os diagnósticos de precisão. Não constituem SBC500 nem resultados científicos finais.

Os relatórios e metadados são cópias byte a byte do trabalho preparatório. Seus caminhos e hashes identificam as fontes de execução daquela época; não devem ser reinterpretados como caminhos portáveis atuais. `historical_diagnose_pilot.py` é o adaptador histórico, dependente do pacote temporário; a implementação reutilizável está em `src/inference/mcmc_diagnostics.py`. As cadeias grandes ficam fora do Git e os seus hashes constam dos relatórios. Novas execuções recebem nomes próprios e não sobrescrevem esses diagnósticos.

O terceiro piloto (`553_refresh`) passou os pisos de Rhat e ESS nos80 alvos, mas ainda falhou em precisão de CDFs e resolução de lotes. Os três confrontos A0d14 usam40 desigualdades nos extremos dos brackets, sem presumir que a CDF no ponto médio seja a probabilidade nominal. `third_pilot_inventory.json` identifica as cópias acrescentadas; o relatório inicial `RELATORIO.md` continua histórico e descreve apenas os dois primeiros pilotos.
