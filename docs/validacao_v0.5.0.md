# Validação de C05 / v0.5.0

Data: 10/09/2026. PDF cumulativo: **47 páginas A4**, 512316 bytes.
SHA-256: `492cb22a07e5619608dd942a8b8326ea9c4b0afc02c37199274e8c4eee8570e9`.

## Verificação científica e computacional

Os 23 testes integrados de `scripts/validar_orf.py` passaram, com NumPy2.4.3 e
SciPy1.17.1. A bateria inclui geometria independente por polarizações explícitas,
rotação global, frequência negativa, covariância real, coincidência e rejeições
de entrada/recurso/sub-resolução. O script e os cinco módulos C05 têm hashes
registrados; `--check` confere as versões e reexecuta a bateria sem alterar evidências.

A campanha de `scripts/benchmark_orf.py` foi executada contra esses mesmos módulos:
58/58 casos passaram em 64,82s. Houve controles separados de nós harmônicos,
truncamento multipolar, quadratura direta e métodos independentes. Auto1D e zerosHD
completam as referências. Configuração e fontes permaneceram inalteradas durante
a execução; `--verify-only` confirmou o registro após sua cópia para o destino final.

Uma cópia separada dos módulos, testes, scripts, configuração e resultados passou
os mesmos 23 testes e a conferência da campanha. Isso verifica a portabilidade da
estrutura de caminhos, sem alegar reprodução em outro sistema operacional. O workflow
Linux reexecuta as baterias curta e simbólica e confere as evidências antes da publicação.
Não executa novamente as 58 integrais durante o release; a receita completa está disponível.

As fórmulas foram confrontadas com Liang–Trodden v3 e Cordes v2; a auditoria independente
está em `docs/pta/`. As campanhas iniciais e suas evidências de equivalência foram
preservadas e distinguidas da execução ampliada. Um erro de refinamento pequeno
não é apresentado como validação de posterior ou garantia em todo o domínio contínuo.

## Conferência do PDF

Todas as 47 páginas foram renderizadas com Poppler e inspecionadas. Capa, resumo,
quadro editorial, sumário, quatro capítulos, equações, tabela, figura e bibliografia
estão legíveis e sem sobreposições/truncamento. Foram conferidas individualmente as
páginas alteradas pela inclusão do relatório final:4,14,33,43,44. O resumo mantém
palavras-chave na mesma página. A figura vetorial foi examinada também em tamanho maior.

Compilação final sem caixas Overfull ou referências/citações indefinidas. Os 30
números de equação de C05, a figura4.1 e suas remissões são consistentes. Textos de
passagem dos capítulos anteriores foram atualizados para refletir C05 concluído.

## Estado e limites

README, estado JSON e quadro editorial indicam C01–C05 concluídos e C06 em andamento.
Este marco valida a resposta tensorial, suas convenções e integração numérica;
não declara massas inferidas, SBC, população escalar ou aplicação observacional.
Fontes, scripts, resultados e configuração integram o manifesto. PDFs de terceiros
permanecem locais e não entram na publicação automática.
