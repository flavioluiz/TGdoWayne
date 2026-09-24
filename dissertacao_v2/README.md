# Dissertação v2.0.0-rc.3 — candidata a revisão humana

**PDF:** [`output/pdf/v2.0.0-rc.3/dissertacao.pdf`](../output/pdf/v2.0.0-rc.3/dissertacao.pdf) (62 páginas)

**Título:** *Polarizações de ondas gravitacionais com gráviton massivo: o modelo de Visser revisitado e as assinaturas em redes de temporização de pulsares*

Esta é uma reescrita completa da dissertação, feita depois que a leitura especializada julgou incoerente a versão v1.x. A reescrita foi preparada pelo Claude (Opus 5.5) a pedido do proponente. Ela reaproveita os cálculos e as simulações já feitos, mas muda a pergunta, a estrutura e a interpretação. **Ainda não passou por revisão humana especializada.** A v1.1.0 continua preservada para comparação.

## Diagnóstico da versão anterior

1. **A pergunta mudou de assunto.** O TG pergunta quais são os estados de polarização de uma onda com gráviton massivo e como um detector os veria. A v1.x passou a perguntar se avaliar uma ORF dispersiva em `f_ref = 1/T`, depois de comprimir as correlações, enviesa a inferência. Essa é uma questão estreita de análise de dados, motivada por um único preprint de 2026. Da física do TG restou pouco.
2. **O experimento numérico foi montado num regime em que os dados quase não informam sobre a massa.** A informação média ganha sobre a massa foi de 0,07 a 0,11 nat com os dados completos e de cerca de 0,004 nat com as correlações comprimidas. Como comparação, excluir 10% do intervalo a priori vale 0,105 nat. Por isso, a comparação central ("a frequência de referência desloca pouco o limite") não valida a aproximação: não havia informação a distorcer. Números como "0,062 nat perdidos" ou "p ≤ 0,005" não têm leitura física.
3. **A física útil estava escondida.** O capítulo 3 da v1 continha uma revisão exata e valiosa do TG, mas escrita como relatório de auditoria. O texto inteiro estava carregado de rótulos internos (A0/CN, B/G, P12K4, C_β) e de detalhes de execução. A revisão do Gemini acrescentou alegações de ineditismo e "diretrizes para consórcios" que os resultados não sustentam.

## O que muda na v2

| Capítulo | Conteúdo |
|---|---|
| 1. Introdução | O TG e o artigo de 2004; o que mudou em vinte anos (teoria, limites, formalismo); três questões encadeadas |
| 2. Fundamentos | Polarizações e classes E(2); família de termos de massa (Fierz–Pauli, `a = 1`; Visser, `a = 1/2`); fantasma, vDVZ, dRGT, Vainshtein; limites; PTAs |
| 3. TG revisitado | Matriz de marés exata; **seis amplitudes em Visser confirmadas exatamente**; o sexto modo é o traço, um fantasma escalar; em Fierz–Pauli, cinco modos e `p_l = −(f_g/f)² p_b`; validade do NP/E(2) (erro de ~60% no exemplo de 2004); supressão `(f_g/f)²` e sua dependência da normalização; fator 2 na massa |
| 4. PTA | A resposta de temporização depende só da matriz de marés do TG; ORFs tensorial e de helicidade zero com termos dos pulsares; degenerescência no limiar explicada por simetria SO(3); discrepância em Liang–Trodden eq. 45 |
| 5. Simulações | Resultados antigos reinterpretados com rótulos físicos: pouca informação sobre a massa; a média fixa em frequência testada remove cerca de 95% dela; a aproximação normal multiplica por ~10 as falsas detecções escalares; limitações declaradas |
| 6. Conclusões | Respostas a Q1–Q3; próximo passo: previsão de sensibilidade para uma rede realista |

## Verificações feitas nesta reescrita

- As identidades algébricas do capítulo 3 foram reverificadas com SymPy: determinante de Visser `ω⁶Δ⁴/(32Σ)`, vínculo escalar de Fierz–Pauli, identidade `p_l + (f_g/f)² p_b = −(Δ/4)H`, razão `(1+β)²/4` e posto no limiar.
- As ORFs apenas-Terra tensorial e escalar foram recalculadas por integração independente em [`scripts/figuras.py`](scripts/figuras.py). O script confere as formas fechadas de Cordes, `P₂/5`, `P₂/10` e `(3+cos ζ)/24`, e reproduz o valor 0,020366 usado na comparação com Liang–Trodden.
- Os números citados foram conferidos nos PDFs das fontes: termo de massa de Visser (`a = ½`), fantasma de Park (2010), limites do GWTC-4 e de Wu et al. (2024) e o artigo de 2004.
- Os números das simulações vêm dos arquivos de resultados existentes. **Não houve nova campanha numérica.**

## Pontos para o revisor especialista

- A interpretação do sexto modo do TG como o fantasma escalar do termo não Fierz–Pauli (Cap. 2.3 e 3.4).
- A discussão sobre normalização canônica versus componentes métricas comparáveis (Seção 3.5). Ela qualifica a conclusão do TG sobre as bandas de frequência.
- A fórmula de redshift com o movimento dos observadores (Eq. 4.3). Foi herdada da v1 e só a identidade `Q = 2E/ω²` foi reverificada aqui.
- O Capítulo 5 é deliberadamente modesto. Um estudo com redes realistas não foi feito.

## Compilação

```bash
make -C dissertacao_v2 figuras   # regenera as figuras (usa .venv)
make -C dissertacao_v2 pdf       # compila e copia para output/pdf/v2.0.0-rc.3/
```

SHA-256 do PDF publicado: `3a2cf918ba00c9c72e3343160cb795f818cff5a38fc585ceb2d45128284e02d3`.

**Nota sobre a rc.1:** o PDF da tag `v2.0.0-rc.1` saiu com o resumo, o abstract e a folha de registro do template ITA (texto de exemplo sobre um manipulador subatuado). A causa foi uma colisão de nomes: `pretextuais/resumo.tex` casava com `templates/ita/PreTextuais/resumo.tex` no disco do macOS, que não diferencia maiúsculas de minúsculas, e o template vinha antes no `TEXINPUTS`. A rc.2 renomeia os arquivos (`resumo_v2.tex`, `abstract_v2.tex`, `referencias_v2.bib`) e põe as fontes da dissertação antes do template. O corpo do texto é o mesmo da rc.1.

**Mudanças na rc.3.** A rc.3 responde a uma revisão crítica do GPT-6 Astra.
- A pouca informação sobre a massa passa a ser apresentada como explicação plausível, não demonstrada, das diferenças pequenas entre as respostas.
- Corrige a descrição dos métodos de integração: a campanha tensorial I usou amostragem por importância.
- Restringe as conclusões sobre compressão à média fixa testada e cita esquemas que preservam informação.
- Deixa claro, no resumo, que as amplitudes de Newman–Penrose do TG são contrações exatas e que só a sua leitura como polarizações é aproximada.
