# Verificação da v0.8.12

- 217 testes científicos existentes aprovados; 58 casos ORF salvos conferidos.
- Dois testes analíticos novos aprovados: reprodução dos nós, colunas e
  normalizadores distintos, momentos/KL/CDF, e recusa de nó não calculado.
- Três ondas reconstruídas dos arquivos dos 36 workers: hashes, contagens,
  autovalores e refinamentos conferidos. Máximos angular/harmônico 2,903e-12
  e 9,659e-15; maior RSS observado 859897856 bytes.
- Mistura conjunta reconstruída por soma exponencial escalada; 10152 novas
  avaliações conferidas, incluindo 162 controles SciPy recuperados.
- Falha de registros SciPy preservada no log da auditoria. Nenhuma resposta
  física repetida na recuperação; discrepância máxima 4,264e-14.
- 163 membros dos três ZIPs relidos e conferidos por SHA-256.
- Cinco referências passam na última onda, sete permanecem pendentes.
  Não substituir a última onda pelos sete passes da intermediária.
- PDF final de 135 páginas, sem overfull nem referências/citações indefinidas.
  Todas as páginas renderizadas a 850 pixels: 112 idênticas à versão anterior
  já revisada; 23 diferentes inspecionadas. Páginas 117–118 examinadas
  individualmente. Resumo ajustado para evitar página isolada de palavras-chave.
- README, estado dos capítulos e manifesto conferidos antes do commit.

O diagnóstico GK não é uma cota rigorosa de erro físico. Quantis/W1/eventos
das distâncias e produção D3/SBC ainda não estão concluídos.
