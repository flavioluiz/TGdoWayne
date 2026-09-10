# v0.5.0 — C05: resposta tensorial de PTA validada

PDF cumulativo de 47 páginas, com quatro capítulos concluídos. O novo capítulo
contém 30 equações, resposta Terra+pulsar, normalização espectral, componentes
temporais dos observadores e duas rotas de integração da ORF. Uma figura vetorial
ilustra Hellings–Downs, variação dispersiva e a ordem dos limites da auto.

A implementação própria passou 23 testes de resposta, geometria e interface,
além dos 19 testes simbólicos de C04. A campanha ampliada executou 58 casos:
20 pares principais, 16 casos de coerência, 20 autos e dois zeros HD. Todos passaram;
maior erro absoluto dos controles: 1,63e-6, abaixo de 1e-5. Nos três primeiros grupos,
os máximos ficaram abaixo de 5,36e-12. Tempo registrado: 64,82 s, específico do ambiente.

A API exige resoluções e recursos explícitos, confere refinamento separado e rejeita
sub-resolução. Conserva fases complexas, auto finita e coincidência contínua. O envelope
de fase é limitado aos benchmarks; não há certificado de precisão uniforme nem
inferência estatística nesta etapa. O PDF foi renderizado e conferido em todas as páginas.

Código, configuração, resultados, documentação, figura, README e manifesto acompanham
o PDF no mesmo commit. Os 22 artigos da revisão continuam no acervo local catalogado.
C06 desenvolverá o experimento Fourier e os estimadores; calibração e artigo seguem
nas etapas posteriores. Os releases C01–C04 permanecem imutáveis.
