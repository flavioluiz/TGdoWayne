# Validação de C04 / v0.4.0

Data: 10/09/2026. PDF cumulativo: **36 páginas A4**, 421287 bytes.
SHA-256: `1b35fc07e946ab78782598e7fd095ab6a9cc1e308912940b46ee09001a4553a0`.

## Verificação científica e computacional

As 19 verificações de `scripts/reproduzir_tg.py` passaram em ambiente virtual local
com SymPy1.14.0 e mpmath1.3.0. Doze testes cobrem curvatura por duas rotas, todas as
256 componentes, simetrias, Bianchi algébrico e diferencial, perturbações de coordenadas,
parametrizações gerais, menores, postos, vínculo escalar, limites e transcrições TG/Hyun.
Sete testes independentes partem da conexão com dez amplitudes e quatro componentes
de q livres, conferindo Einstein, duas assinaturas, dinâmica FP e normalização histórica.

O registro `results/C04/validacao.json` foi gerado e reconferido por `--check`.
Uma cópia separada de `src/`, `tests/`, do script e do registro passou os mesmos 19 testes
quando executada fora da raiz. Isso verifica a resolução dos imports e caminhos;
não é uma reprodução em outro sistema operacional. A execução do workflow Linux
ocorre após o envio da tag e condiciona a publicação do release.

O capítulo apresenta as provas e seus domínios, incluindo menores não nulos para todo
omega diferente de zero e k real. Os exemplos racionais prévios são regressões, não
substitutos da prova geral. A tabela numérica foi confrontada com o JSON preliminar
em precisão decimal ampliada. A auditoria histórica distingue assinatura, Riemann,
tetrada, amplitude métrica/traço invertido e massa operacional. O diagnóstico dos
prefatores não é apresentado como errata editorial confirmada.

## Revisão editorial

As 36 páginas foram renderizadas com Poppler. Um revisor independente examinou pp.1–20,
incluindo imagens ampliadas do resumo e sumário; a raiz examinou pp.21–36 e as 41 novas
equações. Corrigiu-se o resumo para manter palavras-chave na mesma página e o comando
literal `--check` para preservar dois hífens copiáveis. A página alterada foi renderizada
e inspecionada novamente; extração textual confirmou os dois hífens.

Capa, metadados, sumário, quadro de capítulos, equações, matrizes, tabela e referências
estão legíveis, sem truncamentos ou sobreposições. Compilação sem caixas Overfull e sem
citações/referências indefinidas. O relatório independente está em
`docs/fundamentos/revisao_editorial_C04.md`.

## Estado e integridade

README, `project_status.json` e quadro editorial identificam C01–C04 concluídos e C05 em
andamento. As dependências, fontes, testes, resultados e documentação entram no manifesto;
PDFs de terceiros permanecem locais. Os artefatos C01–C03 publicados são preservados.
Não há campanha de inferência estatística concluída nesta versão.
