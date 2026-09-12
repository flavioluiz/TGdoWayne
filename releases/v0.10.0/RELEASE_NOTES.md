# v0.10.0 — Helicidade zero vinculada e inferência condicional

Entrega C10 do plano original, com dissertação cumulativa e C11–C13 abertos.

- Resposta de helicidade zero de Fierz–Pauli derivada com observadores,
  vínculos transversal/longitudinal, limites e normalização explícitos.
  A população escalar é fenomenológica; não se impõe desacoplamento no limite
  sem massa nem se ajustam as duas deformações como modos independentes.
- Piloto de 16 observações e 36 referências completas de evento concluído
  nos critérios operacionais; falhas e refinamentos preservados.
- Campanha de 1.192 observações e 6.344 análises concluída: 500 injeções
  tensoriais, 500 da priori conjunta e seis células mistas com 32 repetições.
  214.227.550 avaliações de likelihood, 5.309,02 s de CPU e nenhum descarte.
- Auditoria independente das evidências, CDFs, quantis, 2.500 eventos e
  86.768.386 associações de valores em células finais aprovada. As diferenças
  máximas de reconstrução ficaram abaixo de 2,74 × 10⁻¹⁴.
- SBC com famílias prospectivas 39/26/6: controles corretos sem rejeição
  nominal e uma decisão indeterminada; aproximações com onze rejeições
  persistentes e três indeterminações; comparações pareadas com duas
  rejeições persistentes e duas indeterminações.
- Falsos positivos nominais de 0,4%, 4,4% e 2,0% em A0_CN, A_CN e B_CN
  no limiar BF10 > 10, acompanhados das contagens certas/possíveis e de
  intervalos binomiais. Recuperação limitada, especialmente perto do limiar;
  não se interpreta ausência de rejeição como aprendizagem ou equivalência.
- Fisher físico em oito pontos e três modelos: 24 matrizes verificadas,
  projeção das quatro nuisances e perda de informação na compressão G.
- 104.184 arquivos lógicos da pré-produção e 110.257 da produção restaurados
  e conferidos, com sobreposição de dependências. Os 74 ZIPs novos de produção
  são anexos deste release; o catálogo versionado conserva URLs e SHA-256.

Validação: 13 testes C10 passaram no workspace e com referências restauradas;
os controles anteriores de fundamentos, ORF, simulador, inferência e robustez
integram o procedimento de publicação. PDF cumulativo com figuras, tabelas e
limitações; manifesto de integridade e restauração reproduzível.

A inferência permanece condicional em massa e potência escalar, com quatro
nuisances conhecidas, no experimento Fourier periódico de dez pulsares e três
canais. Existem eventos e decisões numericamente indeterminados; não há
certificação uniforme do contínuo. O diagnóstico local de Fisher não equivale
a marginalizar nuisances numa posterior de seis parâmetros. Nenhuma nova
restrição observacional ou detecção em dados reais é apresentada.

Consulte `docs/c10_restauracao_producao.md` para obter os anexos e restaurar a
campanha. Próximo marco: v0.11.0, aplicação pública ou extensão simulada
conforme a auditoria e o plano C11; depois, discussão/manuscrito e auditoria final.

A publicação automática do PDF precede o envio dos ZIPs de produção. A
restauração remota completa exige que os 74 anexos do catálogo estejam
disponíveis e passem na verificação de download; a validação local de
restauração, por si só, não comprova esse envio.
