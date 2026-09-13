# Artigo metodológico para revisão — C12

O manuscrito em inglês apresenta a comparação entre compressão, aproximação
normal e resposta dispersiva, com a campanha C11 como resultado central e as
validações C07–C10 como contexto. As identificações acadêmicas são provisórias;
não houve submissão, aceitação ou definição de periódico.

- Fonte: `manuscript.tex`.
- PDF: `manuscript.pdf`.
- Figura: `figures/information.pdf`, regenerada por `scripts/figura_artigo_c12.py`.
- Auditoria de números e semânticas: `scripts/auditar_narrativa_c12.py`.

Na raiz, `make article` compila com pdfLaTeX/Biber, exige referências resolvidas
e ausência de caixas excedentes e preserva o PDF. A figura usa somente as 500
realizações da priori por grupo, sem misturar as 96 verdades fixas.

A dissertação contém as derivações ampliadas, referências e histórico de
validação. A disponibilidade dos arquivos está declarada no manuscrito;
a restauração por hashes não é confundida com uma reexecução física integral.
